from rest_framework.serializers import ModelSerializer
from web.models import FormitableRequest


class FormitableRequestSerialiser(ModelSerializer):
    class Meta:
        model = FormitableRequest
        fields = ('request_data', )
