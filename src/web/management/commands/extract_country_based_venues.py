from django.core.management.base import BaseCommand

from web.management.commands import any_queryset_to_CSV
from web.models import Place
from web.constants import PlaceStatusE


class Command(BaseCommand):
    args = ""
    help = "writes your QuerySet into CSV"

    def handle(self, *args, **options):
        qs = get_venues_qs()

        any_queryset_to_CSV.qs_to_local_csv(
            qs,
            fields=[
                'name',
                'author__full_name',
                'owner__full_name',
                'city',
                'country',
                'created_time',
                'email',
                'id'
            ]
        )


def get_venues_qs():
    venues_qs = Place.active.filter(
        status__in=[
            PlaceStatusE.SUBSCRIBER,
            PlaceStatusE.PUBLISHED]
    ).filter(country__in=['France', 'Belgium', 'Switzerland'])
    return venues_qs
