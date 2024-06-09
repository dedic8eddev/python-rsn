from django.apps import apps
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Deletes all data from Chargebee related tables: Customers, '\
           'Subscriptions, Invoices, Events'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cust',
            action='store_true',
            help='Delete customers only.',
        )

        parser.add_argument(
            '--subs',
            action='store_true',
            help='Delete subscriptions only.',
        )

        parser.add_argument(
            '--inv',
            action='store_true',
            help='Delete invoices only.',
        )

        parser.add_argument(
            '--events',
            action='store_true',
            help='Delete events only.',
        )

        parser.add_argument(
            '--all',
            action='store_true',
            help='Delete all objects.',
        )

    def handle(self, *args, **options):
        if not (options['cust'] or options['subs'] or options['inv'] or options['events'] or options['all']):
            raise CommandError(
                'Please choose one of the following arguments along with '
                'your statement: --cust, --subs, --inv, --events, --all.')

        status = ""

        obj_dict = {
            "cust": "customer",
            "subs": "subscription",
            "inv": "invoice",
            "events": "event",
        }

        if options['all']:
            for obj in obj_dict:
                obj_class = apps.get_model("my_chargebee", obj_dict[obj])
                status = obj_class.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(
                    'Deleted: {} objects: {} \n'.format(status[0], status[1])
                ))
                return None

        obj_to_delete = ""
        for obj in obj_dict:
            if options[obj]:
                obj_to_delete = obj_dict[obj]
                break

        obj_class = apps.get_model("my_chargebee", obj_to_delete)
        status = obj_class.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(
            'Deleted: {} objects: {}'.format(status[0], status[1])
        ))
