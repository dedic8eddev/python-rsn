import json
import pycountry

from django.db.models import JSONField
from django.db import models

from forex_python.converter import CurrencyCodes

from web import models as web_models


class ChargebeeCustomManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted_from_chargebee=False)


class ChargebeeArchivedObjectsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted_from_chargebee=True)


class ChargebeeBaseModel(models.Model):
    id = models.TextField(null=False, primary_key=True)
    is_deleted_from_chargebee = models.BooleanField(null=False, default=False)

    objects = ChargebeeCustomManager()
    archived = ChargebeeArchivedObjectsManager()

    def mark_as_deleted_from_chargebee(self):
        self.is_deleted_from_chargebee = True
        self.save()

    class Meta:
        abstract = True


class Customer(ChargebeeBaseModel):
    auto_collection = models.CharField(
        max_length=10, null=False, default="n.d."
    )
    billing_address = JSONField(null=True)
    company = models.TextField(null=True)
    email = models.EmailField(null=True)
    first_name = models.TextField(null=True)
    last_name = models.TextField(null=True)
    locale = models.CharField(null=True, max_length=20)
    phone = models.TextField(null=True)
    payment_method = JSONField(null=True)
    primary_payment_source_id = models.CharField(null=True, max_length=255)
    preferred_currency_code = models.CharField(null=True, max_length=10)
    vat_number = models.CharField(null=True, max_length=20)

    def get_readable_locale(self):
        if self.locale is not None and "-" not in self.locale:
            return pycountry.languages.get(alpha_2=self.locale).name.title()

        if self.locale is None:
            return None

        lang_code, country_code = self.locale.split("-")
        country = pycountry.countries.get(alpha_2=country_code).name.title()
        language = pycountry.languages.get(alpha_2=lang_code).name.title()

        return "{} ({})".format(language, country)

    def has_active_subscription(self):
        active_subscriptions = [Subscription.ACTIVE, Subscription.IN_TRIAL]
        for subscription in self.subscription_set.all():
            if subscription.status in active_subscriptions:
                return subscription

        return False

    def mark_as_deleted_from_chargebee(self):
        for subscription in self.subscription_set.all():
            subscription.is_deleted_from_chargebee = True
            subscription.save()

        for invoice in self.invoice_set.all():
            invoice.is_deleted_from_chargebee = True
            invoice.save()

        super().mark_as_deleted_from_chargebee()


