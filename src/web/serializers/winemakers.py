from rest_framework import serializers

from web.constants import (MOBILE_DATE_FORMAT, PostStatusE, PostTypeE,
                           UserTypeE, WineStatusE)
from web.models import DrankItToo, Post, Winemaker
from web.serializers.utils import (BadgeExpiryDateMsField, HasBadgeDataField,
                                   ImageUrlField, ImageUrlThumbField,
                                   MentionsField, ToReprMixin)
from web.utils.model_app_legacy import api_status_winemaker
from web.utils.upload_tools import aws_url


class MinimalWinemakerSerializer(ToReprMixin, serializers.ModelSerializer):
    id = serializers.UUIDField(source='pk')
    image = ImageUrlField(source='main_image')

    class Meta:
        model = Winemaker
        fields = ['id', 'image']


class WinemakerSerializerForCombinedSearch(MinimalWinemakerSerializer):
    type = serializers.SerializerMethodField()
    has_badge = serializers.SerializerMethodField()
    badge_expiry_date_ms = serializers.SerializerMethodField()

    full_name = serializers.CharField(source='name')
    short_name = serializers.CharField(source='domain')

    def get_has_badge(self, obj):
        return False

    def get_badge_expiry_date_ms(self, obj):
        return False

    def get_type(self, obj):
        return 'winemaker'

    class Meta:
        model = Winemaker
        fields = ['id', 'has_badge', 'badge_expiry_date_ms', 'full_name',
                  'short_name', 'modified_time', 'image', 'type']


class SimpleWinemakerSerializer(ToReprMixin, serializers.ModelSerializer):
    total_likevote_number = serializers.IntegerField(source="likevote_number")
    main_image = ImageUrlField()
    latitude = serializers.FloatField(source="pin_latitude")
    longitude = serializers.FloatField(source="pin_longitude")
    total_wine_post_number = serializers.IntegerField(source="wineposts_count")
    total_wine_number = serializers.IntegerField(source="wines_count")
    i_drank_it_too = serializers.SerializerMethodField()

    def get_i_drank_it_too(self, obj):
        return obj.drunk_it_toos

    class Meta:
        model = Winemaker
        fields = [
            'country',
            'city',
            'domain',
            'domain_short',
            'i_drank_it_too',
            'id',
            'latitude', 'longitude',
            'main_image',
            'name',
            'name_short',
            'total_likevote_number',
            'total_wine_number',
            'total_wine_post_number'
        ]


