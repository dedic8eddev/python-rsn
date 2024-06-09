from __future__ import absolute_import

import logging

from django.db.models import Case, Count, IntegerField, Q, When
from django.http import JsonResponse
from django.utils.translation import ugettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response

from web.constants import WinemakerStatusE, WineStatusE, PostStatusE, PostTypeE
from web.forms.api_forms import WinemakerItemsForm
from web.models import Winemaker, WinemakerImage
from web.serializers.comments_likes import ImageSerializer
from web.serializers.posts import FullWineSerializer
from web.serializers.winemakers import (LongWinemakerSerializerLegacy,
                                        WinemakerSerializer,
                                        WinemakerProfileSerializer)
from web.utils.api_handling import signed_api, fill_default_response_data
from web.utils.exceptions import ResultEmpty, WrongParametersError
from web.utils.views_common import (list_control_parameters_by_form,
                                    list_last_id,
                                    prevent_using_non_active_account)

log = logging.getLogger(__name__)


# /api/winemaker/items
@signed_api(
    FormClass=WinemakerItemsForm, token_check=True, log_response_data=False
)
def get_winemaker_items(request):
    user = request.user
    prevent_using_non_active_account(user)
    items_dict = {}
    items = []
    query_string = None

    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data
            if cd['query']:
                query_string = cd['query']
            (
                limit, order_dir, last_id, order_by
            ) = list_control_parameters_by_form(cd)
        else:
            raise WrongParametersError(_("Wrong parameters."), form)

        query = Winemaker.active.annotate(
            validated_wines=Count(Case(
                When(wines__status=WineStatusE.VALIDATED, then=1),
                output_field=IntegerField(),
            ))
        )

        if query_string:
            query_string = query_string.strip()
            query_string = query_string.strip("%")

            query = query.filter(
                Q(
                    status=WinemakerStatusE.VALIDATED,
                    validated_wines__gt=0,
                    wines__posts__status=PostStatusE.PUBLISHED,
                    wines__posts__type=PostTypeE.WINE
                ) &
                Q(
                    Q(name__unaccent__icontains=query_string) |
                    Q(domain__unaccent__icontains=query_string)
                )
            )

        else:
            query = query.filter(
                status=WinemakerStatusE.VALIDATED,
                validated_wines__gt=0,
                wines__posts__status=PostStatusE.PUBLISHED,
                wines__posts__type=PostTypeE.WINE
            )

        query = query.distinct().order_by('name')

        if not query.count():
            raise ResultEmpty

        items_dict = WinemakerSerializer(
            query, many=True, context={'request': request}
        ).data

    return {
        'items': items_dict,
        'last_id': list_last_id(items)
    }


# /api/winemaker/profile
class WinemakerProfileView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        query_serializer=WinemakerProfileSerializer,
        operation_summary='Return information about winemaker by '
                          'winemaker_id.',
        operation_description='Return information about winemaker by '
                              'winemaker_id + the list of parent wineposts.',
        security=[]
    )
    def get(self, request, format=None):
        serializer = WinemakerProfileSerializer(data=request.query_params)

        if serializer.is_valid():
            validated_data = serializer.validated_data
            try:
                winemaker = Winemaker.active.get(
                    id=validated_data.get('winemaker_id')
                )
            except Winemaker.DoesNotExist:
                return JsonResponse(
                    {"exception":
                        _("This winemaker does not exist or has been "
                          "deleted.")},
                    status=404, safe=False
                )

            if winemaker.main_image:
                images = WinemakerImage.active.filter(
                    winemaker=winemaker
                ).exclude(id=winemaker.main_image.id).order_by('ordering')
            else:
                images = WinemakerImage.active.filter(
                    winemaker=winemaker
                ).order_by('ordering')

            images_out = ImageSerializer(images, many=True).data

            wines_accepted = winemaker.wines.filter(
                is_archived=False,
                status=WineStatusE.VALIDATED
            ).annotate(
                Count('posts')
            ).filter(
                posts__count__gt=0
            ).order_by('name')

            wines_out = FullWineSerializer(
                wines_accepted, many=True, context={
                    'request': request,
                    'fallback_parent_post_image': True,
                    'fallback_child_post_image': True,
                }
            ).data

            wine_last_id = list_last_id(wines_accepted)
            wm = LongWinemakerSerializerLegacy(winemaker).data

            data = {
                'winemaker': wm,
                'wine_last_id': wine_last_id,
                'wines': wines_out,
                'images': images_out,
                'domain_description_translations': winemaker.get_translations(),  # noqa
            }
            response_data = {'data': data}
            fill_default_response_data(response_data)
            return Response(response_data)

    @swagger_auto_schema(
        request_body=WinemakerProfileSerializer,
        operation_summary='Return information about winemaker by winmaker_id.',
        operation_description='The method POST is deprecated for this '
                              'endpoint.',
        deprecated=True,
        security=[]
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '/api/winemaker/profile')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)
