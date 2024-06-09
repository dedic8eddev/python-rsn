from __future__ import absolute_import

import logging
import random
import time

from django.conf import settings
from django.urls import reverse
from django.templatetags.static import static

from web.constants import (PostStatusE, PostTypeE, UserStatusE,
                           WinemakerStatusE, WineStatusE, PlaceStatusE)
from web.utils.model_tools import beautify_place_name
from web.utils.upload_tools import aws_url

log = logging.getLogger(__name__)


def format_img_html(
    image, alt_text, author=None, side_size=35,
    img_class="", img_style="", add_timestamp=False
):
    if image:
        thumb = aws_url(image, thumb=True)
        image = aws_url(image)
    elif author and author == 'chargebee':
        thumb = settings.SITE_URL + static('assets/img/chargebee.jpg')
        image = settings.SITE_URL + static('assets/img/chargebee.jpg')
    else:
        thumb = settings.SITE_URL + static('assets/img/missing-image.jpg')
        image = settings.SITE_URL + static('assets/img/missing-image.jpg')

    html = '<a href="{image}" data-toggle="lightbox" data-title="{' \
           'name}"> <img width="{side_size}" height="{side_size}" ' \
           'class="{img_class}" style="{img_style}" src="{thumb}" ' \
           'alt="{name}"/></a>'

    if add_timestamp:
        thumb += "?ts=%s-%s" % (time.time(), random.random())

    return html.format(
        image=image, thumb=thumb, name=alt_text, side_size=side_size,
        img_class=img_class, img_style=img_style
    )


def format_img_default_html():
    html = '<img width="{side_size}" height="{side_size}" ' \
           'class="{img_class}" style="{img_style}" src="{thumb}" ' \
           'alt="{name}"/>'

    side_size = 35
    alt_text = ''
    img_class = ''
    img_style = ''
    thumb = static('assets/img/missing.gif')

    return html.format(
        thumb=thumb, name=alt_text, side_size=side_size,
        img_class=img_class, img_style=img_style
    )


def format_user_html(
    author,
    show_author_username=False,
    show_is_banned=False
):
    if not author:
        return ''

    author_edit_url = reverse('edit_user', args=[author.pk])
    author_thumb_url = aws_url(author.image, thumb=True)

    if author.username == 'chargebee':
        tmpl = '<strong class="fa copyright" data-toggle="tooltip" ' \
            'title="" data-placement="top" data-original-title="{}">Ⓒ</strong>'
    else:
        tmpl = '<div class="picture-small" data-original-title="{}" ' \
            'data-toggle="tooltip" title="" data-placement="top">' \
            '<a href="{}">' \
            '<img width="35" height="35" src="{}"' \
            ' alt="{}"/>' \
            '{}</a>{}</div>'

    if show_author_username:
        name_text = '<span>{}</span>'.format(author.username)
    else:
        name_text = ''

    if show_is_banned and author.status == UserStatusE.BANNED:
        banned_icon = '<i class="fa fa-lock activebblue"></i>'
    else:
        banned_icon = ''

    if author.username == 'chargebee':
        html_out = tmpl.format(
            author.username,
        )
    else:
        html_out = tmpl.format(
            author.username,
            author_edit_url,
            author_thumb_url,
            author.username,
            name_text,
            banned_icon
        )

    return html_out


def format_geoloc_html(place):
    if not place:
        return ''

    url = reverse('edit_place', args=[place.id])
    pro_url = reverse('pro_dashboard', args=[place.id])
    name = beautify_place_name(place.name)

    if place.is_subscriber():
        pn = '<a href="{}">{}</a>&nbsp;&nbsp;<a style="text-decoration:none" href="{}">🧰</a>'  # noqa
        return pn.format(url, name, pro_url)

    return '<a href="{}">{}</a>'.format(url, name)


def _format_title_icon(item, style=''):
    title_icon = ''

    if item.is_parent_post:
        if item.status == PostStatusE.PUBLISHED:
            title_icon = '<i style="{}" class="fa fa-bookmark-o" ></i> '.format(style)  # noqa
        elif item.status in [
            PostStatusE.IN_DOUBT,
            PostStatusE.BIO_ORGANIC,
            PostStatusE.REFUSED
        ]:
            title_icon = '<i style="{}"> ®️</i>'.format(style)

    return title_icon


