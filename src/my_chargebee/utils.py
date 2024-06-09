import chargebee
from datetime import datetime

from django.apps import apps

from my_chargebee import models, serializers
from raisin import settings
from web.constants import PlaceStatusE, PlaceSourceInfoE
from web.models import Place


def get_subscription(id):
    try:
        instance = models.Subscription.objects.get(pk=id)
    except models.Subscription.DoesNotExist:
        instance = get_subscription_from_chargebee(id)

    return instance


def get_subscription_from_chargebee(id):
    chargebee.configure(
        settings.RAISIN_CHARGEBEE_SITE_API_KEY,
        settings.RAISIN_CHARGEBEE_SITE
    )

    try:
        result = chargebee.Subscription.retrieve(id)
    except chargebee.APIError as ex:
        return {"exception": str(ex)}

    customer_data = clean_data("Customer", result.customer.values)
    models.Customer.objects.update_or_create(
        id=customer_data.get("id"), defaults=customer_data
    )

    sub_data = clean_data("Subscription", result.subscription.values)
    subscription, _ = models.Subscription.objects.update_or_create(
        id=sub_data.get("id"), defaults=sub_data
    )

    return subscription


def get_invoice_pdf_url_from_chargebee(id):
    chargebee.configure(
        settings.RAISIN_CHARGEBEE_SITE_API_KEY,
        settings.RAISIN_CHARGEBEE_SITE
    )

    result = chargebee.Invoice.pdf(id)

    return result.download.download_url


def clean_data(obj_str, data):
    obj_class = apps.get_model("my_chargebee", obj_str.replace('_', ''))
    data_copy = data.copy()
    for attr in data:
        if not hasattr(obj_class, attr):
            data_copy.pop(attr)
        if attr == "customer_id":
            data_copy["customer"] = models.Customer.objects.get(pk=data[attr])
        if attr == "subscription_id":
            data_copy["subscription"] = models.Subscription.objects.get(
                pk=data[attr]
            )
        if attr in ["next_billing_at",
                    "trial_start",
                    "trial_end",
                    "date",
                    "due_date",
                    "occurred_at"]:
            # convert from timestamp(UTC) in seconds to datetime
            data_copy[attr] = timestamp_to_formatted_date(data[attr])

    return data_copy


def timestamp_to_formatted_date(initial_date):
    if initial_date is None:
        return None

    date = datetime.fromtimestamp(initial_date)

    return date.strftime("%Y-%m-%dT%H:%M:%S")


def get_chargebee_class_from_str(object_str):
    switch_dict = {
        "subscription": chargebee.Subscription,
        "customer": chargebee.Customer,
        "plan": chargebee.Plan,
    }

    return switch_dict.get(object_str)


def get_serializer_from_str(object_str):
    switch_dict = {
        "subscription": serializers.SubscriptionSerializer,
        "customer": serializers.CustomerSerializer,
        "invoice": serializers.InvoiceSerializer,
    }

    return switch_dict.get(object_str)


def process_event(event_obj, event_type, data):
    if event_type == "deleted":
        id = data["content"][event_obj]["id"]
        obj_class = apps.get_model("my_chargebee", event_obj.replace('_', ''))
        try:
            obj = obj_class.objects.get(pk=id)
            obj.mark_as_deleted_from_chargebee()
        except obj_class.DoesNotExist:
            pass

        return True

    if event_obj == "subscription":
        customer_data = clean_data("Customer", data["content"]["customer"])
        models.Customer.objects.update_or_create(
            id=customer_data.get("id"), defaults=customer_data
        )

        sub_data = clean_data("Subscription", data["content"]["subscription"])
        subscription, _ = models.Subscription.objects.update_or_create(
            id=sub_data.get("id"), defaults=sub_data
        )

        sticker_sell_plans = [
            '2-AUTOCOLLANTS-RAISIN-50€-FR-TAX:FR',
            'fast-reg-sticker-$44.99-us-tax:world',
            'AUTOCOLLANT-Raisin-25€-fr-eu-tax:WORLD',
            'AUTOCOLLANT-Raisin-25€-fr-eu-tax:eur',
            'STICKER-RAISIN-25€-EUR-TAX:EUR',
            'AUTOCOLLANT-RAISIN-25€-FR-TAX:FR',
            'raisin-electrostatic-sticker-$25-[us]-[tax:world]'
        ]

        if event_type == "created" and subscription.plan_id not in \
                sticker_sell_plans:
            # create a fake venue based on info about subscription
            # received from ChargeBee
            if sub_data.get("shipping_address") and \
                    sub_data.get("shipping_address").get("company"):
                place_name = sub_data.get("shipping_address").get("company")
            elif customer_data.get("company"):
                place_name = customer_data.get("company")
            else:
                place_name = '{} {}'.format(
                    customer_data.get("first_name"),
                    customer_data.get("last_name")
                )

            if sub_data.get("shipping_address") and \
                    sub_data.get("shipping_address").get("email"):
                email = sub_data.get("shipping_address").get("email")
            else:
                email = customer_data.get("email")

            if sub_data.get("shipping_address") and \
                    sub_data.get("shipping_address").get("phone"):
                phone = sub_data.get("shipping_address").get("phone")
            else:
                phone = customer_data.get("phone")

            place_data = {}
            place_data["name"] = place_name
            place_data["email"] = email
            place_data["phone_number"] = phone

            shipping_address_dict = sub_data.get("shipping_address")
            billing_address_dict = customer_data.get("billing_address")

            if shipping_address_dict:
                address_lines = [
                    shipping_address_dict.get("line1"),
                    shipping_address_dict.get("line2"),
                    shipping_address_dict.get("line3"),
                ]
                city = shipping_address_dict.get("city")
                state = shipping_address_dict.get("state")
                zip_code = shipping_address_dict.get("zip")
                country = shipping_address_dict.get("country")
            elif billing_address_dict:
                address_lines = [
                    billing_address_dict.get("line1"),
                    billing_address_dict.get("line2"),
                    billing_address_dict.get("line3")
                ]
                city = billing_address_dict.get("city")
                state = billing_address_dict.get("state")
                zip_code = billing_address_dict.get("zip")
                country = billing_address_dict.get("country")
            else:
                address_lines = []
                city = None
                state = None
                zip_code = None
                country = None

            full_street_address = " ".join([line for line in address_lines if line])
            place_data["full_street_address"] = full_street_address
            place_data["city"] = city
            place_data["state"] = state
            place_data["zip_code"] = zip_code
            # TODO: temporary use of country iso code value for CMS
            # TODO: country field
            # TODO: as chargebee returns country iso code value only
            place_data["country"] = country

            place = Place(
                author_id=settings.RAISIN_CHARGEBEE_CMS_USER_UUID,
                status=PlaceStatusE.DRAFT,
                subscription_id=sub_data.get("id"),
                src_info=PlaceSourceInfoE.REGISTERED_ON_CHARGEBEE,
                missing_info=True,
                **place_data
            )
            place.save()
        return True

    obj_class = apps.get_model("my_chargebee", event_obj.replace('_', ''))
    data = clean_data(event_obj, data["content"][event_obj])

    obj_class.objects.update_or_create(
        id=data.get("id"), defaults=data
    )

    return True
