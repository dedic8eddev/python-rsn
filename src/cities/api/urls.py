from .viewsets import ContintentViewSet, CountryViewSet, CityViewSet, UrbanAreaViewSet
from .views import SearchCityView, CitiesAutocompleteView, DistrictDeleteApiView
from rest_framework.routers import DefaultRouter
from django.urls import path


router = DefaultRouter()
router.register(r'continents', ContintentViewSet, basename='continents_api')
router.register(r'countries', CountryViewSet, basename='countries_api')
router.register(r'cities', CityViewSet, basename='cities_api')
router.register(r'urban_areas', UrbanAreaViewSet, basename='urban_areas_api')
urlpatterns = router.urls
urlpatterns += [
    path('districts/<int:pk>', DistrictDeleteApiView.as_view(), name='delete_district_api_view'),
    path('search_city/', SearchCityView.as_view(), name='search_city'),
    path('cities_autocomplete/', CitiesAutocompleteView.as_view(), name='search_cities_autocomplete')
]