def winepost_title_html(item):
    if item.type == PostTypeE.NOT_WINE:
        title_link = '<a href="{}">{}</a>'.format(
            reverse('edit_generalpost', args=[item.id]),
            item.title
        )
        return title_link

    title_text = "{} {}".format(
        item.wine.name, item.wine_year
    ) if item.wine_year else item.wine.name
    icons_html = ""
    signs_html = ""

    title_icon = _format_title_icon(item, style='margin-left: 6px;')

    if (
        not title_icon and
        item.is_parent_post and
        item.status in [PostStatusE.DRAFT, PostStatusE.IN_DOUBT]
    ):
        title_icon = '<br /><b>[ TO VALIDATE ]</b>'

    icons_html += title_icon

    if item.is_star_review:
        icons_html += '<i style="margin-left: 6px;" class="fa fa-star onstar" />'  # noqa

    if (
        item.wine.winemaker.status == WinemakerStatusE.VALIDATED and
        (
            item.status in [PostStatusE.DRAFT, PostStatusE.IN_DOUBT] or
            item.wine.status == WineStatusE.ON_HOLD
        )
    ):
        signs_html += (
            '<span data-original-title="Registered wine maker / Wine not ' +
            'yet in database" class="wine" style="margin-left: 5px;" ' +
            'data-toggle="tooltip" title="" data-placement="bottom">?</span>'
        )

    title_text += '<br /><strong>({})</strong>'.format(
        'scanned' if item.is_scanned else 'autocomp.'
    )

    if item.is_archived:
        title_html = '<a href="{}">{}</a>'.format(
            reverse('edit_winepost', args=[item.id]),
            title_text
        )
    else:
        title_html = '<a href="{}">{}{}{}</a>'.format(
            reverse('edit_winepost', args=[item.id]),
            title_text, icons_html, signs_html
        )

    return title_html


def format_winepost_status(item):
    if item.type == PostTypeE.WINE:
        if item.status == PostStatusE.DELETED:
            status_html = '<button class="btn btn-xs delete">deleted</button>'
        elif item.status == PostStatusE.IN_DOUBT:
            status_html = '<button class="btn btn-xs indoubt">in doubt</button>'  # noqa
        elif item.status == PostStatusE.DRAFT:
            status_html = '<button class="btn btn-xs onhold">draft</button>'
        elif item.status == PostStatusE.PUBLISHED:
            status_html = '<button class="btn btn-xs included">natural</button>'  # noqa
        elif item.status == PostStatusE.REFUSED:
            status_html = '<button class="btn btn-xs refused">not natural</button>'  # noqa
        elif item.status == PostStatusE.BIO_ORGANIC:
            status_html = '<button class="btn btn-xs bioorg">bio-organic</button>'  # noqa
        elif item.status == PostStatusE.TO_INVESTIGATE:
            status_html = '<button class="btn btn-xs to_investigate">to investigate</button>'  # noqa
        else:
            status_html = ""
    else:
        if item.status == PostStatusE.DELETED:
            status_html = '<button class="btn btn-xs delete">deleted</button>'
        elif item.status == PostStatusE.DRAFT:
            status_html = '<button class="btn btn-xs draft">draft</button>'
        elif item.status == PostStatusE.PUBLISHED:
            status_html = '<button class="btn btn-xs included">published</button>'  # noqa
        else:
            status_html = ""

    return status_html


def format_winemaker_name(item):
    winemaker_name_html = item.wine.winemaker.name

    if item.wine.winemaker.status in [
        WinemakerStatusE.DRAFT,
        WinemakerStatusE.IN_DOUBT
    ]:
        winemaker_name_html += (
            '<span data-original-title="not included in our database" ' +
            'class="warning" data-toggle="tooltip" title="" ' +
            'data-placement="bottom" style="margin-left:5px;">!</span>'
        )

    return '<a href="{}">{}</a>'.format(
        reverse("edit_winemaker", args=[item.wine.winemaker.id]),
        winemaker_name_html
    )


