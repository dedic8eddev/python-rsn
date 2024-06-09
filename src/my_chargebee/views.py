import datetime

from django.http import JsonResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from my_chargebee import models, utils, serializers

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from web.models import Place
from web.utils.views_common import get_current_user


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def get_subscription_details(request):

    current_user = get_current_user(request)

    if request.method == "DELETE":

        place = Place.objects.get(id=request.data.get('placeId'))
        place.subscription = None
        place.last_modifier = current_user
        place.expert = current_user
        place.is_expert_modified = True
        place.modified_time = datetime.datetime.now()
        place.save()
        place.refresh_from_db()
        return JsonResponse(
            {"data": _("Subscription deleted.")}, status=200, safe=False
        )

    if request.method == "GET":
        place = Place.objects.get(id=request.GET.get('placeId'))
        subscription = place.subscription
        customer = subscription.customer

    else:
        subscription_id = request.POST.get('subscriptionId')
        if subscription_id is None or subscription_id == "":
            return JsonResponse(
                {"exception": _("Please insert a subscription ID.")},
                status=404, safe=False
            )

        subscription = utils.get_subscription(subscription_id)

        if isinstance(subscription, dict):
            return JsonResponse(subscription, status=404, safe=False)

        if subscription.place_set.all().count() != 0:
            return JsonResponse(
                {"exception":
                    _("Subscription ID is already assigned to an"
                      " establishment.")},
                status=404, safe=False
            )

        place = Place.objects.get(id=request.POST.get('placeId'))

        customer = subscription.customer

        if place.owner is None:
            return JsonResponse(
                {"exception":
                    _("Please assign an owner to this establishment first.")},
                status=404, safe=False
            )

        if place.owner.customer and place.owner.customer != customer:
            return JsonResponse(
                {"exception":
                    _("The owner of this place is linked to a different "
                      "Chargebee Customer ID than the subscription you are"
                      " trying to submit.")},
                status=404, safe=False
            )

        if customer.userprofile_set.all().count() > 0 and \
                customer.userprofile_set.all().first() != place.owner:
            return JsonResponse(
                {"exception":
                    _("The Chargebee Customer that has this subscription"
                      " is already linked to a different establishment"
                      " owner.")},
                status=404, safe=False
            )

        place.last_modifier = current_user
        place.expert = current_user
        place.is_expert_modified = True
        place.modified_time = datetime.datetime.now()

        place.subscription = subscription
        place.owner.customer = customer
        place.save()
        place.owner.save()
        place.refresh_from_db()

    billing_address = customer.billing_address\
        if customer.billing_address else None

    return JsonResponse({
        "subscription": serializers.SubscriptionSerializer(subscription).data,
        "customer": serializers.CustomerSerializer(customer).data,
        "billing_address": billing_address,
    }, safe=False)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def chargebee_webhook(request):
    my_objects = ["subscription", "customer", 'invoice', 'payment_source']
    event_obj = None

    for obj in my_objects:
        # event_type e.g.: invoice_generated, invoice_updated, invoice_deleted
        if obj in request.data.get("event_type"):
            event_obj = obj
            obj_str = obj + "_"
            event_type = request.data.get("event_type").replace(obj_str, "")

    event, _ = models.Event.objects.get_or_create(pk=request.data.get("id"))

    if event_obj and event.is_not_processed():
        utils.process_event(event_obj, event_type, request.data)

    event.status = event.PROCESSED
    event.save()

    return JsonResponse({"response": "event processed"}, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_invoice_pdf_url(request):
    id = request.GET.get('id')

    return JsonResponse(
        {'url': utils.get_invoice_pdf_url_from_chargebee(id)},
        status=200
    )
