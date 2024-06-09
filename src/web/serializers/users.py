from datetime import datetime

from django.utils.translation import ugettext_lazy as _
from django_countries.serializers import CountryFieldMixin
from rest_framework import serializers

from my_chargebee.models import Customer, Subscription
from web.constants import MOBILE_DATE_FORMAT, PostStatusE, PostTypeE, \
    UserTypeE, UserOriginE, get_pro_language_choices, UserStatusE
from web.models import UserProfile, Place, UserImage
from web.serializers.common import DynamicFieldsModelSerializer
from web.serializers.nested import PlaceSerializer
from web.serializers.utils import (BadgeExpiryDateMsField, HasBadgeDataField,
                                   ImageUrlField, ImageUrlThumbField,
                                   ToReprMixin)
from web.utils.message_utils import EmailCollection
from web.utils.pro_utils_cms import update_owner_venue
from reports.models import BlockUser


class MinimalUserSerializer(DynamicFieldsModelSerializer):
    id = serializers.UUIDField(source='pk')
    has_badge = HasBadgeDataField(source="*")
    badge_expiry_date_ms = BadgeExpiryDateMsField(source="*")

    image = ImageUrlField()

    full_name = serializers.SerializerMethodField()
    short_name = serializers.CharField(source='username')

    def get_full_name(self, obj):
        return obj.full_name if obj.full_name else obj.username

    class Meta:
        model = UserProfile
        fields = ['id', 'has_badge', 'badge_expiry_date_ms', 'full_name',
                  'short_name', 'modified_time', 'image', 'type']


class UserSerializerForCombinedSearch(MinimalUserSerializer):
    type = serializers.SerializerMethodField()

    def get_type(self, obj):
        return 'user'

    class Meta:
        model = UserProfile
        fields = ['id', 'has_badge', 'badge_expiry_date_ms', 'full_name',
                  'short_name', 'modified_time', 'image', 'type']


class UserSerializer(ToReprMixin, MinimalUserSerializer):
    id = serializers.UUIDField(source="pk")
    created_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)
    modified_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)

    image = ImageUrlField()
    image_thumb = ImageUrlThumbField(source="image")
    company_image = ImageUrlThumbField()

    author = serializers.CharField(source='author_username')
    author_id = serializers.UUIDField()
    author_avatar_url = ImageUrlThumbField(source="author_image")

    has_badge = HasBadgeDataField(source="*")
    badge_expiry_date_ms = BadgeExpiryDateMsField(source="*")
    badge_expiry_date = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    is_premium_venue_subscriber = serializers.SerializerMethodField()

    post_number = serializers.SerializerMethodField()
    wine_post_number = serializers.SerializerMethodField()
    star_review_number = serializers.SerializerMethodField()
    all_posts_number = serializers.SerializerMethodField()

    currency = serializers.SerializerMethodField()

    def get_badge_expiry_date(self, obj):
        badge_expiry_date_ms = obj.get_badge_expiry_date_ms()
        if not badge_expiry_date_ms:
            return None

        return datetime.fromtimestamp(int(round(badge_expiry_date_ms / 1000)))

    def get_is_owner(self, obj):
        return (obj.type == UserTypeE.OWNER)

    def get_is_premium_venue_subscriber(self, obj):
        return (obj.type == UserTypeE.OWNER)

    def get_post_number(self, obj):
        return obj.posts_authored.filter(status=PostStatusE.PUBLISHED).exclude(
            type=PostTypeE.WINE
        ).count()

    def get_wine_post_number(self, obj):
        return obj.posts_authored.filter(
            type=PostTypeE.WINE, status=PostStatusE.PUBLISHED
        ).count()

    def get_star_review_number(self, obj):
        return obj.posts_authored.filter(
            type=PostTypeE.WINE, status=PostStatusE.PUBLISHED,
            is_star_review=True
        ).count()

    def get_all_posts_number(self, obj):
        return obj.posts_authored.filter(status=PostStatusE.PUBLISHED).count()

    def get_currency(self, obj):
        return obj.currency if obj.currency else 'EUR'

    class Meta:
        model = UserProfile
        fields = ['id', 'type', 'status', 'is_confirmed', 'username',
                  'full_name', 'email', 'description', 'website_url',
                  'notify_likes', 'notify_drank_it_toos', 'notify_comments',
                  'notify_wine_reviewed', 'push_user_token', 'push_user_id',
                  'lang', 'currency', 'has_badge', 'badge_expiry_date_ms',
                  'image', 'image_thumb', 'company_image', 'author',
                  'author_id', 'badge_expiry_date', 'created_time',
                  'modified_time', 'author_avatar_url', 'is_owner',
                  'post_number', 'wine_post_number', 'likevote_number',
                  'comment_number', 'drank_it_too_number',
                  'star_review_number', 'all_posts_number',
                  'is_premium_venue_subscriber']


