from web.models import CalEvent
from datetime import datetime
from rest_framework.response import Response
from rest_framework.views import APIView
from web.serializers.events import EventFaireSerializer
from rest_framework.permissions import AllowAny
from rest_framework import status
from web.constants import CalEventTypeE, PostStatusE


class WineFaire(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            dt_today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            dict_filter = {
                'type': CalEventTypeE.EVENT,
                'end_date__gte': dt_today,
                'status': PostStatusE.PUBLISHED,
            }
            faire_data = CalEvent.objects.filter(**dict_filter).order_by('start_date')
            serializer = EventFaireSerializer(faire_data,
                                              context={'request': request},
                                              many=True)
            return Response({"response": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"response": str(e)}, status=status.HTTP_400_BAD_REQUEST)
