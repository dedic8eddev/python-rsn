import datetime as dt
import json
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect

from web.constants import (PostTypeE, SpecialStatusE, WinemakerStatusE,
                           get_post_status_for_wine_status,
                           get_wine_status_for_winemaker_status)
from web.forms.admin_forms import AdminWinemakerForm
from web.models import (Post, Wine, WineImage, Winemaker, WinemakerFile,
                        WinemakerImage)
from web.helpers.winemakers import WinemakerHelper
from web.utils.geoloc import set_address_data_from_cd
from web.utils.mentions import strip_description_update_user_mentions_indexes
from web.utils.temp_images import (create_temp_directory_if_not_exists,
                                   move_uploaded_temp_files)
from web.utils.views_common import is_privileged_account
from web.views.admin.common import get_c, get_winemakers_number


def add_wines_for_winemaker(winemaker, form, c):
    wine_status = get_wine_status_for_winemaker_status(winemaker.status)
    post_status = get_post_status_for_wine_status(wine_status)
    wine_model_items = form.wines_coll.items_as_model_entities(
        ModelClass=Wine, user=c['current_user'],
        defaults={'status': wine_status,
                  'winemaker': winemaker},
        fields_extra_data=['year', 'ordering'])

    w_items = form.wines_coll.items()
    for i, model_item_row in enumerate(wine_model_items):
        model_item = model_item_row['model_item']
        extra_data = model_item_row['extra_data']
        if not model_item.name \
                and not model_item.designation \
                and not model_item.grape_variety \
                and not model_item.year:
            continue
        if model_item.id:
            model_item.save()
            model_item.refresh_from_db()
        else:
            model_item.winemaker = winemaker
            model_item.domain = winemaker.domain
            model_item.region = winemaker.region

            model_item.author = c['current_user']
            model_item.id = None
            model_item.save()
            model_item.refresh_from_db()

            item_post = Post(
                author=c['current_user'],
                wine=model_item,
                title=model_item.name,
                wine_year=extra_data['year'],
                is_parent_post=True,
                grape_variety=model_item.grape_variety,
                type=PostTypeE.WINE,
                status=post_status
            )

            item_post.save()
            item_post.push_to_timeline(
                is_new=True, is_sticky=is_privileged_account(c['current_user'])
            )
            item_post.refresh_from_db()
            w_item = w_items[i]
            temp_dir_wine = w_item['value'][7]
            temp_image_ordering = w_item['value'][8]
            move_uploaded_temp_files(dir_name=temp_dir_wine,
                                     category_dir_name='wines',
                                     user=c['current_user'],
                                     ImageClass=WineImage,
                                     parent_item=model_item,
                                     parent_item_field_name='wine',
                                     temp_image_ordering=temp_image_ordering)
        images = WineImage.active.filter(wine=model_item).order_by('ordering')
        if images:
            model_item.main_image = images[0]
            model_item.save()
            model_item.refresh_from_db()
    form.wines_coll.clear_items()


# # /naturals
# @login_required
# def naturals(request):
#     c = get_c(request=request, active='list_wm_naturals', path='/naturals', add_new_url='add_winemaker_natural')
#     c['wm_type'] = WinemakerTypeE.NATURAL
#     c['ajax_list_url'] = 'get_winemaker_items_naturals_ajax'
#     c['add_wm_url'] = "add_winemaker_natural"
#     return render(request, "lists/winemakers.html", c)
#
#
# # /others
# @login_required
# def others(request):
#     c = get_c(request=request, active='list_wm_others', path='/others', add_new_url='add_winemaker_other')
#     c['wm_type'] = WinemakerTypeE.OTHER
#     c['ajax_list_url'] = 'get_winemaker_items_others_ajax'
#     c['add_wm_url'] = "add_winemaker_other"
#     return render(request, "lists/winemakers.html", c)


# /winemakers
@login_required
def winemakers(request):
    c = get_c(request=request, active='list_wm_all', path='/winemakers', add_new_url='add_winemaker')
    c['ajax_list_url'] = 'get_winemaker_items_all_ajax'
    c['add_wm_url'] = "add_winemaker"
    c['total'], c['naturals'], c['others'] = get_winemakers_number(Q())
    return render(request, "lists/winemakers.html", c)


