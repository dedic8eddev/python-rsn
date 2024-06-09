from django.core.management.base import BaseCommand
from web.models import Place
from cities.models import City
from django.db.models import Q


class Command(BaseCommand):
    help = 'Link venue to Urban Area city by city name'

    def handle(self, *args, **options):
        venues = Place.active.filter(new_city__isnull=True)
        print(venues.count())
        for venue in venues:
            new_city = City.objects.filter(Q(name=venue.city) | Q(osm_name=venue.osm_city_name),
                                           Q(country__name=venue.country) |
                                           Q(country__name=venue.osm_country_name)).first()
            if new_city:
                venue.new_city = new_city
                venue.save()
                print(f'Saved Venue id: {venue.id} | City: {venue.city} | Country: {venue.country}')
            else:
                print(f'Not found Venue id: {venue.id} | City: {venue.city} | Country: {venue.country} '
                      f'| OSM City: {venue.osm_city_name} | OSM Country: {venue.osm_country_name}')
