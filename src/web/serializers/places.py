import pycountry
from django.contrib.contenttypes.models import ContentType
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.core.cache import cache
from django.db.models import Q
from django_countries.serializers import CountryFieldMixin
from rest_framework import serializers
from rest_framework.utils import json

from my_chargebee.models import Subscription, Customer, PaymentSource
from raisin import settings
from web.constants import MOBILE_DATE_FORMAT, PLACE_IMAGES_LIMIT, UserTypeE, PLACE_GEO_CACHE_KEY, PostTypeE
from web.helpers.wineposts import WinepostHelper
from web.models import Comment, LikeVote, Place, PostImage, UserProfile, \
    CmsAdminComment
from web.serializers.comments_likes import AdminCommentSerializer
from web.serializers.common import DynamicFieldsModelSerializer
from web.serializers.nested import PlaceSerializer
from web.serializers.utils import (BadgeExpiryDateMsField, DistanceField,
                                   HasBadgeDataField, ImageUrlThumbField, MentionsField, ToReprMixin, ImageUrlField)
from web.serializers.wineposts import ClosestWinePostSerializer
from web.utils import api_blocked_users
from web.utils.model_app_legacy import api_status_place
from web.utils.model_tools import beautify_place_name, strip_tags
from web.utils.upload_tools import aws_url


class BasePlaceSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    posted_time = serializers.SerializerMethodField()
    relative_time = serializers.SerializerMethodField()

    def get_time_source(self, obj):
        return obj.modified_time

    def get_avatar_source(self, obj):
        return obj.author

    def get_posted_time(self, obj):
        return self.get_time_source(obj).strftime('%d-%m-%Y %H:%M')

    def get_relative_time(self, obj):
        return naturaltime(self.get_time_source(obj))

    def get_avatar(self, obj):
        return aws_url(self.get_avatar_source(obj).image, thumb=True)


class PlaceLikeSerializer(BasePlaceSerializer):
    username = serializers.CharField(
        read_only=True, source="author.username"
    )
    full_name = serializers.CharField(
        read_only=True, source="author.full_name"
    )

    class Meta:
        model = LikeVote
        fields = ['avatar', 'username', 'full_name', 'posted_time',
                  'relative_time']


class PlaceReviewSerializer(BasePlaceSerializer):
    username = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    description = serializers.SerializerMethodField()
    unread_messages = serializers.SerializerMethodField()

    def get_time_source(self, obj):
        place_id = self.context['request'].query_params.get('place_id', None)
        qs = Comment.objects.filter(
            place_id=place_id,
            author=obj,
            is_archived=False
        ).order_by('-modified_time')

        self.latest_comment = qs.first()
        self.unread_messages = qs.filter(read_receipts=None).count()

        return self.latest_comment.modified_time

    def get_avatar_source(self, obj):
        return obj

    def get_description(self, obj):
        return self.latest_comment.description

    def get_unread_messages(self, obj):
        return self.unread_messages

    class Meta:
        model = UserProfile
        fields = ['id', 'avatar', 'username', 'full_name', 'posted_time',
                  'relative_time', 'description', 'unread_messages']


class PlaceCommentSerializer(BasePlaceSerializer):
    username = serializers.CharField(
        read_only=True, source="author.username"
    )
    full_name = serializers.CharField(
        read_only=True, source="author.full_name"
    )
    description = serializers.CharField(read_only=True)
    editable_by_owner = serializers.SerializerMethodField()

    def get_editable_by_owner(self, obj):
        return obj.author == self.context['request'].user

    class Meta:
        model = Comment
        fields = ['id', 'avatar', 'username', 'full_name', 'posted_time',
                  'relative_time', 'description', 'editable_by_owner']


