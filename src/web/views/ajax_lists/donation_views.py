from django.contrib.auth.decorators import login_required
from django.db.models import FloatField, OuterRef, Q, Subquery, Sum
# from django.conf import settings
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from web.constants import DonationFrequencyE
from web.forms.admin_forms import AjaxListForm
from web.models import Donation, UserProfile
from web.utils.exceptions import WrongParametersError
from web.utils.views_common import get_current_user
from web.views.ajax_lists.common import (
    ajax_list_control_with_search_and_ordering, ajax_list_get_offsets)
from web.views.ajax_lists.formatting import format_user_html


# /ajax/est-com/items
@csrf_exempt
@login_required
def get_donation_items(request):
    get_current_user(request)
    page = None
    limit = None
    order_by = '-modified_time'
    start = None
    length = None
    search_value = None
    col_map = {
        0: None,  # 'id',
        1: 'author__username',  # user img
        2: 'author__email',  # user username + link
        3: 'modified_time',  # date of payment
        4: 'value',
        5: 'frequency',
        6: 'date_from',  # place name
        7: 'date_to',  # description
        8: 'total_donation_amount',  # description
    }

    page = None
    limit = None
    order_by = ['-modified_time']
    start = None
    length = None

    if request.method == 'POST':
        form = AjaxListForm(request.POST)
        if form.is_valid():
            (
                page, limit, start, length, search_value, order_by
            ) = ajax_list_control_with_search_and_ordering(
                request,
                col_map=col_map
            )
        else:
            raise WrongParametersError(_("Wrong parameters."), form)

    filters = Q(is_archived=False)

    if search_value is not None:
        search_filters = Q(author__username__unaccent__icontains=search_value)
        filters &= search_filters

    (offset_0, offset_n) = ajax_list_get_offsets(start, length, page, limit)

    user_donations = UserProfile.objects.annotate(
        by_user_donation_amount=Coalesce(
            Sum('donations__value', output_field=FloatField()),
            0
        )
    ).filter(
        id=OuterRef('author_id'),
        is_archived=False
    )

    items = Donation.objects.annotate(
        total_donation_amount=Subquery(
            user_donations.values('by_user_donation_amount')[:1],
            output_field=FloatField()
        )
    ).filter(filters).order_by(*order_by)

    total_count = items.count()
    items = items[offset_0:offset_n]

    items_out = []

    for item in items:
        value = "%s%s" % (item.value, item.currency)

        freq = DonationFrequencyE.names[item.frequency] \
            if item.frequency in DonationFrequencyE.names else ""

        author_img_html = format_user_html(
            item.author, show_author_username=True, show_is_banned=True
        )

        cb = '<input id="colors-%d-toggle-1" name="ids" value="{id}" type="checkbox">'  # noqa

        item_out = {
            'checkbox_id': cb.format(id=item.id),
            'author_img_html': author_img_html,
            'author_email': item.author.email,

            'modified_time': item.modified_time.strftime('%d %b %Y %H:%M'),
            'value_data': value,
            'frequency': freq,

            'date_from': item.date_from.strftime('%d %b %Y %H:%M'),
            'date_to': item.date_to.strftime('%d %b %Y %H:%M'),
            'total_amounts': item.total_donation_amount,
        }
        items_out.append(item_out)

    return JsonResponse({
        "data": items_out,
        "iTotalRecords": total_count,
        "iTotalDisplayRecords": total_count,
    })
