from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class RaisinListSerializer(serializers.Serializer):
    last_id = serializers.IntegerField(required=False)
    start = serializers.IntegerField(required=False)
    limit = serializers.IntegerField(required=False)
    order = serializers.CharField(required=False)
    order_by = serializers.CharField(required=False)


class RandomFoodsWinesGeoSerializer(serializers.Serializer):
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)
    limit = serializers.IntegerField(required=False)
    refresh = serializers.BooleanField(required=False)


class LikeVoteListSerializer(serializers.Serializer):
    post_id = serializers.IntegerField(required=False)
    place_id = serializers.IntegerField(required=False)
    user_id = serializers.CharField(required=False)
    username = serializers.CharField(required=False)
    wine_id = serializers.CharField(required=False)
    event_id = serializers.CharField(required=False)
    limit = serializers.IntegerField(required=False)
    order_dir = serializers.CharField(required=False)
    last_id = serializers.IntegerField(required=False)
    order_by = serializers.CharField(required=False)

    def validate(self, data):
        if ('post_id' not in data or not data.get('post_id')) \
                and ('place_id' not in data or not data.get('place_id')) \
                and ('user_id' not in data or not data.get('user_id')) \
                and ('username' not in data or not data.get('username')) \
                and ('wine_id' not in data or not data.get('wine_id')) \
                and ('event_id' not in data or not data.get('event_id')):
            raise serializers.ValidationError({
                'post_id': [_("Valid 'post_id' or 'place_id' or 'event_id' or 'user_id' or 'username' or "
                              "'wine_id' field is required."), ]
            })
        return data
