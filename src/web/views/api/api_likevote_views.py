from __future__ import absolute_import

import logging

from django.utils.translation import ugettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from reports.models import BlockUser
from web.constants import ParentItemTypeE, PlaceStatusE, TimeLineItemTypeE
from web.forms.api_forms import (LikeVoteCreateForm, LikeVoteDeleteForm,
                                 LikeVotePostOrPlaceForm)
from web.models import (CalEvent, LikeVote, Place, Post, TimeLineItem,
                        UserProfile, Wine)
from web.serializers.comments_likes import LikeVoteSerializer
from web.serializers.events import EventSerializer
from web.serializers.places import FullPlaceSerializer
from web.utils.api_handling import signed_api, fill_default_response_data
from web.utils.exceptions import (ResultEmpty, ResultErrorError,
                                  WrongParametersError)
from web.utils.model_tools import get_filter_criteria_for_order_last_id
from web.utils.views_common import (list_control_parameters_by_form,
                                    list_last_id,
                                    prevent_using_non_active_account)

from .common import get_newest_tl_dict_for_post_and_send_sr_if_needed
from ...authentication import CustomTokenAuthentication
from ...serializers.common import LikeVoteListSerializer

log = logging.getLogger(__name__)


# /api/likes/add
@signed_api(
    FormClass=LikeVoteCreateForm, token_check=True,
    json_used=True, success_status=200
)
def add_likevote(request):
    user = request.user
    prevent_using_non_active_account(user)
    parent_item = None

    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data
            if cd['tl_id']:
                tl_item = TimeLineItem.active.get(
                    id=cd['tl_id'],
                    item_type=TimeLineItemTypeE.POST
                )

                parent_item_type = ParentItemTypeE.POST
                parent_item = tl_item.get_cached_item()

                if not parent_item:
                    parent_item = tl_item.get_item()

                if not parent_item:
                    raise WrongParametersError(_("Wrong parameters."), form)
            elif cd['post_id']:
                parent_item_type = ParentItemTypeE.POST
                parent_item = Post.active.get(id=cd['post_id'])
            elif cd['place_id']:
                parent_item_type = ParentItemTypeE.PLACE
                parent_item = Place.active.get(id=cd['place_id'],
                                               status__in=[
                                                   PlaceStatusE.PUBLISHED,
                                                   PlaceStatusE.SUBSCRIBER])
            elif cd['event_id']:
                parent_item_type = ParentItemTypeE.CAL_EVENT
                parent_item = CalEvent.active.get(id=cd['event_id'])
            else:
                raise WrongParametersError(_("Wrong parameters."), form)

            likevotes = parent_item.like_votes.filter(
                author=user,
                is_archived=False
            )

            if not likevotes:
                likevote = LikeVote(
                    **{'author': user, parent_item_type: parent_item}
                )
                likevote.save()
                parent_item.refresh_from_db()

            if parent_item_type == ParentItemTypeE.POST:
                return get_newest_tl_dict_for_post_and_send_sr_if_needed(
                    request, parent_item
                )
            elif parent_item_type == ParentItemTypeE.CAL_EVENT:
                return EventSerializer(
                    parent_item, context={'request': request}
                ).data
            elif parent_item_type == ParentItemTypeE.PLACE:
                return FullPlaceSerializer(
                    parent_item, context={'request': request}
                ).data
        else:
            raise WrongParametersError(_("Wrong parameters."), form)


# /api/likes/delete
@signed_api(
    FormClass=LikeVoteDeleteForm, token_check=True,
    json_used=True, success_status=200
)
def delete_likevote(request):
    user = request.user
    prevent_using_non_active_account(user)
    parent_item = None
    parent_item_type = None

    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data
            if cd['place_id']:
                parent_item_type = ParentItemTypeE.PLACE
                parent_item = Place.active.get(id=cd['place_id'])
                items = LikeVote.active.filter(
                    place=parent_item,
                    author=user,
                    place__status__in=[PlaceStatusE.PUBLISHED,
                                       PlaceStatusE.SUBSCRIBER]
                ).order_by('-id')
            elif cd['post_id']:
                parent_item_type = ParentItemTypeE.POST
                parent_item = Post.active.get(id=cd['post_id'])
                items = LikeVote.active.filter(
                    post=parent_item,
                    author=user
                ).order_by('-id')
            elif cd['event_id']:
                parent_item_type = ParentItemTypeE.CAL_EVENT
                parent_item = CalEvent.active.get(id=cd['event_id'])
                items = LikeVote.active.filter(
                    cal_event=parent_item,
                    author=user
                ).order_by('-id')
            elif cd['tl_id']:
                tl_item = TimeLineItem.active.get(
                    id=cd['tl_id'],
                    item_type=TimeLineItemTypeE.POST
                )
                parent_item_type = ParentItemTypeE.POST
                parent_item = tl_item.get_item()
                items = LikeVote.active.filter(
                    post=parent_item,
                    author=user
                ).order_by('-id')
            elif cd['likevote_id']:
                items = LikeVote.active.filter(
                    id=cd['likevote_id'],
                    author=user
                ).order_by('-id')
                if items:
                    item = items[0]
                    if item.place:
                        parent_item_type = ParentItemTypeE.PLACE
                        parent_item = item.place
                        if parent_item.status not in [PlaceStatusE.PUBLISHED,
                                                      PlaceStatusE.SUBSCRIBER]:
                            raise ResultErrorError(
                                "Place is not validated yet", 102
                            )
                    elif item.post:
                        parent_item_type = ParentItemTypeE.POST
                        parent_item = item.post
                    elif item.cal_event:
                        parent_item_type = ParentItemTypeE.CAL_EVENT
                        parent_item = item.cal_event
                    if not parent_item:
                        raise ResultErrorError("no parent item for like with id {}".format(cd['likevote_id']))
            else:
                raise WrongParametersError(_("Wrong parameters."), form)

            if not items:
                raise ResultErrorError("no item to use")
            if not parent_item:
                raise ResultErrorError("no parent item for this like")

            for item in items:
                item.archive()
                item.refresh_from_db()
            parent_item.refresh_from_db()

            if parent_item_type == ParentItemTypeE.POST:
                return get_newest_tl_dict_for_post_and_send_sr_if_needed(
                    request, parent_item
                )
            elif parent_item_type == ParentItemTypeE.CAL_EVENT:
                return EventSerializer(
                    parent_item, context={'request': request}
                ).data
            elif parent_item_type == ParentItemTypeE.PLACE:
                return FullPlaceSerializer(
                    parent_item, context={'request': request}
                ).data


