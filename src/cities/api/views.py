from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import DestroyAPIView

from cities.api.serializers import CityLineSerializer, CitiesAutocompleteQueryParametersSerializer, \
    CitiesAutocompleteResultSerializer
from cities.models import City, Country, Region, District, UrbanArea
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Count


class SearchCityView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """
        Return a list of all users.
        """
        if self.request.query_params.get('city'):
            qs = City.objects.filter(name=self.request.query_params.get('city'))
            if qs.exists():
                if qs.count() == 1:
                    city = qs.first()
                else:
                    if not self.request.query_params.get('lat') or not self.request.query_params.get('lng'):
                        return Response({'error': 'lan ant lng is required'}, status=400)
                    # lat: 55.755826, lng: 37.6173
                    lat = self.request.query_params.get('lat')
                    lng = self.request.query_params.get('lng')
                    ref_location = Point(float(lng), float(lat), srid=4326)
                    qs = qs.annotate(distance=Distance('location', ref_location)).order_by('distance')
                    city = qs.first()

                data = {
                    'continent': city.country.continent,
                    'country': city.country,
                    'region': city.region,
                    'city': city,
                    'districts': city.districts.all().order_by('name')
                }
                serializer = CityLineSerializer(data)
                return Response(serializer.data, status=200)
            else:
                return Response({'error': 'City not found'}, status=404)
        else:
            raise Response({'error': 'City is required'}, status=400)


class CitiesAutocompleteView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        query_serializer=CitiesAutocompleteQueryParametersSerializer,
        operation_summary='Search cities entities.',
        operation_description='Search cities entities by name for auticomplete feature',
        security=[]
    )
    def get(self, request, format=None):
        search_name = request.query_params.get('search')
        list_data = []
        cities = City.objects.filter(name__istartswith=search_name)
        cities = cities.annotate(venues_count=Count('places', distinct=True))
        cities = cities.filter(venues_count__gt=0)
        countries = Country.objects.filter(name__istartswith=search_name)
        countries = countries.annotate(venues_count=Count('cities__places', distinct=True))
        countries = countries.filter(venues_count__gt=0)
        regions = Region.objects.filter(name__istartswith=search_name)
        regions = regions.annotate(venues_count=Count('cities__places', distinct=True))
        regions = regions.filter(venues_count__gt=0)
        urban_areas = UrbanArea.objects.filter(name__istartswith=search_name)
        urban_areas = urban_areas.annotate(venues_count=Count('cities__places', distinct=True))
        urban_areas = urban_areas.filter(venues_count__gt=0)
        districts = District.objects.filter(name__istartswith=search_name)
        districts = districts.annotate(venues_count=Count('places', distinct=True))
        districts = districts.filter(venues_count__gt=0)
        list_data.extend(list(countries))
        list_data.extend(list(regions))
        list_data.extend(list(urban_areas))
        list_data.extend(list(cities))
        list_data.extend(list(districts))
        list_data_new = sorted(list_data, key=lambda d: d.venues_count, reverse=True)
        serializer = CitiesAutocompleteResultSerializer(list_data_new, many=True)
        return Response({"suggestions": serializer.data})


class DistrictDeleteApiView(DestroyAPIView):
    queryset = District.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
