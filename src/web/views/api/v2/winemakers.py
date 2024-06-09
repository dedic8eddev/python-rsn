import logging

from django.db.models import Q, Count, OuterRef, Exists
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from web.authentication import CustomTokenAuthentication
from web.constants import WineStatusE, PostStatusE, PostTypeE
from web.models import Winemaker, DrankItToo
from web.pagination import PlacePagination
from web.serializers.winemakers import SimpleWinemakerSerializer

log = logging.getLogger(__name__)


# api/winemakers
# api/winemakers/id
class WinemakerViewSet(viewsets.ModelViewSet):
    serializer_class = SimpleWinemakerSerializer
    queryset = Winemaker.objects.none()
    authentication_classes = (CustomTokenAuthentication,)

    # disable pagination for this endpoint
    pagination_class = None

    # default Paris point
    DEFAULT_LATITUDE = 48.879083
    DEFAULT_LONGITUDE = 2.388551

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        # get query parameters
        qp = self.request.query_params

        # get search keyword to search wines
        search = qp.get('search')

        filters = Q()
        if search:
            search_filters = Q(
                Q(name__unaccent__icontains=search) |
                Q(domain__unaccent__icontains=search) |
                Q(country__unaccent__icontains=search) |
                Q(city__unaccent__icontains=search)
            )
            filters = filters & search_filters
        if self.request.user.is_authenticated:
            drunk_it_too_subquery = DrankItToo.active.filter(author=self.request.user, wine__winemaker=OuterRef('pk'))
        else:
            drunk_it_too_subquery = DrankItToo.active.filter(id=-1)

        queryset = Winemaker.app_winemakers_active.filter(
            wines__status=WineStatusE.VALIDATED,
            wines__posts__status=PostStatusE.PUBLISHED,
            wines__posts__type=PostTypeE.WINE
        ).annotate(
            # annotate additional fields to reduce DB queries from serializer per each winemaker object
            wineposts_count=Count(
                'wines__posts__id',
                filter=Q(wines__status=WineStatusE.VALIDATED, wines__posts__status=PostStatusE.PUBLISHED),
                distinct=True
            ),
            wines_count=Count(
                'wines__id',
                filter=Q(wines__status=WineStatusE.VALIDATED),
                distinct=True
            ),
            drunk_it_toos=Exists(drunk_it_too_subquery)
        ).filter(wines_count__gt=0)
        queryset = queryset.filter(filters)

        # make a images selection to reduce DB calls from serializer
        queryset = queryset.select_related('main_image')

        return queryset.all()


# /api/winemaker/items (same as api/winemakers
# to temporary maintain old mobile versions)
class WinemakersView(ListCreateAPIView):
    serializer_class = SimpleWinemakerSerializer
    queryset = Winemaker.objects.none()
    # authentication_classes = (CustomTokenAuthentication)
    permission_classes = (AllowAny,)
    # disable pagination for this endpoint
    pagination_class = PlacePagination

    # default Paris point
    DEFAULT_LATITUDE = 48.879083
    DEFAULT_LONGITUDE = 2.388551

    def get_queryset(self):
        # get query parameters
        qp = self.request.query_params

        # get search from form (old clients)
        search = self.request.data.get('query')

        if not search:
            # get search keyword to search wines
            search = qp.get('search')

        filters = Q()
        if search:
            search_filters = Q(
                Q(name__unaccent__icontains=search) |
                Q(domain__unaccent__icontains=search)
            )
            filters = filters & search_filters
        if self.request.user.is_authenticated:
            drunk_it_too_subquery = DrankItToo.active.filter(
                author=self.request.user, wine__winemaker=OuterRef('pk'))
        else:
            drunk_it_too_subquery = DrankItToo.objects.filter(id__lt=0)

        queryset = Winemaker.app_winemakers_active.filter(
            wines__status=WineStatusE.VALIDATED,
            wines__posts__status=PostStatusE.PUBLISHED,
            wines__posts__type=PostTypeE.WINE
        ).annotate(
            # annotate additional fields to reduce DB queries from serializer per each winemaker object
            wineposts_count=Count(
                'wines__posts__id',
                filter=Q(wines__status=WineStatusE.VALIDATED,
                         wines__posts__status=PostStatusE.PUBLISHED),
                distinct=True
            ),
            wines_count=Count(
                'wines__id',
                filter=Q(wines__status=WineStatusE.VALIDATED),
                distinct=True
            ),
            drunk_it_toos=Exists(drunk_it_too_subquery)
        ).filter(wines_count__gt=0)
        queryset = queryset.filter(filters)

        # make a images selection to reduce DB calls from serializer
        queryset = queryset.select_related('main_image')

        return queryset.all().order_by('name')

    @swagger_auto_schema(
        security=[],
        operation_summary='Return winemaker items.',
        operation_description='Return winemaker items.'
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        log.warning('The POST method Is deprecated for the endpoint '
                    '/api/winemaker/items')
        return self.list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Return winemaker items.',
        operation_description='Return winemaker items.',
        deprecated=True,
        security=[]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
