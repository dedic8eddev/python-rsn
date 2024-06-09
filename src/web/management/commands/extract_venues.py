import pandas as pd
from django.core.management.base import BaseCommand
from django.db.models import Q

from web.constants import PlaceStatusE
from web.management.commands._extraction import DBExtraction
from web.models import Place


class Command(BaseCommand, DBExtraction):
    args = ""
    help = "Extract all users from Database since specified date."

    def add_arguments(self, parser):
        parser.add_argument(
            '--subscription',
            action='store_true',
            help='Whether to extract venues with subscription or with no subscription'
        )

        parser.add_argument(
            '-status',
            type=int,
            default=20,
            help='Define venue status:'
                 'DRAFT = 10'
                 'IN_DOUBT = 15'
                 'SUBSCRIBER = 18'
                 'PUBLISHED = 20'
                 'CLOSED = 35'
        )

    def handle(self, *args, **options):
        """
        Extract all venues from Database.
        """
        subscription = options.get('subscription')
        status = int(options.get('status'))

        if status not in PlaceStatusE.values:
            raise ValueError("Invalid status value")
        status_name = PlaceStatusE.names.get(status)

        # make the data extraction
        df = self.extract(subscription, status)
        file_name = f"web_places_subscription_{str(subscription).lower()}_status_{status_name.lower()}.csv"

        df.to_csv(self.output_dir() / file_name, index=False)
        self.stdout.write('Venues extraction is DONE!')

    def extract(self, subscription, status):
        """
        Extract venues with/without subscription or in doubt status
        """
        filters = Q(**{
            'status': status,
            'subscription__isnull': not subscription
        })

        # get query set
        qs = Place.objects.filter(filters)

        # extract data to dataframe
        df = pd.DataFrame(
            list(qs.values('name', 'full_street_address', 'zip_code', 'city', 'country', 'email'))
        )

        return df
