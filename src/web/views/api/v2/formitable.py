from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework import permissions
from web.serializers.formitable import FormitableRequestSerialiser
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST


class AppInstallView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=FormitableRequestSerialiser,
        operation_summary='Formitable Webhook uninstalled up',
        operation_description='Formitable Webhook uninstalled up',
        security=[]
    )
    def post(self, request, format=None):
        json_data = request.data
        data = {
            'request_data': json_data
        }
        formitable_request = FormitableRequestSerialiser(data=data)
        if formitable_request.is_valid():
            formitable_request.save()
            return Response(status=HTTP_200_OK)
        else:
            return Response(status=HTTP_400_BAD_REQUEST)


class AppUnInstallView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=FormitableRequestSerialiser,
        operation_summary='Formitable Webhook uninstalled up',
        operation_description='Formitable Webhook uninstalled up',
        security=[]
    )
    def post(self, request, format=None):
        json_data = request.data
        data = {
            'request_data': json_data
        }
        formitable_request = FormitableRequestSerialiser(data=data)
        if formitable_request.is_valid():
            formitable_request.save()
            return Response(status=HTTP_200_OK)
        else:
            return Response(status=HTTP_400_BAD_REQUEST)
