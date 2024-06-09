from django.utils import timezone

from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Case, F, IntegerField, Q, Value, When
from django.http import JsonResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from web.constants import PlaceListForE
from web.forms.admin_forms import AjaxListForm
from web.models import Place, UserProfile
from web.utils.ajax_place_utils import (get_checkbox_id_html,
                                        get_filter_criteria_by_search_value,
                                        get_social_links, get_sticker_html, get_total_wl_score,
                                        get_type_text, get_website_url_link)
from web.utils.exceptions import WrongParametersError
from web.utils.views_common import (get_current_user, get_search_value,
                                    get_sorting,
                                    prevent_using_non_active_account,
                                    get_sorting_from_get_method)
from web.views.ajax_lists.common import ajax_list_control_parameters_by_form
from web.views.ajax_lists.formatting import format_img_html, format_user_html, format_place_status


def _format_for_list(item, style=None):
    type_text = get_type_text(item)  # HTML for Venue type (bar, rest, shop)
    website_url_link = get_website_url_link(item)
    img_html = format_img_html(
        item.main_image, alt_text=item.name, author=item.author.username,
        side_size=35
    )
    status_text = format_place_status(item)
    chargebee_status = item.subscription.get_status_html() if item.subscription else ''  # noqa
    social_links = get_social_links(item, website_url_link)
    sticker_html = get_sticker_html(item)
    total_wl_score = get_total_wl_score(item)
    checkbox_id_html = get_checkbox_id_html(item)

    place_edit_cms_url = reverse('edit_place', args=[item.id])
    place_edit_pro_url = reverse('pro_dashboard', args=[item.id])

    if item.is_subscriber():
        pn = '<a href="{}">{}</a>&nbsp;&nbsp;<a class="editVenue" data-toggle="tooltip" title="EDIT INFO"  data-id={}><i class="fa fa-edit"></i></a>&nbsp;&nbsp;<a style="text-decoration:none" href="{}">🧰</a>'  # noqa
        place_name_html = pn.format(
            place_edit_cms_url, item.name, item.id, place_edit_pro_url
        )
    else:
        pn = '<a href="{}">{}</a>&nbsp;&nbsp;<a class="editVenue" data-toggle="tooltip" title="EDIT INFO" data-id={}><i class="fa fa-edit"></i></a>'  # noqa
        place_name_html = pn.format(
            place_edit_cms_url, item.name, item.id
        )
        # place_name_html = '<a href="{}">{}</a>'.format(
        #     place_edit_cms_url, item.name
        # )

    if item.owner_id:
        oi = '<a class="editOwner" data-toggle="tooltip" title="CONNECTED TO OWNER"  data-owner-id={}  data-id={}><i class="fa fa-chain"></i></a>'  # noqa
        owner_link = oi.format(
            item.owner_id, item.id
        )
    else:
        oi =  '<a class="editOwner" data-toggle="tooltip" title="MUST BE CONNECTED TO OWNER" data-id={}><i class="fa fa-chain-broken"></i></a>'  # noqa
        owner_link = oi.format(
            item.id
        )

    if item.missing_info:
        mi = '<i class="fa fa-warning" data-toggle="tooltip" title="" data-placement="bottom" data-original-title="KEY INFO MISSING"></i>'  # noqa
        missing_info = mi
    else:
        missing_info = ''

    if item.src_info == 10:
        src_info_html = '<small><i class="fa fa-user" data-toggle="tooltip" title="" data-placement="bottom" data-original-title="SUBMITTED ON PRO. WEBSITE"></i></small>'  # noqa
    elif item.src_info == 20:
        src_info_html = '<small><i class="fa fa-mobile-phone" data-toggle="tooltip" title="" data-placement="bottom" data-original-title="SUBMITTED ON APP"></i></small>'  # noqa
    elif item.src_info == 30:
        src_info_html = '<strong class="fa copyright" data-toggle="tooltip" title="" data-placement="bottom" data-original-title="REGISTERED ON CHARGEBEE">Ⓒ</strong>'  # noqa
    elif item.src_info == 40:
        src_info_html = '<small><i class="fa fa-desktop" data-toggle="tooltip" title="" data-placement="bottom" data-original-title="REGISTERED ON CMS"></i></small>'  # noqa
    else:
        src_info_html = ''

    if hasattr(item, 'trial_ends') and item.trial_ends:
        te = str(item.trial_ends.days) + ' ' + 'days'
        trial_ends_html = te
    else:
        trial_ends_html = None

    item_out = {
        'checkbox_id': checkbox_id_html,
        'img_html': img_html,
        'date': item.modified_time.strftime('%d %b %Y %H:%M'),
        'author_img_html': format_user_html(item.author),
        'expert_img_html': format_user_html(item.expert),
        'name': place_name_html,
        # altered street_address to full_street_address
        # to make street numbers visible
        # in CMS main list (Places tab)
        'street_address': item.full_street_address,
        'zip_code': item.zip_code,
        'city': item.city,
        'country': item.country,
        'email': item.email,
        'type_text': type_text,
        'total_wl_score': total_wl_score,
        'status_text': status_text,
        'chargebee_status': chargebee_status,
        'trial_ends': trial_ends_html,
        'src': src_info_html,
        'owner': owner_link,
        'info': missing_info,
    }

    if style == 'place_subscribers':
        owner_edit_url = reverse('edit_user', args=[item.owner_id])
        owner_username = item.owner.username
        item_out['owner_img_html'] = '<a href="{}">{}</a>'.format(
            owner_edit_url, owner_username
        )

    if style == 'userplace':
        item_out.update({
            'website_url_link': website_url_link,
            'social_links': social_links,
            'sticker': sticker_html,
        })

    return item_out


