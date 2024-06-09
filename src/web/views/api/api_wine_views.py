from __future__ import absolute_import

import logging

from django.conf import settings
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response

from reports.models import BlockUser
from web.authentication import CustomTokenAuthentication
from web.constants import (PostStatusE, PostTypeE, UserStatusE, UserTypeE,
                           WineStatusE)
from web.forms.api_forms import (WineItemsForm, WineSimiliarItemsForm)
from web.models import (Comment, DrankItToo, LikeVote, Post, TimeLineItem,
                        Wine)
from web.serializers.comments_likes import (CommentSerializer,
                                            DrankItTooSerializer,
                                            LikeVoteSerializer)
from web.serializers.posts import FullPostSerializer, FullWineSerializer
from web.serializers.wines import WineProfileSerializer
from web.utils.api_handling import signed_api, fill_default_response_data
from web.utils.exceptions import ResultEmpty, WrongParametersError
from web.utils.model_tools import get_filter_criteria_for_order_last_id
from web.utils.views_common import (list_control_parameters_by_form,
                                    list_last_id,
                                    prevent_using_non_active_account)

log = logging.getLogger(__name__)


# /api/wine/items
@signed_api(FormClass=WineItemsForm, token_check=True, log_response_data=False)
def get_wine_items(request):
    user = request.user
    prevent_using_non_active_account(user)

    filter_criteria = {}
    last_id = None
    limit = 10
    offset = 0
    order_dir = 'asc'
    order_by = 'name'

    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data

            if cd.get('winemaker_id', None):
                filter_criteria['winemaker_id'] = cd['winemaker_id']
                filter_criteria['id__in'] = Post.active.filter(
                    is_parent_post=True,
                    wine__winemaker_id=cd['winemaker_id']
                ).values_list("wine_id", flat=True)

            else:
                filter_criteria['id__in'] = Post.active.filter(
                    is_parent_post=True
                ).values_list("wine_id", flat=True)

            (
                limit, order_dirx, last_id, order_byx
            ) = list_control_parameters_by_form(cd)

            if limit == -1 and settings.NO_LIMIT_ALLOWED:
                offset = None
                limit = None
            elif limit == -1:
                limit = 10

        else:
            raise WrongParametersError(_("Wrong parameters."), form)

    filter_criteria = get_filter_criteria_for_order_last_id(
        order_dir, last_id, filter_criteria
    )
    filter_criteria['status'] = WineStatusE.VALIDATED

    items_dict = []
    items = Wine.active.filter(
        **filter_criteria
    ).order_by(order_by)[offset: limit]
    count = Wine.active.filter(**filter_criteria).count()

    if not items:
        raise ResultEmpty

    for item in items:
        item_dict = FullWineSerializer(
            item, context={
                'request': request,
                "fallback_parent_post_image": True,
                "fallback_child_post_image": True,
                "include_winemaker_basic_data": True
            }
        ).data

        q_desc1 = Q(description=None)
        q_desc2 = Q(description="")
        q_desc3 = Q(author__type__in=[UserTypeE.ADMINISTRATOR, UserTypeE.EDITOR])  # noqa
        q_desc_exclude = q_desc1 | q_desc2 | q_desc3

        q_post = Q(type=PostTypeE.WINE) & Q(wine=item) & Q(status=PostStatusE.PUBLISHED)  # noqa
        count_wineposts = Post.active.filter(
            q_post
        ).exclude(q_desc_exclude).count()

        item_dict['total_wine_post_number'] = count_wineposts

        items_dict.append(item_dict)

    return {
        'items': items_dict,
        'count': count,
        'last_id': items[len(items) - 1].id
    }


# /api/wine/similiar/items
@signed_api(FormClass=WineSimiliarItemsForm, token_check=True)
def get_wine_similiar_items(request):
    user = request.user
    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data

            query = 'SELECT id,name,similarity("name", %(wine_name)s) AS similarity FROM web_wine ' \
                    'WHERE similarity("name", %(wine_name)s) >= %(threshold)s AND status <> %(status_excluded)s ' \
                    'ORDER BY similarity DESC'

            params = {
                'wine_name': cd['wine_name'],
                'status_excluded': WineStatusE.HIDDEN,
                'threshold': settings.SIMILARITY_THRESHOLD,
            }

            items = Wine.active.raw(query, params=params)

            items_coll = FullWineSerializer(
                items, context={'request': request}, many=True
            ).data

            return {'items': items_coll}
        else:
            raise WrongParametersError(_("Wrong parameters."), form)