class CommentSerializer(serializers.ModelSerializer):
    place_id = serializers.PrimaryKeyRelatedField(
        queryset=Place.objects.all(), source='place', write_only=True
    )

    in_reply_to_id = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        source='in_reply_to',
        write_only=True,
        allow_null=False
    )

    class Meta:
        model = Comment
        fields = ['id', 'author_id', 'place_id', 'in_reply_to_id',
                  'description']


class PlaceWithExtraDataSerializer(PlaceSerializer):
    venue_owner_id = serializers.UUIDField(source="owner_identifier")
    i_like_it = serializers.SerializerMethodField()
    street_address = serializers.SerializerMethodField()
    closing_dates = serializers.JSONField(source="format_closing_dates")
    opening_hours = serializers.JSONField(source="format_opening_hours")

    def get_i_like_it(self, obj):
        if self.context['request'].user.is_anonymous:
            return False

        return LikeVote.active.filter(
            place=obj,
            author=self.context['request'].user
        ).exists()

    def get_street_address(self, obj):
        return obj.full_street_address if obj.full_street_address else obj.street_address  # noqa

    class Meta:
        model = Place
        fields = PlaceSerializer.Meta.fields + [
            'pin_latitude', 'pin_longitude', 'wl_added', 'free_glass',
            'free_glass_last_action_date', 'free_glass_signup_date',
            'i_like_it', 'street_address', 'closing_dates', 'opening_hours',
            'impression_number', 'visit_number', 'phone_number']


class PlaceGeoSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    is_venue = serializers.BooleanField(source='place_subscribed')
    street_address = serializers.CharField(source='place_street_address')
    main_image = ImageUrlThumbField()
    closing_dates = serializers.JSONField(source="format_closing_dates")
    opening_hours = serializers.JSONField(source="format_opening_hours")
    description = serializers.SerializerMethodField()
    latitude = serializers.FloatField(source='pin_latitude')
    longitude = serializers.FloatField(source='pin_longitude')
    images = serializers.SerializerMethodField()

    def get_street_address(self, obj):
        return obj.full_street_address if obj.full_street_address else obj.street_address

    def get_name(self, obj):
        return beautify_place_name(obj.name)

    def get_description(self, obj):
        return strip_tags(obj.description)

    def get_images(self, obj):
        if not obj.place_subscribed:
            return []

        # filters = {'is_archived': False, 'image_area__isnull': not obj.owner}

        # place_images = obj.place_images.filter(**filters)
        # place_images_no = place_images.count()
        # posts_images = []
        #
        # if place_images_no < PLACE_IMAGES_LIMIT:
        #     limit = PLACE_IMAGES_LIMIT - place_images_no
        #     q_f = Q(author=obj.owner) | Q(author__type=UserTypeE.ADMINISTRATOR)
        #     posts_images = PostImage.active.filter(post__place=obj).\
        #         filter(q_f).order_by('-modified_time')[0:limit]

        return [aws_url(image) for image in obj.place_images.all()]

    def to_representation(self, value):
        ret = super().to_representation(value)

        if not value.owner:
            ret['closest_open_hours'] = {}
            ret['is_open_now'] = False
            ret['is_open_later'] = False
            ret['slot_open_now'] = 0
        else:
            extra_data = value.check_place_open_and_opening_hours_by_tz_data()
            ret['closest_open_hours'] = extra_data['closest_open_hours']
            ret['is_open_now'] = extra_data['is_open_now']
            ret['is_open_later'] = extra_data['is_open_later']
            ret['slot_open_now'] = extra_data['slot_open_now']

        return ret

    class Meta:
        model = Place
        # fields = ('id', 'name')
        fields = ['id', 'name', 'latitude', 'longitude', 'is_venue',
                  'closing_dates', 'opening_hours', 'street_address',
                  'main_image', 'comment_number', 'likevote_number',
                  'is_bar', 'is_restaurant', 'is_wine_shop', 'images',
                  'city', 'country', 'description', 'zip_code', 'tz_name']


class MinimalPlaceSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    is_venue = serializers.SerializerMethodField()
    street_address = serializers.SerializerMethodField()
    main_image = ImageUrlThumbField()
    closing_dates = serializers.JSONField(source="format_closing_dates")
    opening_hours = serializers.JSONField(source="format_opening_hours")
    images = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    latitude = serializers.FloatField(source='pin_latitude')
    longitude = serializers.FloatField(source='pin_longitude')

    # overriden fields
    likevote_number = serializers.SerializerMethodField()
    comment_number = serializers.SerializerMethodField()

    def get_name(self, obj):
        return beautify_place_name(obj.name)

    def get_is_venue(self, obj):
        return obj.is_subscriber()

    def get_street_address(self, obj):
        return obj.full_street_address if obj.full_street_address else obj.street_address  # noqa

    def get_images(self, obj):
        if not obj.is_subscriber():
            return []

        filters = {'is_archived': False, 'image_area__isnull': not obj.owner}

        place_images = obj.place_images.filter(**filters)
        place_images_no = place_images.count()
        posts_images = []

        if place_images_no < PLACE_IMAGES_LIMIT:
            limit = PLACE_IMAGES_LIMIT - place_images_no
            q_f = Q(author=obj.owner) | Q(author__type=UserTypeE.ADMINISTRATOR)
            posts_images = PostImage.active.filter(post__place=obj).\
                filter(q_f).order_by('-modified_time')[0:limit]

        return [aws_url(i) for i in place_images] + [aws_url(i) for i in posts_images] # noqa

    def get_description(self, obj):
        return strip_tags(obj.description)

    def get_likevote_number(self, obj):
        # except likes from blocked users
        return api_blocked_users.get_likevotes_number(self=self, obj=obj)

    def get_comment_number(self, obj):
        # except comments from blocked users
        return api_blocked_users.get_comments_number(self=self, obj=obj)

    def to_representation(self, value):
        place_cache_key = PLACE_GEO_CACHE_KEY.format(value.id)
        cache_value = cache.get(place_cache_key)
        if not cache_value:
            ret = super().to_representation(value)
            cache.set(place_cache_key, ret)
        else:
            ret = cache_value

        if not value.owner:
            ret['closest_open_hours'] = {}
            ret['is_open_now'] = False
            ret['is_open_later'] = False
            ret['slot_open_now'] = 0
        else:
            extra_data = value.check_place_open_and_opening_hours_by_tz_data()
            ret['closest_open_hours'] = extra_data['closest_open_hours']
            ret['is_open_now'] = extra_data['is_open_now']
            ret['is_open_later'] = extra_data['is_open_later']
            ret['slot_open_now'] = extra_data['slot_open_now']

        return ret

    class Meta:
        model = Place
        fields = ['id', 'name', 'latitude', 'longitude', 'is_venue',
                  'closing_dates', 'opening_hours', 'street_address',
                  'main_image', 'comment_number', 'likevote_number',
                  'is_bar', 'is_restaurant', 'is_wine_shop', 'images',
                  'city', 'country', 'description', 'zip_code', 'tz_name']