def get_place_items(request,
                    filter_criteria=Q()):
    user = get_current_user(request)
    prevent_using_non_active_account(user)
    draw = 0
    order_dir = 'desc'
    order_by = None
    order_by_front_end = None
    start = 0
    length = 10
    search_value = None
    col_map = {
        0: 'id',
        1: None,  # img
        2: 'modified_time',
        3: 'author__username',  # author img
        4: 'expert__username',  # expert img
        5: 'name',
        6: 'street_address',
        7: 'zip_code',
        8: 'city',
        9: 'country',
        10: 'email',
        11: None,  # type
        12: 'total_wl_score_coalesced',
        13: 'status',
        14: 'subscription__status',  # chargebee_status
        15: 'trial_ends',  # number of days before the end of subscr. trial
        16: 'src_info',  # the way a place was created
        17: 'owner',  # a place has an owner or has no owner
        18: 'missing_info',  # there is a missed info about place / a place has
        # complete info about itself
    }

    search_value = request.GET.get('search[value]')
    order_by_front_end = get_sorting_from_get_method(
        request, col_map, order_by, order_dir
    )

    # try to get pagination parameters
    try:
        draw = int(request.GET.get('draw'))
        start = int(request.GET.get('start'))
        length = int(request.GET.get('length'))
    except ValueError:
        raise WrongParametersError(_("Wrong pagination parameters."))
    except TypeError:
        pass

    # before search applied
    records_total_count = Place.active.filter(filter_criteria).count()

    filter_criteria &= get_filter_criteria_by_search_value(search_value)

    if start is not None and length is not None:
        offset_0 = start
        offset_n = start + length
    else:
        offset_0 = None
        offset_n = None

    time_now = timezone.now()
    items = Place.active.annotate(
        total_wl_score_coalesced=Case(
            When(wl_added=True, then=F('total_wl_score')),
            default=Value(0),
            output_field=IntegerField()
        )
    ).annotate(
        trial_ends=Case(
            When(subscription__isnull=False,
                 subscription__status='in_trial',
                 subscription__trial_end__isnull=False,
                 then=F('subscription__trial_end') - time_now
                 )
        )
    ).filter(filter_criteria)

    # after search applied
    total_count = items.count()
    records_filtered_count = total_count

    if order_by_front_end:
        items = items.order_by(order_by_front_end)[offset_0:offset_n]
    else:
        items = items.order_by('-modified_time')[offset_0:offset_n]

    # total_count_sliced = items.count()
    items_out = []
    for item in items:
        items_out.append(_format_for_list(item))

    return JsonResponse({
        "data": items_out,
        "draw": draw,
        "recordsTotal": records_total_count,
        "recordsFiltered": records_filtered_count,
        "iTotalRecords": total_count,
        # "iTotalDisplayRecords": total_count_sliced,
        "iTotalDisplayRecords": total_count,
    })


