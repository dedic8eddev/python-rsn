from django.core.management.base import BaseCommand

from web.models import Place
from web.constants import PlaceStatusE


class Command(BaseCommand):
    args = ""
    help = "sets status 'Subscriber' for Published (which have " \
           "status=Published) Places, which have a " \
           "Subscription " \
           "with Subscription.status in [in_trial, active, paused, " \
           "non_renewing]"

    def handle(self, *args, **options):
        Place.active.filter(
            status=PlaceStatusE.PUBLISHED,
            subscription__status__in=['in_trial',
                                      'active',
                                      'paused',
                                      'non_renewing']
        ).update(status=PlaceStatusE.SUBSCRIBER)
