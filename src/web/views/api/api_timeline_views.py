from __future__ import absolute_import

import logging

from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from reports.models import BlockUser
from web.authentication import CustomTokenAuthentication
from web.constants import PostStatusE, PostTypeE, UserStatusE, UserTypeE
from web.forms.api_forms import TimeLineItemsForm, TimeLineOneItemForm
from web.models import Post, TimeLineItem, Wine
from web.serializers.common import RaisinListSerializer
from web.serializers.timeline import TimeLineItemSerializer
from web.utils.api_handling import signed_api, fill_default_response_data
from web.utils.exceptions import ResultEmpty, WrongParametersError
from web.utils.model_tools import get_filter_criteria_for_order_last_id
from web.utils.views_common import (list_control_parameters_by_form,
                                    prevent_using_non_active_account)

log = logging.getLogger(__name__)


# /api/timeline/items
class TimelineItemsView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CustomTokenAuthentication]

    @swagger_auto_schema(
        query_serializer=RaisinListSerializer,
        operation_summary='Return timeline items.',
        operation_description='Return timeline items.',
        security=[]
    )
    def get(self, request, format=None):
        filter_criteria = {}
        last_id = None
        limit = 10
        order_by = '-id'
        order_dir = 'desc'
        serializer = RaisinListSerializer(data=request.query_params)
        if serializer.is_valid(raise_exception=True):
            validated_data = serializer.validated_data
            (limit, order_dir, last_id,
             order_by_old) = list_control_parameters_by_form(validated_data)

        filter_criteria = get_filter_criteria_for_order_last_id(
            order_dir,
            last_id,
            filter_criteria
        )
        # block by author if author = blocked_user
        blocked_users = []
        if not request.user.is_authenticated:
            pass
        else:
            blocked_users = BlockUser.objects.filter(
                user=request.user).values_list('block_user_id')
        q_blocked_author = Q(
            author_id__in=blocked_users
        )
        q_author_type = Q(
            author__type=UserTypeE.USER)
        q_author_status = Q(
            author__status__in=[UserStatusE.ACTIVE, UserStatusE.INACTIVE])
        q_status = Q(
            post_item__status__in=[PostStatusE.PUBLISHED, PostStatusE.DRAFT,
                                   PostStatusE.IN_DOUBT,
                                   PostStatusE.BIO_ORGANIC])
        q_all = ~q_blocked_author & q_author_type & q_author_status & \
            q_status

        timeline_items = TimeLineItem.active.filter(**filter_criteria).filter(
            q_all).order_by(order_by)[0: limit]
        if not timeline_items:
            raise ResultEmpty

        data = {
            'items': TimeLineItemSerializer(
                timeline_items, many=True, context={
                    'request': request,
                    'include_wine_data': True,
                    'include_winemaker_data': True,
                }
            ).data,
            'last_id': timeline_items[len(timeline_items) - 1].id
        }
        response_data = {'data': data}
        fill_default_response_data(response_data, success=True)
        return Response(response_data)

    @swagger_auto_schema(
        request_body=RaisinListSerializer,
        operation_summary='Return timeline items.',
        operation_description='The method POST is deprecated for this '
                              'endpoint.',
        deprecated=True,
        security=[]
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '/api/timeline/items')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)


# /api/timeline/items
@signed_api(FormClass=TimeLineItemsForm, token_check=False, log_response_data=False)
def get_timeline_items(request):
    # user = request.user
    # prevent_using_non_active_account(user)
    filter_criteria = {}
    last_id = None
    limit = 10
    order_by = '-id'
    order_dir = 'desc'
    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data
            (limit, order_dir, last_id, order_by_old) = list_control_parameters_by_form(cd)
        else:
            raise WrongParametersError(_("Wrong parameters."), form)

    filter_criteria = get_filter_criteria_for_order_last_id(order_dir, last_id, filter_criteria)
    q_author_type = Q(author__type=UserTypeE.USER)  # | Q(author__username='alp')
    q_author_status = Q(author__status__in=[UserStatusE.ACTIVE, UserStatusE.INACTIVE])
    q_status = Q(post_item__status__in=[PostStatusE.PUBLISHED, PostStatusE.DRAFT,
                                        PostStatusE.IN_DOUBT, PostStatusE.BIO_ORGANIC])
    q_all = q_author_type & q_author_status & q_status

    timeline_items = TimeLineItem.active.filter(**filter_criteria).filter(q_all).order_by(order_by)[0: limit]
    if not timeline_items:
        raise ResultEmpty

    return {
        'items': TimeLineItemSerializer(
            timeline_items, many=True, context={
                'request': request,
                'include_wine_data': True,
                'include_winemaker_data': True,
            }
        ).data,
        'last_id': timeline_items[len(timeline_items) - 1].id
    }


# /api/timeline/item/newest
@signed_api(FormClass=TimeLineOneItemForm, token_check=True)
def get_newest_timeline_item(request):
    user = request.user
    prevent_using_non_active_account(user)

    filter_criteria = {}
    limit = 1
    # order_dir = 'desc'
    order_by = '-id'

    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data
            limit = 1
            order_by = '-id'
            if cd['post_id']:
                post = Post.active.get(id=cd['post_id'])
                filter_criteria['post_item'] = post
            elif cd['wine_id']:
                wine_item = Wine.active.get(id=cd['wine_id'])
                filter_criteria['post_item__type'] = PostTypeE.WINE
                filter_criteria['post_item__wine'] = wine_item
            elif cd['tl_id']:
                filter_criteria['id'] = cd['tl_id']
            else:
                raise WrongParametersError(_("Wrong parameters."), form)
        else:
            raise WrongParametersError(_("Wrong parameters."), form)

    filter_criteria['post_item__status__in'] = [PostStatusE.PUBLISHED, PostStatusE.DRAFT,
                                                PostStatusE.IN_DOUBT, PostStatusE.BIO_ORGANIC]
    timeline_items = TimeLineItem.active.filter(**filter_criteria).order_by(order_by)[0: limit]

    if not timeline_items:
        raise ResultEmpty

    timeline_item = timeline_items[0]

    return {
        'item': TimeLineItemSerializer(
            timeline_item, context={
                'request': request,
                'include_wine_data': True,
                'include_winemaker_data': True
            }
        ).data,
    }
