import operator
from functools import reduce

from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from web.constants import (UserTypeE, WinemakerStatusE, WinemakerTypeE,
                           wm_type_statuses)
from web.models import Winemaker
from web.views.ajax_lists.common import (
    ajax_list_control_with_search_and_ordering, ajax_list_get_offsets)
from web.views.ajax_lists.formatting import format_img_html, format_user_html, format_winemaker_status


def winemaker_items_col_map_default():
    return {
        0: None,  # id
        1: None,  # img
        2: 'modified_time',
        3: 'author__username',  # author img
        4: 'last_modifier__username',  # expert username

        5: 'name',
        6: 'domain',
        7: 'street_address',
        8: 'zip_code',

        9: 'city',
        10: 'country',
        11: 'region',
        12: 'phone_number',

        13: None,    # 'website_url',
        14: 'status',
        15: None,    # social
    }


def format_winemakers_default(winemakers):
    items_out = []
    for item in winemakers:
        img_html = format_img_html(
            item.main_image, item.name,
            side_size=40
        )

        status_html = format_winemaker_status(item)

        if item.website_url:
            ws = '<a href="{}" title="{}" target="_blank"><span class="fa fa-link"></span></a>'  # noqa
            website_url_link = ws.format(
                'http://' + item.website_url,
                item.website_url
            )
        else:
            website_url_link = ""

        social_links = ''
        if item.social_facebook_url:
            fb = '<a href="{}" class="facebook" target="_blank"><i class="fa fa-facebook"></i></a>'  # noqa
            social_links += fb.format(
                item.social_facebook_url
            )

        if item.social_twitter_url:
            tw = '<a href="{}" class="twitter" target="_blank"><i class="fa fa-twitter"></i></a>'  # noqa
            social_links += tw.format(
                item.social_twitter_url
            )

        if item.social_instagram_url:
            ins = '<a href="{}" class="instagram" target="_blank"><i class="fa fa-instagram"></i></a>'  # noqa
            social_links += ins.format(item.social_instagram_url)

        cb = '<input id="colors-{}-toggle-1" name="ids" value="{}" type="checkbox">'  # noqa
        last_modifier = item.last_modifier if (
            item.last_modifier and item.last_modifier.type in [
                UserTypeE.ADMINISTRATOR, UserTypeE.EDITOR
            ]
        ) else None

        item_out = {
            'checkbox_id': cb.format(item.pk, item.pk),
            'img_html': img_html,
            'date': item.modified_time.strftime('%d %b %Y %H:%M'),
            'author_img_html': format_user_html(item.author),
            'expert_img_html': format_user_html(
                last_modifier
            ) if last_modifier else '',

            'name': '<a href="{}">{}</a>'.format(
                reverse('edit_winemaker', args=[item.pk]),
                item.name
            ),
            'domain': item.domain,

            'address': item.street_address,
            'zip_code': item.zip_code,
            'city': item.city,
            'country': item.country,
            'region': item.region,

            'phone_number': item.phone_number,
            'website_url_link': website_url_link,
            'status_html': status_html,
            'social_links': social_links
        }

        items_out.append(item_out)

    return items_out


def _get_winemakers(request, winemaker_type):
    ManagerClass = Winemaker.active
    col_map = winemaker_items_col_map_default()

    page = None
    limit = None
    order_by = ['-modified_time']
    start = None
    length = None
    (
        page, limit, start, length, search_value, order_by
    ) = ajax_list_control_with_search_and_ordering(
        request,
        col_map=col_map
    )

    if winemaker_type:
        q_base = Q(status__in=wm_type_statuses[winemaker_type])
    else:
        q_base = Q()

    if search_value is not None:
        q_filters = {
            Q(name__unaccent__icontains=search_value),
            Q(domain__unaccent__icontains=search_value),
            Q(street_address__unaccent__icontains=search_value),
            Q(zip_code__unaccent__icontains=search_value),
            Q(city__unaccent__icontains=search_value),
            Q(country__unaccent__icontains=search_value),
            Q(region__unaccent__icontains=search_value),
            Q(phone_number__unaccent__icontains=search_value),
            Q(website_url__unaccent__icontains=search_value),
        }

        if search_value.upper() == 'BIO-ORGANIC':
            search_value = 'bio organic'

        if search_value.upper() in WinemakerStatusE.names_human:
            q_filters.add(Q(
                status=WinemakerStatusE.names_human[search_value.upper()]
            ))
        q_search = reduce(operator.or_, q_filters)

        filter_criteria = q_base & q_search
    else:
        filter_criteria = q_base

    total_count = ManagerClass.filter(filter_criteria).count()
    (offset_0, offset_n) = ajax_list_get_offsets(start, length, page, limit)

    items = ManagerClass.filter(filter_criteria).select_related(
        'main_image', 'author').order_by(*order_by)

    if items and offset_0 is not None and offset_n is not None:
        items = items[offset_0: offset_n]

    items_out = format_winemakers_default(items)

    return JsonResponse({
        "iTotalRecords": total_count,
        "iTotalDisplayRecords": total_count,
        "data": items_out
    })


# /ajax/winemaker/items/all
@csrf_exempt
def get_winemaker_items_all(request):
    return _get_winemakers(request, winemaker_type=None)


# /ajax/winemaker/items/naturals
@csrf_exempt
def get_winemaker_items_naturals(request):
    return _get_winemakers(request, winemaker_type=WinemakerTypeE.NATURAL)


# /ajax/winemaker/items/others
@csrf_exempt
def get_winemaker_items_others(request):
    return _get_winemakers(request, winemaker_type=WinemakerTypeE.OTHER)
