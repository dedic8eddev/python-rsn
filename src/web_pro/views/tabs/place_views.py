from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from web.constants import PlaceImageAreaE
from web.models import Place, PlaceImage
from web_pro.utils.common import (get_user_venue, handle_provided_place_id,
                                  prepare_sidebar_data)
from web_pro.utils.establishment import PlaceOperator


# /pro/establishment
@login_required(login_url='pro_login')
def establishment(request, pid=None):
    res = handle_provided_place_id(request, pid)
    if res['redirect']:
        return res['redirect']

    sidebar_data = prepare_sidebar_data(request, 'establishment')
    sidebar_data['google_api_key'] = settings.GOOGLE_API_KEY

    place = Place.objects.get(pk=pid)
    sidebar_data[
        'establishmentUpdateText'
    ] = place.description if place.description else _(
        '🙋🏻 Please, complete this description to let users know what your venue is all about!'  # noqa
    )

    sidebar_data['establishment_description'] = place.description
    sidebar_data['establishment'] = {
        'lat': place.latitude,
        'lng': place.longitude,
        'pin_lat': place.pin_latitude,
        'pin_lng': place.pin_longitude,
    }
    sidebar_data['pid'] = pid
    sidebar_data['place_op'] = place.opening_hours if place.opening_hours else\
        place.get_default_opening_hours()
    return render(request, "admin/establishment.html", sidebar_data)


# /pro/establishment/hours
@csrf_exempt
def post_opening_hours(request):
    operator = PlaceOperator(request)
    hours, holidays, date_range = operator.update_place_hours()
    data = {
        'hours': hours,
        'holidays': holidays,
        'date_range': date_range
    }

    return JsonResponse(data)


# /pro/establishment/info
@login_required(login_url='pro_login')
def post_establishment_info(request):
    operator = PlaceOperator(request)
    if request.method == 'POST':
        operator.update_place_info()

    return JsonResponse({'result': 'done'})


# /pro/establishment/presentation
@login_required(login_url='pro_login')
def post_establishment_presentation(request, pid):
    if request.method == 'POST':
        place = get_user_venue(request.user.id, request)
        place.description = request.POST['presentation']
        place.save()

    return JsonResponse({})


# /pro/establishment/presentation
@login_required(login_url='pro_login')
def post_establishment_remove_logo(request, pid):
    operator = PlaceOperator(request)

    if request.method == 'POST':
        if request.POST['type'] == 'place':
            operator.remove_place_logo(and_save=True)
        elif request.POST['type'] == 'team':
            operator.remove_team_logo()

    return JsonResponse({})


@login_required(login_url='pro_login')
def post_establishment_update_logo(request, pid):
    operator = PlaceOperator(request)

    if request.method == 'POST':
        image = request.FILES.get('image', '')

        if request.POST['type'] == 'place':
            operator.update_place_logo(image)
        elif request.POST['type'] == 'team':
            operator.update_team_logo(image)

    return JsonResponse({})


# /pro/establishment/delete-img
@login_required(login_url='pro_login')
def post_establishment_delete_img(request, pid):
    if request.method == 'POST' and request.POST.get('image_path'):
        try:
            img = PlaceImage.active.filter(
                place_id=pid,
                image_file=request.POST.get('image_path')
            ).first()
        except PlaceImage.DoesNotExist:
            return JsonResponse({}, status=404)

        img.image_area = PlaceImageAreaE.ARCHIVED
        img.archive()

    return JsonResponse({})


# /pro/establishment/image
@login_required(login_url='pro_login')
def image_upload(request):
    operator = PlaceOperator(request)
    return JsonResponse(operator.update_place_images())
