from datetime import datetime
from itertools import chain

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from web.forms.admin_forms import AjaxListForm
from web.models import FreeGlassEvent, Place, UserProfile
from web.utils.exceptions import WrongParametersError
from web.utils.model_tools import beautify_place_name
from web.utils.upload_tools import aws_url
from web.utils.views_common import get_order_dir, get_search_value
from web.views.ajax_lists.common import ajax_list_control_parameters_by_form


# /ajax/est-free-glass
@csrf_exempt
@login_required
def get_est_free_glass_items(request):
    filter_criteria = {}
    page = None
    limit = None
    order_dir = 'desc'
    order_by = '-modified_time'

    start = None
    length = None
    search_value = None
    col_map = {
        0: None,  # 'id',
        1: None,  # 'place__main_image',  # place img
        2: 'street_address',
        3: 'city',
        4: 'country',
        5: 'name',
        6: 'free_glass_last',
        7: 'free_glass_drinks_geolocated',
        8: 'free_glass_get_free_glass_button',
        9: 'free_glass_got_cnt',
        10: None,  # 'free_glass_users', no ordering by user list
        11: None,  # 'free_glass_donators', no ordering by donators list
    }

    if request.method == 'POST':
        form = AjaxListForm(request.POST)
        search_value = get_search_value(request)
        order_dir = get_order_dir(request, order_dir)
        if "order[0][column]" in request.POST:
            col = int(request.POST["order[0][column]"])
            if col in col_map and col_map[col]:
                order_by = col_map[col] if order_dir == 'asc' else "-" + col_map[col]  # noqa

        if form.is_valid():
            cd = form.cleaned_data
            start = cd['start']
            length = cd['length']
            (
                page, limit, order_by_old, order_dir_old
            ) = ajax_list_control_parameters_by_form(cd)
        else:
            raise WrongParametersError(_("Wrong parameters."), form)

    if limit:
        offset_0 = page * limit - limit
        offset_n = page * limit
    elif start is not None and length is not None:
        offset_0 = start
        offset_n = start + length
    else:
        offset_0 = None
        offset_n = None

    filter_criteria = Q(free_glass=True)

    if search_value is not None:
        date_formats = ['%b %Y', '%B %Y', '%b %y', '%B %y']
        match_date = None
        for date_format in date_formats:
            try:
                match_date = datetime.strptime(search_value, date_format)
                break
            except ValueError:
                pass

        if match_date:
            filter_criteria &= Q(
                free_glass_last_action_date__month=match_date.month,
                free_glass_last_action_date__year=match_date.year
            )

        filter_criteria &= (
            Q(name__unaccent__icontains=search_value) |
            Q(author__username__unaccent__icontains=search_value)
        )

    cur_event = FreeGlassEvent.active.first()
    if cur_event:
        evt_start_date = cur_event.start_date.date()
        evt_end_date = cur_event.end_date.date()
        fg_drinks_conditions = Q(
            is_archived=False,
            created_time__range=(evt_start_date, evt_end_date)
        )
    else:
        fg_drinks_conditions = Q(
            is_archived=False
        )

    items = Place.active.annotate(
        free_glass_last=Coalesce(
            'free_glass_last_action_date', 'free_glass_signup_date'
        ),
        free_glass_drinks_geolocated=Count(
            'get_free_glass_objects',
            filter=(fg_drinks_conditions),
            distinct=True
        ),
        free_glass_got_cnt=Count(
            'got_free_glass_objects',
            filter=(Q(is_archived=False)),
            distinct=True
        )
    ).filter(filter_criteria).order_by(order_by)[offset_0:offset_n]

    items_out = []

    for item in items:
        cb = '<input id="colors-{}-toggle-1" name="ids" value="{}" type="checkbox">'  # noqa
        pl = '<a href="{}" data-toggle="lightbox" data-title="{}"><img width="35" height="35" data-src="{}" alt="{}"/></a>'  # noqa
        name = beautify_place_name(item.name)

        place_img_html = pl.format(
            aws_url(item.main_image), name,
            aws_url(item.main_image, thumb=True), name
        )

        getmy_count = item.get_free_glass_objects.filter(
            is_archived=False
        ).count()

        gfg_user_ids = item.got_free_glass_objects.filter(
            is_archived=False
        ).values_list('author_id', flat=True)

        post_user_ids = item.posts.filter(
            is_archived=False
        ).values_list('author_id', flat=True)

        donation_filters = Q(
            created_time__range=(evt_start_date, evt_end_date)
        ) if cur_event else Q()

        users = UserProfile.objects.annotate(
            donation_amount=Sum('donations__value', filter=donation_filters)
        ).filter(pk__in=chain(gfg_user_ids, post_user_ids))

        fg_users_string = ''
        fg_donors_string = ''

        for index, pl_user in enumerate(users):
            tpl = '<a href="{}" title="@{}">@{}</a>'
            user_html = tpl.format(
                reverse('edit_user', args=[pl_user.id]),
                pl_user.username,
                pl_user.username
            )
            fg_users_string += user_html

            if index % 5 == 4:
                fg_users_string += '<br/>'
            else:
                fg_users_string += ', '

            if not pl_user.donation_amount:
                continue
            donor_html = '<a href="{}" title="@{}">@{} ({}EUR)</a>'.format(
                reverse('edit_user', args=[pl_user.id]),
                pl_user.username, pl_user.username,
                pl_user.donation_amount)
            fg_donors_string += donor_html

            if index % 5 == 4:
                fg_donors_string += '<br/>'
            else:
                fg_donors_string += ', '

        item_out = {
            'checkbox_id': cb.format(item.id, item.id),
            'place_img_html': place_img_html,
            'street_address': item.street_address,
            'city': item.city,
            'country': item.country,
            'name': '<a href="{}">{}</a>'.format(
                reverse('edit_place', args=[item.id]),
                name
            ),
            'free_glass_last_action_date': item.free_glass_last.strftime(
                '%d %b %Y %H:%M'
            ),
            'free_glass_drinks_geolocated': item.free_glass_drinks_geolocated,
            'free_glass_get_free_glass_button': getmy_count,
            'free_glass_got_cnt': item.free_glass_got_cnt,
            'free_glass_users': fg_users_string,
            'free_glass_donators': fg_donors_string,
        }

        items_out.append(item_out)

    return JsonResponse({
        "data": items_out,
        "iTotalRecords": items.count(),
        "iTotalDisplayRecords": items.count(),
    })
