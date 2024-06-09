import logging
import random
from datetime import datetime
from itertools import chain

from django.db.models import Q

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from web.serializers.common import RaisinListSerializer

from web.authentication import CustomTokenAuthentication

from web.constants import CalEventStatusE
from web.models import CalEvent
from web.serializers.events import EventSerializer, ShortEventSerializer, \
    EventGetSerializer
from web.serializers.posts import SearchQuerySerialiser
from web.utils.api_handling import fill_default_response_data
from web.utils.exceptions import ResultEmpty
from web.utils.views_common import list_control_parameters_by_form
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema


log = logging.getLogger(__name__)


def future_qs():
    return Q(end_date__gte=datetime.now()) | Q(end_date__isnull=True)


def standard_filters():
    return {
        'is_archived': False,
        'status': CalEventStatusE.PUBLISHED,
    }


def prefetches():
    return ['like_votes', 'attendees', 'comments']


# /api/events/timeline
class EventTimelineView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CustomTokenAuthentication]

    @swagger_auto_schema(
        query_serializer=RaisinListSerializer,
        operation_summary='Return events timeline',
        operation_description='Return events timeline',
        security=[]
    )
    def get(self, request, format=None):
        last_id = None
        start = 0
        limit = 10

        serializer = RaisinListSerializer(data=request.query_params)
        if serializer.is_valid(raise_exception=True):
            validated_data = serializer.validated_data
            start = validated_data.get('start', start)
            (limit, order_dir, last_id, order_by_old) = list_control_parameters_by_form(validated_data)  # noqa

        filters = standard_filters()

        if last_id:
            filters['ordering__gt'] = last_id

        events = CalEvent.objects.filter(
            Q(**filters) &
            Q(future_qs())
        ).order_by('start_date', 'id').prefetch_related(*prefetches())

        if limit:
            events = events[start:start + limit]

        if not events:
            raise ResultEmpty

        items_out = EventSerializer(events, context={
            'request': request, 'child_limit': 12
        }, many=True).data

        data = {
            'items': items_out,
            'last_id': events[len(events) - 1].ordering if events else None
        }
        response_data = {'data': data}
        fill_default_response_data(response_data)
        return Response(response_data)

    @swagger_auto_schema(
        request_body=RaisinListSerializer,
        operation_summary='Return events timeline',
        operation_description='The method POST is deprecated for this '
                              'endpoint.',
        deprecated=True,
        security=[]
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '# /api/events/timeline')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)


# /api/events/carousel
class EventCarouselView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CustomTokenAuthentication]
    last_id = None
    # limit does not work. this is legacy.
    limit = 6

    @swagger_auto_schema(
        query_serializer=RaisinListSerializer,
        operation_summary='Return list of events for carousel.',
        operation_description='Return list of events for carousel.',
        security=[]
    )
    def get(self, request, format=None):
        serializer = RaisinListSerializer(data=request.query_params)
        # prevent_using_non_active_account(request.user)

        if serializer.is_valid():
            cd = serializer.validated_data

            (self.limit, self.order_dir, self.last_id, self.order_by_old) \
                = list_control_parameters_by_form(cd, default_limit=6)  # noqa
        print(self.limit, self.order_dir, self.last_id, self.order_by_old)
        filters = standard_filters()

        if self.last_id:
            filters['id__lt'] = self.last_id

        featured_events = CalEvent.objects.filter(
            Q(**filters) & Q(is_featured=True) & Q(future_qs())
        ).prefetch_related(
            'like_votes', 'attendees', 'comments'
        ).order_by('-modified_time')

        not_featured_events = CalEvent.objects.filter(
            Q(**filters) & Q(is_featured=False) & Q(future_qs())
        )

        featured_ids = []
        ids = []
        if featured_events.exists():
            featured_ids += list(featured_events.values_list('id', flat=True))
            sample_size = 5
        else:
            sample_size = 6

        if not_featured_events.exists():
            index_pool = not_featured_events.values_list('id', flat=True)
            if sample_size > len(index_pool):
                sample_size = len(index_pool)
            ids = random.sample(list(index_pool), sample_size)

        non_featured_events = CalEvent.objects.filter(
            pk__in=ids).prefetch_related(
            'like_votes', 'attendees', 'comments'
        ).order_by('-is_featured', 'start_date')

        events = list(chain(featured_events, non_featured_events))

        if not events:
            raise ResultEmpty

        items_out = EventSerializer(
            events, context={'request': request}, many=True
        ).data
        data = {
            'items': items_out,
            'last_id': events[len(events) - 1].id if events else None
        }
        response_data = {'data': data}
        fill_default_response_data(response_data)
        return Response(response_data)

    @swagger_auto_schema(
        request_body=RaisinListSerializer,
        operation_summary='Return list of events for carousel,',
        operation_description='The method POST is deprecated for this endpoint.'
                              '/api/events/carousel',
        deprecated=True,
        security=[]
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '/api/events/carousel')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)


