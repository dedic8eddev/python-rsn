from random import randrange
from time import sleep

import requests

OSM_BASE_URL = 'https://nominatim.openstreetmap.org/'


# https://nominatim.openstreetmap.org/search?q=3 Rue Jouye-Rouve, Paris, France&format=json&accept-language=en
# https://nominatim.org/release-docs/develop/api/Search/
def osm_search(search_request):
    osm_params = [
        'format=json',
        'accept-language=en'
    ]
    osm_path = 'search?q={}'.format(search_request)
    reqeust_url = '{base_url}{osm_path}&{osm_params}'.format(
        base_url=OSM_BASE_URL,
        osm_path=osm_path,
        osm_params='&'.join(osm_params)
    )
    print(reqeust_url)
    r = requests.get(reqeust_url)
    if r.status_code == 200:
        return r.json()
    raise Exception(r.text)


# https://nominatim.openstreetmap.org/details?osmtype=N&osmid=4858023696&addressdetails=1&format=json&accept-language=en
# https://nominatim.org/release-docs/develop/api/Details/
def osm_details(place_id):
    osm_params = [
        'addressdetails=1',
        'format=json',
        'accept-language=en'
    ]
    # osm_path = 'details?osmtype=N&osmid={}'.format(osm_id)
    osm_path = 'details?place_id={}'.format(place_id)
    reqeust_url = '{base_url}{osm_path}&{osm_params}'.format(
        base_url=OSM_BASE_URL,
        osm_path=osm_path,
        osm_params='&'.join(osm_params)
    )
    print(reqeust_url)
    r = requests.get(reqeust_url)
    if r.status_code == 200:
        return r.json()
    raise Exception(r.text)


def get_place_id_by_address(address):
    json_data = osm_search(address)
    if json_data and isinstance(json_data, list) and len(json_data) > 0:
        return json_data[0].get('place_id')
    return None


def get_osm_address(admin_level, address):
    osm_address = None
    place_id = get_place_id_by_address(address)
    if place_id:
        details = osm_details(place_id)
        if details and 'address' in details:
            addresses = details.get('address')
            for address in addresses:
                if str(address.get('admin_level')) == admin_level and address.get('isaddress', False) and \
                        address.get('osm_type', '') == 'R':
                    osm_address = address
                    break
    return osm_address


def get_osm_city_location(second_request=False, **kwargs):
    osm_params = [
        'format=json',
        'accept-language=en'
    ]
    search_params = [
        f'{k}={v}' for k, v in kwargs.items()
    ]
    osm_path = 'search?{}'.format('&'.join(search_params))
    reqeust_url = '{base_url}{osm_path}&{osm_params}'.format(
        base_url=OSM_BASE_URL,
        osm_path=osm_path,
        osm_params='&'.join(osm_params)
    )
    print(reqeust_url)
    r = requests.get(reqeust_url)

    if r.status_code == 200:
        response_data = r.json()
        if len(response_data) > 0:
            if response_data[0].get('lon') and response_data[0].get('lat'):
                location = (float(response_data[0].get('lon')), float(response_data[0].get('lat')))
                return location
            return None
        elif not second_request and 'state' in kwargs:
            region = kwargs.pop('state')
            print(f'Exclude Region from request: {region}')
            return get_osm_city_location(second_request=True, **kwargs)
        else:
            return None
    raise Exception(r.text)


def get_osm_city_name_by_lon_lat(lon, lat):
    osm_params = [
        'format=json',
        'accept-language=en'
    ]
    search_params = [
        f'lat={lat}',
        f'lon={lon}'
    ]
    osm_path = 'reverse?{}'.format('&'.join(search_params))
    reqeust_url = '{base_url}{osm_path}&{osm_params}'.format(
        base_url=OSM_BASE_URL,
        osm_path=osm_path,
        osm_params='&'.join(osm_params)
    )
    r = requests.get(reqeust_url)

    if r.status_code == 200:
        response_data = r.json()
        if len(response_data) > 0:
            if 'address' in response_data:
                address_data = response_data.get('address')
                name = address_data.get('city') or address_data.get('town') or address_data.get('village') or \
                    address_data.get('suburb') or address_data.get('hamlet') or \
                    address_data.get('city_district') or address_data.get('state_district')
                return name
            return None
        else:
            return None
    print(reqeust_url)
    raise Exception(r.text)


def get_osm_city_and_country_name_by_lon_lat(lon, lat):
    osm_params = [
        'format=json',
        'accept-language=en'
    ]
    search_params = [
        f'lat={lat}',
        f'lon={lon}'
    ]
    osm_path = 'reverse?{}'.format('&'.join(search_params))
    reqeust_url = '{base_url}{osm_path}&{osm_params}'.format(
        base_url=OSM_BASE_URL,
        osm_path=osm_path,
        osm_params='&'.join(osm_params)
    )
    r = requests.get(reqeust_url)

    if r.status_code == 200:
        response_data = r.json()
        if len(response_data) > 0:
            if 'address' in response_data:
                address_data = response_data.get('address')
                city = address_data.get('city') or address_data.get('town') or address_data.get('village') or \
                    address_data.get('suburb') or address_data.get('hamlet') or \
                    address_data.get('city_district') or address_data.get('state_district')
                country = address_data.get('country')
                return city, country
            return None
        else:
            return None
    elif r.status_code in [504, 502]:
        sleep_sec = randrange(5, 10)
        sleep(sleep_sec)
        return get_osm_city_and_country_name_by_lon_lat(lon, lat)
    print(reqeust_url)
    raise Exception(r.text)