# /ajax/place/items-opti
@login_required
def get_place_items_opti(request, list_for):
    get_current_user(request)

    current_year = timezone.now().year
    yearly_sticker_plans = [
        'yearly-3-179$us-tax:world',
        'Yearly-135€-EN-TAX:EUR',
        'Annuel-135€-FR-TAX:WORLD',
        'Annuel-135€-FR-TAX:FR',
        'Annuel-135€-FR-TAX:EUR'
    ]
    monthly_sticker_plans = [
        'MONTHLY-2-19.99$US-TAX:WORLD',
        'MonthlyFastStick-EN-TAX:EUR',
        'Mensuel-Fast-Stick-14.99€FR-tax:WORLD',
        'Mensuel-Fast-Stick-14.99€FR-tax:EUR',
        'Mensuel-Fast-Stick-14.99€FR-tax:FR',
        'Mensuel-39.99€FR-TAX:WORLD',
        'Mensuel-Sticker-39.99€-FR-TAX:EUR',
        'Mensuel-39.99€FR-TAX:FR',
        'MONTHLY-Stick-39.99€-EN-TAX:EUR'
    ]
    sticker_only_plans = [
        '2-AUTOCOLLANTS-RAISIN-50€-FR-TAX:FR',
        'fast-reg-sticker-$44.99-us-tax:world',
        'AUTOCOLLANT-Raisin-25€-fr-eu-tax:WORLD',
        'AUTOCOLLANT-Raisin-25€-fr-eu-tax:eur',
        'STICKER-RAISIN-25€-EUR-TAX:EUR',
        'AUTOCOLLANT-RAISIN-25€-FR-TAX:FR',
        'raisin-electrostatic-sticker-$25-[us]-[tax:world]'
    ]
    sticker_plans = \
        yearly_sticker_plans \
        + monthly_sticker_plans

    if list_for == PlaceListForE.FREE:
        filter_criteria = Q(subscription__isnull=True) | Q(
            subscription__status='cancelled')
    elif list_for == PlaceListForE.SUBSCRIBERS:
        filter_criteria = Q(subscription__isnull=False) & ~Q(
            subscription__status='cancelled')
    elif list_for == PlaceListForE.IN_TRIAL:
        filter_criteria = Q(subscription__status='in_trial')
    elif list_for == PlaceListForE.NOT_CONNECTED:
        filter_criteria = Q(subscription__isnull=False, owner=None) & ~Q(
            subscription__status='cancelled'
        )
    elif list_for == PlaceListForE.STICKERS_TO_SEND:
        filter_criteria = (Q(sticker_sent_dates=None) | ~Q(
            sticker_sent_dates__icontains=current_year
        )) & (Q(
            subscription__plan_id__in=sticker_plans,
            subscription__status__in=['active', 'cancelled']
        ) | Q(
            subscription__plan_id__in=sticker_only_plans,
            subscription__status='active'
        ))
    elif list_for == PlaceListForE.STICKERS:
        filter_criteria = Q(
            sticker_sent_dates__icontains=current_year
        ) & (Q(
            subscription__plan_id__in=sticker_plans,
            subscription__status__in=['active', 'cancelled']
        ) | Q(
            subscription__plan_id__in=sticker_only_plans,
            subscription__status='active'
        ))
    else:
        filter_criteria = Q()

    return get_place_items(
        request,
        filter_criteria=filter_criteria
    )


