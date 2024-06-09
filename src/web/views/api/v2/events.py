from collections import OrderedDict
from datetime import datetime

from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from web.authentication import CsrfExemptSessionAuthentication
from web.constants import PostStatusE, CalEventTypeE
from web.models import CalEvent
from web.serializers.events import (EventInfoSerializer,
                                    EventImagesSerializer,
                                    EventFaireSerializer)


# api/event/create/info
class EventInfoAPIView(ListCreateAPIView):
    permission_classes = [AllowAny]
    authentication_classes = (
        CsrfExemptSessionAuthentication, BasicAuthentication)
    queryset = CalEvent.objects.all()
    serializer_class = EventInfoSerializer

    @swagger_auto_schema(
        security=[],
        operation_summary='Creates a DRAFT Event.',
        operation_description='Creates an Event via ProRaisin submitting form.'
    )
    def create(self, request, *args, **kwargs):
        data = OrderedDict()
        data.update(request.data)
        data['status'] = PostStatusE.DRAFT
        data['description'] = request.data.get(
            'description', 'no-description')

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        if request.data.get('image_file'):
            dict_data = {
                'image_file': self.request.FILES.getlist('image_file')[0],
                'event': event.id,
            }
            serializer_images = EventImagesSerializer(data=dict_data)
            serializer_images.is_valid(raise_exception=True)
            event = serializer_images.save()
            serializer = EventInfoSerializer(event)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)


# api/events/faire
class EventFaireAPIView(ListCreateAPIView):
    queryset = CalEvent.objects.all()
    serializer_class = EventFaireSerializer

    def list(self, request):
        queryset = self.get_queryset()
        dt_today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        dict_filter = {
            'type': CalEventTypeE.EVENT,
            'end_date__gte': dt_today,
        }
        queryset = queryset.filter(**dict_filter).order_by('start_date')
        serializer = EventFaireSerializer(queryset,
                                          context={'request': request},
                                          many=True)
        return Response(serializer.data)
