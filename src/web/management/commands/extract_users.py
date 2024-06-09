import pandas as pd
from django.core.management.base import BaseCommand
from django.db.models import Q

from web.management.commands._extraction import DBExtraction
from web.models import UserProfile


class Command(BaseCommand, DBExtraction):
    args = ""
    help = "Extract all users from Database since specified date."

    def add_arguments(self, parser):
        # Start extraction date
        parser.add_argument('date_from', type=str, help='The start extract date')

        # Lang: 'EN' or 'FR'
        parser.add_argument('--lang', type=str, default='EN', help="Specify lang to extract users for")

    def handle(self, *args, **options):
        """
        Extract all users from Database since specified date.
        Default 'lang' attribute value is 'EN'

        Examples:
            # Extract all users starting from '2020-08-18'
            python manage.py extract_users 2020-08-18

            # Extract all users starting from '2020-08-18' with lang is FR
            python manage.py extract_users 2020-08-18 --lang FR

            # Extract all users starting from '2020-08-18' with lang is EN
            python manage.py extract_users 2020-08-18 --lang EN
        """
        #  December 22h 2020.
        date_from = options.get('date_from')

        lang = options.get('lang')
        if lang.upper() not in ['EN', 'FR']:
            raise ValueError("Invalid lang attribute passed or not supported. Possible correct value: 'EN' or 'FR'")

        df = self.extract(date_from, lang=lang)

        df.to_csv(self.output_dir() / f"users_from_{date_from}_{lang.upper()}.csv", index=False)
        self.stdout.write('Users extraction is DONE!')

    def extract(self, date_from, lang):
        filters = Q(**{
            'date_joined__gte': pd.to_datetime(date_from).date(),
            'lang': lang.upper()
        })

        qs = UserProfile.objects.filter(filters)
        df = pd.DataFrame(list(qs.values('id', 'email', 'date_joined')))

        return df
