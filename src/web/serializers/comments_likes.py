from rest_framework import serializers

from web.constants import MOBILE_DATE_FORMAT, PostTypeE, PlaceStatusE, UserTypeE
from web.models import (AbstractImage, Comment, DrankItToo, GetMyFreeGlass,
                        LikeVote, UserNotification, CmsAdminComment, Like)
from web.serializers.utils import (BadgeExpiryDateMsField, HasBadgeDataField,
                                   ImageUrlField, ImageUrlThumbField,
                                   MentionsField, ToReprMixin)
from web.utils.upload_tools import aws_url


class CommentSerializer(ToReprMixin, serializers.ModelSerializer):
    author_avatar_url = ImageUrlThumbField(source="author.image")
    author_image = ImageUrlThumbField(source="author.image")
    author_has_badge = HasBadgeDataField(source="author")
    author_badge_expiry_date_ms = BadgeExpiryDateMsField(source="author")

    author_username = serializers.CharField(source="author.username")
    author = serializers.CharField(source="author.username")
    author_status = serializers.CharField(source="author.status")
    mentions = MentionsField(source="user_mentions")

    created_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)
    modified_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)

    user_banned = serializers.SerializerMethodField()
    can_ban_user = serializers.SerializerMethodField()

    author_is_owner = serializers.SerializerMethodField()
    author_place_id = serializers.SerializerMethodField()

    def get_user_banned(self, obj):
        return obj.author.is_banned()

    def get_can_ban_user(self, obj):
        if not self.context or not self.context['request'].user:
            return False

        user = self.context['request'].user

        return not (obj.author_id == user.id or obj.author.is_banned())

    def get_author_is_owner(self, obj):
        return obj.author.type == UserTypeE.OWNER

    def get_author_place_id(self, obj):
        return obj.author.place_owner.first().id \
            if obj.author.type == UserTypeE.OWNER and obj.author.place_owner.all().exists() else None

    class Meta:
        model = Comment
        fields = ['id', 'author_id', 'author_avatar_url', 'author_has_badge',
                  'author_badge_expiry_date_ms', 'author_username',
                  'description', 'mentions', 'author_image', 'author',
                  'created_time', 'modified_time', 'author_status',
                  'user_banned', 'can_ban_user', 'author_is_owner',
                  'author_place_id']


class LikeVoteSerializer(ToReprMixin, serializers.ModelSerializer):
    author = serializers.CharField(source="author.username")
    author_id = serializers.CharField(source="author.id")
    author_image = ImageUrlThumbField(source="author.image")
    author_has_badge = HasBadgeDataField(source="author")
    author_badge_expiry_date_ms = BadgeExpiryDateMsField(source="author")
    wine_kind = serializers.SerializerMethodField()

    created_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)
    modified_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)

    author_is_owner = serializers.SerializerMethodField()
    author_place_id = serializers.SerializerMethodField()

    class Meta:
        model = LikeVote
        fields = ['id', 'author', 'author_image', 'author_has_badge',
                  'author_badge_expiry_date_ms', 'created_time',
                  'modified_time', 'wine_kind', 'author_id',
                  'author_is_owner', 'author_place_id']

    def get_wine_kind(self, obj):
        return obj.get_wine_kind()

    def get_author_is_owner(self, obj):
        return obj.author.type == UserTypeE.OWNER

    def get_author_place_id(self, obj):
        return obj.author.place_owner.first().id \
            if obj.author.type == UserTypeE.OWNER and obj.author.place_owner.all().exists() else None


class DrankItTooSerializer(ToReprMixin, serializers.ModelSerializer):
    author = serializers.CharField(source="author.username")
    author_username = serializers.CharField(source="author.username")
    author_id = serializers.CharField(source="author.id")
    author_image = ImageUrlThumbField(source="author.image")
    author_avatar_url = ImageUrlThumbField(source="author.image")
    author_has_badge = HasBadgeDataField(source="author")
    author_badge_expiry_date_ms = BadgeExpiryDateMsField(source="author")
    wine_kind = serializers.SerializerMethodField()
    post_main_image = serializers.SerializerMethodField()

    def get_wine_kind(self, obj):
        return obj.get_wine_kind()

    def get_post_main_image(self, obj):
        return obj.post.get_post_main_image_url(
            fallback_wine_image=True
        ) if obj.post else None

    class Meta:
        model = DrankItToo
        fields = ['id', 'author', 'author_image', 'author_has_badge',
                  'author_badge_expiry_date_ms', 'created_time',
                  'modified_time', 'wine_kind', 'author_id',
                  'author_avatar_url', 'author_username', 'post',
                  'post_id', 'post_main_image']