# /api/wine/profile
class WineProfileView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CustomTokenAuthentication]

    @swagger_auto_schema(
        query_serializer=WineProfileSerializer,
        operation_summary='Return profile wine by wine_id',
        operation_description='Return profile wine by wine_id',
        security=[]
    )
    def get(self, request, format=None):
        serializer = WineProfileSerializer(data=request.query_params)

        if serializer.is_valid():
            validated_data = serializer.validated_data
            wine = Wine.objects.get(id=validated_data['wine_id'])
            offset_0 = 0
            offset_n = 10

            blocked_users = []
            if request.user.is_authenticated:
                blocked_users = BlockUser.objects.filter(
                    user=request.user).values_list('block_user_id')
            reviews = Post.active.filter(
                type=PostTypeE.WINE, wine=wine, is_star_review=False
            ).exclude(
                author_id__in=blocked_users
            ).select_related(
                'main_image', 'author', 'wine'
            ).order_by(
                '-is_parent_post', '-modified_time'
            )[offset_0: offset_n]
            star_reviews = Post.active.filter(
                type=PostTypeE.WINE, wine=wine, is_star_review=True,
                status=PostStatusE.PUBLISHED,
                author__status__in=[UserStatusE.ACTIVE,
                                    UserStatusE.INACTIVE],
                author__type=UserTypeE.USER,
                wine__status=WineStatusE.VALIDATED
            ).exclude(
                author_id__in=blocked_users
            ).select_related(
                'main_image', 'author', 'wine'
            ).order_by('-created_time')
            star_review_dict = None
            reviews_out = None

            # # star reviews
            if star_reviews:
                star_review = star_reviews[0]
                star_review_dict = FullPostSerializer(star_review, context={
                    'request': request,
                    'include_wine_data': False,
                    'fallback_wine_image': True
                }).data if star_review else None

                timeline_items = TimeLineItem.active.filter(
                    post_item__id=star_review.id
                ).order_by('-id')[0: 1]
                if timeline_items:
                    timeline_item = timeline_items[0]
                    tl_id = timeline_item.id
                    star_review_dict['tl_id'] = tl_id
                else:
                    star_review_dict['tl_id'] = None

            # reviews
            if reviews:
                reviews_out = FullPostSerializer(reviews, many=True,
                                                 context={
                                                     'request': request,
                                                     'include_wine_data': False,
                                                     'fallback_wine_image': True
                                                 }).data

                for review_out in reviews_out:
                    timeline_items = TimeLineItem.active.filter(
                        post_item__id=review_out['id']
                    ).order_by('-id')[0: 1]
                    if timeline_items:
                        timeline_item = timeline_items[0]
                        tl_id = timeline_item.id
                        review_out['tl_id'] = tl_id
                    else:
                        review_out['tl_id'] = None

            likevotes = LikeVote.active.filter(
                wine=wine
            ).exclude(
                author_id__in=blocked_users
            ).select_related(
                'post', 'author'
            ).order_by('-created_time')[offset_0: offset_n]

            comments = Comment.active.filter(
                wine=wine
            ).exclude(
                author_id__in=blocked_users
            ).select_related(
                'post', 'author'
            ).order_by('-created_time')[offset_0: offset_n]

            drank_it_toos = DrankItToo.active.filter(
                wine=wine
            ).exclude(
                author_id__in=blocked_users
            ).select_related(
                'post', 'author'
            ).order_by('-created_time')[offset_0: offset_n]

            review_last_id = list_last_id(reviews)
            likevote_last_id = list_last_id(likevotes)
            comment_last_id = list_last_id(comments)
            drank_it_too_last_id = list_last_id(drank_it_toos)

            likevotes_out = LikeVoteSerializer(likevotes, many=True).data
            comments_out = CommentSerializer(comments, many=True).data
            drank_it_toos_out = DrankItTooSerializer(
                drank_it_toos, many=True
            ).data

            wine_dict = FullWineSerializer(
                wine, context={
                    'request': request,
                    'include_winemaker_data': True,
                    'fallback_parent_post_image': True,
                    'fallback_child_post_image': True
                }
            ).data

            wine_dict['region'] = wine_dict['winemaker']['region']
            data = {
                'wine': wine_dict,

                'star_review': star_review_dict,
                'reviews': reviews_out,

                'likevotes': likevotes_out,
                'comments': comments_out,
                'drank_it_toos': drank_it_toos_out,

                'review_last_id': review_last_id,
                'likevote_last_id': likevote_last_id,
                'comment_last_id': comment_last_id,
                'drank_it_too_last_id': drank_it_too_last_id,
            }
            response_data = {'data': data}
            fill_default_response_data(response_data)
            return Response(response_data)

    @swagger_auto_schema(
        request_body=WineProfileSerializer,
        operation_summary='Return profile wine by wine_id',
        operation_description='The method POST is deprecated for this '
                              'endpoint.',
        deprecated=True,
        security=[]
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '/api/wine/profile')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)
