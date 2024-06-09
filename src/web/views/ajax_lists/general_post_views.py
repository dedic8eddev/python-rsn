import operator
from functools import reduce

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from web.constants import PostStatusE, PostTypeE
from web.models import Post
from web.utils.model_tools import cut_string
from web.utils.views_common import get_current_user
from web.views.ajax_lists.common import (
    ajax_list_control_with_search_and_ordering, ajax_list_get_offsets)
from web.views.ajax_lists.formatting import (format_geoloc_html,
                                             format_img_html, format_user_html)


def general_post_items_col_map_default():
    return {
        0: 'id',
        1: None,  # img
        2: 'modified_time',
        3: 'author__username',  # author img

        4: 'title',
        5: 'description',
        6: 'status',

        7: 'place__name',
        8: 'comment_number',
        9: 'likevote_number',
    }


def food_items_col_map_default():
    return {
        0: 'id',
        1: None,  # img
        2: 'modified_time',
        3: 'place__name',
        4: 'author__username',  # author img

        5: 'title',
        6: 'description',
        7: 'status',

        8: 'comment_number',
        9: 'likevote_number',
    }


def format_status(item):
    if item.status == PostStatusE.DRAFT:
        return '<button class="btn btn-xs draft">draft</button>'

    if item.status == PostStatusE.PUBLISHED:
        return '<button class="btn btn-xs included">published</button>'

    return ""


def format_title(item, post_type):
    return '<a href="%s">%s</a>' % (
        reverse('edit_' + post_type, args=[item.id]), item.title
    )


def format_for_general_posts(items):
    items_out = []
    for item in items:
        img_html = format_img_html(item.main_image, item.title, side_size=35)
        status_html = format_status(item)
        title_html = format_title(item, 'generalpost')

        cb = '<input id="colors-{}-toggle-1" name="ids" value="{}" type="checkbox">'  # noqa

        item_out = {
            'checkbox_id': cb.format(item.id, item.id),
            'img_html': img_html,
            'date': item.modified_time.strftime('%d %b %Y %H:%M'),
            'author_img_html': format_user_html(item.author),
            'title': title_html,
            'description': "{} [{}]".format(
                cut_string(item.description, 382), len(item.description) if
                item.description is not None else 0
            ),
            'status_html': status_html,
            'place_html': format_geoloc_html(item.place),
            'comment_number': item.comment_number,
            'likevote_number': item.likevote_number,
        }

        items_out.append(item_out)

    return items_out


def format_for_food_posts(items):
    items_out = []
    for item in items:
        img_html = format_img_html(item.main_image, item.title, side_size=35)
        status_html = format_status(item)
        title_html = format_title(item, 'food')

        cb = '<input id="colors-{}-toggle-1" name="ids" value="{}" type="checkbox">'  # noqa

        item_out = {
            'checkbox_id': cb.format(item.id, item.id),
            'img_html': img_html,
            'date': item.modified_time.strftime('%d %b %Y %H:%M'),
            'place_html': format_geoloc_html(item.place),
            'author_img_html': format_user_html(item.author),
            'title': title_html,
            'description': "{} [{}]".format(
                cut_string(item.description, 382), len(item.description)
            ),
            'status_html': status_html,
            'comment_number': item.comment_number,
            'likevote_number': item.likevote_number,
        }

        items_out.append(item_out)

    return items_out


def _retrieve_non_wine_posts(
    request, col_map=None, post_type=PostTypeE.NOT_WINE,
    format_items_fn=format_for_general_posts
):
    page = None
    limit = None
    order_by = ['-modified_time']
    start = None
    length = None
    search_value = None

    (
        page, limit, start, length, search_value, order_by
    ) = ajax_list_control_with_search_and_ordering(
        request,
        col_map=col_map
    )
    (offset_0, offset_n) = ajax_list_get_offsets(start, length, page, limit)

    filter_criteria = Q(type=post_type)

    if search_value:
        search_filters = {
            Q(title__unaccent__icontains=search_value),
            Q(author__username__unaccent__icontains=search_value),
            Q(description__unaccent__icontains=search_value),
            Q(expert__username__unaccent__icontains=search_value),
            Q(place__name__unaccent__icontains=search_value)
        }

        if search_value.upper() in PostStatusE.names_human:
            search_filters.add(Q(
                status=PostStatusE.names_human[search_value.upper()]
            ))

        q_search = reduce(operator.or_, search_filters)
        filter_criteria &= q_search

    items = Post.objects.filter(filter_criteria).order_by(*order_by)

    items_count = items.count()
    items = items[offset_0:offset_n]

    items_out = format_items_fn(items)

    return JsonResponse({
        "iTotalRecords": items_count,
        "iTotalDisplayRecords": items_count,
        "data": items_out
    })


# /ajax/post/items
@csrf_exempt
@login_required
def get_general_post_items(request):
    get_current_user(request)

    return _retrieve_non_wine_posts(
        request,
        col_map=general_post_items_col_map_default(),
        format_items_fn=format_for_general_posts,
        post_type=PostTypeE.NOT_WINE
    )


# /ajax/post/items
@csrf_exempt
@login_required
def get_food_items(request):
    get_current_user(request)

    return _retrieve_non_wine_posts(
        request,
        col_map=food_items_col_map_default(),
        format_items_fn=format_for_food_posts,
        post_type=PostTypeE.FOOD
    )