class UserNotificationSerializer(serializers.ModelSerializer):
    notification_id = serializers.IntegerField(source="id")
    notification_type = serializers.IntegerField(source="type")

    user_id = serializers.UUIDField(source="user.id")
    user_name = serializers.UUIDField(source="user.username")
    user_avatar_url = ImageUrlThumbField(source="user.image")

    user_place_id = serializers.SerializerMethodField()
    user_place_name = serializers.SerializerMethodField()
    user_place_image_url = serializers.SerializerMethodField()

    date = serializers.DateTimeField(
        format=MOBILE_DATE_FORMAT, source="created_time"
    )

    class Meta:
        model = UserNotification
        fields = ['notification_id', 'notification_type', 'user_id',
                  'user_name', 'user_avatar_url', 'date', 'user_place_id',
                  'user_place_name', 'user_place_image_url']

    def get_user_place_id(self, instance):
        place = self.get_place(instance)
        return place.id if place else None

    def get_user_place_name(self, instance):
        place = self.get_place(instance)
        return place.name if place else None

    def get_user_place_image_url(self, instance):
        place = self.get_place(instance)
        return place.get_main_image() if place else None

    def get_place(self, instance):
        return instance.user.place_owner.filter(status__in=[
            PlaceStatusE.SUBSCRIBER,
            PlaceStatusE.PUBLISHED]).first()


class UserNotificationAsPostSerializer(UserNotificationSerializer):
    wine_name = serializers.SerializerMethodField()
    post_image_url = serializers.SerializerMethodField()
    start_comment_post = serializers.CharField(source="contents")

    def get_wine_name(self, obj):
        if not obj.post or obj.post.type != PostTypeE.WINE:
            return None

        return obj.post.wine.name

    def get_post_image_url(self, obj):
        if not obj.post:
            return None

        post_main_image = obj.post.main_image

        wine_main_image = obj.post.wine.main_image if obj.post.wine else None

        if post_main_image:
            return aws_url(post_main_image)

        if wine_main_image:
            return aws_url(wine_main_image)

    class Meta:
        model = UserNotification
        fields = UserNotificationSerializer.Meta.fields + [
            'post_id', 'post_image_url', 'start_comment_post', 'wine_name'
        ]


class UserNotificationAsPlaceSerializer(ToReprMixin, UserNotificationSerializer):
    place_name = serializers.CharField(source="place_name_property")
    place_image_url = ImageUrlField(source="place_main_image")
    start_comment_place = serializers.CharField(source="contents")

    class Meta:
        model = UserNotification
        fields = UserNotificationSerializer.Meta.fields + [
            'place_id', 'place_image_url', 'place_name', 'start_comment_place'
        ]


class ImageSerializer(serializers.ModelSerializer):
    image_url = ImageUrlField(source="*")
    image_url_thumb = ImageUrlThumbField(source="*")

    created_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)
    modified_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)

    class Meta:
        model = AbstractImage
        fields = ['id', 'created_time', 'modified_time', 'width', 'height',
                  'image_url', 'image_url_thumb']


class GetMyFreeGlassSerializer(serializers.ModelSerializer):
    author_id = serializers.UUIDField(source="author.id")
    author_name = serializers.CharField(source="author.username")
    author_has_badge = HasBadgeDataField(source="author")
    author_badge_expiry_date_ms = BadgeExpiryDateMsField(source="author")

    place_name = serializers.CharField(source="place_name_property")

    class Meta:
        model = GetMyFreeGlass
        fields = ['id', 'author_name', 'author_has_badge',
                  'author_badge_expiry_date_ms', 'place_name', 'author_id',
                  'place_id']


