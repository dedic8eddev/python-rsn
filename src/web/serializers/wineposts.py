from rest_framework import serializers

from web.constants import WineColorE, MOBILE_DATE_FORMAT, PostStatusE
from web.helpers.wineposts import WinepostHelper
from web.models import Post
from web.serializers.nested import VenueSerializer
from web.serializers.wines import WineSerializer

from web.utils.model_tools import (format_currency,
                                   format_price)
from web.utils.time import get_datetime_human
from web.utils.upload_tools import aws_url
from web.utils.wine_utils import get_winepost_status_data
from web.serializers.users import MinimalUserSerializer


class WinepostSerializer(serializers.ModelSerializer):

    # nested model serializers
    author = MinimalUserSerializer(
        fields=(
            'id', 'full_name', 'short_name', 'has_badge', 'image', 'type'
        ),
        many=False,
        read_only=True
    )
    wine = serializers.SerializerMethodField()
    place = VenueSerializer(many=False, read_only=True)

    # overridden fields
    color = serializers.SerializerMethodField()
    modified_time_human = serializers.SerializerMethodField()
    price_currency = serializers.SerializerMethodField()
    thumb_image = serializers.SerializerMethodField()
    wine_year = serializers.SerializerMethodField()
    post_status = serializers.SerializerMethodField()

    distance = serializers.SerializerMethodField()

    def get_wine(self, obj):
        """
        Get wine serialized data and extend it with fields:
            - i_like_it
            - i_drank_it_too
        """
        wine_data = WineSerializer(
            instance=obj.wine,
            many=False,
            read_only=True,
            context={'request': self.context['request']}
        ).data

        # add 'i_like_it' & 'i_drank_it_too' to wine object because its related to wine, not to post
        if wine_data:
            wine_data['i_like_it'] = obj.get_i_like_it(user=self.context['request'].user)
            wine_data['i_drank_it_too'] = obj.get_i_drank_it_too(user=self.context['request'].user)
        return wine_data

    def get_color(self, obj):
        """
        Get color
        """
        return WineColorE.names.get(obj.wine.color)

    def get_modified_time_human(self, obj):
        """
        Get human representation of 'modified_time' field
        """
        return get_datetime_human(obj.modified_time)

    def get_price_currency(self, obj):
        """
        Get formatted price currency
        """
        if not (obj.price and obj.currency):
            return ''

        return f"{format_price(obj.price)} {format_currency(obj.currency)}"

    def get_thumb_image(self, obj):
        """
        Get thumb image from 'main_image' field source
        """
        if obj.main_image:
            return aws_url(obj.main_image, thumb=True)

        return aws_url(
            obj.wine.main_image,
            thumb=True, fallback='pro_assets/img/wines/void.gif'
        )

    def get_wine_year(self, obj):
        """
        Get wine year
        """
        year = obj.wine_year
        return year if year and str(year).isnumeric() and int(year) > 0 else ""

    def get_post_status(self, obj):
        """
        Get post status object based on post 'status' field
        Contains:
            - badge
            - description
            - status_short
            - style_color
        """
        # get post status object
        post_status = get_winepost_status_data(obj.status)

        # ensure that only statuses supported: IN_DOUBT, PUBLISHED, BIO_ORGANIC, REFUSED
        # otherwise we will have an issue with 'badge' of unsupported status on a mobile
        if obj.status not in WinepostHelper.app_winepost_display_statuses:
            post_status['badge'] = None
            return post_status

        return post_status

    def get_distance(self, obj):
        """
        Get distance in meters
        """
        try:
            return int(obj.distance.m)
        except Exception:
            return 0

    # def get_distance(self, obj):
    #     """
    #     Get place distance to ref location
    #     """
    #     try:
    #         if obj.distance.m < 250:
    #             # distance in meters (e.g. 13 m, 157 m)
    #             return str(obj.distance.m) + " m"
    #
    #         if obj.distance.m < 1000:
    #             # round to nearest 250m (e.g. )
    #             return str(obj.distance.m // 250 * 250) + " m"
    #
    #         if obj.distance.km < 1000:
    #             # round to nearest .25 km (e.g. 4.25 km, 85.5 km, 543.75 km)
    #             return str(round(obj.distance.km * 4) / 4) + " km"
    #
    #         # round to nearest 50 km (e.g. 1050 km, 1500 km, 2250 km)
    #         return str(round(obj.distance.km // 50 * 50)) + " km"
    #     except Exception:
    #         return str(obj.distance)

    class Meta:
        model = Post
        fields = (
            'id', 'color', 'impression_number', 'modified_time_human', 'price_currency', 'place',
            'modified_time', 'author', 'wine', 'thumb_image', 'wine_year', 'post_status', 'distance'
        )