# /api/likes/get-i-like
@signed_api(FormClass=LikeVotePostOrPlaceForm, token_check=True)
def get_i_like(request):
    user = request.user
    prevent_using_non_active_account(user)

    filter_criteria = {}
    i_like_it = False
    i_drank_it_too = False

    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data
            if cd['post_id']:
                item = Post.active.get(id=cd['post_id'])
                filter_criteria['post'] = item
                i_drank_it_too = item.drank_it_toos.filter(
                    author=user
                ).exists()
            elif cd['place_id']:
                item = Place.active.get(id=cd['place_id'],
                                        status__in=[PlaceStatusE.PUBLISHED,
                                                    PlaceStatusE.SUBSCRIBER])
                filter_criteria['place'] = item
            elif cd['event_id']:
                item = CalEvent.active.get(id=cd['event_id'])
                filter_criteria['cal_event'] = item
            else:
                raise WrongParametersError(_("Wrong parameters."), form)

        return {'i_like_it': i_like_it, 'i_drank_it_too': i_drank_it_too}


# /api/likes/list
class LikeVoteListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CustomTokenAuthentication]

    @swagger_auto_schema(
        query_serializer=LikeVoteListSerializer,
        operation_summary='A list of likes.',
        operation_description='A list of like votes provided for one of '
                              'the following entities: Post, Place, '
                              'UserProfile, Wine, Event.',
        security=[]
    )
    def get(self, request, format=None):
        serializer = LikeVoteListSerializer(data=request.query_params)
        if serializer.is_valid(raise_exception=True):
            filter_criteria = {}
            validated_data = serializer.validated_data
            if validated_data.get('post_id'):
                post = Post.active.get(id=validated_data['post_id'])
                filter_criteria['post'] = post
            elif validated_data.get('place_id'):
                place = Place.active.get(
                    id=validated_data.get('place_id'),
                    status__in=[PlaceStatusE.PUBLISHED,
                                PlaceStatusE.SUBSCRIBER]
                )
                filter_criteria['place'] = place
            elif validated_data.get('event_id'):
                item = CalEvent.active.get(id=validated_data.get('event_id'))
                filter_criteria['cal_event'] = item
            elif validated_data.get('user_id'):
                user_item = UserProfile.active.get(id=validated_data['user_id'])
                filter_criteria['author'] = user_item
            elif validated_data.get('username'):
                user_item = UserProfile.active.get(username=validated_data['username'])
                filter_criteria['author'] = user_item
            elif validated_data.get('wine_id'):
                wine_item = Wine.active.get(id=validated_data.get('wine_id'))
                filter_criteria['wine'] = wine_item

            (limit, order_dir, last_id, order_by) = list_control_parameters_by_form(
                validated_data, default_limit=None
            )

            filter_criteria = get_filter_criteria_for_order_last_id(
                order_dir, last_id, filter_criteria
            )

            # exclude likevotes from blocked users
            blocked_users = []
            if request.user.is_authenticated:
                blocked_users = BlockUser.objects.filter(
                    user=request.user).values_list('block_user_id')

            likevotes = LikeVote.active.filter(
                **filter_criteria
            ).exclude(
                author_id__in=blocked_users
            ).order_by(order_by)[0:limit]

            if not likevotes:
                raise ResultEmpty

            last_id = list_last_id(likevotes)
            likevotes_out = LikeVoteSerializer(
                likevotes, many=True, context={'request': request}
            ).data

            data = {'likes': likevotes_out, 'last_id': last_id}
            response_data = {'data': data}
            fill_default_response_data(response_data)
            return Response(response_data)

    @swagger_auto_schema(
        request_body=LikeVoteListSerializer,
        operation_summary='A list of likes.',
        operation_description='The method POST is deprecated for this '
                              'endpoint.',
        deprecated=True,
        security=[]
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '# /api/likes/list')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)
