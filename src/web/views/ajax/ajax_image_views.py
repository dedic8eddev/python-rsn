from __future__ import absolute_import

import base64
import binascii
import io
import json
import logging
import mimetypes

import pyheif
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, reverse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image

from web.constants import PostTypeE
from web.forms.admin_forms import (AjaxDataFileUploadForm, AjaxFileDeleteForm,
                                   AjaxFileUploadForm, AjaxTempFileDeleteForm,
                                   AjaxTempFileRefreshForm,
                                   AjaxTempFileUploadForm,
                                   PlaceImageOrderingForm,
                                   RefreshVuforiaImageForm, SetAsVuforiaForm,
                                   WinemakerImageOrderingForm)
from web.models import (Place, PlaceImage, Post, PostFile, PostImage,
                        VuforiaImage, Wine, WineImage, Winemaker, WinemakerFile,
                        WinemakerImage)
from web.utils.filenames import get_extension
from web.utils.images import icon_manager_formats, image_formats
from web.utils.temp_images import (create_temp_directory_if_not_exists,
                                   delete_temp_image, get_current_images,
                                   get_current_temp_images, handle_temp_upload)
from web.utils.upload_tools import aws_url, get_file_from_url
from web.utils.views_common import (get_current_user,
                                    prevent_using_non_active_account)
from web.utils.vuforia import vuf_set_images_to_delete_for_wine
from web.utils.vuforia_models import create_from_b64_data, create_from_x_image

log = logging.getLogger(__name__)


# /ajax/image/vuforia/get/(?P<pid>[0-9]+)$
def get_vuforia_image(request, pid):
    img = VuforiaImage.objects.filter(id=pid).first()
    if not img:
        return HttpResponse()

    image_url = aws_url(img)
    msg = "AJAX - GET_VUFORIA_IMAGE - IMAGE URL: {} for image id: {} POST ID: {} WINE ID: %s"  # noqa
    log.debug(msg.format(image_url, pid, img.post_id, img.wine_id))
    content_type = mimetypes.guess_type(image_url)[0]

    data = get_file_from_url(image_url)
    return HttpResponse(data, content_type=content_type)


# -- UTILITY FUNCTIONS
def get_current_temp_images_with_ordering(request, dir_name, category_dir_name):
    create_temp_directory_if_not_exists(dir_name, category_dir_name)
    form1 = AjaxTempFileRefreshForm(request.POST)
    if form1.is_valid():
        cd = form1.cleaned_data
        temp_image_ordering = cd['temp_image_ordering']
    else:
        temp_image_ordering = None
    return get_current_temp_images(
        dir_name, category_dir_name, temp_image_ordering
    )


def decorate_other_files(files):
    for i, file in enumerate(files):
        ext = get_extension(file['url']).strip('.').lower()
        if ext in image_formats:
            files[i]['url_icon'] = file['url_thumb']
        elif ext in icon_manager_formats:
            files[i]['url_icon'] = '/static/assets/images/file-manager-icons/%s.png' % ext
        else:
            files[i]['url_icon'] = '/static/assets/images/file-manager-icons/_any_.png'
    return files


def reorder_images(ImageClass, parent_item_name, parent_item):
    if ImageClass.__name__ == 'PlaceImage' and parent_item.__class__.__name__ == 'Place':
        filter_criteria = {
            parent_item_name: parent_item,
            'image_area__isnull': True,
        }
    else:
        filter_criteria = {
            parent_item_name: parent_item,
        }

    images_x = ImageClass.active.filter(**filter_criteria).order_by('ordering')

    order_index = 0
    for image_x in images_x:
        image_x.ordering = order_index
        image_x.save()
        image_x.refresh_from_db()
        order_index += 1
    if ImageClass in (WineImage, PostImage, WinemakerImage, PlaceImage):
        # add to ordering info
        images = ImageClass.active.filter(**filter_criteria).order_by('ordering')
        if images:
            parent_item.main_image = images[0]
            parent_item.save()
        else:
            parent_item.main_image = None
            parent_item.save()


# -- VIEWS - current items
def current_images_view_common(request, parent_id, ParentItemClass, ImageClass, criteria_parent_name, c={},
                               tpl="base/elements/edit/general.current-images.html"):
    _ = get_current_user(request)
    c['images'] = get_current_images(parent_item_id=parent_id, ParentItemClass=ParentItemClass, ImageClass=ImageClass,
                                     criteria_parent_name=criteria_parent_name)
    return render(request, tpl, c)


