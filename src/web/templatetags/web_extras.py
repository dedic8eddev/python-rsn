import json
from datetime import datetime

import pycountry
from django import template

from raisin import settings

register = template.Library()


@register.simple_tag()
def dump(value):
    if hasattr(value, "__dict__"):
        print(vars(value))
    else:
        print(str(value))


@register.simple_tag()
def get_chargebee_url():
    return settings.RAISIN_CHARGEBEE_URL


@register.filter(name="keyval")
def keyval(dictionary, key):
    if dictionary == '' or dictionary is None:
        return {}

    if type(key) == int and dictionary.get(key) is None:
        return dictionary.get(str(key))

    return dictionary.get(key)


@register.filter(name="jsonkey")
def jsonkey(jsonstr, key):
    if jsonstr is None:
        return None

    dictionary = json.loads(jsonstr)

    if key != 'country':
        return dictionary.get(key)

    if dictionary.get(key):
        return pycountry.countries.get(alpha_2=dictionary.get(key)).name
    return ''


@register.filter(name="get_days_until")
def daysuntil(until_date):
    if isinstance(until_date, datetime):
        delta = until_date - datetime.now()

        return delta.days

    return '-'
