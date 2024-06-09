from web.constants import (PostStatusE, PostTypeE, WinemakerTypeE, wm_type_statuses)
from web.models import Post, Winemaker
from web.utils.views_common import get_current_user


def get_main_menu():
    main_menu = [
        {
            'item': 'venues',
            'url': 'list_places',
            'label': 'Recommended venues',
        },
        {
            'item': 'wineposts',
            'url': 'list_wineposts',
            'label': 'Wines',
        },
        {
            'item': 'winemakers',
            'url': 'list_wm_all',
            'label': 'winemakers',
        },
        {
            'label': 'Posted content',
            'item': 'posts',
            'url': 'list_generalposts'
        },
        {
            'label': 'Our Content',
            'url': 'list_featured_venues',
            'item': 'featured_venues'
        },
        {
            'item': 'events',
            'url': 'list_events',
            'label': 'events',
        },
        {
            'item': 'users',
            'url': 'list_users',
            'label': 'users',
        },
        {
            'item': 'ocr',
            'url': 'ocrpoc',
            'label': 'OCR',
        },
        {
            'item': 'donations',
            'url': 'list_donations',
            'label': 'Donations',
        },
        {
            'item': 'cities',
            'url': 'continent_list',
            'label': 'Areas',
        },
        {
            'item': 'reports',
            'url': 'reports',
            'label': 'Reported'
        }
    ]
    return main_menu


def get_c(
    request, active, path, sub_active=False, add_new_url=None,
    bc_path_alt=None, old_c=None
):
    current_user = get_current_user(request)

    home_tuple = ('/', 'Home')

    if bc_path_alt:
        bc_path = bc_path_alt
    elif path != '/':
        bc_path = [
            ('/' + i, i) if i != '' else home_tuple for i in path.split('/')
        ]
    else:
        bc_path = [home_tuple, ('/', 'places')]

    if old_c:
        c = old_c
    else:
        c = {}

    c['main_menu'] = get_main_menu()
    c['active'] = active if active else None
    c['sub_active'] = sub_active if sub_active else None
    c['bc_path'] = bc_path
    c['add_new_url'] = add_new_url
    c['current_user'] = current_user
    return c


def get_wineposts_number(query_filter):
    query = Post.active.filter(type=PostTypeE.WINE).filter(query_filter)
    total = query.exclude(status=PostStatusE.DRAFT).count()
    drafts = query.filter(status=PostStatusE.DRAFT).count()

    return total, drafts


def get_winemakers_number(query_filter):
    query = Winemaker.active.filter(query_filter)
    total = query.count()
    naturals = query.filter(
        status__in=wm_type_statuses[WinemakerTypeE.NATURAL]
    ).count()
    others = query.filter(
        status__in=wm_type_statuses[WinemakerTypeE.OTHER]
    ).count()

    return total, naturals, others
