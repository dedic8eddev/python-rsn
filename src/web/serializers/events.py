from datetime import datetime

from rest_framework import serializers

from reports.models import BlockUser
from web.constants import UserTypeE
from web.models import Attendee, CalEvent, EventImage
from web.serializers.comments_likes import CommentSerializer
from web.serializers.utils import (BadgeExpiryDateMsField, HasBadgeDataField,
                                   ImageUrlThumbField, ToReprMixin)
from web.utils.geoloc import update_lat
from web.utils.upload_tools import aws_url


class ShortEventSerializer(serializers.ModelSerializer):
    loc_lat = serializers.SerializerMethodField()

    i_like_it = serializers.SerializerMethodField()
    is_attn = serializers.SerializerMethodField()
    is_user_there = serializers.SerializerMethodField()

    is_past = serializers.SerializerMethodField()
    is_ongoing = serializers.SerializerMethodField()

    image_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()
    gif_url = serializers.SerializerMethodField()
    poster_url = serializers.SerializerMethodField()

    all_comments = serializers.SerializerMethodField()
    all_likes = serializers.SerializerMethodField()
    all_attns = serializers.SerializerMethodField()

    def get_image_url(self, obj):
        return aws_url(obj.image, horizontal=True)

    def get_preview_url(self, obj):
        return aws_url(obj.image, thumb=True)

    def get_gif_url(self, obj):
        if not obj.gif_image_file:
            return obj.external_image_url
        return aws_url(obj.gif_image_file.name)

    def get_poster_url(self, obj):
        if not obj.poster_image_file:
            return None
        return aws_url(obj.poster_image_file.name, poster=True)

    def get_loc_lat(self, obj):
        return update_lat(obj.loc_lat)

    def get_i_like_it(self, obj):
        if self.context['request'].user.is_authenticated:
            return obj.like_votes.filter(
                is_archived=False,
                author=self.context['request'].user,
            ).exists()
        return False

    def get_is_attn(self, obj):
        if self.context['request'].user.is_authenticated:
            return obj.attendees.filter(
                author=self.context['request'].user,
                is_archived=False
            ).exists()
        return False

    def get_is_user_there(self, obj):
        if self.context['request'].user.is_authenticated:
            return obj.attendees.filter(
                author=self.context['request'].user,
                is_user_there=True,
                is_archived=False
            ).exists()
        return False

    def get_is_past(self, obj):
        return bool(obj.end_date < datetime.now()) if obj.start_date else False

    def get_is_ongoing(self, obj):
        return bool(
            obj.start_date <= datetime.now() <= obj.end_date
        ) if obj.start_date else True

    def get_all_likes(self, obj):
        # except likes from blocked users
        if self.context['request'].user.is_authenticated:
            blocked_users = BlockUser.objects.filter(
                user=self.context['request'].user).values_list('block_user_id')
            return obj.like_votes.filter(is_archived=False).exclude(
                author_id__in=blocked_users
            ).count()
        else:
            return obj.like_votes.filter(is_archived=False).count()

    def get_all_attns(self, obj):
        # except blocked users
        if self.context['request'].user.is_authenticated:
            blocked_users = BlockUser.objects.filter(
                user=self.context['request'].user).values_list('block_user_id')
            return obj.attendees.filter(is_archived=False).exclude(
                author_id__in=blocked_users
            ).count()
        else:
            return obj.attendees.filter(is_archived=False).count()

    def get_all_comments(self, obj):
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
        model = CalEvent
        fields = ['id', 'title', 'start_date', 'end_date', 'i_like_it',
                  'is_attn', 'is_user_there', 'is_past', 'is_ongoing',
                  'is_raisin_participating',
                  'image_url', 'preview_url', 'image_width', 'image_height',
                  'gif_url', 'poster_url',
                  'loc_name', 'loc_lat', 'loc_lng', 'loc_country',
                  'loc_state', 'loc_city', 'loc_zip_code',
                  'all_comments', 'all_likes', 'all_attns', 'type',
                  'external_url', 'use_external_link',
                  'wine_faire_url', 'tickets_url',
                  ]