class MinimalPlace2Serializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    is_venue = serializers.SerializerMethodField()
    street_address = serializers.SerializerMethodField()
    main_image = ImageUrlThumbField()
    closing_dates = serializers.JSONField(source="format_closing_dates")
    opening_hours = serializers.JSONField(
        source="format_opening_hours")  # 2 sec for 500 items
    description = serializers.SerializerMethodField()
    latitude = serializers.FloatField(source='pin_latitude')
    longitude = serializers.FloatField(source='pin_longitude')
    images = serializers.SerializerMethodField()

    # overriden fields
    # likevote_number = serializers.SerializerMethodField()
    # comment_number = serializers.SerializerMethodField()

    def get_likevote_number(self, obj):
        # except likes from blocked users
        return obj.likevotes_count

    def get_comment_number(self, obj):
        # except comments from blocked users
        return obj.comments_count

    class Meta:
        model = Place
        fields = ['id', 'name', 'is_venue', 'street_address', 'main_image',
                  'closing_dates', 'opening_hours',
                  'description', 'latitude', 'longitude', 'comment_number',
                  'likevote_number',
                  'is_bar', 'comment_number', 'is_wine_shop', 'is_restaurant',
                  'images',
                  'city', 'country', 'description', 'zip_code', 'tz_name']

    def get_name(self, obj):
        return beautify_place_name(obj.name)

    def get_is_venue(self, obj):
        return obj.is_subscriber()

    def get_street_address(self, obj):
        return obj.full_street_address \
            if obj.full_street_address \
            else obj.street_address

    def get_description(self, obj):
        return strip_tags(obj.description)

    def get_images(self, obj):
        if not obj.is_subscriber():
            return []

        if obj.owner:
            place_images = obj.test_place_images_with_area
        else:
            place_images = obj.test_place_images_without_area
        place_images_list = [aws_url(i) for i in
                             place_images[:PLACE_IMAGES_LIMIT] if i]

        place_images_no = len(place_images_list)
        posts_images = []

        if place_images_no < PLACE_IMAGES_LIMIT:
            limit = PLACE_IMAGES_LIMIT - place_images_no
            q_f = Q(author=obj.owner) | Q(author__type=UserTypeE.ADMINISTRATOR)
            posts_images = PostImage.active.filter(post__place=obj). \
                filter(q_f).order_by('-modified_time')[0:limit]

        return place_images_list + [aws_url(i) for i in posts_images]


class PlaceWithLocationSerializer(PlaceWithExtraDataSerializer):
    distance = DistanceField()

    class Meta:
        model = Place
        fields = PlaceWithExtraDataSerializer.Meta.fields + ['distance']


class FullPlaceSerializer(PlaceWithExtraDataSerializer):
    author = serializers.UUIDField(source="author.username")
    author_id = serializers.UUIDField(source="author.id")
    author_avatar_url = ImageUrlThumbField(source="author.image")
    author_has_badge = HasBadgeDataField(source="author")
    author_badge_expiry_date_ms = BadgeExpiryDateMsField(source="author")

    created_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)
    modified_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)

    owner = serializers.UUIDField(source="owner_username")
    owner_id = serializers.UUIDField(source="owner_identifier")
    owner_avatar_url = ImageUrlThumbField(source="owner_image")

    modifier = serializers.UUIDField(source="last_modifier_username")
    modifier_id = serializers.UUIDField(source="last_modifier_identifier")
    modifier_avatar_url = ImageUrlThumbField(source="last_modifier_image")

    expert = serializers.UUIDField(source="expert_username")
    expert_id = serializers.UUIDField(source="expert_identifier")
    expert_avatar_url = ImageUrlThumbField(source="expert_image")

    mentions = MentionsField(source="user_mentions")
    holidays = serializers.JSONField(source='holidays_date')
    holidays_range = serializers.JSONField(source='holidays_date_range')

    def to_representation(self, obj):
        data = super().to_representation(obj)

        place_status = api_status_place(obj)
        data['status'] = place_status['status']
        data['in_doubt'] = place_status['in_doubt']

        return data

    class Meta:
        model = Place
        fields = PlaceWithExtraDataSerializer.Meta.fields + [
            'author', 'author_id', 'owner_id', 'owner', 'author_avatar_url',
            'author_has_badge', 'author_badge_expiry_date_ms',
            'owner_avatar_url', 'modifier', 'modifier_id',
            'modifier_avatar_url', 'expert', 'expert_id', 'expert_avatar_url',
            'created_time', 'modified_time', 'status', 'in_doubt',
            'is_archived', 'website_url', 'email', 'total_wl_score',
            'sticker_sent', 'social_facebook_url', 'social_twitter_url',
            'social_instagram_url', 'mentions', 'holidays', 'holidays_range']