def current_temp_images_view_common(request, dir_name, category_dir_name, c={},
                                    tpl="base/elements/edit/general.current-images.html"):
    _ = get_current_user(request)
    c['images'] = get_current_temp_images_with_ordering(request, dir_name, category_dir_name)
    return render(request, tpl, c)


def delete_image_view_common(request, ParentItemClass, ImageClass, criteria_parent_name, c={},
                             tpl="base/elements/edit/general.current-images.html"):
    _ = get_current_user(request)
    c['images'] = None
    form1 = AjaxFileDeleteForm(request.POST)
    if form1.is_valid():
        cd = form1.cleaned_data
        id = cd['id']
        image = ImageClass.active.get(id=id)
        image.archive()
        parent_item = getattr(image, criteria_parent_name)
        c['images'] = get_current_images(parent_item_id=parent_item.id, ParentItemClass=ParentItemClass,
                                         ImageClass=ImageClass, criteria_parent_name=criteria_parent_name)
        reorder_images(ImageClass, parent_item_name=criteria_parent_name, parent_item=parent_item)
    return render(request, tpl, c)


def delete_image_temp_view_common(request, dir_name, category_dir_name, c={},
                                  tpl="base/elements/edit/general.current-images.html"):
    _ = get_current_user(request)
    c['images'] = None
    form1 = AjaxTempFileDeleteForm(request.POST)
    if form1.is_valid():
        cd = form1.cleaned_data
        filename = cd['filename']
        temp_image_ordering = cd['temp_image_ordering']
        delete_temp_image(filename, dir_name, category_dir_name)
        c['images'] = get_current_temp_images(dir_name, category_dir_name, temp_image_ordering)
    return render(request, tpl, c)


def upload_image_view_common(request, ParentItemClass, ImageClass, parent_item_name, c={},
                             tpl="base/elements/edit/general.current-images.html"):
    user = get_current_user(request)
    form1 = AjaxFileUploadForm(request.POST, request.FILES)
    files = request.FILES.getlist('file')
    if form1.is_valid():
        cd = form1.cleaned_data
        parent_id = cd['parent_id']
        parent_item = ParentItemClass.active.get(id=parent_id)
        for file in files:
            if ImageClass.__name__ == 'PlaceImage':
                file._name = "{}---{}".format(parent_item.id, file._name)

            image = ImageClass(**{
                'author': user,
                parent_item_name: parent_item,
                'image_file': file,
                'real_name': file.name
            })
            image.save()
            image.refresh_from_db()
            parent_item.refresh_from_db()
        reorder_images(ImageClass, parent_item_name, parent_item)
    c['images'] = get_current_images(parent_item_id=parent_id, ParentItemClass=ParentItemClass, ImageClass=ImageClass,
                                     criteria_parent_name=parent_item_name)
    return render(request, tpl, c)


def upload_image_temp_view_common(
    request,
    category_dir_name,
    c={},
    tpl="base/elements/edit/general.current-images.html"
):
    _ = get_current_user(request)
    form1 = AjaxTempFileUploadForm(request.POST, request.FILES)
    files = request.FILES.getlist('file')
    dir_name = None
    if form1.is_valid():
        cd = form1.cleaned_data
        dir_name = cd['dir_name']
        for file in files:
            handle_temp_upload(file, dir_name, category_dir_name)
    c['images'] = get_current_temp_images(dir_name, category_dir_name)
    return render(request, tpl, c)


# --------------------------- image current images views - permanent images --------------------------------------
@csrf_exempt
@login_required
def current_wm_files(request, id):
    tpl = "base/elements/edit/general.current-other-files.html"
    _ = get_current_user(request)
    c = {}
    files = get_current_images(parent_item_id=id, ParentItemClass=Winemaker,
                               ImageClass=WinemakerFile, criteria_parent_name='winemaker')
    c['images'] = decorate_other_files(files)
    return render(request, tpl, c)


@csrf_exempt
@login_required
def current_winepost_files(request, id):
    tpl = "base/elements/edit/general.current-other-files.html"
    _ = get_current_user(request)
    c = {}
    files = get_current_images(parent_item_id=id, ParentItemClass=Post,
                               ImageClass=PostFile, criteria_parent_name='post')
    c['images'] = decorate_other_files(files)
    return render(request, tpl, c)


