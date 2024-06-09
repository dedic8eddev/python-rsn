from rest_framework import serializers


class APIVersionSerializer(serializers.Serializer):
    app_version = serializers.CharField(required=True)
    build_version = serializers.CharField(required=False)
