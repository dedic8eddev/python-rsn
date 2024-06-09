import operator
from datetime import datetime
from functools import reduce

from django.db.models import Q

from web.constants import PlaceStatusE


def get_checkbox_id_html(item):
    htm = '<input id="colors-{}-toggle-1" name="ids" value="{}" type="checkbox">'  # noqa
    return htm.format(item.id, item.id)


def get_type_text(item):
    type_text = ""
    if item.is_wine_shop:
        type_text += '<button class="badge wineshop" style="margin: 2px;">Wine shop</button>'  # noqa

    if item.is_bar:
        type_text += '<button class="badge bar" style="margin: 2px;">Bar</button>'  # noqa

    if item.is_restaurant:
        type_text += '<button class="badge restaurant" style="margin: 2px;">Restaurant</button>'  # noqa
    return type_text


def get_website_url_link(item):
    if not item.website_url:
        return ''

    ws = '<a href="{}" title="{}" target="_blank"><i class="fa fa-link" aria-hidden="true"></i></a>'  # noqa
    return ws.format(item.website_url, item.website_url)


def get_social_links(item, website_url_link):
    social_links = ""
    if item.social_facebook_url:
        l = '<a href="{}" class="facebook" target="_blank"><i class="fa fa-facebook"></i></a>'  # noqa
        social_links += l.format(item.social_facebook_url)

    if item.social_twitter_url:
        l = '<a href="{}" class="twitter" target="_blank"><i class="fa fa-twitter"></i></a>'  # noqa
        social_links += l.format(item.social_twitter_url)

    if item.social_instagram_url:
        l = '<a href="{}" class="instagram" target="_blank"><i class="fa fa-instagram"></i></a>'  # noqa
        social_links += l.format(item.social_instagram_url)

    if website_url_link:
        social_links += website_url_link
    return social_links


def get_sticker_html(item):
    st = '<i class="fa {}" data-toggle="tooltip" title="{}" data-placement="bottom"><span style="padding: 4px;">{}</span></i>'  # noqa
    if item.sticker_sent:
        return st.format('fa-check-square', 'Sticker sent', 'YES')
    else:
        return st.format('fa-square-o', 'Sticker not yet sent', 'NO')


def get_total_wl_score(item):
    if not item.wl_added:
        return ''

    if item.total_wl_score:
        return "{}%".format(round(float(item.total_wl_score), 2))

    return "0%"


def get_filter_criteria_by_search_value(
    search_value, search_author=True, search_owner=False
):
    if search_value is None:
        return Q()

    date_formats = ['%b %Y', '%B %Y', '%b %y', '%B %y']
    match_date = None
    for date_format in date_formats:
        try:
            match_date = datetime.strptime(search_value, date_format)
            break
        except ValueError:
            pass

    if match_date:
        return Q(
            modified_time__month=match_date.month,
            modified_time__year=match_date.year
        )

    q_filters = [
        Q(name__unaccent__icontains=search_value),
        Q(street_address__unaccent__icontains=search_value),
        Q(house_number__unaccent__icontains=search_value),
        Q(city__unaccent__icontains=search_value),
        Q(zip_code__unaccent__icontains=search_value),
        Q(country__unaccent__icontains=search_value),
        Q(email__unaccent__icontains=search_value),
        Q(website_url__unaccent__icontains=search_value),
        Q(social_facebook_url__unaccent__icontains=search_value),
        Q(social_twitter_url__unaccent__icontains=search_value),
        Q(social_instagram_url__unaccent__icontains=search_value),
        Q(subscription__status__unaccent__icontains=search_value),
        Q(email__unaccent__icontains=search_value),
        Q(website_url__unaccent__icontains=search_value),
        Q(social_facebook_url__unaccent__icontains=search_value),
    ]

    if search_author:
        q_filters.append(Q(author__username__unaccent__icontains=search_value))

    if search_owner:
        q_filters.append(Q(owner__username__unaccent__icontains=search_value))

    if search_value.upper() in PlaceStatusE.names_human:
        q_filters.append(Q(
            status=PlaceStatusE.names_human[search_value.upper()]
        ))

    return reduce(operator.or_, q_filters)