class WinePostSerializer(serializers.ModelSerializer):
    """
    Define wine post serializer for 'Post' model
    """

    price_currency = serializers.SerializerMethodField()
    thumb_image = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    modified_time_human = serializers.SerializerMethodField()
    modified_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)
    year = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    post_id = serializers.IntegerField(read_only=True, source="id")
    id = serializers.IntegerField(read_only=True, source="wine_identifier")

    name = serializers.CharField(read_only=True, source="wine_name")
    name_short = serializers.CharField(read_only=True, source="wine_name_short")
    domain = serializers.CharField(read_only=True, source="wine_domain")
    winemaker_name = serializers.CharField(read_only=True, source="wine_winemaker")
    author = serializers.CharField(read_only=True)

    def get_modified_time_human(self, obj):
        """
        Get human representation of 'modified_time' field
        """
        return get_datetime_human(obj.modified_time)

    def get_year(self, obj):
        year = obj.wine_year
        return year if year and str(year).isnumeric() and int(year) > 0 else ""

    def get_status(self, obj):
        return get_winepost_status_data(obj.status)

    def get_color(self, obj):
        return WineColorE.names[obj.wine.color]

    def get_thumb_image(self, obj):
        if obj.main_image:
            return aws_url(obj.main_image, thumb=True)

        return aws_url(
            obj.wine.main_image,
            thumb=True, fallback='pro_assets/img/wines/void.gif'
        )

    def get_price_currency(self, obj):
        if not (obj.price and obj.currency):
            return ''

        return "{} {}".format(
            format_price(obj.price),
            format_currency(obj.currency)
        )

    class Meta:
        model = Post
        fields = (
            'author', 'color', 'domain', 'id', 'impression_number', 'modified_time_human', 'modified_time', 'name',
            'name_short', 'post_id', 'price_currency', 'thumb_image', 'status', 'year', 'winemaker_name',
        )


class ClosestWinePostSerializer(WinePostSerializer):
    """
    Extend wine post serializer with extra fields:
        - winemaker_id
        - is_organic
        - is_biodynamic

    Override:
        - status - 'badge' is not supported for 'DRAFT' status
    """
    winemaker_id = serializers.IntegerField(read_only=True,
                                            source="wine_winemaker_identifier")
    status = serializers.SerializerMethodField()

    def get_status(self, obj):

        # handle 'DRAFT' specific case
        # draft status does not support 'badge' at the moment, so send back None
        if obj.status == PostStatusE.DRAFT:
            wine_status = get_winepost_status_data(obj.status)
            wine_status['badge'] = None
            return wine_status

        # for others form and send status object as usual
        return get_winepost_status_data(obj.status)

    class Meta(WinePostSerializer.Meta):
        """
        Extend meta with additional fields
        """
        fields = WinePostSerializer.Meta.fields + ('winemaker_id', 'is_organic', 'is_biodynamic')


class FoodPostSerializer(serializers.ModelSerializer):
    price_currency = serializers.SerializerMethodField()
    modified_time_human = serializers.SerializerMethodField()
    modified_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)
    ref_image = serializers.SerializerMethodField()

    def get_modified_time_human(self, obj):
        """
        Get human representation of 'modified_time' field
        """
        return get_datetime_human(obj.modified_time)

    def get_price_currency(self, obj):
        if not (obj.price and obj.currency):
            return ''

        return "{} {}".format(
            format_price(obj.price),
            format_currency(obj.currency)
        )

    def get_ref_image(self, obj):
        return aws_url(
            obj.main_image,
            thumb=True,
            fallback='pro_assets/img/food/food-void-min.png'
        )

    class Meta:
        model = Post
        fields = ['id', 'title', 'description', 'modified_time_human',
                  'price_currency', 'ref_image', 'modified_time']
