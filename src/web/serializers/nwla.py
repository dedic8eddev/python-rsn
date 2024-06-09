from web.models import NWLAExcludedWord
from rest_framework import serializers


class ExcludedWordSerializer(serializers.ModelSerializer):
    class Meta:
        model = NWLAExcludedWord
        fields = ['id', 'word']
        read_only_fields = ('id', )

    def create(self, validated_data):
        if 'request' in self.context and self.context['request']:
            validated_data['author'] = self.context['request'].user
        return NWLAExcludedWord.objects.create(**validated_data)
