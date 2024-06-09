import json
import os
import re

from django.db import connection
from django.db.models import F
from django.urls import reverse
from unidecode import unidecode

from web.constants import WineListStatusE, PostTypeE, PostStatusE,\
    WinemakerStatusE
from web.models import Place, Winemaker, Post
from web.utils.fetches import fetchalldict
from web.utils.upload_tools import aws_url

from .defs import shorts


def clean_row(row):
    if not row:
        return ""
    row = unidecode(row)
    # '+' is for 'A+' issue
    # '&' is for [&, e, et] -> 'and' replacement
    if re.search(r"[^a-zA-Z0-9\s,.&:';+/-]", row, re.IGNORECASE):
        row = re.sub(r"[^a-zA-Z0-9\s,.&:';+/-]", '', row)  # exclude strange
        # characters (other than in set)
        row = re.sub(r"\s{2,}", ' ', row).strip()  # shrink whitespaces
    row = row.lower()
    return row


def replace_hyphen(match_obj):
    if match_obj.group(0) is not None:
        return match_obj.group(0).replace('-', ' ')


def replace_plus(match_obj):
    if match_obj.group(0) is not None:
        return match_obj.group(0).replace('+', 'plus')


def unify_spelling_row(row):
    if not row:
        return ""
    if re.search(r"\s&\s", row):
        row = re.sub(r"\s&\s", ' and ', row)  # replace '&' with 'and'
    if re.search(r"\set\s", row, re.IGNORECASE):
        row = re.sub(r"\set\s", ' and ', row)  # replace 'et' with 'and'
    if re.search(r"\se\s", row, re.IGNORECASE):
        row = re.sub(r"\se\s", ' and ', row)  # replace 'e' with 'and'

    # replace '-' inside words with whitespace.
    # Inside words only. Doesn't replace standalone hyphens.
    row = re.sub(r"\w-\w", replace_hyphen, row)

    # replace '+' in the end of any word with 'plus'.
    # Made exclusively for (wine name = 'A+') issue.
    # Leaves standalone pluses as is.
    row = re.sub(r"\w\+", replace_plus, row)
    return row


def deabbr_row(row):
    """ ROW MUST BE CLEANED FIRST with clean_row(row) !!! """
    if not row:
        return ""
    row_ls = row.split(" ")  # remove leading and trailing whitespaces
    for i, item in enumerate(row_ls):
        item_low = item.lower()
        if item_low in shorts:
            row_ls[i] = shorts[item_low]
    return " ".join(row_ls)


def fetch_validated_winemakers():
    natural_wms = []
    bio_organic_wms = []
    not_natural_wms = []
    to_investigate_wms = []
    in_doubt_wms = []
    other_wms = []

    winemakers = [natural_wms,
                  bio_organic_wms,
                  not_natural_wms,
                  to_investigate_wms,
                  in_doubt_wms,
                  other_wms]

    items = list(
        Winemaker.active.exclude(
            name__regex=r'^[a-zA-Z]$'
        ).exclude(
            name_short__regex=r'^[a-zA-Z]$'
        ).exclude(
            domain__regex=r'^[a-zA-Z]$'
        ).exclude(
            domain_short__regex=r'^[a-zA-Z]$'
        ).values()
    )
    for i in items:
        i['unac_name'] = clean_row(i['name'])
        i['uni_spelled_name'] = unify_spelling_row(i['unac_name'])
        i['deabbr_name'] = deabbr_row(i['uni_spelled_name'])
        i['unac_name_short'] = clean_row(i['name_short'])
        i['uni_spelled_name_short'] = unify_spelling_row(i['unac_name_short'])
        i['deabbr_name_short'] = deabbr_row(i['uni_spelled_name_short'])
        i['unac_domain'] = clean_row(i['domain'])
        i['uni_spelled_domain'] = unify_spelling_row(i['unac_domain'])
        i['deabbr_domain'] = deabbr_row(i['uni_spelled_domain'])
        i['unac_domain_short'] = clean_row(i['domain_short'])
        i['uni_spelled_domain_short'] = unify_spelling_row(i['unac_domain_short'])  # noqa
        i['deabbr_domain_short'] = deabbr_row(i['uni_spelled_domain_short'])
        if i['status'] == WinemakerStatusE.VALIDATED:
            natural_wms.append(i)
        elif i['status'] == WinemakerStatusE.BIO_ORGANIC:
            bio_organic_wms.append(i)
        elif i['status'] == WinemakerStatusE.REFUSED:
            not_natural_wms.append(i)
        elif i['status'] == WinemakerStatusE.TO_INVESTIGATE:
            to_investigate_wms.append(i)
        elif i['status'] == WinemakerStatusE.IN_DOUBT:
            in_doubt_wms.append(i)
        else:
            other_wms.append(i)
    return winemakers


