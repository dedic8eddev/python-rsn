from __future__ import absolute_import

import logging

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from my_chargebee.models import Subscription
from my_chargebee.serializers import SubscriptionListSerializer

from web.constants import (PlaceStatusE, PostStatusE, PostTypeE, UserStatusE,
                           UserTypeE, WineColorE, WinemakerStatusE, WineStatusE)
from web.forms.admin_forms import (AutocompleteAddressForm,
                                   AutocompleteAddressFormPlaceId,
                                   ChangeParentPostWineListForm,
                                   ChangeParentPostWinemakerListForm,
                                   PublishedPlaceListForm,
                                   UpdateOriginalWinemakerForm)
from web.helpers.winemakers import WinemakerHelper
from web.models import Place, Post, UserProfile, Wine, Winemaker
from web.utils.autocomplete_common import autocomplete_common_ajax
from web.utils.geoloc import (get_addr_data_by_google_place_id,
                              get_address_data_for_latlng)
from web.utils.views_common import (get_current_user,
                                    prevent_using_non_active_account)

log = logging.getLogger(__name__)


# /ajax/place/published/list
@csrf_exempt
@login_required
def published_places_list(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)
    request_data = request.POST if request.method == 'POST' else request.GET
    form = PublishedPlaceListForm(request_data)
    limit = 30
    order_by = '-modified_time'
    if form.is_valid():
        cd = form.cleaned_data
        query = cd['q']
        page = cd['page'] if cd['page'] else 1
        offset_0 = page * limit - limit
        offset_n = page * limit
        filter_criteria = Q(status=PlaceStatusE.PUBLISHED) | Q(
            status=PlaceStatusE.SUBSCRIBER)
        if query:
            filter_criteria &= (Q(name__unaccent__icontains=query) | Q(street_address__unaccent__icontains=query) |
                                Q(city__unaccent__icontains=query) | Q(country__unaccent__icontains=query))

        items = Place.active.filter(
            filter_criteria
        ).order_by(order_by)[offset_0: offset_n]
        items_out = [{
            'id': None,
            'name': '',
            'street_address': '',
            'zip_code': '',
            'city': '',
            'country': '',
        }]
        items_out += [{
            'id': item.id, 'name': item.name,
            'street_address': '{}'.format(
                item.street_address
            ) if item.street_address else '',
            'zip_code': ', {}'.format(item.zip_code) if item.zip_code else '',
            'city': ', {}'.format(item.city) if item.city else '',
            'country': ', {}'.format(item.country) if item.country else '',
        } for item in items]
        return JsonResponse({'items': items_out})


