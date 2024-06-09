from __future__ import absolute_import

import logging

from django.http import JsonResponse
from django.utils.translation import ugettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import DestroyAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from reports.models import BlockUser
from web.api_permissions import PostOwnerCanDeleteCommentPermission
from web.authentication import CustomTokenAuthentication
from web.constants import (ParentItemTypeE, PlaceStatusE, PostTypeE, StatusE,
                           TimeLineItemTypeE)
from web.forms.api_forms import (CommentCreateForm, CommentDeleteForm,
                                 CommentUpdateForm)
from web.models import (CalEvent, Comment, Place, Post, TimeLineItem,
                        UserProfile, Wine, select_star_review_for_winepost)
from web.serializers.comments_likes import CommentSerializer
from web.serializers.common import LikeVoteListSerializer
from web.serializers.events import EventSerializer
from web.serializers.places import FullPlaceSerializer
from web.serializers.posts import FullPostSerializer
from web.serializers.timeline import TimeLineItemSerializer
from web.utils.api_handling import signed_api, fill_default_response_data
from web.utils.exceptions import (ResultEmpty, ResultErrorError,
                                  WrongParametersError)
from web.utils.model_tools import get_filter_criteria_for_order_last_id
from web.utils.views_common import (list_control_parameters_by_form,
                                    prevent_using_non_active_account)

log = logging.getLogger(__name__)


# /api/comments/add
@signed_api(
    FormClass=CommentCreateForm, token_check=True,
    json_used=True, success_status=200
)
def add_comment(request):
    user = request.user
    tl_item = None

    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form = request.form

        if form.is_valid():
            cd = form.cleaned_data

            # =========================================================
            if cd['tl_id']:
                tl_item = TimeLineItem.active.get(id=cd['tl_id'])
                if tl_item.item_type not in (
                    TimeLineItemTypeE.POST, TimeLineItemTypeE.PLACE
                ):
                    raise WrongParametersError(_("Wrong parameters."), form)

                parent_item_type = tl_item.get_cached_item_type_as_parent_item_type()  # noqa
                parent_item = tl_item.get_cached_item()
                if not parent_item_type or not parent_item or (
                    parent_item_type == ParentItemTypeE.PLACE and
                    parent_item.status == PlaceStatusE.CLOSED
                ):
                    raise WrongParametersError(_("Wrong parameters."), form)
            elif cd['post_id']:
                parent_item = Post.active.get(id=cd['post_id'])
                parent_item_type = ParentItemTypeE.POST
            elif cd['place_id']:
                parent_item = Place.active.get(
                    id=cd['place_id'],
                    status__in=[
                        PlaceStatusE.SUBSCRIBER,
                        PlaceStatusE.PUBLISHED,
                        PlaceStatusE.IN_DOUBT,
                        PlaceStatusE.DRAFT
                    ]
                )
                parent_item_type = ParentItemTypeE.PLACE

                if parent_item.status not in [PlaceStatusE.SUBSCRIBER,
                                              PlaceStatusE.PUBLISHED]:
                    raise ResultErrorError("Place is not validated yet", 102)
            elif cd['event_id']:
                parent_item = CalEvent.active.get(id=cd['event_id'])
                parent_item_type = ParentItemTypeE.CAL_EVENT
            else:
                raise WrongParametersError(_("Wrong parameters."), form)

            comment = Comment(**{
                'author': user,
                parent_item_type: parent_item,
                'status': StatusE.PUBLISHED,
                'description': cd['description'],
            })

            comment.save()
            parent_item.refresh_from_db()
            comment.refresh_from_db()

            if tl_item:
                tl_item.refresh_from_db()

            if parent_item_type == ParentItemTypeE.POST and parent_item.type == PostTypeE.WINE:  # noqa
                select_star_review_for_winepost(parent_item)

            comment.update_user_mentions(
                cd['mentions'] if cd['mentions'] else None, save_item=True
            )

            if parent_item_type == ParentItemTypeE.POST:
                parent_item_ser = FullPostSerializer(
                    parent_item, context={
                        'request': request,
                        'include_wine_data': True,
                        'include_winemaker_data': True
                    }
                ).data
            elif parent_item_type == ParentItemTypeE.PLACE:
                parent_item_ser = FullPlaceSerializer(
                    parent_item, context={'request': request}
                ).data
            elif parent_item_type == ParentItemTypeE.CAL_EVENT:
                parent_item_ser = EventSerializer(
                    parent_item, context={'request': request}
                ).data

            return {
                'comment': CommentSerializer(comment).data,
                parent_item_type: parent_item_ser,
                'tl_item': TimeLineItemSerializer(
                    tl_item, context={
                        'request': request,
                        'include_wine_data': True,
                        'include_winemaker_data': True,
                    }
                ).data,
            }
        else:
            raise WrongParametersError(_("Wrong parameters."), form)