def add_wine_into_appropriate_wm(item, items_list):
    if not item['winemaker_id'] in items_list:
        items_list[item['winemaker_id']] = []
    items_list[item['winemaker_id']].append(item)


def fetch_validated_wines_with_wms():
    accepted_winepost_statuses = [PostStatusE.DRAFT,
                                  PostStatusE.PUBLISHED,
                                  PostStatusE.BIO_ORGANIC,
                                  PostStatusE.IN_DOUBT,
                                  PostStatusE.REFUSED,
                                  PostStatusE.TO_INVESTIGATE]

    queryset = Post.active.filter(
        type=PostTypeE.WINE,
        is_parent_post=True,
        status__in=accepted_winepost_statuses
    ).exclude(
        wine__name__regex=r'^[a-zA-Z]$'
    ).exclude(
        wine__name_short__regex=r'^[a-zA-Z]$'
    ).select_related(
        'wine',
        'wine__winemaker'
    ).annotate(
        wp_id=F('id'),
        wp_status=F('status'),
        winemaker_id=F('wine__winemaker_id'),
        wm_name=F('wine__winemaker__name'),
        wm_name_short=F('wine__winemaker__name_short'),
        wm_domain=F('wine__winemaker__domain'),
        wm_domain_short=F('wine__winemaker__domain_short'),
        wine_name=F('wine__name'),
        wine_name_short=F('wine__name_short'),
        wine_status=F('wine__status')
    )
    items = list(queryset.values(
        'wp_id',
        'wp_status',
        'winemaker_id',
        'wine_name',
        'wine_name_short',
        'wine_status',
        'wm_name',
        'wm_name_short',
        'wm_domain',
        'wm_domain_short',
    ))

    natural_items_by_wm = {}
    bio_organic_items_by_wm = {}
    not_natural_items_by_wm = {}
    to_investigate_items_by_wm = {}
    in_doubt_items_by_wm = {}
    other_items_by_wm = {}

    items_by_wm = [natural_items_by_wm,
                   bio_organic_items_by_wm,
                   not_natural_items_by_wm,
                   to_investigate_items_by_wm,
                   in_doubt_items_by_wm,
                   other_items_by_wm]
    for i in items:
        i['unac_name'] = clean_row(i['wine_name'])
        i['uni_spelled_name'] = unify_spelling_row(i['unac_name'])
        i['deabbr_name'] = deabbr_row(i['uni_spelled_name'])
        i['unac_name_short'] = clean_row(i['wine_name_short'])
        i['uni_spelled_name_short'] = unify_spelling_row(i['unac_name_short'])
        i['deabbr_name_short'] = deabbr_row(i['uni_spelled_name_short'])
        i['unac_wm_name'] = clean_row(i['wm_name'])
        i['uni_spelled_wm_name'] = unify_spelling_row(i['unac_wm_name'])
        i['deabbr_wm_name'] = deabbr_row(i['uni_spelled_wm_name'])
        i['unac_wm_name_short'] = clean_row(i['wm_name_short'])
        i['uni_spelled_wm_name_short'] = unify_spelling_row(i['unac_wm_name_short'])  # noqa
        i['deabbr_wm_name_short'] = deabbr_row(i['uni_spelled_wm_name_short'])
        i['unac_wm_domain'] = clean_row(i['wm_domain_short'])
        i['uni_spelled_wm_domain'] = unify_spelling_row(i['unac_wm_domain'])
        i['deabbr_wm_domain'] = deabbr_row(i['uni_spelled_wm_domain'])

        if i['wp_status'] == PostStatusE.PUBLISHED:
            add_wine_into_appropriate_wm(i, natural_items_by_wm)
        elif i['wp_status'] == PostStatusE.BIO_ORGANIC:
            add_wine_into_appropriate_wm(i, bio_organic_items_by_wm)
        elif i['wp_status'] == PostStatusE.REFUSED:
            add_wine_into_appropriate_wm(i, not_natural_items_by_wm)
        elif i['wp_status'] == PostStatusE.TO_INVESTIGATE:
            add_wine_into_appropriate_wm(i, to_investigate_items_by_wm)
        elif i['wp_status'] == PostStatusE.IN_DOUBT:
            add_wine_into_appropriate_wm(i, in_doubt_items_by_wm)
        else:
            add_wine_into_appropriate_wm(i, other_items_by_wm)
    return {"items": items, "items_by_wm": items_by_wm}


