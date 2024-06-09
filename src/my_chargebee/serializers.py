from rest_framework import serializers

from my_chargebee import models


class CustomerSerializer(serializers.ModelSerializer):
    readable_locale = serializers.CharField(source="get_readable_locale")

    class Meta:
        model = models.Customer
        fields = "__all__"


class SubscriptionSerializer(serializers.ModelSerializer):
    next_billing_on = serializers.DateTimeField(
        source='next_billing_at', format='%d-%b-%Y %H:%m',
        required=False
    )
    converted_price = serializers.DecimalField(
        max_digits=7, decimal_places=2,
        source='get_converted_price', read_only=True
    )
    addons = serializers.CharField(source="get_formatted_addons")
    status_html = serializers.CharField(source="get_status_html")

    class Meta:
        model = models.Subscription
        fields = "__all__"


class SubscriptionListSerializer(serializers.ModelSerializer):
    list_format = serializers.CharField(source="get_list_format")

    class Meta:
        model = models.Subscription
        fields = ["id", "list_format"]


class InvoiceSerializer(serializers.ModelSerializer):
    amount = serializers.CharField()
    company = serializers.CharField()
    establishment = serializers.CharField()
    date = serializers.DateTimeField(format="%Y/%m/%d")

    class Meta:
        model = models.Invoice
        fields = ["id", "establishment", "company", "date", "status", "amount"]
