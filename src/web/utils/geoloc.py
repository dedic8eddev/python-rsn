import re
import json
import requests
import math
import logging
from django.conf import settings
from timezonefinder import TimezoneFinder


log = logging.getLogger(__name__)


def set_address_data_from_cd(cd, entity):
    entity.country = cd['country']
    address_data_latlng = get_address_data_for_latlng(cd['latitude'], cd['longitude'])

    if cd['country_iso_code']:
        entity.country_iso_code = cd['country_iso_code']
    else:
        entity.country_iso_code = address_data_latlng['iso']

    if cd['country']:
        entity.country = cd['country']
    elif address_data_latlng['country']:
        entity.country = address_data_latlng['country']
    else:
        entity.country = None

    if cd['city']:
        entity.city = cd['city']
    elif address_data_latlng['city'] and address_data_latlng['quality'] < 3:
        entity.city = address_data_latlng['city']
    else:
        entity.city = None

    if cd['state']:
        entity.state = cd['state']
    elif address_data_latlng['state'] and address_data_latlng['quality'] < 3:
        entity.state = address_data_latlng['state']
    else:
        entity.state = None

    if str(cd['latitude']) and str(cd['longitude']):
        entity.latitude  = cd['latitude']
        entity.longitude = cd['longitude']
    else:
        entity.latitude  = None
        entity.longitude = None

    if str(cd['pin_latitude']) and str(cd['pin_longitude']):
        entity.pin_latitude  = cd['pin_latitude']
        entity.pin_longitude = cd['pin_longitude']
    else:
        entity.pin_latitude  = None
        entity.pin_longitude = None

    if cd['full_street_address']:
        entity.full_street_address = cd['full_street_address']
        entity.street_address = cd['full_street_address']
    elif cd['street_address']:
        entity.street_address = cd['street_address']
        entity.full_street_address = cd['street_address']


def get_address_data_for_latlng(latitude, longitude, lang='en', get_route=False):
    """
    getting place for latitude %s and longitude %s
    :param latitude:
    :param longitude:
    :param lang:
    :param get_route:
    :return:
    """

    city = None
    country = None
    iso = None
    state = None
    postal_code = None
    route = None
    street_number = None
    quality = 99
    retrieved = False
    full_street_address = None

    sublocalities = {}

    response_json = get_reverse_geocode_response(latitude, longitude, result_type="locality|postal_code", lang=lang)

    if response_json:
        quality = 1
    else:
        response_json = get_reverse_geocode_response(latitude, longitude, result_type="political|premise", lang=lang)
        if response_json and response_json['results']:
            quality = 2
        else:
            response_json = get_reverse_geocode_response(latitude, longitude, result_type="", lang=lang)
            if response_json and response_json['results']:
                quality = 3
            else:  # NO geolocation  results
                return {"city": city, "country": country, "iso": iso, "state": state, "postal_code": postal_code,
                        "route": route, "street_number": street_number,
                        "quality": quality, "retrieved": retrieved, "full_street_address": full_street_address}

    if response_json['results']:
        retrieved = True

        addr_components = response_json['results'][0]['address_components']
        for addr_comp in addr_components:
            if not city and "types" in addr_comp and "locality" in addr_comp['types']:
                city = addr_comp['long_name']
            if (not country or not iso) and "types" in addr_comp and "country" in addr_comp['types']:
                country = addr_comp['long_name']
                iso = addr_comp['short_name']

            if not state and "types" in addr_comp and "administrative_area_level_1" in addr_comp['types']:
                state = addr_comp['short_name']

            if not street_number and "types" in addr_comp and "street_number" in addr_comp['types']:
                street_number = addr_comp['short_name']

            if not postal_code and "types" in addr_comp and "postal_code" in addr_comp['types']:
                postal_code = addr_comp['short_name']

            # if not route and "types" in addr_comp and "route" in addr_comp['types']:
            #     route_0 = addr_comp['long_name']

            for type_test in addr_comp['types']:
                x = re.search('^sublocality_level_(.+)', type_test)
                if x:
                    subloc_no = x.groups()[0]
                    sublocalities[subloc_no] = addr_comp['long_name']

        if get_route:
            route = response_json['results'][0]['name'] if response_json and 'results' in response_json and \
                                       response_json['results'] and 'name' in response_json['results'][0] else None

            if not route and (iso.upper() == 'JP' or lang == 'ja') and sublocalities:
                sorted_items = sorted(sublocalities.items())
                route = ", ".join([str(item[1]) for item in sorted_items])

    return {"city": city, "country": country, "iso": iso, "state": state, "postal_code": postal_code, "route": route,
            "street_number": street_number, "quality": quality, "retrieved": retrieved,
            "full_street_address": full_street_address}


