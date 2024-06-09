import json
import jwt
import logging

import requests
from django.templatetags.static import static
from django.shortcuts import redirect, resolve_url
from django.utils.translation import activate
from django.utils.translation import ugettext_lazy as _

from raisin.settings import (CANNY_API_KEY_EN, CANNY_API_KEY_FR, CANNY_URL,
                             CANNY_PRIVATE_KEY_EN, CANNY_PRIVATE_KEY_FR)
from web.constants import WineColorE, user_admin_types
from web.models import Comment, Place
from web.utils.api_handling import get_lang_from_request_pro

log = logging.getLogger("web")


def get_user_venue(user_id, request):
    is_admin = request.user.type in user_admin_types

    if is_admin and request.session.get('pro_place_id'):
        return Place.active.filter(id=request.session['pro_place_id']).first()

    return Place.active.filter(owner_id=user_id).first()


def get_owner_user(request):
    user = request.user
    is_admin = request.user.type in user_admin_types

    if is_admin and request.session.get('pro_place_id'):
        place = Place.active.filter(id=request.session['pro_place_id'])

        if place:
            user = place.first().owner

    user_lang = get_final_user_lang(user, request)
    activate(user_lang)

    return user


def get_user_currency(owner_user, request):
    return owner_user.currency.upper() if owner_user.currency else 'EUR'


def get_final_user_lang(owner_user, request):
    user_lang = owner_user.get_lang()
    lang_req = get_lang_from_request_pro(request)

    if not user_lang and lang_req:
        return lang_req

    if user_lang:
        return user_lang

    return 'EN'


def prepare_sidebar_data(request, tab):
    owner_user = get_owner_user(request)
    user_id = owner_user.id
    place = get_user_venue(user_id, request)

    address_info_list = []

    if place:
        address = place.full_street_address if place.full_street_address else place.street_address  # noqa
        if not address:
            address = 'n/a'

        city = place.city if place.city else 'n/a'
        state = place.state if place.state else 'n/a'
        country = place.country if place.country else 'n/a'
        zip_code = place.zip_code if place.zip_code else 'n/a'

        address_info_list.append(address)
        address_info_list.append(city)
        address_info_list.append(state)

        if country.upper() not in [
            'USA', 'US', 'U.S.A'
        ] and place.country_iso_code != 'US':
            address_info_list.append(country)

        address_info_list.append(zip_code)

    address_info = '<strong>Our office</strong><br>' + ', '.join(
        address_info_list
    )
    full_address = ' - '.join(address_info_list)

    user_lang = get_final_user_lang(owner_user, request)
    user_currency = get_user_currency(owner_user, request)

    ftmpl = 'https://www.pro.raisin.digital/{}/faq{}.html'
    faq_url = ftmpl.format(
        'fr', '-fr'
    ) if user_lang == 'FR' else ftmpl.format('en', '')

    if place:
        unread_comments = Comment.objects.filter(
            place_id=place.id,
            in_reply_to=None,
            is_archived=False,
            read_receipts=None
        ).count()
    else:
        unread_comments = 0

    return {
        'current_tab': tab,
        'establishment_name': place.name if place else 'n/a',
        'full_address': full_address,
        'address_info': address_info,
        'user': request.user,
        'user_lang': user_lang,
        'user_currency': user_currency,
        'owner_user': owner_user,
        'faq_url': faq_url,
        'unread_comments': unread_comments,
        'logged_as_admin': request.user.type in user_admin_types,
        'subscription': place.subscription if place and place.subscription else None
    }


def redirect_to_pro_page(request, page_handle):
    user_venue = get_user_venue(get_owner_user(request), request)

    return redirect(
        page_handle, pid=user_venue.id
    ) if user_venue else redirect(page_handle)


def resolve_url_to_pro_page(request, page_handle):
    user_venue = get_user_venue(get_owner_user(request), request)

    return resolve_url(
        page_handle, pid=user_venue.id
    ) if user_venue else resolve_url(page_handle)


def del_session_pro_place_id(request):
    if request.session.get('pro_place_id'):
        del request.session['pro_place_id']


def handle_provided_place_id(request, pid=None):
    res = {'redirect': None}
    is_admin = request.user.type in user_admin_types

    if not is_admin:
        del_session_pro_place_id(request)

        return res

    if pid:
        place = Place.active.filter(id=pid).first()

        if not place or not place.owner:
            res['redirect'] = redirect('list_places_subscribers')
        request.session['pro_place_id'] = pid

        return res

    if not request.session.get('pro_place_id'):
        res['redirect'] = redirect('list_places_subscribers')

    return res


def get_color_config():
    color_config = {}
    for color in ['red', 'white', 'sparkling', 'pink', 'orange']:
        color_config[color] = {
            'capitalised': _(color.capitalize() + ' wines'),
            'icon': static('pro_assets/img/wine-icon-{}.png'.format(color)),
        }

    for value, color in WineColorE.names.items():
        color_config[color.lower()]['value'] = value

    color_config['sparkling']['value'] = 'sparkling'

    return color_config


def get_canny_boards(lang):
    API_KEY = CANNY_API_KEY_EN if lang == "EN" else CANNY_API_KEY_FR
    url = CANNY_URL + API_KEY
    response = requests.get(url)

    if response.status_code != 200:
        log.debug("Canny request error! status_code: {} error: {}".format(
            response.status_code, response.text
        ))
        return None

    return json.loads(response.text)


def create_canny_token(user, lang):
    user_data = {
        'email': user.email,
        'id': str(user.id),
        'name': user.username,
    }

    private_key = CANNY_PRIVATE_KEY_EN if lang == "EN" else CANNY_PRIVATE_KEY_FR  # noqa
    return jwt.encode(user_data, private_key, algorithm='HS256').decode('utf-8') # noqa