@login_required
@csrf_exempt
def autocomplete_address_place_id(request):
    addr_data = {"city": None,
                 "country": None,
                 "iso": None,
                 "state": None,
                 "postal_code": None,
                 "route": None,
                 "street_number": None,
                 "quality": None,
                 "retrieved": None,
                 "full_street_address": None}

    if request.method == 'POST':
        form = AutocompleteAddressFormPlaceId(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            place_id = cd['place_id']
            lang = cd['lang']

            addr_data = get_addr_data_by_google_place_id(
                google_place_id=place_id, lang=lang
            )

    return JsonResponse(addr_data)


@login_required
@csrf_exempt
def autocomplete_address_textsearch(request):
    addr_data = {"city": None,
                 "country": None,
                 "iso": None,
                 "state": None,
                 "postal_code": None,
                 "route": None,
                 "street_number": None,
                 "quality": None,
                 "retrieved": None,
                 "full_street_address": None}

    if request.method == 'POST':
        form = AutocompleteAddressForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            lat = cd['lat']
            lng = cd['lng']
            lang = cd['lang']

            addr_data = get_address_data_for_latlng(
                latitude=lat, longitude=lng, lang=lang, get_route=True
            )

    return JsonResponse(addr_data)


# ------------------ AJAX AUTOCOMPLETES ---------------------------------------
# /ajax/autocomplete/winemaker
@login_required
def autocomplete_winemaker(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)

    return JsonResponse(
        autocomplete_common_ajax(
            request=request, EntityClass=Winemaker, entity_field="name",
            extra_filter_criteria={'status__in': [WinemakerStatusE.VALIDATED]}
        )
    )


@login_required
@csrf_exempt
def update_original_winemaker_name(request):
    user = get_current_user(request)

    try:
        prevent_using_non_active_account(user)

        if request.method == 'POST':
            form = UpdateOriginalWinemakerForm(request.POST)
        elif request.method == 'GET':
            form = UpdateOriginalWinemakerForm(request.GET)

        if form.is_valid():
            cd = form.cleaned_data

            winemaker = Winemaker.active.get(id=cd['winemaker_id'])
            winemaker.name = cd['winemaker_name']
            winemaker.save()
            winemaker.refresh_from_db()

            status = "OK"
        else:
            status = "ERROR"
    except Exception:
        status = "ERROR"

    result = {
        'status': status,
    }

    return JsonResponse(result)


# WINEMAKERS FOR "DEFINE AS CHILDREN"
@login_required
@csrf_exempt
def change_parent_post_winemaker_list(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form = ChangeParentPostWinemakerListForm(request.POST)
    elif request.method == 'GET':  # noqa eg. http://localhost:8000/ajax/autocomplete/winemaker/?min_letters=2&query=Bre
        form = ChangeParentPostWinemakerListForm(request.GET)

    limit = 30
    order_by = 'name'

    if form.is_valid():
        cd = form.cleaned_data
        query = cd['q']
        page = cd['page']
        edited_post_id = cd['edited_post_id']

        # filter_criteria = Q(status=WinemakerStatusE.VALIDATED)
        filter_criteria = Q(status__in=WinemakerHelper.parent_post_selector_statuses)

        if edited_post_id:
            try:
                edited_post = Post.active.get(
                    id=edited_post_id, type=PostTypeE.WINE
                )
            except Post.DoesNotExist:
                return JsonResponse({})

            post_winemaker_id = (edited_post.wine.winemaker.id
                                 if (edited_post.wine and edited_post.wine.winemaker)
                                 else None)

            if post_winemaker_id:
                # noqa draft_criteria = Q(status__in=[WinemakerStatusE.DRAFT, WinemakerStatusE.IN_DOUBT]) \
                #                  & Q(id=post_winemaker_id)
                draft_criteria = Q(status__in=[WinemakerStatusE.DRAFT]) & Q(id=post_winemaker_id)
                filter_criteria |= draft_criteria

        if query:
            q_query = (Q(name__unaccent__icontains=query) | Q(domain__unaccent__icontains=query))
            filter_criteria &= q_query

        if not page:
            page = 1

        offset_0 = page * limit - limit
        offset_n = page * limit

        items = Winemaker.active.filter(
            filter_criteria
        ).order_by(order_by)[offset_0: offset_n]
        items_out = [{
            'id': None,
            'name': '',
            'domain': '',
            'editable': False,
        }]

        for item in items:
            if item.status == WinemakerStatusE.VALIDATED:
                name_str = "%s [%s]" % (item.name, item.domain) if item.domain else "%s [no domain]" % item.name  # noqa
                domain_name_str = item.domain if item.domain else ""
            else:
                status_name = WinemakerStatusE.names[item.status]
                name_str = "%s: %s [%s]" % (
                    item.name, item.domain, status_name) if item.domain else "%s [DRAFT]" % item.name  # noqa
                domain_name_str = "%s [%s]" % (item.domain, status_name) if item.domain else ""  # noqa

            item_out = {
                'id': item.id,
                'name': name_str,
                "domain": domain_name_str,
                'editable': bool(item.status in [
                    WinemakerStatusE.DRAFT, WinemakerStatusE.IN_DOUBT
                ])
            }
            items_out.append(item_out)

        result = {
            'items': items_out,
        }

        return JsonResponse(result)


@login_required
@csrf_exempt
def change_parent_post_list_winemaker(request, id):
    user = get_current_user(request)
    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form = ChangeParentPostWinemakerListForm(request.POST)
    elif request.method == 'GET':  # noqa eg. http://localhost:8000/ajax/autocomplete/winemaker/?min_letters=2&query=Bre
        form = ChangeParentPostWinemakerListForm(request.GET)

    limit = 30
    order_by = 'name'

    if form.is_valid():
        cd = form.cleaned_data
        query = cd['q']
        page = cd['page']
        edited_post_id = cd['edited_post_id']

        # filter_criteria = Q(status=WinemakerStatusE.VALIDATED)
        filter_criteria = Q(status__in=WinemakerHelper.parent_post_selector_statuses)

        if edited_post_id:
            try:
                edited_post = Post.active.get(
                    id=edited_post_id, type=PostTypeE.WINE
                )
            except Post.DoesNotExist:
                return JsonResponse({})

            post_winemaker_id = (edited_post.wine.winemaker.id
                                 if (edited_post.wine and edited_post.wine.winemaker)
                                 else None)

            if post_winemaker_id:
                # noqa draft_criteria = Q(status__in=[WinemakerStatusE.DRAFT, WinemakerStatusE.IN_DOUBT]) \
                #                  & Q(id=post_winemaker_id)
                draft_criteria = Q(status__in=[WinemakerStatusE.DRAFT]) & Q(id=post_winemaker_id)
                filter_criteria |= draft_criteria

        if query:
            q_query = (Q(name__unaccent__icontains=query) | Q(domain__unaccent__icontains=query))
            filter_criteria &= q_query

        if not page:
            page = 1

        offset_0 = page * limit - limit
        offset_n = page * limit

        items_filtered = Winemaker.active.filter(
            filter_criteria
        ).exclude(id=id).order_by(order_by)[offset_0: offset_n]
        item_first = Winemaker.active.filter(id=id)
        items = item_first.union(items_filtered, all=True)
        items_out = []
        if item_first.count() == 0:
            items_out.append({
                'id': None,
                'name': '',
                'domain': '',
                'editable': False,
            })

        for item in items:
            if item.status == WinemakerStatusE.VALIDATED:
                name_str = "%s [%s]" % (item.name, item.domain) if item.domain else "%s [no domain]" % item.name  # noqa
                domain_name_str = item.domain if item.domain else ""
            else:
                status_name = WinemakerStatusE.names[item.status]
                name_str = "%s: %s [%s]" % (
                    item.name, item.domain, status_name) if item.domain else "%s [DRAFT]" % item.name  # noqa
                domain_name_str = "%s [%s]" % (item.domain, status_name) if item.domain else ""  # noqa

            item_out = {
                'id': item.id,
                'name': name_str,
                "domain": domain_name_str,
                'editable': bool(item.status in [
                    WinemakerStatusE.DRAFT, WinemakerStatusE.IN_DOUBT
                ])
            }
            items_out.append(item_out)

        result = {
            'items': items_out,
        }

        return JsonResponse(result)


# WINES FOR "DEFINE AS CHILDREN"
@login_required
@csrf_exempt
def change_parent_post_wine_list(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form = ChangeParentPostWineListForm(request.POST)
    elif request.method == 'GET':  # noqa eg. http://localhost:8000/ajax/autocomplete/winemaker/?min_letters=2&query=Bre
        form = ChangeParentPostWineListForm(request.GET)

    order_by = 'wine__name'
    mode = 'categories'  # categories, flat

    if form.is_valid():
        cd = form.cleaned_data
        winemaker_id = cd['winemaker_id']
        post_statuses = [PostStatusE.PUBLISHED,
                         PostStatusE.BIO_ORGANIC,
                         PostStatusE.IN_DOUBT,
                         PostStatusE.REFUSED]

        wine_statuses = [WineStatusE.VALIDATED,
                         WineStatusE.BIO_ORGANIC,
                         WineStatusE.IN_DOUBT,
                         WineStatusE.REFUSED]

        filter_criteria = {
            'status__in': post_statuses,
            'wine__winemaker_id': winemaker_id,
            'wine__status__in': wine_statuses,
            'is_parent_post': True,
        }

        items = Post.active.filter(**filter_criteria).order_by(order_by)
        items_out = []

        if mode == 'flat':
            for item in items:
                item_name = "%s %s" % (item.wine.name, item.wine_year) if item.wine_year else item.wine.name  # noqa
                items_out.append({
                    'post_id': item.id,
                    'wine_id': item.wine.id,
                    'name': item_name,
                    'color': item.wine.color,
                    'color_name': WineColorE.names[item.wine.color],
                })
        else:
            items_temp = {}

            for item in items:
                item_name = "%s %s" % (item.wine.name, item.wine_year) if item.wine_year else item.wine.name  # noqa
                color = item.wine.color
                if color in WineColorE.names:
                    color_name = str(WineColorE.names[color]).capitalize()
                else:
                    color_name = "Other"
                    color = '600'

                if color not in items_temp:
                    items_temp[color] = {
                        'id': color,
                        'text': color_name,
                        'children': [],
                    }

                items_temp[color]['children'].append({
                    'id': item.id,
                    'text': item_name,
                })

            items_out = list(items_temp.values())

        result = {
            'items': items_out
        }

        return JsonResponse(result)


# /ajax/autocomplete/domain
@login_required
def autocomplete_domain(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)

    return JsonResponse(
        autocomplete_common_ajax(
            request=request, EntityClass=Wine, entity_field="domain",
            extra_filter_criteria={'status__in': [WineStatusE.VALIDATED]}
        )
    )


# /ajax/autocomplete/wine
@login_required
def autocomplete_wine(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)

    return JsonResponse(
        autocomplete_common_ajax(
            request=request, EntityClass=Wine, entity_field="name",
            extra_filter_criteria={'status__in': [WineStatusE.VALIDATED]}
        )
    )


# /ajax/autocomplete/place
@login_required
def autocomplete_place(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)
    result = autocomplete_common_ajax(
        request=request, EntityClass=Place, entity_field="name"
    )

    if result['items']:
        for item in result['items']:
            item['edit_url'] = reverse('edit_place', args=[item['id']])

    return JsonResponse(result)


# /ajax/autocomplete/place/for-featured-venue
@login_required
def autocomplete_place_for_featured_venue(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)
    request_data = request.POST if request.method == 'POST' else request.GET
    form = PublishedPlaceListForm(request_data)
    limit = 300
    order_by = 'name'
    if form.is_valid():
        cd = form.cleaned_data
        query = cd['q']
        page = cd['page'] if cd['page'] else 1
        offset_0 = page * limit - limit
        offset_n = page * limit
        filter_criteria = Q(status=PlaceStatusE.PUBLISHED) | Q(
            status=PlaceStatusE.SUBSCRIBER)
        if query:
            filter_criteria &= (Q(name__unaccent__icontains=query) | Q(street_address__unaccent__icontains=query) |
                                Q(city__unaccent__icontains=query) | Q(country__unaccent__icontains=query))

        items = Place.active.filter(
            filter_criteria
        )
        if request.GET.get("for_quote", None):
            items = items.filter(Q(is_bar=True) | Q(is_restaurant=True))
            if request.GET.get("exclude_id", None) and request.GET.get("exclude_id") != "None":
                items = items.filter(Q(venue_quote__isnull=True) | Q(id=request.GET.get("exclude_id")))
            else:
                items = items.filter(Q(venue_quote__isnull=True))
        if request.GET.get("for_quote_8_list", None):
            items = items.filter(venue_quote__isnull=False, venue_quote__quote_fetured__isnull=True,
                                 venue_quote__is_archived=False, venue_quote__deleted=False).distinct()
        if request.GET.get("for_cheffe", None):
            items = items.filter(Q(is_bar=True) | Q(is_restaurant=True))
            if request.GET.get("exclude_id", None) and request.GET.get("exclude_id") != "None":
                items = items.filter(Q(venue_cheffe__isnull=True) | Q(id=request.GET.get("exclude_id")))
            else:
                items = items.filter(Q(venue_cheffe__isnull=True))
        if request.GET.get("for_cheffe_8_list", None):
            items = items.filter(venue_cheffe__isnull=False, venue_cheffe__cheffe_fetured__isnull=True,
                                 venue_cheffe__is_archived=False, venue_cheffe__deleted=False).distinct()

        items = items.order_by(order_by)[offset_0: offset_n]
        items_out = [{
            'id': None,
            'name': '',
            'street_address': '',
            'zip_code': '',
            'city': '',
            'country': '',
            'type': ''
        }]
        items_out += [{
            'id': item.id, 'name': item.name,
            'street_address': '{}'.format(
                item.street_address
            ) if item.street_address else '',
            'zip_code': ', {}'.format(item.zip_code) if item.zip_code else '',
            'city': ', {}'.format(item.city) if item.city else '',
            'country': ', {}'.format(item.country) if item.country else '',
            'type': f' ({"Bar" if item.is_bar else ""}{",Restaurant" if item.is_restaurant else ""}\
                     {",Wine Shop" if item.is_wine_shop else ""})'.replace("(,", "(")
        } for item in items]
        return JsonResponse({'items': items_out})


# /ajax/autocomplete/username
@login_required
def autocomplete_username(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)

    return JsonResponse(
        autocomplete_common_ajax(
            request=request, EntityClass=UserProfile, entity_field="username",
            extra_filter_criteria={
                'type': UserTypeE.USER,
                'status__in': [UserStatusE.ACTIVE, UserStatusE.INACTIVE]
            }
        )
    )


@login_required
def get_domain_name(request):
    winemaker = Winemaker.active.filter(
        name=request.GET.get('winemaker')
    ).first()

    if winemaker:
        return JsonResponse(
            {'domain': winemaker.domain}
        )

    return JsonResponse({'domain': ''})


@login_required
def subscriptions_list(request):
    customer_id = request.GET.get('customer')
    subscription_set = Subscription.objects.filter(customer=customer_id)
    ser_subs = SubscriptionListSerializer(subscription_set, many=True)

    return JsonResponse({'items': ser_subs.data})
