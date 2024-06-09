import logging
import os

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from web.forms.admin_forms import (AjaxFileIdForm, AjaxWinelistFileUploadForm,
                                   OCRIncludeForm)
from web.models import Place, WineList, WineListFile
from web.utils.ocr.scores import recalc_by_row_score
from web.utils.ocr_tools import (calc_place_total_score, get_current_files,
                                 update_place_score)
from web.utils.upload_tools import aws_url
from web.utils.views_common import get_current_user

log = logging.getLogger(__name__)


# /ajax/winelist/items
@csrf_exempt
@login_required
def get_winelist_items(request, pid):
    _ = get_current_user(request)
    tpl = 'ocr/place.winelists.html'
    c = {}
    items_out = get_current_files(parent_id=pid, is_temp=False)
    items_out['scores'] = {
        'last_wl_an_time': items_out['place'].last_wl_an_time,
        'total_wl_score': round(items_out['place'].total_wl_score, 2) if items_out['place'].total_wl_score else 0.0,
    }
    # items_out = calc_place_total_score(items_out)
    c['data'] = items_out
    return render(request, tpl, c)


# /ajax/right_panel/winelist/items
@login_required
def get_winelist_items_for_right_panel(request, pid):
    items_out = get_current_files(parent_id=pid, is_temp=False)
    items_out['scores'] = {
        'last_wl_an_time': items_out['place'].last_wl_an_time,
        'total_wl_score': round(
            items_out['place'].total_wl_score, 2
        ) if items_out['place'].total_wl_score else 0.0,
    }
    return JsonResponse(
        {
            'scores': items_out['scores'],
            'files': items_out['files']
        }
    )


# /ajax/winelist/temp/items - for TEMP winelists
@csrf_exempt
@login_required
def get_winelist_temp_items(request, pid):
    _ = get_current_user(request)
    tpl = 'ocr/place.winelists.html'
    c = {}
    items_out = get_current_files(parent_id=pid, is_temp=True)
    items_out = calc_place_total_score(items_out)
    c['data'] = items_out
    return render(request, tpl, c)


# /ajax/winelist/shared/items - for SHARED winelists
@csrf_exempt
@login_required
def get_winelist_shared_items(request):
    _ = get_current_user(request)
    tpl = 'ocr/place.winelists.html'
    c = {}
    items_out = get_current_files(is_in_shared_pool=True)
    c['data'] = items_out
    return render(request, tpl, c)


# /ajax/winelist/item - for PERMANENT winelists
@csrf_exempt
@login_required
def get_winelist_item(request, id):
    form = AjaxFileIdForm(request.POST)
    item_out = None
    if form.is_valid():
        cd = form.cleaned_data
        id = cd['id']
        wl = WineList.active.get(id=id)
        wfs = WineListFile.active.filter(winelist=wl)
        if wfs:
            wf = wfs[0]
            item_out = {
                'id': wl.id,
                'wf_id': wf.id,
                'file_url': aws_url(wf.image_file),
                # 'wl_url': reverse('get_winelist_item_ajax', args=[wl.id]),
                'name': os.path.basename(wf.image_file),
            }
    return JsonResponse({
        "data": item_out,
    })


# /ajax/winelist/item/update - both for TEMP and PERMANENT winelists (doesn't
# matter here)
@csrf_exempt
@login_required
def update_winelist_item(request):
    _ = get_current_user(request)
    tpl = 'ocr/place.winelists.update.html'
    c = {'all_scores': None, 'file': None, 'wl_id': None}

    if request.method == 'POST':
        form = OCRIncludeForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            wl = WineList.active.get(id=cd['id'])
            moderated_row_index = cd.get('moderated')
            sc = wl.total_score_data
            if sc:
                sc = recalc_by_row_score(sc, cd['incs'])
                if isinstance(moderated_row_index, int):  # update 'moderated'
                    # flag for single row in WineList.total_score_data
                    sc['rows_out'][moderated_row_index]['moderated'] = True
                wl.total_score_data = sc
                wl.save()
                wl.refresh_from_db()
                c['filename'] = sc['file']
                c['all_scores'] = [sc]
                c['wl_id'] = wl.id
    else:
        form = OCRIncludeForm(request.GET)

        id = request.GET.get('id', None)
        if not id:
            return render(request, tpl, c)
        wl = WineList.active.get(id=int(id))
        sc = wl.total_score_data
        c['filename'] = sc['file']
        c['all_scores'] = [sc]
        c['wl_id'] = wl.id
    return render(request, tpl, c)