class VenueWithWinePostSerializer(ToReprMixin, DynamicFieldsModelSerializer):
    """
    Define venue place serializer
    """
    name = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    wine = serializers.SerializerMethodField()
    i_like_it = serializers.SerializerMethodField()
    main_image = ImageUrlField()

    # uncomment for testing purpose if needed and add field to 'fields' in Meta
    distance = serializers.SerializerMethodField()

    def get_name(self, obj):
        return beautify_place_name(obj.name)

    def get_latitude(self, obj):
        return obj.point.y

    def get_longitude(self, obj):
        return obj.point.x

    def get_wine(self, obj):
        """
        Get the latest wine post
        Apply request search filters if any (optional)
        """
        filters = self.get_winepost_filters()
        search = self.context['request'].query_params.get('search')

        if search:
            filters = filters & Q(
                Q(wine__name__unaccent__icontains=search) |
                Q(wine__domain__unaccent__icontains=search) |
                Q(wine__winemaker__name__unaccent__icontains=search)
            )

        # get latest winepost by created time
        latest_winepost = obj.posts.filter(filters).latest('created_time')

        return ClosestWinePostSerializer(latest_winepost, context={'request': self.context['request']}).data

    def get_i_like_it(self, obj):
        if self.context['request'].user.is_anonymous:
            return False

        return LikeVote.active.filter(
            place=obj,
            author=self.context['request'].user
        ).exists()

    def get_distance(self, obj):
        """
        Get place distance to ref location
        """
        if obj.distance.m < 250:
            # distance in meters (e.g. 13 m, 157 m)
            return str(obj.distance.m) + " m"

        if obj.distance.m < 1000:
            # round to nearest 250m (e.g. )
            return str(obj.distance.m // 250 * 250) + " m"

        if obj.distance.km < 1000:
            # round to nearest .25 km (e.g. 4.25 km, 85.5 km, 543.75 km)
            return str(round(obj.distance.km * 4) / 4) + " km"

        # round to nearest 50 km (e.g. 1050 km, 1500 km, 2250 km)
        return str(round(obj.distance.km // 50 * 50)) + " km"

    def get_winepost_filters(self):
        """
        Get winepost filters list:
            - type
            - wine_id
            - is_archived
            - status
        """
        filters = Q(
            Q(type=PostTypeE.WINE) &
            Q(wine_id__isnull=False) &
            Q(is_archived=False) &
            Q(status__in=WinepostHelper.app_winepost_display_statuses)
        )

        return filters

    class Meta:
        model = Place
        fields = ('id', 'name', 'main_image', 'is_bar', 'is_restaurant',
                  'is_wine_shop', 'likevote_number', 'i_like_it', 'wine',
                  'latitude', 'longitude', 'distance', 'subscription')


class FilteredVenueWithWinepostSerializer(VenueWithWinePostSerializer):
    def get_wine(self, obj):
        """
        Override to get the latest wine post
        Apply request search filters if any (optional)
        """
        filters = self.get_winepost_filters()

        wine_name = self.context['request'].query_params.get('wine_name')
        wine_domain = self.context['request'].query_params.get('wine_domain')
        winemaker_name = self.context['request'].query_params.get('winemaker_name')

        if wine_name:
            filters = filters & Q(wine__name__unaccent__icontains=wine_name)

        if wine_domain:
            filters = filters & Q(wine__domain__unaccent=wine_domain)

        if winemaker_name:
            filters = filters & Q(wine__winemaker__name__unaccent=winemaker_name)

        # get latest winepost by created time
        latest_winepost = obj.posts.filter(filters).latest('created_time')

        return ClosestWinePostSerializer(latest_winepost, context={'request': self.context['request']}).data


class PlaceGetSerializer(serializers.Serializer):
    place_id = serializers.IntegerField(required=True)


class WinesForPlaceSerializer(serializers.Serializer):
    place_id = serializers.IntegerField(required=True)
    type = serializers.CharField(required=False)


class RightPanelPlaceSerializer(CountryFieldMixin,
                                serializers.ModelSerializer):
    comments_by_team = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    google_api_key = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = (
            'name',
            'phone_number',
            'is_bar',
            'is_wine_shop',
            'is_restaurant',
            'status',
            'email',
            'website_url',
            'social_facebook_url',
            'social_instagram_url',
            'social_twitter_url',
            'comments_by_team',
            'street_address',
            'full_street_address',
            'house_number',
            'zip_code',
            'city',
            'country',
            'state',
            'country_iso_code',
            'latitude',
            'longitude',
            'point',
            'pin_latitude',
            'pin_longitude',
            'country_old',
            'country_iso_code_old',
            'city_old',
            'images',
            'last_wl_an_time',
            'total_wl_score',
            'missing_info',
            'type_sub',
            'sticker_sent_dates',
            'media_post_date',
            'media_post_url',
            'src_info',
            'google_api_key'
        )

    def get_comments_by_team(self, obj):
        content_type_id = ContentType.objects.get(
            app_label='web', model='place').id
        comments_by_team = CmsAdminComment.objects.filter(
            content_type_id=content_type_id,
            object_id=obj.id).order_by('-id')
        serializer_context = {'request': self.context.get('request')}
        return AdminCommentSerializer(comments_by_team,
                                      many=True,
                                      context=serializer_context).data

    def get_images(self, obj):
        return [aws_url(image) for image in obj.place_images.all()]

    def get_google_api_key(self, obj):
        return settings.GOOGLE_API_KEY


class JSONSerializerField(serializers.Field):
    """Serializer for JSONField -- required to make field writable"""

    def to_representation(self, value):
        json_data = {}
        try:
            json_data = json.loads(value)
        except ValueError as e:
            raise e
        finally:
            return json_data

    def to_internal_value(self, data):
        return json.dumps(data)


class RightPanelCheckSubcriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = (
            'id',
            'name',
            'subscription'
        )


class RightPanelPlaceCustomerSerializer(serializers.ModelSerializer):
    billing_address = JSONSerializerField()
    payment_method = JSONSerializerField()

    class Meta:
        model = Customer
        fields = '__all__'


class RightPanelPlacePaymentSourceSerializer(serializers.ModelSerializer):
    card = JSONSerializerField()

    class Meta:
        model = PaymentSource
        fields = '__all__'


class RightPanelPlaceSubscriptionSerializer(serializers.ModelSerializer):
    shipping_address = JSONSerializerField()
    event_based_addons = JSONSerializerField()
    customer = RightPanelPlaceCustomerSerializer()
    payment_source = serializers.SerializerMethodField()
    billing_info_country = serializers.SerializerMethodField()
    shipping_info_country = serializers.SerializerMethodField()
    subscription_url = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = '__all__'

    def get_billing_info_country(self, obj):
        if obj.customer.billing_address:
            country = obj.customer.billing_address.get('country')
            if country:
                return pycountry.countries.get(alpha_2=country).name.title()
            else:
                return None
        else:
            return None

    def get_shipping_info_country(self, obj):
        if obj.shipping_address:
            country = obj.shipping_address.get('country')
            if country:
                return pycountry.countries.get(alpha_2=country).name.title()
            else:
                return None
        else:
            return None

    def get_payment_source(self, obj):
        if not obj.customer.primary_payment_source_id:
            return None

        payment_source = obj.customer.paymentsource_set.get(
            id=obj.customer.primary_payment_source_id)

        serializer_context = {'request': self.context.get('request')}
        return RightPanelPlacePaymentSourceSerializer(
            payment_source,
            many=False,
            context=serializer_context).data

    def get_subscription_url(self, obj):
        site_name = settings.RAISIN_CHARGEBEE_SITE
        return ('https://' + site_name +
                '.chargebee.com/subscriptions?view_code=all&Subscriptions'
                '.search=' + obj.id)