# /winemaker/add
@login_required
@csrf_protect
def add_winemaker_common(request):
    # active_list = "list_wm_naturals" if wm_type == WinemakerTypeE.NATURAL else "list_wm_others"
    # add_wm = "add_winemaker_natural" if wm_type == WinemakerTypeE.NATURAL else "add_winemaker_other"
    active_list = 'list_wm_all'
    add_wm = 'add_winemaker'

    bc_path = [
        ('/', 'Home'),
        (reverse(active_list), 'Winemakers'),
        (reverse(add_wm), 'add')
    ]
    print('BC_PATH: ', bc_path)
    c = get_c(request=request, active=active_list, path=None, bc_path_alt=bc_path)
    print('BC_PATH AFTER: ', c['bc_path'])
    winemaker = Winemaker(
        author=c['current_user'],
        status=WinemakerStatusE.VALIDATED
    )

    if request.method == 'POST':
        c["is_just_open"] = False

        form = AdminWinemakerForm(request.POST, instance=winemaker)

        if form.is_valid():
            cd = form.cleaned_data
            winemaker.author = c['current_user']

            # this is adding of a new winemaker, so if it has status "VALIDATED", we can set "validated_xxxx" fields
            # without any hesitation
            if cd['status'] == WinemakerStatusE.VALIDATED:
                winemaker.validated_by = request.user
                winemaker.validated_at = dt.datetime.now()

            set_address_data_from_cd(cd, winemaker)
            # if str(cd['latitude']) and str(cd['longitude']) and \
            #         (not cd['country_iso_code'] or cd['country_iso_code'] != 'JP'):
            #     address_data_latlng = get_address_data_for_latlng(cd['latitude'], cd['longitude'])
            #     if address_data_latlng['country']:
            #         winemaker.country = address_data_latlng['country']
            #     if address_data_latlng['iso']:
            #         winemaker.country_iso_code = address_data_latlng['iso']
            #     if address_data_latlng['city'] and address_data_latlng['quality'] < 3:
            #         winemaker.city = address_data_latlng['city']
            #     if address_data_latlng['state'] and address_data_latlng['quality'] < 3:
            #         winemaker.state = address_data_latlng['state']
            # elif cd['country_iso_code'] and cd['country_iso_code'] == 'JP':
            #     winemaker.country_iso_code = cd['country_iso_code']

            try:
                winemaker.domain_description_translations = json.loads(cd['current_translations'])
            except ValueError:
                pass

            winemaker.save()
            winemaker.refresh_from_db()

            move_uploaded_temp_files(dir_name=cd['images_temp_dir_wm'], category_dir_name='winemakers',
                                     user=c['current_user'], ImageClass=WinemakerImage, parent_item=winemaker,
                                     parent_item_field_name='winemaker', temp_image_ordering=cd['image_ordering'])

            move_uploaded_temp_files(dir_name=cd['images_temp_dir_wm'], category_dir_name='wm-other-files',
                                     user=c['current_user'], ImageClass=WinemakerFile, parent_item=winemaker,
                                     parent_item_field_name='winemaker', temp_image_ordering=cd['image_ordering'])

            images = WinemakerImage.active.filter(winemaker=winemaker).order_by('ordering')
            if images:
                winemaker.main_image = images[0]
                winemaker.save()
                winemaker.refresh_from_db()

            add_wines_for_winemaker(winemaker, form, c)
            c["is_just_open"] = True

            return redirect('edit_winemaker', winemaker.id)
    else:
        form = AdminWinemakerForm(instance=winemaker)
        dir_name = str(uuid.uuid4())
        form.fields["images_temp_dir_wm"].initial = dir_name
        create_temp_directory_if_not_exists(dir_name, 'winemakers')
        c["is_just_open"] = True

    c["form"] = form
    c["google_api_key"] = settings.GOOGLE_API_KEY
    c["winemaker"] = winemaker
    c["action_url"] = reverse(add_wm)
    c["is_new"] = True
    c['add_wm_url'] = add_wm

    c["pdg_title"] = "[New winemaker]"

    # opts_in = WinemakerStatusE.names
    c["pdg_options"] = WinemakerHelper.get_pdg_options()

    return render(request, "edit/winemaker.html", c)


def add_winemaker(request):
    return add_winemaker_common(request)


# def add_winemaker_natural(request):
#     return add_winemaker_common(request, WinemakerTypeE.NATURAL)
#
#
# def add_winemaker_other(request):
#     return add_winemaker_common(request, WinemakerTypeE.OTHER)