def format_img_html_wp(item, with_rating=False):
    if item.main_image:
        img_html = format_img_html(item.main_image, item.title)
    elif item.wine.main_image:
        img_html = format_img_html(item.wine.main_image, item.title)
    else:
        img_html = format_img_default_html()

    if not with_rating:
        return img_html

    title_icon = _format_title_icon(item)
    if item.status == PostStatusE.PUBLISHED:
        title_html = '<a href="{}" style="font-size:11px;">{}</a>'.format(
            reverse('edit_winepost', args=[item.id]),
            item.title
        )
    else:
        title_html = '<a href="{}" style="color:black!important; font-size:11px;">{}</a>'.format(  # noqa
            reverse('edit_winepost', args=[item.id]),
            item.title
        )

    vrt = item.get_vuf_rating_tracking()

    rating_html = "<strong>{}/6</strong>".format(
        int(vrt) + 1
    ) if vrt is not None else "<strong>n.a.</strong>"

    adding_method = '<strong>({})</strong>'.format(
        'scanned' if item.is_scanned else 'autocomp'
    )

    if item.is_archived:
        return '{}<br />{}<br />{}<br />{}'.format(
            img_html, title_html, rating_html, adding_method
        )

    return '{}{}<br />{}<br />{}<br />{}'.format(
        title_icon, img_html, title_html, rating_html, adding_method
    )


def format_wine_label(item, with_rating=False):
    if item.wine.main_image:
        return format_img_html(item.wine.main_image, item.title)
    elif item.main_image:
        return format_img_html(item.main_image, item.title)
    else:
        return format_img_default_html()


def format_vuforia_image(item, with_rating=False):
    if not item.wine.ref_image:
        return format_img_default_html()

    img_html = format_img_html(
        item.wine.ref_image, item.title, add_timestamp=True
    )

    if not with_rating:
        return img_html

    img_html += "<br />&nbsp;"

    vrt = item.wine.ref_image.rating_tracking

    rating_html = "<strong>{}/6</strong>".format(
        int(vrt) + 1
    ) if vrt is not None else "<strong>n.a.</strong>"

    return "<br />" + img_html + rating_html + "<br />"


def move_to_vuforia_arrow(item, what):
    ht = '<br /><a class="vuf-big-arrow" href="#" onclick="move_to_vuforia_from_list({}, \'{}\'); return false;" ' \
         'data-original-title="Move to Vuforia" data-toggle="tooltip" title="Move to Vuforia" data-placement="top"> ' \
         '<span>&#8682;</span></a>'

    return ht.format(item.id, what)


def format_place_status(item):
    """
    Format place status in HTML
    """
    if int(item.status) == PlaceStatusE.IN_DOUBT:
        status_text = '<button class="btn btn-xs indoubt">in doubt</button>'
    elif int(item.status) == PlaceStatusE.DRAFT:
        status_text = '<button class="btn btn-xs onhold">DRAFT</button>'
    elif int(item.status) == PlaceStatusE.PUBLISHED:
        status_text = '<button class="btn btn-xs published">Published</button>'
    elif int(item.status) == PlaceStatusE.SUBSCRIBER:
        status_text = '<button class="btn btn-xs subscriber">Subscriber</button>'  # noqa
    elif int(item.status) == PlaceStatusE.CLOSED:
        status_text = '<button class="btn btn-xs delete">Closed</button>'
    elif int(item.status) == PlaceStatusE.ELIGIBLE:
        status_text = '<button class="btn btn-xs eligible">Eligible</button>'
    elif int(item.status) == PlaceStatusE.NOT_ELIGIBLE:
        status_text = '<button class="btn btn-xs noteligible">Not Eligible</button>'  # noqa
    elif int(item.status) == PlaceStatusE.IN_REVIEW:
        status_text = '<button class="btn btn-xs inreview">In Review</button>'
    elif int(item.status) == PlaceStatusE.TO_PUBLISH:
        status_text = '<button class="btn btn-xs topublish">To Publish</button>'  # noqa
    else:
        status_text = ""
    return status_text


def format_winemaker_status(item):
    """
    Format winemaker status in HTML
    """
    if int(item.status) == WinemakerStatusE.VALIDATED:
        status_html = '<button class="btn btn-xs included">natural</button>'
    elif int(item.status) == WinemakerStatusE.IN_DOUBT:
        status_html = '<button class="btn btn-xs indoubt">in doubt</button>'
    elif int(item.status) == WinemakerStatusE.DRAFT:
        status_html = '<button class="btn btn-xs onhold">draft</button>'
    elif int(item.status) == WinemakerStatusE.REFUSED:
        status_html = '<button class="btn btn-xs refused">not natural</button>'
    elif int(item.status) == WinemakerStatusE.BIO_ORGANIC:
        status_html = '<button class="btn btn-xs bioorg">bio-organic</button>'
    elif int(item.status) == WinemakerStatusE.TO_INVESTIGATE:
        status_html = '<button class="btn btn-xs to_investigate">to investigate</button>'
    else:
        status_html = ""

    return status_html