def get_by_query_address(addr, lat, lng):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json?query={addr}&" \
          "location={lat},{lng}&radius=10000&key={google_api_key}". \
            format(lat=lat, lng=lng, addr=addr, google_api_key=settings.GOOGLE_API_KEY)

    try:
        response = requests.get(url)
        response_text = response.text
        response_json = json.loads(response_text)
        return response_json
    except Exception as e:
        log.debug("errors in data fetching, skipping item - msg: %s" % str(e))
        return None


def get_place_json_data_by_google_place_id(google_place_id, lang='en'):
    url = "https://maps.googleapis.com/maps/api/place/details/json?placeid={place_id}&key={google_api_key}" \
          "&language={lang}".\
        format(place_id=google_place_id, google_api_key=settings.GOOGLE_API_KEY, lang=lang)
    try:
        response = requests.get(url)
        response_text = response.text
        response_json = json.loads(response_text)
        return response_json
    except Exception as e:
        log.debug("errors in data fetching, skipping item - msg: %s" % str(e))
        return None


def get_addr_data_by_google_place_id(google_place_id, lang='en'):
    response_json = get_place_json_data_by_google_place_id(google_place_id, lang=lang)
    city = None
    country = None
    iso = None
    state = None
    postal_code = None
    route = None
    street_number = None
    quality = 99
    retrieved = False
    full_street_address = None
    sublocalities = {}

    if response_json['result']:
        retrieved = True

        addr_components = response_json['result']['address_components']
        for addr_comp in addr_components:
            if not city and "types" in addr_comp and "locality" in addr_comp['types']:
                city = addr_comp['long_name']
            if (not country or not iso) and "types" in addr_comp and "country" in addr_comp['types']:
                country = addr_comp['long_name']
                iso = addr_comp['short_name']

            if not state and "types" in addr_comp and "administrative_area_level_1" in addr_comp['types']:
                state = addr_comp['short_name']

            if not street_number and "types" in addr_comp and "street_number" in addr_comp['types']:
                street_number = addr_comp['short_name']

            if not postal_code and "types" in addr_comp and "postal_code" in addr_comp['types']:
                postal_code = addr_comp['short_name']

            # if not route and "types" in addr_comp and "route" in addr_comp['types']:
            #     route_0 = addr_comp['long_name']

            for type_test in addr_comp['types']:
                x = re.search('^sublocality_level_(.+)', type_test)
                if x:
                    subloc_no = x.groups()[0]
                    sublocalities[subloc_no] = addr_comp['long_name']

        route = response_json['result']['name']
        if not route and iso.upper() == 'JP' and sublocalities:
            sorted_items = sorted(sublocalities.items())
            route = ", ".join([str(item[1]) for item in sorted_items])
    return {"city": city, "country": country, "iso": iso, "state": state, "postal_code": postal_code, "route": route,
            "street_number": street_number, "quality": quality, "retrieved": retrieved,
            "full_street_address": route}


def get_reverse_geocode_response(latitude, longitude, result_type="locality|postal_code|political|premise", lang='en'):
    url = "https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={google_api_key}&" \
          "language={lang}&result_type={result_type}". \
        format(lat=latitude, lng=longitude, google_api_key=settings.GOOGLE_API_KEY, result_type=result_type, lang=lang)

    try:
        response = requests.get(url)
        response_text = response.text
        response_json = json.loads(response_text)
        return response_json
    except Exception as e:
        log.debug("errors in data fetching, skipping item - msg: %s" % str(e))
        return None


def meters_to_deg(meters, latitude):
    return meters / (111.32 * 1000 * math.cos(latitude * (math.pi / 180)))


def update_lat(latitude):
    if not latitude:
        return None
    latitude += meters_to_deg(15, latitude)
    return latitude


def get_timezone_id_by_lat_lng(lat, lng):
    tz_finder = TimezoneFinder()
    tz_id = tz_finder.timezone_at(lng=lng, lat=lat)
    return tz_id