# /winemaker/edit/{id}
@login_required
def edit_winemaker(request, id):
    winemaker = Winemaker.objects.get(id=id)
    # active_list = "list_wm_naturals" if winemaker.get_is_natural() else "list_wm_others"
    # add_wm = "add_winemaker_natural" if winemaker.get_is_natural() else "add_winemaker_other"
    active_list = 'list_wm_all'
    add_wm = 'add_winemaker'
    old_status = winemaker.status
    bc_path = [
        ('/', 'Home'),
        (reverse(active_list), 'Winemakers'),
        (reverse('edit_winemaker', args=[id]), winemaker.name)
    ]

    c = get_c(request=request, active=active_list, path=None, bc_path_alt=bc_path)

    if request.method == 'POST':
        c["is_just_open"] = False
        form = AdminWinemakerForm(request.POST, instance=winemaker)
        if form.is_valid():
            cd = form.cleaned_data
            # active_list = "list_wm_naturals" if winemaker.get_is_natural() else "list_wm_others"
            # add_wm = "add_winemaker_natural" if winemaker.get_is_natural() else "add_winemaker_other"
            active_list = 'list_wm_all'
            add_wm = 'add_winemaker'
            bc_path = [
                ('/', 'Home'),
                (reverse(active_list), 'Winemakers'),
                (reverse('edit_winemaker', args=[id]), winemaker.name)
            ]
            c = get_c(request=request, active=active_list, path=None, bc_path_alt=bc_path, old_c=c)

            cd['user_mentions'] = winemaker.user_mentions
            cd = strip_description_update_user_mentions_indexes(cd, mentions_field='user_mentions')
            if cd['status'] == SpecialStatusE.DELETE:
                winemaker.archive(modifier_user=request.user)
                return redirect(active_list)
            elif cd['status'] == SpecialStatusE.DUPLICATE:
                new_winemaker = winemaker.duplicate()
                return redirect("edit_winemaker", **{'id': new_winemaker.id})
            else:
                winemaker.last_modifier = c['current_user']
                winemaker.modified_time = dt.datetime.now()
                set_address_data_from_cd(cd, winemaker)

                if cd['status'] == WinemakerStatusE.VALIDATED and old_status != WinemakerStatusE.VALIDATED and \
                        not winemaker.validated_at and not winemaker.validated_by:
                    winemaker.validated_by = request.user
                    winemaker.validated_at = dt.datetime.now()
                elif cd['status'] == WinemakerStatusE.REFUSED and winemaker.status != WinemakerStatusE.REFUSED:
                    winemaker.refuse(modifier_user=request.user)
                    winemaker.refresh_from_db()
                elif cd['status'] == WinemakerStatusE.TO_INVESTIGATE:
                    winemaker.set_to_investigate(modifier_user=request.user)
                winemaker.status = cd['status']
                try:
                    winemaker.domain_description_translations = json.loads(cd['current_translations'])
                except ValueError:
                    pass

                winemaker.save()
                winemaker.refresh_from_db()

                wines = Wine.active.filter(winemaker=winemaker)
                if wines:
                    for wine in wines:
                        wine.domain = winemaker.domain
                        wine.save()
                        wine.refresh_from_db()

                images = WinemakerImage.active.filter(winemaker=winemaker).order_by('ordering')
                if images:
                    winemaker.main_image = images[0]
                    winemaker.save()
                    winemaker.refresh_from_db()

                add_wines_for_winemaker(winemaker, form, c)
                c["is_just_open"] = True

                wines = Wine.active.filter(winemaker=winemaker)
                if wines:
                    for wine in wines:
                        wine.region = winemaker.region
                        wine.save()
                        wine.refresh_from_db()

            winemaker.refresh_from_db()
            form = AdminWinemakerForm(instance=winemaker)
    else:
        form = AdminWinemakerForm(instance=winemaker)
        c["is_just_open"] = True

    c["google_api_key"] = settings.GOOGLE_API_KEY

    c["form"] = form
    c["winemaker"] = winemaker
    c["action_url"] = reverse('edit_winemaker', args=[id])
    c["is_new"] = False

    if winemaker.last_modifier:
        c["saved_by"] = winemaker.last_modifier
        c["saved_at"] = winemaker.modified_time
    else:
        c["saved_by"] = winemaker.author
        c["saved_at"] = winemaker.created_time

    c["pdg_title"] = winemaker.name
    c["pdg_author"] = winemaker.author
    c["pdg_created_at"] = winemaker.created_time
    c["pdg_validated_at"] = winemaker.validated_at
    c["pdg_validated_by"] = winemaker.validated_by
    c['add_wm_url'] = add_wm

    # opts_in = WinemakerStatusE.names
    c["pdg_options"] = WinemakerHelper.get_pdg_options()

    return render(request, "edit/winemaker.html", c)
