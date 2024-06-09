from django.core.management.base import BaseCommand

from web.management.commands import any_queryset_to_CSV
from web.models import Winemaker
from web.constants import WinemakerStatusE


class Command(BaseCommand):
    args = ""
    help = "writes your QuerySet into CSV"

    def handle(self, *args, **options):
        qs = get_winemakers_qs()

        any_queryset_to_CSV.qs_to_local_csv(
            qs,
            fields=[
                'name',
                'author__full_name',
                'region',
                'city',
                'country',
                'created_time',
                'domain',
                'email',
                'in_doubt',
                'is_archive',
                'is_biodynamic',
                'is_organic',
                'id'
            ]
        )


def get_winemakers_qs():
    winemakers_qs = Winemaker.active.filter(
        status=WinemakerStatusE.VALIDATED
    ).filter(country__in=['France', 'Belgium', 'Switzerland'])
    return winemakers_qs