# ajax/images/winemaker/current/{id}
@csrf_exempt
@login_required
def current_images_winemaker(request, id):
    return current_images_view_common(request, parent_id=id, ParentItemClass=Winemaker, ImageClass=WinemakerImage,
                                      criteria_parent_name='winemaker')


# ajax/images/wine/current/{id}
@csrf_exempt
@login_required
def current_images_wine(request, id):
    return current_images_view_common(request, parent_id=id, ParentItemClass=Wine, ImageClass=WineImage,
                                      criteria_parent_name='wine')


# ajax/images/place/current/{id}
@csrf_exempt
@login_required
def current_images_place(request, id):
    return current_images_view_common(request, parent_id=id, ParentItemClass=Place, ImageClass=PlaceImage,
                                      criteria_parent_name='place')


# --------------------------- image current images views - temporary images --------------------------------------
# ajax/images/wm-other-files/temp/{id}
@csrf_exempt
@login_required
def current_temp_wm_files(request, id):
    tpl = "base/elements/edit/general.current-other-files.html"
    c = {}
    files = get_current_temp_images_with_ordering(request, dir_name=id, category_dir_name='wm-other-files')
    c['images'] = decorate_other_files(files)
    return render(request, tpl, c)


# ajax/images/winemaker/temp/{id}
@csrf_exempt
@login_required
def current_temp_images_winemaker(request, id):
    return current_temp_images_view_common(request, dir_name=id, category_dir_name='winemakers')


# ajax/images/wine/temp/{id}
@csrf_exempt
@login_required
def current_temp_images_wine(request, id):
    return current_temp_images_view_common(request, dir_name=id, category_dir_name='wines')


# ajax/images/place/temp/{id}
@csrf_exempt
@login_required
def current_temp_images_place(request, id):
    return current_temp_images_view_common(request, dir_name=id, category_dir_name='places')


# --------------------------- image delete views - permanent images ---------------------------------------------
def delete_other_file_view_common(request, ParentItemClass, ImageClass, criteria_parent_name,
                                  tpl="base/elements/edit/general.current-other-files.html"):
    _ = get_current_user(request)
    c = {'images': None}
    form1 = AjaxFileDeleteForm(request.POST)
    if form1.is_valid():
        cd = form1.cleaned_data
        id = cd['id']
        image = ImageClass.active.get(id=id)
        image.archive()
        parent_item = getattr(image, criteria_parent_name)
        files = get_current_images(parent_item_id=parent_item.id, ParentItemClass=ParentItemClass,
                                   ImageClass=ImageClass, criteria_parent_name=criteria_parent_name)
        c['images'] = decorate_other_files(files)
    return render(request, tpl, c)


def delete_other_file_temp_view_common(request, dir_name, category_dir_name, c={},
                                       tpl="base/elements/edit/general.current-other-files.html"):
    _ = get_current_user(request)
    c['images'] = None
    form1 = AjaxTempFileDeleteForm(request.POST)
    if form1.is_valid():
        cd = form1.cleaned_data
        filename = cd['filename']
        # temp_image_ordering = cd['temp_image_ordering']
        delete_temp_image(filename, dir_name, category_dir_name)
        files = get_current_temp_images(dir_name, category_dir_name)
        c['images'] = decorate_other_files(files)
    return render(request, tpl, c)


# /ajax/images/wm-other-files/delete/
@csrf_exempt
@login_required
def delete_wm_file(request):
    return delete_other_file_view_common(request, ParentItemClass=Winemaker, ImageClass=WinemakerFile,
                                         criteria_parent_name='winemaker')


# /ajax/images/winepost-other-files/delete/
@csrf_exempt
@login_required
def delete_winepost_file(request):
    return delete_other_file_view_common(request, ParentItemClass=Post, ImageClass=PostFile,
                                         criteria_parent_name='post')


# /ajax/images/winemaker/delete/
@csrf_exempt
@login_required
def delete_image_winemaker(request):
    return delete_image_view_common(request, ParentItemClass=Winemaker, ImageClass=WinemakerImage,
                                    criteria_parent_name='winemaker')