class WinemakerSerializer(ToReprMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk')

    total_wine_number = serializers.SerializerMethodField()
    total_wine_post_number = serializers.SerializerMethodField()
    total_likevote_number = serializers.IntegerField(source="likevote_number")
    i_drank_it_too = serializers.SerializerMethodField()

    main_image = ImageUrlField()
    main_image_thumb = ImageUrlThumbField(source='main_image')

    latitude = serializers.FloatField(source="pin_latitude")
    longitude = serializers.FloatField(source="pin_longitude")

    country = serializers.CharField()

    def get_total_wine_number(self, obj):
        if hasattr(obj, 'total_wine_number_annotated'):
            return obj.total_wine_number_annotated
        return obj.wines.filter(
            status=WineStatusE.VALIDATED,
            is_archived=False
        ).count()

    def get_total_wine_post_number(self, obj):
        if hasattr(obj, 'total_wine_post_number_annotated'):
            return obj.total_wine_post_number_annotated
        return Post.active.filter(
            type=PostTypeE.WINE,
            wine__winemaker=obj,
            status=PostStatusE.PUBLISHED,
            wine__status=WineStatusE.VALIDATED
        ).count()

    def get_i_drank_it_too(self, obj):
        if self.context['request'].user.is_authenticated:
            return DrankItToo.active.filter(
                wine__winemaker=obj,
                author=self.context['request'].user
            ).exists()
        return False

    class Meta:
        model = Winemaker
        fields = ['id', 'name', 'name_short', 'domain', 'domain_short',
                  'total_wine_number', 'total_wine_post_number',
                  'total_likevote_number', 'main_image', 'main_image_thumb',
                  'country', 'i_drank_it_too', 'latitude', 'longitude']


class LongWinemakerSerializer(WinemakerSerializer):
    author = serializers.CharField(source='author.username')
    author_has_badge = HasBadgeDataField(source='author')
    author_badge_expiry_date_ms = BadgeExpiryDateMsField(source='author')

    created_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)
    modified_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)

    expert = serializers.SerializerMethodField()
    expert_id = serializers.SerializerMethodField()
    expert_avatar_url = serializers.SerializerMethodField()
    author_avatar_url = ImageUrlThumbField(source='author.image')
    modifier_avatar_url = ImageUrlThumbField(source='last_modifier_image')
    modifier = serializers.CharField(source='last_modifier_username')
    modifier_id = serializers.UUIDField(source='last_modifier_identifier')

    street_address = serializers.SerializerMethodField()
    mentions = MentionsField(source="user_mentions")

    # expert_avatar_file(?), main_image_file(?),
    # author_avatar_file(?), 'modifier_avatar_file'(?)

    country_iso_code = serializers.CharField()

    def get_expert(self, obj):
        if not obj.last_modifier or obj.last_modifier.type not in [
            UserTypeE.ADMINISTRATOR, UserTypeE.EDITOR
        ]:
            return None

        return obj.last_modifier.username

    def get_expert_id(self, obj):
        if not obj.last_modifier or obj.last_modifier.type not in [
            UserTypeE.ADMINISTRATOR, UserTypeE.EDITOR
        ]:
            return None

        return obj.last_modifier.pk

    def get_expert_avatar_url(self, obj):
        if not obj.last_modifier or obj.last_modifier.type not in [
            UserTypeE.ADMINISTRATOR, UserTypeE.EDITOR
        ]:
            return None

        return aws_url(obj.last_modifier.image, thumb=True)

    def get_street_address(self, obj):
        if obj.full_street_address:
            return obj.full_street_address

        if obj.street_address and obj.house_number:
            return "{}, {}".format(obj.house_number, obj.street_address)

        return obj.street_address

    class Meta:
        model = Winemaker
        fields = ['id', 'author', 'author_has_badge',
                  'author_badge_expiry_date_ms', 'expert', 'expert_id',
                  'expert_avatar_url', 'name', 'name_short', 'description',
                  'domain', 'domain_short', 'street_address', 'house_number',
                  'zip_code', 'city', 'country_iso_code', 'region',
                  'phone_number', 'mobile_phone_number', 'website_url',
                  'email', 'latitude', 'longitude', 'pin_latitude',
                  'pin_longitude', 'social_facebook_url', 'social_twitter_url',
                  'social_instagram_url', 'author_id', 'main_image',
                  'main_image_thumb', 'author_avatar_url', 'modifier',
                  'modifier_id', 'modifier_avatar_url',
                  'created_time', 'modified_time', 'status', 'in_doubt',
                  'total_wine_number', 'total_wine_post_number',
                  'total_likevote_number', 'comment_number',
                  'total_star_review_number', 'total_is_parent_post_number',
                  'mentions', 'is_organic', 'is_biodynamic', 'certified_by',
                  'wine_trade', 'plough_horse', 'domain_description']


class LongWinemakerSerializerLegacy(LongWinemakerSerializer):
    def to_representation(self, obj):
        data = super().to_representation(obj)

        wm_status = api_status_winemaker(obj)
        data['status'] = wm_status['status']
        data['in_doubt'] = wm_status['in_doubt']
        data['is_archived'] = wm_status['is_archived']

        return data

    class Meta:
        model = Winemaker
        fields = LongWinemakerSerializer.Meta.fields + [
            'in_doubt', 'is_archived'
        ]


class ShortWinemakerSerializer(ToReprMixin, serializers.ModelSerializer):
    total_wine_number = serializers.SerializerMethodField()
    total_wine_post_number = serializers.SerializerMethodField()
    total_likevote_number = serializers.IntegerField(source="likevote_number")

    def get_total_wine_number(self, obj):
        return obj.wines.filter(status=WineStatusE.VALIDATED).count()

    def get_total_wine_post_number(self, obj):
        return Post.active.filter(
            type=PostTypeE.WINE,
            wine__winemaker=obj,
            status=PostStatusE.PUBLISHED,
            wine__status=WineStatusE.VALIDATED
        ).count()

    class Meta:
        model = Winemaker
        fields = ['name', 'domain', 'city', 'zip_code', 'region', 'country',
                  'total_wine_number', 'total_wine_post_number',
                  'total_likevote_number']


class WinemakerProfileSerializer(serializers.Serializer):
    winemaker_id = serializers.IntegerField(required=True)
