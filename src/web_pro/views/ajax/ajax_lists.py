from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from my_chargebee.models import Subscription
from my_chargebee.serializers import InvoiceSerializer
from web.constants import WineStatusE
from web.models import Wine, Winemaker
from web.utils.wine_utils import get_wine_status_image


# /pro/ajax/typeahead/<str option>
@login_required
def get_typeahead_data(request, option):
    result = []
    if option == 'wine_name':
        q_param = request.GET.get('q', '')
        items_out = Wine.active.exclude(status=WineStatusE.HIDDEN).filter(
            posts__is_archived=False, posts__is_parent_post=True,
            winemaker__is_archived=False, name__unaccent__istartswith=q_param
        ).values(
            'id', 'name', 'domain', 'winemaker__name',
            'posts__status', 'grape_variety', 'color', 'is_sparkling'
        ).distinct()

        for item in items_out:
            item['image'] = get_wine_status_image(item['posts__status'])
        result = list(items_out)

    elif option == 'winemakers':
        result = Winemaker.objects.filter(
            is_archived=False
        ).order_by('name').values_list('name', flat=True).distinct()

        result = list(result)

    elif option == 'domain':
        result = Wine.objects.filter(
            is_archived=False,
            winemaker__is_archived=False
        ).order_by('domain').values_list('domain', flat=True).distinct()

        result = list(result)

    return JsonResponse({'result': result})


# /pro/ajax/settings/invoices/$
@login_required
def get_invoices(request):
    subscription_id = request.GET.get('subscription_id')

    try:
        subscription = Subscription.objects.get(pk=subscription_id)
        invoices = subscription.invoice_set.exclude(total=Decimal('0.00'))
    except Subscription.DoesNotExist:
        subscription = None
        invoices = None

    serializer = InvoiceSerializer(invoices, many=True)

    return JsonResponse({'data': serializer.data})