class UserWithVenuesSerializer(UserSerializer):
    venues = serializers.SerializerMethodField()

    def get_venues(self, obj):
        venues = obj.place_owner.order_by('-created_time')
        serializer = PlaceSerializer(venues,
                                     context=self.context,
                                     many=True)

        return serializer.data

    class Meta:
        model = UserProfile
        fields = UserSerializer.Meta.fields + ['venues']


class UserProfileOptionsSerializer(serializers.Serializer):
    get_likes = serializers.BooleanField(required=False)
    get_drank_it_toos = serializers.BooleanField(required=False)
    get_comments = serializers.BooleanField(required=False)
    get_general_posts = serializers.BooleanField(required=False)
    get_wineposts = serializers.BooleanField(required=False)
    get_star_reviews = serializers.BooleanField(required=False)
    get_posts = serializers.BooleanField(required=False)

    like_last_id = serializers.IntegerField(required=False)
    dit_last_id = serializers.IntegerField(required=False)
    post_last_id = serializers.IntegerField(required=False)
    sr_last_id = serializers.IntegerField(required=False)

    limit = serializers.IntegerField(required=False)


class UserProfileAnyOptionsSerializer(UserProfileOptionsSerializer):
    user_id = serializers.CharField(required=False)
    username = serializers.CharField(required=False)


class RightPanelUserSerializer(serializers.ModelSerializer):
    # place_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            "id",
            "password",
            "last_login",
            "is_superuser",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "is_active",
            "date_joined",
            "username",
            "key",
            "push_user_id",
            "push_user_token",
            "created_time",
            "modified_time",
            "last_failed_attempt_time",
            "failed_attempts_no",
            "secondary_emails",
            "full_name",
            "description",
            "type",
            "origin",
            "status",
            "is_archived",
            "is_confirmed",
            "is_owner",
            "website_url",
            "wine_post_number",
            "comment_number",
            "post_number",
            "likevote_number",
            "drank_it_too_number",
            "star_review_number",
            "activation_reminder_sent_number",
            "activation_reminder_sent_last_date",
            "notify_likes",
            "notify_drank_it_toos",
            "notify_comments",
            "notify_wine_reviewed",
            "has_badge",
            "has_p_once",
            "has_p_monthly",
            "badge_expiry_date_ms",
            "badge_last_updated_date_ms",
            "badge_last_purchase_date_ms",
            "p_once_expiry_date_ms",
            "p_once_last_updated_date_ms",
            "p_once_last_purchase_date_ms",
            "p_monthly_expiry_date_ms",
            "p_monthly_expiry_date_ms_apple",
            "p_monthly_expiry_date_ms_android",
            "p_monthly_last_updated_date_ms",
            "p_monthly_last_updated_date_ms_apple",
            "p_monthly_last_updated_date_ms_android",
            "p_monthly_last_purchase_date_ms",
            "p_monthly_last_purchase_date_ms_apple",
            "p_monthly_last_purchase_date_ms_android",
            "lang",
            "currency",
            "formitable_url",
            "formitable_uid",
            "customer",
            "author",
            "last_modifier",
            "image",
            "company_image",
            "groups",
            "user_permissions",
            # "place_id"
        )

    # def validate_place_id(self, value):
    #     return value

    def validate(self, attrs):
        if not attrs.get('email'):
            raise serializers.ValidationError("Email required")
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data['author'] = request.user
        # ToDo: need exception here like ValidationError
        validated_data['status'] = UserStatusE.ACTIVE
        validated_data['type'] = UserTypeE.OWNER
        validated_data['is_active'] = True

        # ToDo: Validation error is preferred but doesn't work here
        # if not self.initial_data.get('place_id'):
        #     raise serializers.ValidationError("Place_id is required")

        # CustomerID + Venue + Subscription are tagged as mandatory fields
        # on FE
        place = Place.active.get(pk=self.initial_data.get('place_id'))
        subscription = self.initial_data.get('subscription')
        already_subscribed_places = Place.active.filter(
            subscription=subscription
        ).exclude(
            owner=None
        )
        if not already_subscribed_places:
            place.subscription_id = subscription
            place.save()
        else:
            res = serializers.ValidationError(
                {'message': 'Subscription ID is already assigned to another '
                            'place'})
            res.status_code = 400
            raise res

        user = super(RightPanelUserSerializer, self).create(
            validated_data)

        profile_photo = self.initial_data.get('profile_photo')
        if profile_photo:
            user_image = UserImage(image_file=profile_photo, user=user)
            user_image.save()
            user.image = user_image
            user.save()
            user.refresh_from_db()

        update_owner_venue(user, place)
        EmailCollection().send_activation_email(user)

        return user


