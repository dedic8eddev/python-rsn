from rest_framework import viewsets
from .serializers import (ContinentSerializer, CountrySerializer, CitySerializer, UrbanAreaSerializer)
from cities.models import (Continent, Country, City, UrbanArea)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import (F, Count, Q)


class ContintentViewSet(viewsets.ModelViewSet):
    serializer_class = ContinentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['^name']
    ordering_fields = ['name', 'venues_count', 'country_count']

    def get_queryset(self):
        qs = Continent.objects.all()
        qs = qs.annotate(
            venues_count=Count('countries__cities__places', distinct=True),
            country_count=Count(
                'countries',
                distinct=True,
                filter=Q(countries__cities__places__isnull=False)
            ),
            cities_count=Count(
                'countries__cities',
                distinct=True,
                filter=Q(countries__cities__places__isnull=False)
            )
        )
        qs = qs.prefetch_related('alt_names')
        return qs


class CountryViewSet(viewsets.ModelViewSet):
    serializer_class = CountrySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['^name'],
    filter_fields = ['continent__code']
    ordering_fields = ['name', 'cities_count', 'venues_count', 'urban_area_count', 'cities_and_ua']

    def get_queryset(self):
        qs = Country.objects.all()
        # qs = qs.filter(continent__code=self.kwargs.get('code'))
        qs = qs.annotate(venues_count=Count('cities__places', distinct=True))
        qs = qs.filter(venues_count__gt=0)
        qs = qs.annotate(
            cities_count=Count(
                'cities',
                distinct=True,
                filter=Q(cities__urban_area__isnull=True) & Q(cities__places__isnull=False)
            ),
            urban_area_count=Count(
                'cities__urban_area',
                distinct=True,
                filter=Q(cities__places__isnull=False)
            )
        ).annotate(cities_and_ua=F('cities_count') + F('urban_area_count'))
        # qs = qs.annotate(alt_name_codes=ArrayAgg('alt_names__language_code', distinct=True))
        return qs


class CityViewSet(viewsets.ModelViewSet):
    serializer_class = CitySerializer
    queryset = City.objects.all()
    search_fields = ['^name']


class UrbanAreaViewSet(viewsets.ModelViewSet):
    serializer_class = UrbanAreaSerializer
    queryset = UrbanArea.objects.all()
    search_fields = ['^name']