# /ajax/images/wine/delete/
@csrf_exempt
@login_required
def delete_image_wine(request):
    return delete_image_view_common(request, ParentItemClass=Wine, ImageClass=WineImage,
                                    criteria_parent_name='wine')


# /ajax/images/place/delete/
@csrf_exempt
@login_required
def delete_image_place(request):
    return delete_image_view_common(request, ParentItemClass=Place, ImageClass=PlaceImage,
                                    criteria_parent_name='place')


# --------------------------- image delete views - temporary images ---------------------------------------------
# /ajax/images/wm-other-files/temp/delete/{dir_name}/
@csrf_exempt
@login_required
def delete_wm_file_temp(request, dir_name):
    return delete_other_file_temp_view_common(request, dir_name, category_dir_name='wm-other-files')


# # /ajax/images/winemaker/temp/delete/{dir_name}/
@csrf_exempt
@login_required
def delete_image_winemaker_temp(request, dir_name):
    return delete_image_temp_view_common(request, dir_name=dir_name, category_dir_name='winemakers')


# /ajax/images/wine/temp/delete/{dir_name}/
@csrf_exempt
@login_required
def delete_image_wine_temp(request, dir_name):
    return delete_image_temp_view_common(request, dir_name=dir_name, category_dir_name='wines')


# /ajax/images/place/temp/delete/{dir_name}/s
@csrf_exempt
@login_required
def delete_image_place_temp(request, dir_name):
    return delete_image_temp_view_common(request, dir_name=dir_name, category_dir_name='places')


# --------------------------- image upload views - permanent images ---------------------------------------------


@csrf_exempt
@login_required
# /ajax/image/upload/winemaker/
def upload_wm_file(request):
    return upload_image_view_common(request, Winemaker, WinemakerFile, 'winemaker')


@csrf_exempt
@login_required
# /ajax/image/upload/winepost-other-files/
def upload_winepost_file(request):
    return upload_image_view_common(request, Post, PostFile, 'post')


@csrf_exempt
@login_required
# /ajax/image/upload/winemaker/
def image_upload_winemaker(request):
    return upload_image_view_common(request, Winemaker, WinemakerImage, 'winemaker')


@csrf_exempt
@login_required
# /ajax/image/upload/wine/
def image_upload_wine(request):
    return upload_image_view_common(request, Wine, WineImage, 'wine')


# /ajax/image/upload/place/
@csrf_exempt
@login_required
def image_upload_place(request):
    return upload_image_view_common(request, Place, PlaceImage, 'place')


# --------------------------- image upload views - temporary images ---------------------------------------------
@csrf_exempt
@login_required
# /ajax/image/upload/wm-other-files/temp/
def upload_wm_file_temp(request):
    return upload_image_temp_view_common(request, 'wm-other-files')


@csrf_exempt
@login_required
# /ajax/image/upload/winemaker/temp/
def image_upload_winemaker_temp(request):
    return upload_image_temp_view_common(request, 'winemakers')


@csrf_exempt
@login_required
# /ajax/image/upload/wine/temp/
def image_upload_wine_temp(request):
    return upload_image_temp_view_common(request, 'wines')


# /ajax/image/upload/place/temp/
@csrf_exempt
@login_required
def image_upload_place_temp(request):
    return upload_image_temp_view_common(request, 'places')


# --------------------------- image update ordering views - permanent images ----------------------------------------
def image_update_ordering_common(request, ParentItemClass, FormClass, ImageClass, parent_item_field):
    _ = get_current_user(request)
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            parent_item = ParentItemClass.active.get(id=cd['parent_item_id'])
            order_index = 0
            if cd['ids']:
                ids_array = cd['ids'].split(',')
                for id in ids_array:
                    image_item = ImageClass.active.get(**{'id': int(id), parent_item_field: parent_item})
                    image_item.ordering = order_index
                    image_item.save()
                    image_item.refresh_from_db()
                    if order_index == 0:
                        parent_item.main_image = image_item
                        parent_item.save()
                        parent_item.refresh_from_db()
                    order_index += 1
    result = {
        "status": "OK",
    }
    return JsonResponse(result)


# /ajax/image/ordering/place/update/
@csrf_exempt
@login_required
def image_update_ordering_place(request):
    return image_update_ordering_common(request, ParentItemClass=Place, FormClass=PlaceImageOrderingForm,
                                        ImageClass=PlaceImage, parent_item_field='place')