# /ajax/winelist/item/upload/ - BOTH for TEMP and PERMANENT winelists (handled
# inside this function)
@csrf_exempt
@login_required
def upload_winelist_item(request):
    tpl = 'ocr/place.winelists.html'
    c = {'data': None}
    form1 = AjaxWinelistFileUploadForm(request.POST)

    if form1.is_valid():
        cd = form1.cleaned_data

        wl_file_id = cd['winelist_file_id']
        parent_id = cd.get('parent_id', None)
        is_temp = cd.get('is_temp', False)
        is_in_shared_pool = cd.get('is_in_shared_pool', False)
        wl_file = WineListFile.active.get(pk=wl_file_id)

        if is_temp:
            wl_file.winelist.temp_parent_id = parent_id
            wl_file.winelist.is_temp = True
        elif is_in_shared_pool:
            wl_file.winelist.is_in_shared_pool = True
        else:
            parent_item = wl_file.winelist.place = Place.active.get(
                id=parent_id)
            parent_item.wl_added = True
            parent_item.save()
            parent_item.refresh_from_db()

        wl_file.winelist.save()

        c['data'] = get_current_files(parent_id=parent_id, is_temp=is_temp,
                                      is_in_shared_pool=is_in_shared_pool)
        if is_temp:
            c['data'] = calc_place_total_score(c['data'])
        elif is_in_shared_pool:
            pass
        else:
            total_wl_score = round(c['data']['place'].total_wl_score, 2) if c['data']['place'].total_wl_score else 0.0
            c['data']['scores'] = {
                'last_wl_an_time': c['data']['place'].last_wl_an_time,
                'total_wl_score': total_wl_score,
            }
            log.info(f"NWLA results: {c['data']['scores']}")

    return render(request, tpl, c)


# /ajax/winelist/delete - BOTH for TEMP and PERMANENT winelists (handled inside this function)
@csrf_exempt
@login_required
def delete_winelist_item(request):
    _ = get_current_user(request)
    tpl = 'ocr/place.winelists.html'
    c = {'data': None}
    form1 = AjaxFileIdForm(request.POST)

    if form1.is_valid():
        cd = form1.cleaned_data
        id = cd['id']

        wl = WineList.active.get(id=id)
        wl.archive()
        if wl.place:
            place = wl.place
            ic = WineList.active.filter(place=place).count()
            if ic:
                place.wl_added = True
            else:
                place.wl_added = False
            place.save()
            place.refresh_from_db()
            c['data'] = get_current_files(parent_id=place.id)
            c['data']['scores'] = {
                'last_wl_an_time': c['data']['place'].last_wl_an_time,
                'total_wl_score': round(c['data']['place'].total_wl_score, 2) if c['data'][
                    'place'].total_wl_score else 0.0,
            }
        elif wl.is_temp and wl.temp_parent_id:
            c['data'] = get_current_files(parent_id=wl.temp_parent_id, is_temp=True)
            c['data'] = calc_place_total_score(c['data'])
    return render(request, tpl, c)


# /ajax/winelist/refresh_place_score/
@csrf_exempt
@login_required
def refresh_place_score(request, pid):
    _ = get_current_user(request)
    tpl = 'ocr/place.winelists.html'
    c = {}
    ret = update_place_score(pid)
    c['data'] = ret
    return render(request, tpl, c)
