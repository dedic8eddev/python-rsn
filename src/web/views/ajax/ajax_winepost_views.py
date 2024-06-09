from __future__ import absolute_import

import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from web.constants import PostTypeE, UserStatusE, UserTypeE, WineStatusE
from web.forms.admin_forms import (ChangeParentPostForm, DeleteYearlyDataForm,
                                   FetchYearlyDataForm, UpdateYearlyDataForm)
from web.models import Place, Post, UserProfile, Wine
from web.utils.autocomplete_common import autocomplete_common_ajax
from web.utils.common_winepost import define_as_children_obj
from web.utils.views_common import (get_current_user,
                                    prevent_using_non_active_account)
from web.utils.yearly_data import (delete_yearly_data_with_parent_post,
                                   get_yearly_data_for_winepost,
                                   update_yearly_data_with_parent_post)

log = logging.getLogger(__name__)


# /ajax/winepost/fetch-yearly-data
@login_required
@csrf_exempt
def fetch_yearly_data(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form = FetchYearlyDataForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            winepost_id = cd['winepost_id']
            try:
                winepost = Post.active.get(id=winepost_id, type=PostTypeE.WINE)
            except Post.DoesNotExist:
                return JsonResponse({})
            yd = {}
            if winepost.is_parent_post:
                yd = get_yearly_data_for_winepost(winepost)
            else:
                pposts = Post.objects.filter(
                    wine=winepost.wine, is_parent_post=True
                )
                if pposts:
                    yd = get_yearly_data_for_winepost(pposts[0])
            return JsonResponse(yd)
    return JsonResponse({})


# /ajax/winepost/update-yearly-data
@login_required
@csrf_exempt
def update_yearly_data(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form = UpdateYearlyDataForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            cur_year = str(cd['cur_year'])
            winepost_id = cd['winepost_id']
            winepost = Post.active.get(id=winepost_id, type=PostTypeE.WINE)
            data_cur_year = {
                'free_so2': cd['cur_free_so2'] if cd['cur_free_so2'] else None,
                'total_so2': cd['cur_total_so2'] if cd['cur_total_so2'] else None,  # noqa
                'grape_variety': cd['cur_grape_variety'],
            }

            action = update_yearly_data_with_parent_post(
                winepost, cur_year, data_cur_year
            )
            winepost.refresh_from_db()

            resp = JsonResponse({
                'yearly_data': get_yearly_data_for_winepost(winepost),
                'action': action
            })
            return resp

    return JsonResponse({'yearly_data': [], 'action': 'ERROR'})


# /ajax/winepost/delete-yearly-data
@login_required
@csrf_exempt
def delete_yearly_data(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)
    if request.method == 'POST':
        form = DeleteYearlyDataForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            year = str(cd['year'])
            winepost_id = cd['winepost_id']
            winepost = Post.active.get(id=winepost_id, type=PostTypeE.WINE)
            action = delete_yearly_data_with_parent_post(winepost, year)
            winepost.refresh_from_db()
            resp = JsonResponse({
                'yearly_data': get_yearly_data_for_winepost(winepost),
                'action': action})
            return resp

    return JsonResponse({'yearly_data': [], 'action': 'ERROR'})


# DEFINE AS CHILDREN - old name was "change_parent_post"
@login_required
@csrf_exempt
def define_as_children(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)
    if request.method == 'POST':
        form = ChangeParentPostForm(request.POST)
    elif request.method == 'GET':
        # noqa eg. http://localhost:8000/ajax/autocomplete/winemaker/?min_letters=2&query=Bre
        form = ChangeParentPostForm(request.GET)

    if form.is_valid():
        cd = form.cleaned_data
        # the winepost to be moved
        winepost_id = cd['winepost_id']
        winepost = Post.objects.get(id=winepost_id, type=PostTypeE.WINE)
        new_parent_post_id = cd['new_parent_post_id']
        define_as_children_obj(winepost, new_parent_post_id, user)
        result = {
            'status': 'OK',
            'new_parent_post_id': new_parent_post_id
        }
        return JsonResponse(result)


# /ajax/autocomplete/domain
@login_required
def autocomplete_domain(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)
    return JsonResponse(
        autocomplete_common_ajax(
            request=request, EntityClass=Wine, entity_field="domain",
            extra_filter_criteria={'status__in': [WineStatusE.VALIDATED]}
        )
    )


# /ajax/autocomplete/wine
@login_required
def autocomplete_wine(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)
    return JsonResponse(
        autocomplete_common_ajax(
            request=request, EntityClass=Wine, entity_field="name",
            extra_filter_criteria={'status__in': [WineStatusE.VALIDATED]}
        )
    )


# /ajax/autocomplete/place
@login_required
def autocomplete_place(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)
    result = autocomplete_common_ajax(
        request=request, EntityClass=Place, entity_field="name"
    )
    if result['items']:
        for item in result['items']:
            item['edit_url'] = reverse('edit_place', args=[item['id']])
    return JsonResponse(result)


# /ajax/autocomplete/username
@login_required
def autocomplete_username(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)
    return JsonResponse(
        autocomplete_common_ajax(
            request=request, EntityClass=UserProfile, entity_field="username",
            extra_filter_criteria={
                'type': UserTypeE.USER,
                'status__in': [UserStatusE.ACTIVE, UserStatusE.INACTIVE]
            }
        )
    )
