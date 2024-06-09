import datetime as dt
import logging
import re

from django.core.files.storage import default_storage

from web.constants import WineListStatusE
from web.models import Place, WineList, WineListFile
from web.utils.ocr.db import (fetch_validated_winemakers,
                              fetch_validated_wines_with_wms, get_current_files)
from web.utils.ocr.scores import get_by_row_score
from web.utils.ocr.text_reader import get_text_rows_from_ocr

log = logging.getLogger(__name__)
log_cmd = logging.getLogger("command")


def calc_place_total_score(items_out):
    total_score = 0.0
    total_num_rows_yes = 0
    total_num_rows_total = 0
    num_files = 0
    if items_out['files']:
        for file in items_out['files']:
            if file['status'] == WineListStatusE.BG:
                continue
            num_rows_yes = int(file['num_rows_yes'])
            num_rows_total = int(file['num_rows_total'])
            total_num_rows_yes += num_rows_yes
            total_num_rows_total += num_rows_total
            num_files += 1
            wl_obj = WineList.objects.get(pk=file['id'])
            wl_obj.status = WineListStatusE.OK
            wl_obj.save()
    if num_files and total_num_rows_total != 0:
        total_score = total_num_rows_yes / total_num_rows_total
    last_wl_an_time = dt.datetime.now()
    total_wl_score = total_score * 100

    items_out['scores'] = {
        'last_wl_an_time': last_wl_an_time,
        'total_wl_score': round(total_wl_score, 2) if total_wl_score else 0.0,
    }
    return items_out


def update_place_score(place_id):
    items_out = get_current_files(parent_id=place_id, is_temp=False)
    items_out = calc_place_total_score(items_out)

    place = Place.active.get(id=place_id)
    place.last_wl_an_time = items_out['scores']['last_wl_an_time']
    place.total_wl_score = items_out['scores']['total_wl_score']
    place.modified_at = dt.datetime.now()
    place.wl_added = True if items_out['files'] else False
    place.save()
    place.refresh_from_db()

    items_out = get_current_files(parent_id=place_id)
    c = {
        'items_out': items_out,
        'scores': {
            'last_wl_an_time': place.last_wl_an_time,
            'total_wl_score': round(
                place.total_wl_score, 2
            ) if place.total_wl_score else 0.0,
        }
    }
    return c


def get_text_rows(file):
    t_rows = get_text_rows_from_ocr(file)
    # cleanup text_rows
    single_letters = re.compile('^[^ \t\n\r\f\v]$')
    digits_only = re.compile('^([.\-\s\d]+)$')  # noqa
    text_rows = []
    for ro in t_rows:
        if ro == "" or single_letters.match(ro) or digits_only.match(ro):
            pass
        else:
            # leading and trailing digits
            ro = re.sub(r'^\b\d+[,/.]?\d+\b', '', ro)
            ro = re.sub(r'\b\d+[,/.]?\d+\b$', '', ro)
            # extra whitespaces
            ro = re.sub(r'\s+', ' ', ro)  # compress all whitespaces
            ro = re.sub(r'^\s+', '', ro)  # remove leading whitespaces
            ro = re.sub(r'\s+$', '', ro)  # remove trailing whitespaces

            text_rows.append(ro)
    return text_rows


def get_score(
    text_rows, winemakers=None, wines=None, wines_by_wm=None,
        moderated_indexes=None, new_exclusion_word_row=None
):
    winemakers = fetch_validated_winemakers() if not winemakers else winemakers
    wines = fetch_validated_wines_with_wms()['items'] if not wines else wines
    wines_by_wm = fetch_validated_wines_with_wms()[
        'items_by_wm'
    ] if not wines_by_wm else wines_by_wm
    by_row_score = get_by_row_score(
        winemakers_by_status=winemakers,
        wines=wines, wines_by_wm=wines_by_wm,
        text_rows=text_rows,
        moderated_indexes=moderated_indexes,
        new_exclusion_word_row=new_exclusion_word_row
    )

    return by_row_score


def move_uploaded_temp_winelists(temp_parent_id, dst_parent_id):
    wls = WineList.active.filter(temp_parent_id=temp_parent_id, is_temp=True)
    if wls:
        for wl in wls:
            wl.place_id = dst_parent_id
            wl.temp_parent_id = None
            wl.is_temp = False
            wl.save()
            wl.refresh_from_db()

            wl_files = WineListFile.active.filter(winelist=wl)
            for wl_file in wl_files:
                file_name = wl_file.image_file.name
                new_file_name = file_name.replace(
                    'temp/{}'.format(temp_parent_id), str(dst_parent_id)
                )
                wl_file.image_file.name = new_file_name
                wl_file.save()

                default_storage.delete(file_name)

    update_place_score(dst_parent_id)


def duplicate_wls_for_place(src_place, dst_place):
    wls = WineList.objects.filter(place=src_place)
    if wls:
        for wl in wls:
            duplicate_wl(src_wl=wl, dst_place=dst_place)

    update_place_score(dst_place.id)


def duplicate_wl(src_wl, dst_place):
    dst_wl = WineList(
        place=dst_place,
        status=src_wl.status,
        is_archived=src_wl.is_archived,
        total_score_data=src_wl.total_score_data,
        is_temp=src_wl.is_temp,
        temp_parent_id=src_wl.temp_parent_id
    )
    dst_wl.save()
    dst_wl.refresh_from_db()

    wfs = WineListFile.objects.filter(winelist=src_wl)
    for wf in wfs:
        duplicate_wf(src_wf=wf, src_wl=src_wl, dst_wl=dst_wl)

    return dst_wl


def duplicate_wf(src_wf, src_wl, dst_wl):
    image_file = src_wf.image_file
    new_file_name = image_file.name.replace(
        str(src_wl.place.id), str(dst_wl.place.id)
    )
    image_file.name = new_file_name

    dst_wf = WineListFile(
        winelist=dst_wl,
        author=src_wf.author,
        created_time=dt.datetime.now(),
        modified_time=dt.datetime.now(),
        is_archived=src_wf.is_archived,
        ordering=src_wf.ordering,
        width=src_wf.width,
        height=src_wf.height,
        image_file=image_file,
        item_text_rows=src_wf.item_text_rows
    )
    dst_wf.save()
    dst_wf.refresh_from_db()