class RightPanelUserReadSerializer(CountryFieldMixin,
                                   serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    email = serializers.EmailField(source='owner.email')
    full_name = serializers.CharField(max_length=255, source='owner.full_name')
    username = serializers.CharField(max_length=255, source='owner.username')
    secondary_emails = serializers.ListField(source='owner.secondary_emails')
    website_url = serializers.URLField(source='owner.website_url')
    lang = serializers.CharField(max_length=2, source='owner.lang')
    origin = serializers.SerializerMethodField()
    customer_id = serializers.CharField(max_length=255,
                                        source='owner.customer_id')
    profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = (
            'id',
            'name',
            'email',
            'full_name',
            'username',
            'secondary_emails',
            'website_url',
            'lang',
            'origin',
            'type',
            'customer_id',
            'subscription',
            'profile_photo'
        )

    def get_type(self, obj):
        return UserTypeE.names.get(obj.owner.type)

    def get_origin(self, obj):
        return UserOriginE.names.get(obj.owner.origin)

    def get_profile_photo(self, obj):
        return obj.owner.get_images()['image_thumb']

    # def get_subscription(self, obj):
    #     return my_chargebee.models.Subscription.objects.filter(
    #         customer_id=obj.customer).values_list('id', 'plan_id',
    #                                               'status').first()

    # def get_venue(self, obj):
    #     return Place.active.filter(owner=obj).values_list('name', flat=True)


class RightPanelUserUpdateSerializer(serializers.ModelSerializer):
    # define owner fields
    email = serializers.EmailField(source='owner.email', required=False)
    full_name = serializers.CharField(source='owner.full_name', required=False)
    username = serializers.CharField(source='owner.username', required=False)
    secondary_emails = serializers.ListField(source='owner.secondary_emails',
                                             required=False)
    website_url = serializers.URLField(source='owner.website_url',
                                       required=False)
    lang = serializers.ChoiceField(choices=get_pro_language_choices(),
                                   source='owner.lang',
                                   required=False)
    origin = serializers.ChoiceField(list(UserOriginE.names.values()),
                                     source='owner.origin',
                                     required=False)
    customer_id = serializers.CharField(max_length=255,
                                        source='owner.customer_id',
                                        required=False)

    subscription_id = serializers.CharField(max_length=255,
                                            required=False)
    venue_id = serializers.IntegerField(required=False)
    type = serializers.ChoiceField(list(UserTypeE.names.values()),
                                   required=False)
    profile_photo = serializers.ImageField(source='owner.image.image_file',
                                           required=False)

    def validate_email(self, value):
        if not value:
            return None
        if self.instance.owner:
            users_count = UserProfile.objects.filter(email=value).exclude(
                id=self.instance.owner.id).count()
        else:
            users_count = UserProfile.objects.filter(email=value).count()
        if users_count > 0:
            msg = _('Email already exists.')
            raise serializers.ValidationError(msg)
        else:
            return value

    def validate_username(self, value):
        if not value:
            return None
        if self.instance.owner:
            users_count = UserProfile.objects.filter(username=value).exclude(
                id=self.instance.owner.id).count()
        else:
            users_count = UserProfile.objects.filter(username=value).count()
        if users_count > 0:
            msg = _('A user with that username already exists.')
            raise serializers.ValidationError(msg)
        else:
            return value

    def validate_customer_id(self, value):
        if not value or value == '':
            if self.instance and self.instance.subscription:
                self.instance.subscription = None
                self.instance.save()
            return None

        try:
            customer = Customer.objects.get(id=value)
        except Customer.DoesNotExist:
            msg = _('This Chargebee Customer ID is invalid.')
            raise serializers.ValidationError(msg)

        if self.instance.owner:
            customer_users_count = UserProfile.objects.filter(
                customer=value
            ).exclude(id=self.instance.id).count()

            for establishment in self.instance.owner.place_owner.all():
                if establishment.subscription \
                        and establishment.subscription.customer != customer:
                    establishment.subscription = None

        else:
            customer_users_count = UserProfile.objects.filter(  # noqa
                customer=value
            ).count()

        # commented until one user - more establishemnts is implemented
        # if customer_users_count > 0:
        #     msg = _('Customer ID is already assigned to another user.')
        #     raise serializers.ValidationError(msg)

        return customer.id

    def validate_subscription_id(self, value):
        customer_id = self.initial_data.get('customer_id') if \
            self.initial_data.get('customer_id') else \
            self.instance.owner.customer_id

        if not value or not customer_id or value == '':
            return

        try:
            Subscription.objects.get(id=value)
        except Subscription.DoesNotExist:
            msg = _('Invalid subscription ID.')
            raise serializers.ValidationError(msg)

        if Subscription.objects.get(id=value).customer_id != customer_id:
            msg = _('The Customer ID assigned to this Subscription is '
                    'other than the Customer ID assigned to the user.')
            raise serializers.ValidationError(msg)

        if self.instance and value:
            subscription_places_count = Place.active.filter(
                subscription=value
            ).exclude(id=self.instance.id).count()

        else:
            subscription_places_count = Place.active.filter(
                subscription=value
            ).count()

        if subscription_places_count > 0:
            msg = _('Subscription ID is already assigned '
                    'to another place.')
            raise serializers.ValidationError(msg)

        return value

    def validate(self, attrs):
        # reminder about not supported Japanese Pro Raisin

        if attrs.get('owner') and attrs.get('owner').get('lang') == 'JA':
            raise serializers.ValidationError(
                _("PRO is not supported for Japanese language.")
            )

        # force establishment input for customer
        if not attrs.get('venue_id'):
            raise serializers.ValidationError(
                _("You must connect this owner to an establishment")
            )
        return attrs

    def update(self, instance, validated_data):
        if validated_data.get('owner'):
            instance.owner.email = validated_data.get(
                'owner').get('email',
                             instance.owner.email)
            instance.owner.full_name = validated_data.get(
                'owner').get('full_name',
                             instance.owner.full_name)
            instance.owner.username = validated_data.get(
                'owner').get('username',
                             instance.owner.username)
            instance.owner.secondary_emails = validated_data.get(
                'owner').get('secondary_emails',
                             instance.owner.secondary_emails)
            instance.owner.website_url = validated_data.get(
                'owner').get('website_url',
                             instance.owner.website_url)
            instance.owner.lang = validated_data.get(
                'owner').get('lang',
                             instance.owner.lang)

            if validated_data.get('owner').get('origin', None):
                user_origin_integers = list(UserOriginE.names.keys())
                user_origin_words = list(UserOriginE.names.values())
                instance.owner.origin = user_origin_integers[
                    user_origin_words.index(
                        validated_data.get('owner').get('origin')
                    )
                ]

            if validated_data.get('owner').get('type', None):
                user_type_integers = list(UserTypeE.names.keys())
                user_type_words = list(UserTypeE.names.values())
                instance.owner.type = user_type_integers[
                    user_type_words.index(
                        validated_data.get('owner').get('type')
                    )
                ]

            instance.owner.customer_id = validated_data.get(
                'customer_id',
                instance.owner.customer_id)

            if validated_data.get('owner').get('image') and \
                    validated_data.get('owner').get('image').get('image_file'):
                user_image = UserImage(
                    image_file=validated_data.get(
                        'owner').get(
                        'image').get(
                        'image_file'
                    ),
                    user=instance.owner)
                user_image.save()
                instance.owner.image = user_image

            instance.owner.save()

        # unlink current owner+subscription from an old_venue and
        # link current owner+subscription to a new Venue
        # if Venue has been changed
        if validated_data.get('venue_id') != instance.id:
            new_venue = Place.objects.get(
                id=self.validated_data.get('venue_id')
            )
            new_venue.subscription_id = validated_data.get(
                'subscription_id', instance.subscription_id)
            new_venue.owner = instance.owner
            new_venue.save()

            instance.subscription = None
            # until each UserProfile has only one Establishment by UX/UI
            instance.owner = None
            instance.save()
            return new_venue
        else:
            instance.subscription_id = validated_data.get(
                'subscription_id',
                instance.subscription_id)
            instance.save()
        return instance

    class Meta:
        model = Place
        fields = (
            'email',
            'full_name',
            'username',
            'secondary_emails',
            'website_url',
            'lang',
            'origin',
            'type',
            'customer_id',
            'subscription_id',
            'venue_id',
            'profile_photo'
        )


class BlockUserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = BlockUser
        fields = [
            'block_user'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        validated_data['user'] = user
        return BlockUser.objects.create(**validated_data)
