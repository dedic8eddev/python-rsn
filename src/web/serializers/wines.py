from rest_framework import serializers

from web.models import Wine
from web.utils import api_blocked_users


class WineSerializer(serializers.ModelSerializer):
    """
    Define serializer declaration for 'Wine' model
    """

    # get winemaker id from relationships with 'Winemaker' model
    winemaker_id = serializers.IntegerField(read_only=True, source="winemaker_identifier")
    winemaker_name = serializers.CharField(read_only=True, source="winemaker")
    likevote_number = serializers.SerializerMethodField()
    comment_number = serializers.SerializerMethodField()
    drank_it_too_number = serializers.SerializerMethodField()

    def get_likevote_number(self, obj):
        # except likes from blocked users
        return api_blocked_users.get_likevotes_number(self=self, obj=obj)

    def get_comment_number(self, obj):
        # except comments from blocked users
        return api_blocked_users.get_comments_number(self=self, obj=obj)

    def get_drank_it_too_number(self, obj):
        # except drank_it_toos from blocked users
        return api_blocked_users.get_drank_it_toos_number(self=self, obj=obj)

    class Meta:
        model = Wine
        fields = (
            'id', 'winemaker_id', 'name', 'name_short', 'domain', 'winemaker_name', 'likevote_number',
            'comment_number', 'drank_it_too_number'
        )


class WineProfileSerializer(serializers.Serializer):
    wine_id = serializers.IntegerField(required=True)
