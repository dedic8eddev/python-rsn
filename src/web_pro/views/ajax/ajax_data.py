from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from web_pro.utils.establishment import PlaceDataOperator


# /pro/ajax/establishment/opening-hours/
@login_required
def get_opening_hours_and_holidays(request):
    operator = PlaceDataOperator(request)
    if request.method == 'GET':
        return JsonResponse(operator.get_place_opening_hours_and_holidays())


# /pro/ajax/establishment/data/
@login_required
def get_establishment_data(request):
    operator = PlaceDataOperator(request)
    if request.method == 'GET':
        return JsonResponse(operator.get_place_data())


# /pro/ajax/establishment/get_images/
@login_required
def get_establishment_images(request):
    operator = PlaceDataOperator(request)
    if request.method == 'POST':
        return JsonResponse(operator.get_place_images())
