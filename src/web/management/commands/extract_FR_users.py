from django.core.management.base import BaseCommand
from django.db.models import Q

from web.management.commands import any_queryset_to_CSV
from web.models import UserProfile


class Command(BaseCommand):
    args = ""
    help = "writes your QuerySet into CSV"

    def handle(self, *args, **options):
        qs = get_users_qs()

        any_queryset_to_CSV.qs_to_local_csv(
            qs,
            fields=[
                'username',
                'email',
                'lang',
                'id'
            ]
        )


def get_users_qs():
    users_qs = UserProfile.active.filter(
        Q(lang__in=['FR', 'fr', 'Fr', 'France']) |
        Q(email__iregex=r'.*\.fr') |
        Q(email__iregex=r'.*laposte\.net')
    ).exclude(
        email__icontains='_erased'
    )
    return users_qs