# /ajax/place/subscribers
@csrf_exempt
@login_required
def get_place_subscribers_items(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)
    page = None
    limit = None
    order_dir = 'desc'
    order_by = '-modified_time'
    start = None
    length = None
    search_value = None
    col_map = {
        0: 'id',
        1: None,  # img
        2: 'modified_time',
        3: 'owner__username',  # author img
        4: 'expert__username',  # expert img
        5: 'name',
        6: 'street_address',
        7: 'zip_code',
        8: 'city',
        9: 'country',
        10: 'email',
        11: None,  # type
        12: 'total_wl_score_coalesced',
        13: 'status',
        14: 'chargebee_status'
    }

    if request.method == 'POST':
        form = AjaxListForm(request.POST)
        search_value = get_search_value(request)
        order_by = get_sorting(request, col_map, order_by, order_dir)
        if form.is_valid():
            cd = form.cleaned_data
            start = cd['start']
            length = cd['length']
            (page, limit, order_by_old, order_dir_old) = \
                ajax_list_control_parameters_by_form(cd)
        else:
            raise WrongParametersError(_("Wrong parameters."), form)

    filter_criteria = Q(owner__isnull=False) & get_filter_criteria_by_search_value(
        search_value,
        search_author=False,
        search_owner=True
    )

    total_count = Place.active.filter(filter_criteria).exclude(
        owner__username__unaccent__istartswith='genowner__'
    ).count()

    if limit:
        offset_0 = page * limit - limit
        offset_n = page * limit
    elif start is not None and length is not None:
        offset_0 = start
        offset_n = start + length
    else:
        offset_0 = None
        offset_n = None

    order_by_whole = ['-is_expert_modified', order_by]
    items = Place.active.annotate(
        total_wl_score_coalesced=Case(
            When(wl_added=True, then=F('total_wl_score')),
            default=Value(0),
            output_field=IntegerField()
        )
    ).annotate(
        trial_ends=Case(
            When(subscription__isnull=False,
                 subscription__status='in_trial',
                 subscription__trial_end__isnull=False,
                 then=F('subscription__trial_end') - timezone.now()
                 )
        )
    ).filter(filter_criteria).exclude(
        owner__username__unaccent__istartswith='genowner__'
    ).select_related(
        'main_image', 'owner'
    ).order_by(*order_by_whole)[offset_0:offset_n]

    items_out = []
    for item in items:
        items_out.append(_format_for_list(item, style="place_subscribers"))

    return JsonResponse({
        "data": items_out,
        "iTotalRecords": total_count,
        "iTotalDisplayRecords": total_count,
    })


# /ajax/userplace/items/{uid}
@csrf_exempt
@login_required
def get_userplace_items(request, uid):
    user = get_current_user(request)
    prevent_using_non_active_account(user)
    author = UserProfile.active.get(id=uid)
    page = None
    limit = None
    order_dir = 'desc'
    order_by = '-modified_time'
    start = None
    length = None
    search_value = None
    filter_criteria = Q()
    col_map = {
        0: 'id',
        1: None,  # img
        2: 'modified_time',
        4: 'expert__username',  # expert img
        5: 'name',
        6: 'street_address',
        7: 'zip_code',
        8: 'city',
        9: 'country',
        10: 'email',
        11: None,  # type
        12: 'website_url',
        13: 'status',
        14: None,  # social
        15: 'sticker_sent',
    }

    if request.method == 'POST':
        form = AjaxListForm(request.POST)
        search_value = get_search_value(request)
        order_by = get_sorting(request, col_map, order_by, order_dir)
        if form.is_valid():
            cd = form.cleaned_data
            start = cd['start']
            length = cd['length']
            (page, limit, order_by_old, order_dir_old) = \
                ajax_list_control_parameters_by_form(cd)
        else:
            raise WrongParametersError(_("Wrong parameters."), form)

    filter_criteria = get_filter_criteria_by_search_value(
        search_value, search_author=False
    )
    filter_criteria &= (Q(author=author) | Q(validated_by=author))
    total_count = Place.active.filter(filter_criteria).count()

    if limit:
        offset_0 = page * limit - limit
        offset_n = page * limit
    elif start is not None and length is not None:
        offset_0 = start
        offset_n = start + length
    else:
        offset_0 = None
        offset_n = None

    order_by_whole = ['-is_expert_modified', order_by]
    items = Place.active.filter(filter_criteria).select_related(
        'main_image', 'author'
    ).order_by(*order_by_whole)[offset_0:offset_n]

    items_out = []
    for item in items:
        items_out.append(_format_for_list(item, "userplace"))

    return JsonResponse({
        "data": items_out,
        "iTotalRecords": total_count,
        "iTotalDisplayRecords": total_count,
    })
