import binascii
import json
import logging
import os
import re
from html.parser import HTMLParser

log = logging.getLogger(__name__)


def format_price_float(price):
    if not price:
        return 0
    price_float = get_float(price)
    return price_float


def format_price(price):
    return "{0:.2f}".format(get_float(price)) if price else ""


def format_currency(currency):
    if not currency:
        return ""
    if currency == 'JPY':
        return "¥"
    else:
        return currency


def get_float_dot_or_comma(val_str):
    if not isinstance(val_str, str):
        val_str = str(val_str)
    val_str = re.sub(',', '.', val_str)
    return get_float(val_str)


def get_float(val_str):
    try:
        val_float = float(val_str)
        return val_float
    except ValueError:
        return None


def int_from_str_or_zero(text):
    if not text or text == '':
        return 0
    else:
        return int(text)


def strip_leading_zero(text):
    if not text or text == '':
        return text
    if text[0] == '0' and len(text) > 1:
        text = text[1:]
    return text


def strip_leading_zero_ret_int_or_zero(text):
    text = str(text) if text else ''
    text = strip_leading_zero(text)
    return int_from_str_or_zero(text)


def get_filter_criteria_for_order_last_id(
    order_dir, last_id, filter_criteria={}
):
    if last_id and order_dir == 'desc':
        filter_criteria['id__lt'] = last_id
    elif last_id and order_dir == 'asc':
        filter_criteria['id__gt'] = last_id

    return filter_criteria


def cut_string(string, length=120, suffix='...'):
    if not string:
        return ''

    if len(string) <= length:
        return string
    else:
        cut_point = length - 1

        if string[cut_point].isalpha():
            for i in range(cut_point, 0, -1):
                if not string[i].isalpha():
                    return string[0:i] + suffix
        return string[0:cut_point] + suffix


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    if not html:
        return ''
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def load_json(json_text, ret_if_fail={}):
    try:
        data_json = json.loads(json_text)
        return data_json
    except json.JSONDecodeError:
        return ret_if_fail
    except ValueError:
        return ret_if_fail
    except Exception:
        return ret_if_fail


def load_json_if_str(json_x, ret_if_fail={}):
    if not json_x:
        return ret_if_fail
    elif isinstance(json_x, str):
        return load_json(json_x, ret_if_fail)
    else:
        return json_x


def beautify_place_name(place_name):
    place_name = re.sub("'", "’", place_name)
    return place_name


def make_winepost_title(wine_name, wine_year):
    if wine_year:
        return "%s %s" % (wine_name, wine_year)
    else:
        return wine_name


def generate_key():
    return binascii.hexlify(os.urandom(20)).decode()


def get_sulfur_levels_from_yearly_data(pp_yearly_data):
    pp_yearly_data = load_json_if_str(pp_yearly_data, {})
    sulfur_levels = []
    if pp_yearly_data:
        for ppyd_year, ppyd_data in pp_yearly_data.items():
            sulfur_levels.append({
                'year': int(ppyd_year) if ppyd_year.isdigit() else None,
                'free_so2': ppyd_data['free_so2'] if 'free_so2' in ppyd_data else None,  # noqa
                'total_so2': ppyd_data['total_so2'] if 'total_so2' in ppyd_data else None,  # noqa
                'grape_variety': ppyd_data['grape_variety'] if 'grape_variety' in ppyd_data else None,  # noqa
            })
    return sulfur_levels