class DrankItTooUDSerializer(serializers.ModelSerializer):
    post_main_image = serializers.SerializerMethodField()
    wine_kind = serializers.SerializerMethodField()

    def get_wine_kind(self, obj):
        return obj.get_wine_kind()

    def get_post_main_image(self, obj):
        return obj.post.get_post_main_image_url(
            fallback_wine_image=True
        ) if obj.post else None

    class Meta:
        model = DrankItToo
        fields = ['post_id', 'wine_kind', 'post_main_image']


class LikeVoteUDSerializer(ToReprMixin, serializers.ModelSerializer):
    event_id = serializers.IntegerField(source="cal_event_id")

    place_main_image = ImageUrlField(source="place_main_image_property")

    event_main_image = serializers.SerializerMethodField()
    post_main_image = serializers.SerializerMethodField()
    wine_kind = serializers.SerializerMethodField()

    def get_wine_kind(self, obj):
        return obj.get_wine_kind()

    def get_post_main_image(self, obj):
        return obj.post.get_post_main_image_url(
            fallback_wine_image=True
        ) if obj.post else None

    def get_event_main_image(self, obj):
        return aws_url(obj.cal_event.image) if obj.cal_event else None

    class Meta:
        model = LikeVote
        fields = ['post_id', 'place_id', 'event_id', 'wine_kind',
                  'post_main_image', 'place_main_image', 'event_main_image']


class AdminCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    author_images = serializers.SerializerMethodField()
    content_type_name = serializers.SerializerMethodField()
    created_formatted = serializers.SerializerMethodField()
    last_updated_formatted = serializers.SerializerMethodField()
    author_status = serializers.SerializerMethodField()

    class Meta:
        model = CmsAdminComment
        fields = '__all__'

    def get_author_name(self, obj):
        author = obj.author
        return author.get_name()

    def get_content_type_name(self, obj):
        content_type = obj.content_type
        return content_type.name

    def get_created_formatted(self, obj):
        return obj.created.strftime('%d %b %Y %H:%M')

    def get_last_updated_formatted(self, obj):
        return obj.last_updated.strftime('%d %b %Y %H:%M')

    def get_author_images(self, obj):
        author = obj.author
        return author.get_images()

    def get_author_status(self, obj):
        author = obj.author
        return author.status


class AdminCommentReadSerializer(AdminCommentSerializer):
    pass


class AdminCommentEditSerializer(AdminCommentSerializer):
    class Meta(AdminCommentSerializer.Meta):
        fields = '__all__'
        read_only_fields = ('object_id', 'content_type', 'author',
                            'created', 'last_updated')


class AdminCommentCreateSerializer(AdminCommentEditSerializer):
    def create(self, validated_data):
        comment_data = self.context['comment_data']

        comment_data.update(validated_data)
        return CmsAdminComment.objects.create(**comment_data)


class LikeSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    author_images = serializers.SerializerMethodField()
    content_type_name = serializers.SerializerMethodField()
    created_formatted = serializers.SerializerMethodField()
    last_updated_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Like
        fields = '__all__'

    def get_author_name(self, obj):
        author = obj.author
        return author.full_name

    def get_content_type_name(self, obj):
        content_type = obj.content_type
        return content_type.name

    def get_created_formatted(self, obj):
        return obj.created.strftime('%d %b %Y %H:%M')

    def get_last_updated_formatted(self, obj):
        return obj.last_updated.strftime('%d %b %Y %H:%M')

    def get_author_images(self, obj):
        author = obj.author
        return author.get_images()


class LikeReadSerializer(LikeSerializer):
    pass


class LikeEditSerializer(LikeSerializer):
    class Meta(LikeSerializer.Meta):
        fields = '__all__'
        read_only_fields = ('object_id', 'content_type', 'author',
                            'created', 'last_updated')


class LikeCreateSerializer(LikeEditSerializer):
    def create(self, validated_data):
        like_data = self.context['like_data']

        like_data.update(validated_data)
        return Like.objects.create(**like_data)