# /ajax/image/ordering/winemaker/update/
@csrf_exempt
@login_required
def image_update_ordering_winemaker(request):
    return image_update_ordering_common(request, ParentItemClass=Winemaker, FormClass=WinemakerImageOrderingForm,
                                        ImageClass=WinemakerImage, parent_item_field='winemaker')


@login_required
@csrf_exempt
def set_as_vuforia(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)
    ref_img = None
    url = ""
    if request.method == 'POST':
        form = SetAsVuforiaForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            winepost_id = cd['winepost_id']
            what = cd['what']
            winepost = Post.objects.get(id=winepost_id, type=PostTypeE.WINE)
            if what == 'primary':
                if winepost.wine.main_image:
                    ref_img = create_from_x_image(winepost.wine.main_image, winepost)
            elif what == 'secondary':
                if winepost.main_image:
                    ref_img = create_from_x_image(winepost.main_image, winepost)

            if ref_img:
                winepost.wine.ref_image = ref_img
                winepost.wine.save()
                winepost.wine.refresh_from_db()
                winepost.ref_image = ref_img
                winepost.save()
                winepost.refresh_from_db()

            winepost.refresh_from_db()
            winepost.wine.refresh_from_db()
            url = reverse('get_vuforia_image_ajax', kwargs={'pid': ref_img.id})

            resp = JsonResponse({
                'url': url,
                'status': 'OK'
            })
            return resp

    return JsonResponse({'url': "", 'status': 'ERROR'})


@login_required
@csrf_exempt
def refresh_vuforia_image(request):
    user = get_current_user(request)
    prevent_using_non_active_account(user)
    if request.method == 'POST':
        form = RefreshVuforiaImageForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            winepost_id = cd['winepost_id']
            winepost = Post.objects.get(id=winepost_id, type=PostTypeE.WINE)
            vuf_set_images_to_delete_for_wine(winepost.wine.id, winepost.id)
            if winepost.wine.ref_image:
                vuf_image = winepost.wine.ref_image
            elif winepost.ref_image:
                vuf_image = winepost.ref_image
            else:
                vuf_image = None
            if vuf_image:
                url = aws_url(vuf_image)
                vuf_image.is_dirty = True
                vuf_image.update_rating = True
                vuf_image.save()
                vuf_image.refresh_from_db()
                resp = JsonResponse({
                    'url': url,
                    'status': 'OK'})
                return resp
    return JsonResponse({'url': "", 'status': 'ERROR'})


@csrf_exempt
@login_required
# /ajax/image/upload/winepost-ref-image/   # upload after Pixie Editor "Save"
def upload_winepost_ref_image(request):
    ParentItemClass = Post
    user = get_current_user(request)
    image_url = None
    dest_file = None
    try:
        data_in_json = json.loads(request.body.decode('utf-8'))
        form1 = AjaxDataFileUploadForm(data=data_in_json)

        if form1.is_valid():
            cd = form1.cleaned_data
            parent_id = cd['parent_id']
            parent_item = ParentItemClass.objects.get(id=parent_id)
            image = create_from_b64_data(user, cd['data'], parent_item.wine, parent_item)
            # file_name = os.path.basename(str(image.image_file))
            parent_item.wine.ref_image = image
            parent_item.wine.save()
            parent_item.wine.refresh_from_db()
            parent_item.ref_image = image
            parent_item.save()
            parent_item.refresh_from_db()
            image_url = reverse(
                'get_vuforia_image_ajax', kwargs={'pid': image.id}
            )
            status = 'ok'
            dest_file = str(image.image_file)
        else:
            status = 'error'
    except ValueError:
        status = 'error'
    except binascii.Error:
        status = 'error'
    except Exception as e:
        print(e.args)
        status = 'error'

    return JsonResponse({'url': image_url, 'dest_file': dest_file, 'status': status})


@csrf_exempt
@login_required
def convert_heic(request):
    i = pyheif.read(request.FILES['file'])
    pi = Image.frombytes(
        mode=i.mode, size=i.size, data=i.data
    )

    output = io.BytesIO()
    pi.save(output, format="jpeg")
    output.seek(0)

    return JsonResponse({
        'result': "data:image/jpeg;base64," + base64.b64encode(
            output.getvalue()
        ).decode(),
    }, status=200)
