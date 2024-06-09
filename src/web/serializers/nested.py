from rest_framework import serializers

from reports.models import BlockUser
from web.models import Place
from web.serializers.common import DynamicFieldsModelSerializer
from web.serializers.utils import ToReprMixin, ImageUrlField, ImageUrlThumbField
from web.utils import api_blocked_users
from web.utils.model_tools import beautify_place_name, strip_tags
from web.utils.time import get_offset_for_tz_name
from web.utils.upload_tools import aws_url


class VenueSerializer(ToReprMixin, DynamicFieldsModelSerializer):
    name = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    i_like_it = serializers.SerializerMethodField()
    main_image = ImageUrlField()
    is_subscribing = serializers.SerializerMethodField()

    # overriden fields
    likevote_number = serializers.SerializerMethodField()

    def get_name(self, obj):
        return beautify_place_name(obj.name)

    def get_latitude(self, obj):
        return obj.point.y

    def get_longitude(self, obj):
        return obj.point.x

    def get_i_like_it(self, obj):
        return obj.get_i_like_it(user=self.context['request'].user)

    # TODO: temporary fix fo iOS needed exactly field with the name 'is_venue' which is override same DB field
    # incorrect naming and for removal
    def get_is_venue(self, obj):
        return obj.is_subscriber()

    def get_is_subscribing(self, obj):
        return obj.is_subscriber()

    def get_likevote_number(self, obj):
        # except likes from blocked users
        return api_blocked_users.get_likevotes_number(self=self, obj=obj)

    class Meta:
        model = Place
        fields = (
            'id', 'name', 'main_image', 'is_bar', 'is_restaurant', 'is_wine_shop', 'likevote_number',
            'i_like_it', 'latitude', 'longitude', 'subscription', 'is_subscribing'
        )


class PlaceSerializer(ToReprMixin, DynamicFieldsModelSerializer):
    venue_owner_id = serializers.UUIDField(source='author_id')
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    tz_offset = serializers.SerializerMethodField()
    main_image = ImageUrlField()
    main_image_thumb = ImageUrlThumbField(source="main_image")

    images = serializers.SerializerMethodField()
    country = serializers.CharField()
    country_iso_code = serializers.CharField()

    is_30_p_natural_already = serializers.SerializerMethodField()

    likevote_number = serializers.SerializerMethodField()
    comment_number = serializers.SerializerMethodField()

    # TODO: candidate for removal
    is_venue = serializers.SerializerMethodField()

    def get_name(self, obj):
        return beautify_place_name(obj.name)

    def get_description(self, obj):
        return strip_tags(obj.description)

    def get_tz_offset(self, obj):
        return get_offset_for_tz_name(obj.tz_name)

    def get_is_venue(self, obj):
        return obj.is_subscriber()

    def get_images(self, obj):
        filters = {'is_archived': False, 'image_area__isnull': not obj.owner}
        exclude_f = {'id': obj.main_image.id if obj.main_image else None}

        return [
            aws_url(i) for i in obj.place_images.filter(**filters).exclude(
                **exclude_f
            ).order_by('ordering')
        ]

    def get_is_30_p_natural_already(self, obj):
        return not obj.is_30_p_natural_already

    def get_likevote_number(self, obj):
        # except likevotes from blocked users
        if self.context['request'].user.is_authenticated:
            blocked_users = BlockUser.objects.filter(
                user=self.context['request'].user).values_list('block_user_id')
            return obj.like_votes.filter(is_archived=False).exclude(
                author_id__in=blocked_users
            ).count()
        else:
            return obj.like_votes.filter(is_archived=False).count()

    def get_comment_number(self, obj):
        # except comments from blocked users
        if self.context['request'].user.is_authenticated:
            blocked_users = BlockUser.objects.filter(
                user=self.context['request'].user).values_list('block_user_id')
            return obj.comments.filter(is_archived=False).exclude(
                author_id__in=blocked_users
            ).count()
        else:
            return obj.comments.filter(is_archived=False).count()

    class Meta:
        model = Place
        fields = ['id', 'city', 'is_bar', 'is_restaurant', 'is_wine_shop',
                  'latitude', 'longitude', 'zip_code', 'tz_name', 'tz_offset',
                  'tz_dst', 'country', 'house_number', 'venue_owner_id',
                  'main_image', 'main_image_thumb', 'is_30_p_natural_already',
                  'full_street_address', 'likevote_number', 'comment_number',
                  'name', 'description', 'is_venue', 'images', 'type', 'state',
                  'country_iso_code']
