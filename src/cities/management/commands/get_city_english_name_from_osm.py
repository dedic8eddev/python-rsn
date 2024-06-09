from django.core.management.base import BaseCommand
from cities.models import City
from cities.osm import get_osm_city_name_by_lon_lat


class Command(BaseCommand):
    help = 'Import English City name from OSM'

    def handle(self, *args, **options):
        cities = City.objects.filter(location__isnull=False, osm_name__exact='').distinct()
        print(cities.count())
        for city in cities:
            try:
                lon, lat = city.location.coords
                name = get_osm_city_name_by_lon_lat(lat=lat, lon=lon)
                if name:
                    # if city.name != name:
                    #     print(f'id: {city.id} | City name: {city.name} | OSM name: {name} | {lat, lon}')
                    city.osm_name = name
                    city.save()
                else:
                    print(f"Not found id: {city.id} | city:{city.name} | Country: {city.country.name} | {lat, lon} ")
            except Exception as e:
                print(f'Error: {e}')
