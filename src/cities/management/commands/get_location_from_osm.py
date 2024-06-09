from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from cities.models import City
from cities.osm import get_osm_city_location
from django.contrib.gis.geos import Point


class Command(BaseCommand):
    help = 'Import location from OSM and add zoom_scale'

    def handle(self, *args, **options):
        cities = City.objects.all()
        cities = cities.annotate(venues_count=Count('places', filter=Q(places__is_archived=False), distinct=True))
        cities = cities.filter(venues_count__gt=0)
        countries_updates = []
        regions_updates = []
        for city in cities:
            location = get_osm_city_location(city=city.name, state=city.region.name, country=city.country.name)
            if location:
                print(*location)
                city.location = Point(*location)
                print(city.location)
                city.save()

            country = city.country.name
            if country not in countries_updates:
                location = get_osm_city_location(country=country)
                if location:
                    print(*location)
                    city.country.location = Point(*location)
                    city.country.save()
                    countries_updates.append(country)

            region = city.region.name
            if region not in regions_updates:
                location = get_osm_city_location(state=region)
                if location:
                    print(*location)
                    city.region.location = Point(*location)
                    city.region.save()
                    regions_updates.append(region)