def get_current_files(parent_id=None, is_temp=False, is_in_shared_pool=False):
    if is_temp:
        items_out = {
            'files': [],
            'place': None,
            'is_temp': True,
            'pid': parent_id,
        }

        sql = "SELECT wl.id as wl_id, wl.total_score_data, wl.status, wf.id as wf_id, wf.image_file FROM " \
              "    web_winelist wl INNER JOIN winelist_file wf ON wf.winelist_id = wl.id WHERE " \
              "    wl.is_archived=false AND wf.is_archived=false AND wl.status IN (%s, %s, %s) " \
              "    AND wl.is_temp = true AND wl.temp_parent_id = %s " \
              "    ORDER by wl.modified_time DESC"
        params = [WineListStatusE.OK, WineListStatusE.ON_HOLD, WineListStatusE.BG, parent_id]
    elif is_in_shared_pool:
        items_out = {
            'files': [],
            'place': None,
            'is_temp': False,
            'pid': parent_id,
        }

        sql = "SELECT wl.id as wl_id, wl.total_score_data, wl.status, wf.id as wf_id, wf.image_file FROM " \
              "    web_winelist wl INNER JOIN winelist_file wf ON wf.winelist_id = wl.id WHERE " \
              "    wl.is_archived=false AND wf.is_archived=false AND wl.status IN (%s, %s, %s) " \
              "    AND wl.is_in_shared_pool = true " \
              "    ORDER by wl.modified_time DESC"
        params = [WineListStatusE.OK, WineListStatusE.ON_HOLD,
                  WineListStatusE.BG]
    else:
        place = Place.active.get(id=parent_id)
        items_out = {
            'files': [],
            'place': place,
            'is_temp': False,
            'pid': parent_id,
        }

        sql = "SELECT wl.id as wl_id, wl.total_score_data, wl.status, wf.id as wf_id, wf.image_file FROM " \
              "    web_winelist wl INNER JOIN winelist_file wf ON wf.winelist_id = wl.id WHERE " \
              "    wl.is_archived=false AND wf.is_archived=false AND wl.status IN (%s, %s, %s) AND wl.place_id = %s " \
              "    ORDER by wl.modified_time DESC"
        params = [WineListStatusE.OK, WineListStatusE.ON_HOLD, WineListStatusE.BG, parent_id]

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        items = fetchalldict(cursor)
        for item in items:
            num_rows_yes = 0
            num_rows_no = 0
            num_rows_total = 0
            score_percent = 0.0

            if item['total_score_data']:
                try:
                    score = json.loads(item['total_score_data'])
                    num_rows_yes = int(score['num_rows_yes']) if 'num_rows_yes' in score else 0
                    num_rows_no = int(score['num_rows_no']) if 'num_rows_no' in score else 0
                    num_rows_total = int(score['num_rows_total']) if 'num_rows_total' in score else 0
                    score_percent = float(score['score_percent']) if 'score_percent' in score else 0.0
                except Exception:
                    pass

            file_url = aws_url(item['image_file'])

            item_out = {
                'id': item['wl_id'],
                'wf_id': item['wf_id'],
                'file_url': file_url,
                'wl_url': reverse('get_winelist_item_ajax', args=[item['wl_id']]),
                'name': os.path.basename(item['image_file']),
                'score_percent': score_percent,
                'num_rows_yes': num_rows_yes,
                'num_rows_no': num_rows_no,
                'num_rows_total': num_rows_total,
                'status': item['status'],
                'in_bg': True if item['status'] == WineListStatusE.BG else False,
            }
            items_out['files'].append(item_out)
    return items_out