# /api/comments/update
@signed_api(
    FormClass=CommentUpdateForm, token_check=True,
    json_used=True, success_status=200
)
def update_comment(request):
    user = request.user

    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form = request.form

        if form.is_valid():
            cd = form.cleaned_data

            comment = Comment.active.get(id=cd['comment_id'])

            if comment.place and comment.place.status == PlaceStatusE.CLOSED:
                raise WrongParametersError(_("Wrong parameters."), form)

            if comment.author != user:
                raise ResultErrorError(_(
                    "You are not permitted to update this comment."
                ))

            comment.description = cd['description']

            comment.save()
            comment.refresh_from_db()
            comment.update_user_mentions(
                cd['mentions'] if cd['mentions'] else None, save_item=True
            )

            if comment.post and comment.post.type == PostTypeE.WINE and comment.post.wine:  # noqa
                select_star_review_for_winepost(comment.post)

            return CommentSerializer(comment).data
        else:
            raise WrongParametersError(_("Wrong parameters."), form)


# /api/comments/delete
@signed_api(
    FormClass=CommentDeleteForm, token_check=True,
    json_used=True, success_status=200
)
def delete_comment(request):
    user = request.user

    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form = request.form

        if form.is_valid():
            cd = form.cleaned_data

            comment = Comment.active.get(id=cd['comment_id'], author=user)

            if comment.place and comment.place.status == PlaceStatusE.CLOSED:
                raise WrongParametersError(_("Wrong parameters."), form)

            comment.archive()

            if comment.post and comment.post.type == PostTypeE.WINE and comment.post.wine:  # noqa
                select_star_review_for_winepost(comment.post)

            return JsonResponse({}, status=204)
        else:
            raise WrongParametersError(_("Wrong parameters."), form)


class CommentDeleteApiView(DestroyAPIView):
    permission_classes = [IsAuthenticated, PostOwnerCanDeleteCommentPermission]
    authentication_classes = [CustomTokenAuthentication]
    queryset = Comment.active.all()


# /api/comments/list
class CommentListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CustomTokenAuthentication]

    @swagger_auto_schema(
        query_serializer=LikeVoteListSerializer,
        operation_summary='A list of comments.',
        operation_description='A list of commentaries provided for one of '
                              'the following entities: Post, Place, '
                              'UserProfile, Wine, Event.',
        security=[]
    )
    def get(self, request, format=None):
        serializer = LikeVoteListSerializer(data=request.query_params)
        if serializer.is_valid(raise_exception=True):

            if request.user.is_authenticated:
                user = request.user
                prevent_using_non_active_account(user)

            filter_criteria = {}
            validated_data = serializer.validated_data
            if validated_data.get('post_id'):
                post = Post.active.get(id=validated_data['post_id'])
                filter_criteria['post'] = post
            elif validated_data.get('place_id'):
                place = Place.active.get(
                    id=validated_data['place_id'],
                    status__in=[
                        PlaceStatusE.SUBSCRIBER,
                        PlaceStatusE.PUBLISHED,
                        PlaceStatusE.DRAFT,
                        PlaceStatusE.IN_DOUBT
                    ]
                )
                filter_criteria['place'] = place

                if place.status not in [PlaceStatusE.SUBSCRIBER,
                                        PlaceStatusE.PUBLISHED]:
                    raise ResultErrorError("Place is not validated yet", 102)
            elif validated_data.get('user_id'):
                user_item = UserProfile.active.get(id=validated_data['user_id'])
                filter_criteria['author'] = user_item
            elif validated_data.get('username'):
                user_item = UserProfile.active.get(username=validated_data['username'])
                filter_criteria['author'] = user_item
            elif validated_data.get('wine_id'):
                wine_item = Wine.active.get(id=validated_data['wine_id'])
                filter_criteria['wine'] = wine_item

            elif validated_data.get('event_id'):
                cal_event = CalEvent.active.get(id=validated_data['event_id'])
                filter_criteria['cal_event'] = cal_event

            (limit, order_dir, last_id, order_by) = \
                list_control_parameters_by_form(validated_data)  # noqa

            filter_criteria = get_filter_criteria_for_order_last_id(
                order_dir, last_id, filter_criteria
            )

            # exclude comments from blocked (by requester) users
            comments_from_blocked_users_criteria = {}
            if request.user.is_authenticated:
                blocked_users = BlockUser.objects.filter(
                    user=request.user).values_list('block_user_id')
                comments_from_blocked_users_criteria = {
                    "author_id__in": blocked_users
                }

            comments = Comment.active.filter(
                **filter_criteria
            ).exclude(
                **comments_from_blocked_users_criteria
            ).order_by(order_by)[0:limit]

            if not comments:
                raise ResultEmpty

            comments_out = CommentSerializer(comments, many=True).data

            data = {'comments': comments_out, 'last_id': last_id}
            response_data = {'data': data}
            fill_default_response_data(response_data)
            return Response(response_data)

    @swagger_auto_schema(
        request_body=LikeVoteListSerializer,
        operation_summary='A list of comments.',
        operation_description='The method POST is deprecated for this '
                              'endpoint.',
        deprecated=True,
        security=[]
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '# /api/comments/list')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)
