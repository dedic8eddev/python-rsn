from csv import reader

import chargebee

from my_chargebee import models
from my_chargebee.utils import clean_data
from raisin import settings
from web.models import Place


def get_bulk_subscriptions_and_customers_from_chargebee():
    """Retrieves Chargebee Subscriptions and Customers and saves them to db"""

    chargebee.configure(
        settings.RAISIN_CHARGEBEE_SITE_API_KEY,
        settings.RAISIN_CHARGEBEE_SITE
    )

    result = {
        'customers': {'created': 0, 'updated': 0},
        'subscriptions': {'created': 0, 'updated': 0}
    }

    try:
        config = {'limit': 100}
        next_offset = True

        while next_offset:
            if next_offset is not True:
                config['offset'] = next_offset

            entries_slice = chargebee.Subscription.list(config)

            for entry in entries_slice:
                customer_data = clean_data("Customer", entry.customer.values)
                _, c_created = models.Customer.objects.update_or_create(
                    id=customer_data.get("id"), defaults=customer_data
                )

                sub_data = clean_data("Subscription", entry.subscription.values) # noqa
                _, s_created = models.Subscription.objects.update_or_create(
                    id=sub_data.get("id"), defaults=sub_data
                )

                key = 'created' if c_created else 'updated'
                result['customers'][key] += 1

                key = 'created' if s_created else 'updated'
                result['subscriptions'][key] += 1

            next_offset = entries_slice.next_offset

    except chargebee.APIError as ex:
        return {"exception": str(ex)}

    return result


def get_bulk_payment_sources_from_chargebee():
    """Retrieves Chargebee PaymentSources and saves them to db"""

    chargebee.configure(
        settings.RAISIN_CHARGEBEE_SITE_API_KEY,
        settings.RAISIN_CHARGEBEE_SITE
    )

    result = {'payment_sources': {'created': 0, 'updated': 0}}

    try:
        config = {'limit': 100}
        next_offset = True

        while next_offset:
            if next_offset is not True:
                config['offset'] = next_offset

            entries_slice = chargebee.PaymentSource.list(config)

            for entry in entries_slice:
                payment_source_data = clean_data("payment_source",
                                                 entry.payment_source.values)
                _, i_created = models.PaymentSource.objects.update_or_create(
                    id=payment_source_data.get("id"),
                    defaults=payment_source_data
                )

                key = 'created' if i_created else 'updated'
                result['payment_sources'][key] += 1

            next_offset = entries_slice.next_offset

    except chargebee.APIError as ex:
        return {"exception": str(ex)}

    return result


def get_bulk_invoices_from_chargebee():
    """Retrieves Chargebee Invoices and saves them to db"""

    chargebee.configure(
        settings.RAISIN_CHARGEBEE_SITE_API_KEY,
        settings.RAISIN_CHARGEBEE_SITE
    )

    result = {'invoices': {'created': 0, 'updated': 0}}

    try:
        config = {'limit': 100}
        next_offset = True

        while next_offset:
            if next_offset is not True:
                config['offset'] = next_offset

            entries_slice = chargebee.Invoice.list(config)

            for entry in entries_slice:
                invoice_data = clean_data("invoice", entry.invoice.values)
                _, i_created = models.Invoice.objects.update_or_create(
                    id=invoice_data.get("id"), defaults=invoice_data
                )

                key = 'created' if i_created else 'updated'
                result['invoices'][key] += 1

            next_offset = entries_slice.next_offset

    except chargebee.APIError as ex:
        return {"exception": str(ex)}

    return result


def get_bulk_events_from_chargebee():
    """Retrieves Chargebee Events and saves them to db"""

    chargebee.configure(
        settings.RAISIN_CHARGEBEE_SITE_API_KEY,
        settings.RAISIN_CHARGEBEE_SITE
    )

    result = {'events': {'created': 0, 'updated': 0}}

    try:
        config = {'limit': 100}
        next_offset = True

        while next_offset:
            if next_offset is not True:
                config['offset'] = next_offset

            entries_slice = chargebee.Event.list(config)

            for entry in entries_slice:
                event_data = clean_data("event", entry.event.values)
                _, i_created = models.Event.objects.update_or_create(
                    id=event_data.get("id"), defaults=event_data
                )

                key = 'created' if i_created else 'updated'
                result['events'][key] += 1

            next_offset = entries_slice.next_offset

    except chargebee.APIError as ex:
        return {"exception": str(ex)}

    return result


def add_subscriptions_to_places():
    counter = 0
    errors = []
    with open('cms.csv', 'r') as read_obj:

        csv_reader = reader(read_obj)
        for row in csv_reader:
            try:
                place = Place.active.get(pk=row[0])
                subscription = models.Subscription.objects.get(pk=row[1])
                place.subscription = subscription
                place.owner.customer = subscription.customer

                place.save()
                place.owner.save()

                counter = counter + 1
            except models.Subscription.DoesNotExist as e:
                errors.append(e)
            except Place.DoesNotExist as e:
                errors.append(e)

    return counter, errors
