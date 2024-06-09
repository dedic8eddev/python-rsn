from rest_framework import serializers

from web.constants import MOBILE_DATE_FORMAT, TimeLineItemTypeE
from web.models import TimeLineItem
from web.serializers.posts import TimelinePostSerializer
from web.serializers.users import UserSerializer


class TimeLineItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk')
    author = serializers.SerializerMethodField()
    cached_item = serializers.SerializerMethodField()
    i_like_it = serializers.SerializerMethodField()
    i_drank_it_too = serializers.SerializerMethodField()

    created_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)
    modified_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)

    def get_author(self, obj):
        if obj.item_type != TimeLineItemTypeE.POST:
            return None

        fresh_item = obj.get_cached_item()

        if not fresh_item:
            fresh_item = obj.get_item()

        if type(fresh_item) is None:
            return None

        return UserSerializer(fresh_item.author, context=self.context).data

    def get_cached_item(self, obj):
        if obj.item_type != TimeLineItemTypeE.POST:
            return None

        fresh_item = obj.get_cached_item()

        if not fresh_item:
            fresh_item = obj.get_item()

        return TimelinePostSerializer(fresh_item, context=self.context).data

    def get_i_like_it(self, obj):
        if obj.item_type != TimeLineItemTypeE.POST:
            return None

        fresh_item = obj.get_cached_item()

        if not fresh_item:
            fresh_item = obj.get_item()

        if self.context['request'].user.is_authenticated:
            return fresh_item.like_votes.filter(
                is_archived=False,
                author=self.context['request'].user
            ).exists()
        return False

    def get_i_drank_it_too(self, obj):
        if obj.item_type != TimeLineItemTypeE.POST:
            return None

        fresh_item = obj.get_cached_item()

        if not fresh_item:
            fresh_item = obj.get_item()
        if self.context['request'].user.is_authenticated:
            return fresh_item.drank_it_toos.filter(
                author=self.context['request'].user
            ).exists()
        return False

    class Meta:
        model = TimeLineItem
        fields = ['id', 'author', 'created_time', 'modified_time',
                  'is_archived', 'is_sticky', 'item_description',
                  'cached_item', 'item_type', 'i_like_it', 'i_drank_it_too']
