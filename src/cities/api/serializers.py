from rest_framework import serializers
from cities.models import (AlternativeName, Continent, Country, City, UrbanArea, Region, District)


class AlternativeNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlternativeName
        fields = '__all__'


class ContinentSerializer(serializers.ModelSerializer):
    venues_count = serializers.IntegerField(default=0)
    country_count = serializers.IntegerField(default=0)
    cities_count = serializers.IntegerField(default=0)

    class Meta:
        model = Continent
        fields = '__all__'


class CountrySerializer(serializers.ModelSerializer):
    alt_names = AlternativeNameSerializer(many=True)

    class Meta:
        model = Country
        fields = '__all__'


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'


class UrbanAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UrbanArea
        fields = '__all__'


class ContinentShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Continent
        fields = [
            'id',
            'name',
        ]


class CountryShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = [
            'id',
            'name',
            'code'
        ]


class RegionShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = [
            'id',
            'name',
            'name_std',
            'code'
        ]


class CityShortSerializer(serializers.ModelSerializer):
    slug_city = serializers.CharField(source='slugify')

    class Meta:
        model = City
        fields = [
            'id',
            'name',
            'slug_city'
        ]


class DistrictShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = [
            'id',
            'name'
        ]


class UrbanAreaShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = UrbanArea
        fields = [
            'id',
            'name'
        ]


class CityLineSerializer(serializers.Serializer):
    """
    Serializer for searching Country,Region,City
    """
    continent = ContinentShortSerializer(read_only=True, required=False)
    country = CountryShortSerializer(read_only=True, required=False)
    region = RegionShortSerializer(read_only=True, required=False)
    city = CityShortSerializer(read_only=True, required=False)
    districts = DistrictShortSerializer(read_only=True, required=False, many=True)


class CitiesAutocompleteQueryParametersSerializer(serializers.Serializer):
    search = serializers.CharField(required=True)


class CitiesAutocompleteResultSerializer(serializers.Serializer):
    value = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    venues_count = serializers.IntegerField()

    def get_value(self, obj):
        return f'{obj.name} [{obj.__class__.__name__}]'

    def get_url(self, obj):
        return obj.get_absolute_url()