# /api/events/details
class EventDetailView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CustomTokenAuthentication]

    @swagger_auto_schema(
        query_serializer=EventGetSerializer,
        operation_summary='Return event details by event_id',
        operation_description='Return event details by event_id',
        security=[]
    )
    def get(self, request, format=None):
        event_out = None

        serializer = EventGetSerializer(data=request.query_params)
        if serializer.is_valid(raise_exception=True):
            validated_data = serializer.validated_data

            event = CalEvent.active.get(id=validated_data['event_id'])
            event_out = EventSerializer(
                event, context={'request': request}
            ).data
        data = event_out
        response_data = {'data': data}
        fill_default_response_data(response_data)
        return Response(response_data)

    @swagger_auto_schema(
        request_body=EventGetSerializer,
        operation_summary='Return event details by event_id',
        operation_description='The method POST is deprecated for this '
                              'endpoint.',
        deprecated=True,
        security=[]
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '/api/events/details')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)


# /api/events/map
class EventsMapView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CustomTokenAuthentication]
    last_id = None
    limit = 6
    order_dir = None
    order_by_old = None

    @swagger_auto_schema(
        query_serializer=RaisinListSerializer,
        operation_summary='Return list of events for map.',
        operation_description='Return list of events for map.',
        security=[]
    )
    def get(self, request, format=None):
        serializer = RaisinListSerializer(data=request.query_params)
        if serializer.is_valid():
            vd = serializer.validated_data

            (self.limit, self.order_dir, self.last_id, self.order_by_old) = \
                list_control_parameters_by_form(vd, default_limit=None)

        filters = standard_filters()
        if self.last_id:
            filters['id__lt'] = self.last_id

        events = CalEvent.objects.filter(
            Q(**filters) & Q(future_qs())
        ).order_by('start_date').prefetch_related(*prefetches())
        if not events.exists():
            raise ResultEmpty

        if self.limit:
            events = events[:self.limit]

        items_out = ShortEventSerializer(
            events, context={'request': request}, many=True
        ).data

        data = {
            'items': items_out,
            'last_id': events[len(events) - 1].id if events else None
        }
        response_data = {'data': data}
        fill_default_response_data(response_data)
        return Response(response_data)

    @swagger_auto_schema(
        request_body=RaisinListSerializer,
        operation_summary='Return list of events for map,',
        operation_description='The method POST is deprecated for this endpoint.'
                              '/api/events/map',
        deprecated=True,
        security=[]
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '/api/events/map')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)


# /api/search/events
class SearchEventView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CustomTokenAuthentication]

    @swagger_auto_schema(
        query_serializer=SearchQuerySerialiser,
        operation_summary='Search events.',
        operation_description='Search events.',
        security=[]
    )
    def get(self, request, format=None):
        last_id = None
        limit = 6
        query = None
        serializer = SearchQuerySerialiser(data=request.query_params)
        if serializer.is_valid(raise_exception=True):
            validated_data = serializer.validated_data
            query = validated_data.get('query')

            (limit, order_dir, last_id, order_by_old) = list_control_parameters_by_form(validated_data, default_limit=None)  # noqa

        filters = standard_filters()

        if last_id:
            filters['ordering__gt'] = last_id

        if query:
            filters['title__unaccent__icontains'] = query

        events = CalEvent.objects.filter(Q(**filters)).order_by(
            'ordering'
        ).prefetch_related(*prefetches())

        if limit:
            events = events[:limit]

        items_out = ShortEventSerializer(
            events, context={'request': request}, many=True
        ).data

        data = {
            'items': items_out,
            'last_id': events[len(events) - 1].ordering if events else None
        }
        response_data = {'data': data}
        fill_default_response_data(response_data)
        return Response(response_data)

    @swagger_auto_schema(
        request_body=SearchQuerySerialiser,
        operation_summary='Search events',
        operation_description='The method POST is deprecated for this '
                              'endpoint.',
        deprecated=True,
        security=[]
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '# /api/search/events')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)