class PaymentSource(ChargebeeBaseModel):
    PAYMENT_SOURCES = (
        ('card', 'card'),
        ('paypal_express_checkout', 'paypal_express_checkout'),
        ('amazon_payments', 'amazon_payments'),
        ('direct_debit', 'direct_debit'),
        ('generic', 'generic'),
        ('alipay', 'alipay'),
        ('unionpay', 'unionpay'),
        ('apple_pay', 'apple_pay'),
        ('wechat_pay', 'wechat_pay'),
        ('ideal', 'ideal'),
        ('google_pay', 'google_pay'),
        ('sofort', 'sofort'),
        ('bancontact', 'bancontact'),
        ('giropay', 'giropay'),
        ('dotpay', 'dotpay'),
        ('upi', 'upi'),
        ('netbanking_emandates', 'netbanking_emandates'),
    )

    STATUSES = (
        ('valid', 'valid'),
        ('expiring', 'expiring'),
        ('expired', 'expired'),
        ('invalid', 'invalid'),
        ('pending_verification', 'pending_verification'),
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    type = models.CharField(max_length=23, choices=PAYMENT_SOURCES)
    status = models.CharField(max_length=20, choices=STATUSES, default='valid')
    card = JSONField(blank=True, null=True)


class Subscription(ChargebeeBaseModel):
    original_status = None

    def __init__(self, *args, **kwargs):
        super(Subscription, self).__init__(*args, **kwargs)
        self.original_status = self.status

    def __str__(self):
        return "{} - {} - {}".format(self.id, self.plan_id, self.status)

    # ToDo: use project variable instead of username='chargebee' query
    # ToDo: after including RAISIN_CHARGEBEE_CMS_USER_UUID variable into code
    # ToDo: from chargebee_webhooks branch
    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        chargebee_edit_user = web_models.UserProfile.objects.get(
            username='chargebee'
        )

        if self.status != self.original_status and self.place_set.all().count(): # noqa
            self.place_set.first().last_modifier = chargebee_edit_user
            self.place_set.first().save(
                modified_time=True, last_modifier=chargebee_edit_user
            )

        super(Subscription, self).save(*args, **kwargs)
        self.original_status = self.status

    event_based_addons = JSONField(null=True)
    shipping_address = JSONField(null=True)
    auto_collection = models.CharField(
        max_length=10, null=False, default="n.d."
    )
    billing_period = models.IntegerField(null=True)
    billing_period_unit = models.CharField(max_length=10, null=True)
    currency_code = models.CharField(null=False, max_length=10)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    mrr = models.FloatField(null=True, blank=True)
    next_billing_at = models.DateTimeField(null=True, blank=True)
    plan_id = models.CharField(null=False, max_length=50)
    plan_unit_price = models.DecimalField(
        null=True, max_digits=7, decimal_places=2
    )
    trial_end = models.DateTimeField(null=True, blank=True)
    trial_start = models.DateTimeField(null=True, blank=True)

    FUTURE = 'future'
    IN_TRIAL = 'in_trial'
    ACTIVE = 'active'
    NON_RENEWING = 'non_renewing'
    PAUSED = 'paused'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = (
        (FUTURE, 'future'),
        (IN_TRIAL, 'in_trial'),
        (ACTIVE, 'active'),
        (NON_RENEWING, 'non_renewing'),
        (PAUSED, 'paused'),
        (CANCELLED, 'cancelled'),
    )
    status = models.CharField(
        null=False, choices=STATUS_CHOICES, max_length=20
    )

    def get_converted_price(self):
        return self.plan_unit_price / 100

    def get_formatted_addons(self):
        if self.event_based_addons is None:
            return None
        addons = ""
        addons_json = json.dumps(self.event_based_addons)
        for addon in json.loads(addons_json):
            addons += "{} ,".format(addon['id'])

        return addons[:-2]

    def get_status_html(self):
        formatter_dict = {
            "future": {
                'class': 'btn-cgb-future',
                'text': 'FUTURE',
            },
            "in_trial": {
                'class': 'btn-cgb-in-trial',
                'text': 'IN_TRIAL',
            },
            "active": {
                'class': 'btn-cgb-active',
                'text': 'ACTIVE',
            },
            "non_renewing": {
                'class': 'btn-cgb-non-renewing',
                'text': 'NON_RENEWING',
            },
            "paused": {
                'class': 'btn-cgb-paused',
                'text': 'PAUSED',
            },
            "cancelled": {
                'class': 'btn-cgb-cancelled',
                'text': 'CANCELLED',
            },
        }

        status_html = \
            '<button class="{} btn btn-xs" type="button">{}</button>'.format(
                formatter_dict[self.status]['class'],
                formatter_dict[self.status]['text'],
            )

        return status_html

    def get_list_format(self):
        return str(self)

    @property
    def periodicity(self):
        periods = {
            '1_day': 'daily',
            '1_week': 'weekly',
            '1_month': 'monthly',
            '3_month': 'quarterly',
            '6_month': 'semianually',
            '1_year': 'annually'
        }

        period = "{}_{}".format(self.billing_period, self.billing_period_unit)

        if period in periods:
            return periods[period]

        return "every {} {}s".format(
            self.billing_period, self.billing_period_unit
        )

    def mark_as_deleted_from_chargebee(self):
        for invoice in self.invoice_set.all():
            invoice.is_deleted_from_chargebee = True
            invoice.save()

        super().mark_as_deleted_from_chargebee()


class Invoice(ChargebeeBaseModel):
    PAID = 'paid'
    POSTED = 'posted'
    PAYMENT_DUE = 'payment_due'
    NOT_PAID = 'not_paid'
    VOIDED = 'voided'
    PENDING = 'pending'

    STATUS_CHOICES = (
        (PAID, 'paid'),
        (POSTED, 'posted'),
        (PAYMENT_DUE, 'payment_due'),
        (NOT_PAID, 'not_paid'),
        (VOIDED, 'voided'),
        (PENDING, 'pending'),
    )

    currency_code = models.CharField(null=True, max_length=10)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        null=False, choices=STATUS_CHOICES, max_length=20
    )
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    total = models.DecimalField(null=True, max_digits=10, decimal_places=2)

    @property
    def amount(self):
        return self.currency_symbol + str(self.total / 100)

    @property
    def company(self):
        b_address_customer_json = json.dumps(self.customer.billing_address)
        b_address_customer = json.loads(b_address_customer_json)\
            .get('company') if self.customer.billing_address else None

        return self.customer.company or b_address_customer

    @property
    def establishment(self):
        return web_models.Place.objects.filter(
            subscription__id=self.subscription.id
        ).first()

    @property
    def currency_symbol(self):
        return CurrencyCodes().get_symbol(self.currency_code)


class Event(ChargebeeBaseModel):
    content = JSONField(null=True)
    event_type = models.CharField(null=True, max_length=255)
    occurred_at = models.DateTimeField(null=True)

    PROCESSED = 1
    NOT_PROCESSED = 0

    STATUS_CHOICES = (
        (PROCESSED, 'processed'),
        (NOT_PROCESSED, 'not processed')
    )

    status = models.BooleanField(
        null=False, choices=STATUS_CHOICES, default=NOT_PROCESSED
    )

    def is_not_processed(self):
        return not self.status
