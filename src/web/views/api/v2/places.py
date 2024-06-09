from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db.models import Q, Case, When, Value, IntegerField, BooleanField, Prefetch
from rest_framework import viewsets, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from web.authentication import CustomTokenAuthentication
from web.constants import PostTypeE
from web.helpers.places import PlaceHelper
from web.helpers.wineposts import WinepostHelper
from web.models import Place, PlaceImage
from web.serializers.places import FilteredVenueWithWinepostSerializer, VenueWithWinePostSerializer, PlaceGeoSerializer


class PlacesGeoViewSet(viewsets.ModelViewSet):
    pagination_class = None
    serializer_class = PlaceGeoSerializer
    queryset = Place.objects.none()
    authentication_classes = (CustomTokenAuthentication,)

    def get_queryset(self):
        # bad named 'is_venue' annotated as is_subscribed
        queryset = Place.app_active.annotate(
            place_subscribed=Case(
                When(Q(subscription__status__in=PlaceHelper.place_subscribing_statuses), then=True),
                default=False,
                output_field=BooleanField()
            ),
            place_street_address=Case(
                When(Q(full_street_address__isnull=False), then='full_street_address'),
                default='street_address'
            ),
        )

        prefetch_place_images = Prefetch(
            'place_images',
            queryset=PlaceImage.objects.filter(is_archived=False).order_by('image_area', 'abstractimage_ptr_id', )
        )
        # prefetch_place_posts_images = Prefetch(
        #     'posts__images',
        #     queryset=PostImage.objects.filter(is_archived=False)
        # )

        queryset = queryset.select_related('owner', 'main_image').prefetch_related(
            prefetch_place_images
        )

        return queryset.all()


# TODO: remove it later on, endpoint is not used anymore
class ClosestWinepostVenueViewSet(viewsets.ModelViewSet):
    """
    Get unique closest winepost venues (places)

    GET parameters:
            - latitude - Optional, latitude point value
            - longitude - Optional, longitude point value
            - search - Optional, search keyword to find wines
    """
    serializer_class = VenueWithWinePostSerializer
    queryset = Place.objects.none()
    authentication_classes = (CustomTokenAuthentication,)

    def get_posts_filters(self):
        """
        Get posts filters list:
            - posts type
            - posts wine_id
            - posts is_archived
            - posts status in: IN DOUBT - NATURAL - NOT NATURAL - BIO/ORGANIC
        """
        # filter posts by type=WINE and ensure 'wine_id' is not null
        # its default filters since we find wines we need 'WINE' type
        # wine posts displayed on the app : IN DOUBT - NATURAL - NOT NATURAL - BIO/ORGANIC
        filters = Q(
            Q(posts__type=PostTypeE.WINE) &
            Q(posts__wine_id__isnull=False) &
            Q(posts__is_archived=False) &
            Q(posts__status__in=WinepostHelper.app_winepost_display_statuses)
        )

        return filters

    def get_queryset(self):
        # default point
        latitude_paris, longitude_paris = 48.879083, 2.388551

        # get query parameters
        qp = self.request.query_params

        # if not specified in request GET parameters, use default paris point values
        latitude = float(qp.get('latitude', latitude_paris))
        longitude = float(qp.get('longitude', longitude_paris))

        # get search keyword to search wines
        search = qp.get('search')

        # create geolocation reference point by latitude & longitude values
        reference = Point(longitude, latitude, srid=4326)

        # get base queryset filters
        filters = self.get_posts_filters()

        # filter all places that posts matches search criteria
        # one or many place posts can match search criteria
        # Post serializer will filter out all except the last wine post
        if search:
            # Search input is based on: [wine name] + [Winemaker’s Name] + [Domain Name]
            search_filters = Q(
                Q(posts__wine__name__unaccent__icontains=search) |
                Q(posts__wine__domain__unaccent__icontains=search) |
                Q(posts__wine__winemaker__name__unaccent__icontains=search)
            )
            filters = filters & search_filters

        # apply all filters
        queryset = self.get_filtered_queryset(
            queryset=Place.app_active,
            filters=filters,
            ref_point=reference
        )
        return queryset.all()

    def get_filtered_queryset(self, queryset, filters, ref_point):
        """
        Get distinct places ordered by distance to reference point 'ref_point'

        Ordering:
          - venues with subscription by distance
          - venues with no subscription by distance
        """
        qs = queryset.filter(filters).annotate(
            priority=Case(
                When(subscription__isnull=False, then=Value(1)),
                When(subscription__isnull=True, then=Value(0)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).annotate(
            distance=Distance("point", ref_point)
        ).distinct().order_by('-priority', 'distance')

        return qs


# TODO: remove it later on, endpoint is not used anymore
class FilteredWinepostVenueViewSet(ClosestWinepostVenueViewSet):
    serializer_class = FilteredVenueWithWinepostSerializer
    queryset = Place.objects.none()
    authentication_classes = (CustomTokenAuthentication,)

    def get_queryset(self):
        # default point
        latitude_paris, longitude_paris = 48.879083, 2.388551

        # get query parameters
        qp = self.request.query_params

        # if not specified in request GET parameters, use default paris point values
        latitude = float(qp.get('latitude', latitude_paris))
        longitude = float(qp.get('longitude', longitude_paris))

        # create ref location point by latitude & longitude values
        reference = Point(longitude, latitude, srid=4326)

        wine_name = qp.get('wine_name')
        wine_domain = qp.get('wine_domain')
        winemaker_name = qp.get('winemaker_name')

        filters = self.get_posts_filters()

        if wine_name:
            filters = filters & Q(posts__wine__name__unaccent__icontains=wine_name)

        if wine_domain:
            filters = filters & Q(posts__wine__domain__unaccent=wine_domain)

        if winemaker_name:
            filters = filters & Q(posts__wine__winemaker__name__unaccent=winemaker_name)

        # filter all places that posts matches search criteria
        queryset = self.get_filtered_queryset(
            queryset=Place.app_active,
            filters=filters,
            ref_point=reference
        )

        return queryset.all()


class GoogleAPIKeyView(views.APIView):
    permission_classes = [AllowAny]
    """
    View to providing google-api-key for FE
    """
    def get(self, request):
        return Response({'google_api_key': settings.GOOGLE_API_KEY})
