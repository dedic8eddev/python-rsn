from django.urls import path
from .views import (ContinentListView, ContinentUpdateView, CountryListView, CountryUpdateView,
                    UrbanAreaAndCitiesListView, CitiesByUAListView, CityUpdateView, UrbanAreaUpdateView,
                    VenuesByCityListView, RegionListView, RegionUpdateView, DistrictListView, DistrictUpdateView,
                    DistrictCreateView)

urlpatterns = [
    path('', ContinentListView.as_view(), name='continent_list'),
    path('<slug:slug>/edit/<str:language>', ContinentUpdateView.as_view(), name="continent_update"),
    path('<slug:continent_slug>/', CountryListView.as_view(),
         name='country_list'),
    path('<slug:continent_slug>/<slug:slug>/edit/<str:language>', CountryUpdateView.as_view(),
         name='country_update'),
    path('<slug:continent_slug>/<str:country_slug>/',
         RegionListView.as_view(),
         name='region_list'),
    path('<slug:continent_slug>/<str:country_slug>/<str:slug>/edit/<str:language>/',
         RegionUpdateView.as_view(),
         name='region_update'),
    path('<slug:continent_slug>/<slug:country_slug>/<str:slug>/',
         UrbanAreaAndCitiesListView.as_view(),
         name='ua_cities_list'),
    path('<slug:continent_slug>/<str:country_slug>/<str:region_slug>/<str:name>/',
         CitiesByUAListView.as_view(),
         name='cities_by_ua_list'),
    path('<slug:continent_slug>/<str:country_slug>/<str:region_slug>/districts/<str:city_slug>/',
         DistrictListView.as_view(),
         name='district_list'),
    path('<slug:continent_slug>/<str:country_slug>/<str:region_slug>/districts/<str:city_slug>/<str:slug>/'
         '<str:language>/',
         DistrictUpdateView.as_view(),
         name='district_update'),
    path('districts/new/district_create/<slug:continent_code>/<str:country_slug>/<str:region_slug>/districts/'
         '<str:city_slug>/<str:language>/',
         DistrictCreateView.as_view(),
         name='district_create'),
    path('<slug:continent_slug>/<str:country_slug>/<str:region_slug>/city/<str:slug>/',
         VenuesByCityListView.as_view(),
         name='venues_by_city_list'),
    path('<slug:continent_slug>/<str:country_slug>/<str:region_slug>/city_<str:slug>/edit/<str:language>/',
         CityUpdateView.as_view(),
         name='city_update'),
    path('<slug:continent_slug>/<str:country_slug>/<str:region_slug>/ua_<str:pk>/edit/<str:language>/',
         UrbanAreaUpdateView.as_view(),
         name='ua_update'),
    path('<slug:continent_slug>/<str:country_slug>/<str:region_slug>/<str:name>/city_<str:slug>/',
         VenuesByCityListView.as_view(),
         name='venues_by_ua_city_list'),
    # path(r'^$', place_views.places, name="list_places"),
]
