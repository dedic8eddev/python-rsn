from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.utils import timezone
from django.db.models import F, Q, Case, When, Value, IntegerField
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from my_chargebee.models import Subscription
from reports.models import BlockUser
from web.authentication import CustomTokenAuthentication
from web.constants import UserTypeE
from web.helpers.places import PlaceHelper
from web.models import Post
from rest_framework import mixins

from web.serializers.wineposts import WinepostSerializer
from web.utils.api_utils import boolean
import logging


class WinepostList(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Get all winepost list, including:
        - wineposts with subscribing venues
        - wineposts with not subscribing venues
        - not geolocated wineposts
        - users

    URI: `api/find-wineposts`
    """
    serializer_class = WinepostSerializer
    queryset = Post.objects.none()
    authentication_classes = (CustomTokenAuthentication,)
    permission_classes = [AllowAny]

    DEFAULT_LATITUDE = 48.879083
    DEFAULT_LONGITUDE = 2.388551

    wineposts_filters = Q()

    @swagger_auto_schema(
        security=[]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_latitude(self):
        """
        Get query latitude or default
        """
        try:
            lat = float(self.request.query_params.get(
                'latitude', self.DEFAULT_LATITUDE)
            )
        except ValueError:
            lat = self.DEFAULT_LATITUDE
        return lat

    def get_longitude(self):
        """
        Get query longitude or default
        """
        try:
            lng = float(self.request.query_params.get(
                'longitude', self.DEFAULT_LONGITUDE)
            )
        except ValueError:
            lng = self.DEFAULT_LONGITUDE
        return lng

    def get_ref_point(self):
        """
        Get reference point
        """
        latitude = self.get_latitude()
        longitude = self.get_longitude()

        return Point(longitude, latitude, srid=4326)

    def get_search_filters(self, search):
        """
        Get search filters
        """
        filters = Q(
            Q(wine__name__unaccent__icontains=search) |
            Q(wine__domain__unaccent__icontains=search) |
            Q(wine__winemaker__name__unaccent__icontains=search)
        )

        return filters

    def get_wineposts_filters(self):
        """
        Places with app display statuses or None places

        Get additional filters for wineposts data manager.
        You can override this method when subclass
        """
        # in general find wines screen we display wine posts with specific to application place statuses (geolocated)
        # or wine posts by users (non geolocated)
        filters = Q(
            Q(place__status__in=PlaceHelper.app_place_display_statuses) |
            Q(place__id__isnull=True)
        )
        return filters

    def get_owners_with_subscription_filter(self):
        """
        Get venues owners wine posts filters with subscription.
        Include all subscription statuses except 'CANCELED'
        """
        filters = Q(
            Q(author__type__in=[UserTypeE.OWNER, UserTypeE.ADMINISTRATOR]) &
            Q(place__subscription__isnull=False) &
            Q(place__owner=F('author')) &
            ~Q(place__subscription__status=Subscription.CANCELLED)
        )
        return filters

    def get_geolocated_filter(self):
        """
        Geolocated wine posts
        """
        filters = Q(place__id__isnull=False)
        return filters

    def get_queryset(self):
        # get query parameters
        qp = self.request.query_params

        # get search keyword to search wines
        search = qp.get('search')

        # get wineposts filters if any
        self.wineposts_filters = self.get_wineposts_filters()

        if search:
            # Search input is based on: [wine name] + [Winemaker’s Name] + [Domain Name]
            search_filters = self.get_search_filters(search)
            self.wineposts_filters = self.wineposts_filters & search_filters

        # get all wineposts
        # order priority:
        #   - with subscription
        #   - geolocated
        #   - users
        queryset = self.get_filtered_queryset()
        logging.info(queryset.query)

        return queryset.all()

    def get_filtered_queryset(self):
        """
        Get filtered queryset. Apply wineposts filters & search filters if any
        Apply blocked users filter
        """

        # block by author if author = blocked_user
        blocked_users = []
        if not self.request.user.is_authenticated:
            pass
        else:
            blocked_users = BlockUser.objects.filter(
                user=self.request.user).values_list('block_user_id')

        queryset = Post.app_wineposts_active.filter(
            self.wineposts_filters
        ).exclude(
            author__type=UserTypeE.ADMINISTRATOR
        ).exclude(
            author_id__in=blocked_users
        ).annotate(
            priority=Case(
                When(self.get_owners_with_subscription_filter(), then=Value(2)),
                When(self.get_geolocated_filter(), then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).annotate(
            distance=Distance("place__point", self.get_ref_point())
        ).distinct().order_by('-priority', 'distance', '-modified_time')

        return queryset


class WinepostGeolocatedList(WinepostList):
    """
    Endpoint API to get places wineposts

    URI: `api/find-wineposts/geolocated`
    """

    def get_wineposts_filters(self):
        """
        Get additional wineposts filters:
            - Exclude wineposts with None Place object
            - Include only wineposts with mobile app Place statuses
        """
        filters = Q(
            place__id__isnull=False,
            place__status__in=PlaceHelper.app_place_display_statuses
        )
        return filters

    def get_filtered_queryset(self):
        """
        Get filtered queryset overridden.
        """
        # queryset objects prioritizing & ordering
        queryset = Post.app_wineposts_active.filter(
            self.wineposts_filters
        ).exclude(
            Q(modified_time__lt=timezone.now() - timezone.timedelta(days=60)),
            Q(place__owner=F('author'))
        ).annotate(
            priority=Case(
                When(self.get_owners_with_subscription_filter(), then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).annotate(
            distance=Distance("place__point", self.get_ref_point())
        ).distinct().order_by('-priority', 'distance', '-modified_time')
        return queryset


class FilteredWinepostGeolocatedList(WinepostGeolocatedList):
    """
    Endpoint API to find filtered wineposts by:
        - wine_name - optional, the search field
        - wine_domain - optional, the exact wine domain field
        - winemaker_name - optional, the exact winemaker_name field

    URI: `api/find-wineposts-filtered/geolocated`
    """

    def get_wine_name_selected(self, wine_name):
        """
        Get wine name button selection
        """

        # if no filter, force disabling selection
        if not wine_name:
            return False

        # check whether 'wine_name' button is tapped
        selected = boolean(self.request.query_params.get('wine_name_selected'))
        return selected

    def get_winemaker_name_selected(self, winemaker_name):
        """
        Get winemaker name button selection
        """

        # if no filter, force disabling selection
        if not winemaker_name:
            return False

        # check whether 'winemaker_name' button is tapped
        selected = boolean(self.request.query_params.get('winemaker_name_selected'))
        return selected

    def get_wine_domain_selected(self, wine_domain):
        """
        Get wine domain button selection
        """

        # if no filter, force disabling selection
        if not wine_domain:
            return False

        # check whether 'wine_domain' button is tapped
        wine_domain_selected = boolean(self.request.query_params.get('wine_domain_selected'))
        return wine_domain_selected

    def get_queryset(self):

        # get query parameters
        qp = self.request.query_params

        wine_name = qp.get('wine_name', None)
        wine_domain = qp.get('wine_domain', None)
        winemaker_name = qp.get('winemaker_name', None)

        # check whether 'wine_name' button is tapped
        wine_name_selected = self.get_wine_name_selected(wine_name)

        # check whether 'wine_domain' button is tapped
        wine_domain_selected = self.get_wine_domain_selected(wine_domain)

        # check whether 'winemaker_name' button is tapped
        winemaker_name_selected = self.get_winemaker_name_selected(winemaker_name)

        # if no button selected, return empty result set
        if not wine_name_selected and not wine_domain_selected and not winemaker_name_selected:
            return self.queryset

        # no any information of scanned image
        if not wine_name and not wine_domain and not winemaker_name:
            return self.queryset

        # get wineposts filters if any
        # inherit wineposts filters from winepost geolocated
        self.wineposts_filters = self.get_wineposts_filters()

        # add search filter by wine name
        if wine_name:
            # include wine posts with 'wine_name'
            if wine_name_selected:
                self.wineposts_filters = self.wineposts_filters & Q(wine__name__unaccent=wine_name)
            # exclude 'wine_name' from the result set
            else:
                self.wineposts_filters = self.wineposts_filters & ~Q(wine__name__unaccent=wine_name)

        # add filter by wine domain
        if wine_domain:
            # include wine posts with 'wine_domain'
            if wine_domain_selected:
                self.wineposts_filters = self.wineposts_filters & Q(wine__domain__unaccent=wine_domain)
            # exclude 'wine_domain' from the result set
            else:
                self.wineposts_filters = self.wineposts_filters & ~Q(wine__domain__unaccent=wine_domain)

        # add filter by winemaker name
        if winemaker_name:
            # include wine posts with 'winemaker_name'
            if winemaker_name_selected:
                self.wineposts_filters = self.wineposts_filters & Q(wine__winemaker__name__unaccent=winemaker_name)
            # exclude 'winemaker_name' from the result set
            else:
                self.wineposts_filters = self.wineposts_filters & ~Q(wine__winemaker__name__unaccent=winemaker_name)

        # apply wineposts filters
        queryset = self.get_filtered_queryset()
        logging.info(queryset.query)

        return queryset.all()
