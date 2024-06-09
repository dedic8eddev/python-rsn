from django.core.management.base import BaseCommand
from web.models import Place
from cities.osm import get_osm_city_and_country_name_by_lon_lat


class Command(BaseCommand):
    help = 'Import English City name from OSM'

    def handle(self, *args, **options):
        venues = Place.active.filter(new_city__isnull=True, latitude__isnull=False, longitude__isnull=False)
        print(venues.count())
        for venue in venues:
            city, country = get_osm_city_and_country_name_by_lon_lat(lat=venue.latitude, lon=venue.longitude)
            if city:
                if venue.osm_city_name != venue.city:
                    print(f'Venue id: {venue.id} | City name: {venue.city} | OSM name: {city} | '
                          f'{venue.latitude, venue.longitude}')
                venue.osm_city_name = city
                venue.osm_country_name = country
                venue.save()
            else:
                print(f"Not found city:{venue.city} | Venue id: {venue.id} | {venue.latitude, venue.longitude} ")
