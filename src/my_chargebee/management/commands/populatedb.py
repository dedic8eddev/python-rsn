from django.core.management.base import BaseCommand, CommandError

from my_chargebee import helpers


class Command(BaseCommand):
    help = 'Populates database with Chargebee specific objects:'\
           ' Subscriptions, Customers, Payment Sources, Events, Invoices.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sub-cust',
            action='store_true',
            help='Update subscriptions and customers only.',
        )

        parser.add_argument(
            '--payment-sources',
            action='store_true',
            help='Update payment sources only.',
        )

        parser.add_argument(
            '--inv',
            action='store_true',
            help='Update invoices only.',
        )

        parser.add_argument(
            '--events',
            action='store_true',
            help='Update events only.',
        )

        parser.add_argument(
            '--all',
            action='store_true',
            help='Update all objects.',
        )

    def handle(self, *args, **options):
        if not (options['sub_cust'] or
                options['payment_sources'] or
                options['inv'] or
                options['events'] or
                options['all']):
            raise CommandError(
                'Please choose one of the following arguments along with '
                'your statement: --sub-cust, --payment-sources --inv, '
                '--events, --all.')

        if options['sub_cust'] or options['all']:
            self.get_subscriptions_and_customers()

        if options['payment_sources'] or options['all']:
            self.get_payment_sources()

        if options['events'] or options['all']:
            self.get_events()

        if options['inv'] or options['all']:
            self.get_invoices()

    def get_subscriptions_and_customers(self):
        r1 = helpers.get_bulk_subscriptions_and_customers_from_chargebee()
        self.stdout.write(self.style.SUCCESS(
            'Status for subscriptions and customers: {}'.format(r1)
        ))

    def get_payment_sources(self):
        r2 = helpers.get_bulk_payment_sources_from_chargebee()
        self.stdout.write(self.style.SUCCESS(
            'Status for payment_sources: {}'.format(r2)
        ))

    def get_invoices(self):
        r2 = helpers.get_bulk_invoices_from_chargebee()
        self.stdout.write(self.style.SUCCESS(
            'Status for invoices: {}'.format(r2)
        ))

    def get_events(self):
        r2 = helpers.get_bulk_events_from_chargebee()
        self.stdout.write(self.style.SUCCESS(
            'Status for events: {}'.format(r2)
        ))