class EventSerializer(ShortEventSerializer):
    attns = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    comment_last_id = serializers.SerializerMethodField()

    def get_comments(self, obj):
        # except comments from blocked users
        if self.context['request'].user.is_authenticated:
            blocked_users = BlockUser.objects.filter(
                user=self.context['request'].user).values_list('block_user_id')
            comments = obj.comments.filter(is_archived=False).exclude(
                author_id__in=blocked_users
            ).all()
        else:
            comments = obj.comments.filter(is_archived=False).all()
        if 'child_limit' in self.context:
            comments = comments[:self.context['child_limit']]

        serializer = CommentSerializer(comments, many=True)

        return serializer.data

    def get_comment_last_id(self, obj):
        # except comments from blocked users
        if self.context['request'].user.is_authenticated:
            blocked_users = BlockUser.objects.filter(
                user=self.context['request'].user).values_list('block_user_id')
            comments = obj.comments.filter(is_archived=False).exclude(
                author_id__in=blocked_users
            ).all()
        else:
            comments = obj.comments.filter(is_archived=False).all()
        if 'child_limit' in self.context:
            comments = comments[:self.context['child_limit']]

        return comments[len(comments) - 1].id if comments else None

    def get_attns(self, obj):
        # except blocked users
        if self.context['request'].user.is_authenticated:
            blocked_users = BlockUser.objects.filter(
                user=self.context['request'].user).values_list('block_user_id')
            attendees = obj.attendees.filter(is_archived=False).exclude(
                author_id__in=blocked_users
            ).all()
        else:
            attendees = obj.attendees.filter(is_archived=False)
        if 'child_limit' in self.context:
            attendees = attendees[:self.context['child_limit']]

        serializer = AttendeeSerializer(attendees, many=True)

        return serializer.data

    class Meta:
        model = CalEvent
        fields = ShortEventSerializer.Meta.fields + [
            'ordering', 'description', 'price', 'is_pro',
            'loc_full_street_address', 'i_like_it', 'is_attn',
            'attns', 'comments', 'comment_last_id'
        ]


class AttendeeSerializer(ToReprMixin, serializers.ModelSerializer):
    id = serializers.CharField(source="author_id")
    author_image = ImageUrlThumbField(source="author.image")
    author_avatar_url = ImageUrlThumbField(source="author.image")
    author_has_badge = HasBadgeDataField(source="author")
    author_badge_expiry_date_ms = BadgeExpiryDateMsField(source="author")

    author_username = serializers.CharField(source="author.username")
    username = serializers.CharField(source="author.username")

    author_is_owner = serializers.SerializerMethodField()
    author_place_id = serializers.SerializerMethodField()

    def get_author_is_owner(self, obj):
        return obj.author.type == UserTypeE.OWNER

    def get_author_place_id(self, obj):
        return obj.author.place_owner.first().id \
            if obj.author.type == UserTypeE.OWNER and obj.author.place_owner.all().exists() else None

    class Meta:
        model = Attendee
        fields = ['id', 'author_avatar_url', 'author_has_badge',
                  'author_badge_expiry_date_ms', 'author_username',
                  'is_user_there', 'username', 'author_id', 'author_image',
                  'author_is_owner', 'author_place_id']


class EventGetSerializer(serializers.Serializer):
    event_id = serializers.IntegerField(required=True)


class EventImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventImage
        fields = [
            'image_file',
            'event',
        ]

    def create(self, validated_data):
        event = validated_data.get('event')
        event_image = EventImage(**validated_data)
        event_image.save()
        event.image = event_image
        event.save()
        event.refresh_from_db()
        return event


class EventInfoSerializer(serializers.ModelSerializer):
    status = serializers.CharField(required=False)
    image = EventImagesSerializer(required=False)
    image_url = serializers.SerializerMethodField()
    poster_url = serializers.SerializerMethodField()

    class Meta:
        model = CalEvent
        fields = [
            'id',
            'external_submitter_email', 'type', 'status',
            'title',
            'image', 'gif_image_file', 'poster_image_file',
            'image_url', 'poster_url',
            'external_url', 'use_external_link',
            'price',
            'is_pro',
            'wine_faire_url',
            'tickets_url',
            'start_date', 'end_date',
            'loc_full_street_address', 'loc_name', 'loc_country',
            'loc_state', 'loc_city', 'loc_zip_code',
            'description', 'external_author_name',
            'wine_faire_url', 'tickets_url', 'loc_lat', 'loc_lng'
        ]

    def to_internal_value(self, data):
        # check for "start_date/end_date": "" and convert to None
        # This must be done before .validate()
        if data['start_date'] == '':
            data['start_date'] = None
        if data['end_date'] == '':
            data['end_date'] = None
        return super(EventInfoSerializer, self).to_internal_value(data)

    def get_image_url(self, obj):
        return aws_url(obj.image, horizontal=True)

    def get_poster_url(self, obj):
        if not obj.poster_image_file:
            return None
        return aws_url(obj.poster_image_file.name, poster=True)


class EventFaireSerializer(EventSerializer):
    class Meta:
        model = CalEvent
        fields = ['id', 'title', 'description', 'start_date', 'end_date',
                  'is_past', 'is_ongoing',
                  'image_url', 'preview_url', 'image_width', 'image_height',
                  'gif_url', 'poster_url',
                  'loc_name', 'loc_lat', 'loc_lng',
                  'loc_country', 'loc_city', 'loc_state',
                  'all_comments', 'all_likes', 'all_attns', 'type',
                  'external_url', 'use_external_link',
                  'price', 'is_pro', 'is_raisin_participating',
                  'wine_faire_url', 'tickets_url',
                  'loc_zip_code', 'loc_full_street_address',
                  ]
