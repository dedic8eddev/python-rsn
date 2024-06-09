from __future__ import absolute_import

import logging

from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from reports.models import BlockUser
from web.authentication import CustomTokenAuthentication
from web.constants import (PostStatusE, PostTypeE, UserStatusE, UserTypeE,
                           WinemakerStatusE)
from web.models import Post, UserProfile, Winemaker
from web.serializers.posts import FullPostSerializer, SearchQuerySerialiser
from web.serializers.users import UserSerializerForCombinedSearch
from web.serializers.winemakers import WinemakerSerializerForCombinedSearch
from web.utils.api_handling import fill_default_response_data


log = logging.getLogger(__name__)


# /api/search/posts
class SearchPostView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CustomTokenAuthentication]

    @swagger_auto_schema(
        query_serializer=SearchQuerySerialiser,
        operation_summary='Search posts.',
        operation_description='Search posts.',
        security=[]
    )
    def get(self, request, format=None):
        serializer = SearchQuerySerialiser(data=request.query_params)
        if serializer.is_valid(raise_exception=True):
            validated_data = serializer.validated_data
            query = validated_data.get('query', '')
            query = query.replace('’', "'")
            force_winepost_name_only = validated_data.get('force_winepost_name_only')
            if validated_data.get('min_letters'):
                if len(query) < validated_data.get('min_letters'):
                    return {'query': query, 'items': []}

            # block by author if author = blocked_user
            blocked_users = []
            if not request.user.is_authenticated:
                pass
            else:
                blocked_users = BlockUser.objects.filter(
                    user=request.user).values_list('block_user_id')

            posts = Post.active.filter(
                wine__is_archived=False,
                status=PostStatusE.PUBLISHED,
                type=PostTypeE.WINE,
                author__status=UserStatusE.ACTIVE
            ).exclude(
                author_id__in=blocked_users
            )

            if query:
                posts = posts.filter(title__unaccent__icontains=query)
            posts = posts.distinct()[:50]

            if force_winepost_name_only:
                posts_out = FullPostSerializer(
                    posts, many=True, context={
                        'request': request,
                        'include_wine_data': True,
                        'include_winemaker_minimal_data': True
                    }
                ).data
            else:
                posts_out = FullPostSerializer(
                    posts, many=True, context={
                        'request': request,
                        'include_wine_data': True,
                        'include_winemaker_data': True
                    }
                ).data

            data = {'items': posts_out,
                    'query': query,
                    'count': posts.count()}

            response_data = {'data': data}
            fill_default_response_data(response_data)
            return Response(response_data)

    @swagger_auto_schema(
        request_body=SearchQuerySerialiser,
        operation_summary='Search posts.',
        operation_description='The method POST is deprecated for this '
                              'endpoint.',
        deprecated=True,
        security=[]
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '/api/search/posts')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)


def search_users_users(query_string, blocked_users):
    users = UserProfile.objects.filter(
        (
            Q(username__unaccent__icontains=query_string) |
            Q(full_name__unaccent__icontains=query_string)
        ) & Q(
            type=UserTypeE.USER,
            status__in=[UserStatusE.ACTIVE, UserStatusE.INACTIVE]
        ) & ~Q(
            id__in=blocked_users
        )
    )

    return UserSerializerForCombinedSearch(users, many=True).data


def search_users_winemakers(query_string):
    winemakers = Winemaker.objects.filter(
        name__unaccent__icontains=query_string,
        status=WinemakerStatusE.VALIDATED
    )

    return WinemakerSerializerForCombinedSearch(winemakers, many=True).data


# /api/search/users
class SearchUserView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CustomTokenAuthentication]

    @swagger_auto_schema(
        query_serializer=SearchQuerySerialiser,
        operation_summary='Search users.',
        operation_description='Search users.',
        security=[]
    )
    def get(self, request, format=None):
        serializer = SearchQuerySerialiser(data=request.query_params)
        if serializer.is_valid(raise_exception=True):
            validated_data = serializer.validated_data
            query_string = validated_data['query'].strip()
            query_string = query_string.replace('’', "'")
            query_string = query_string.strip("%")

            blocked_users = []
            if request.user.is_authenticated:
                blocked_users = BlockUser.objects.filter(
                    user=request.user).values_list('block_user_id')
            users_data = search_users_users(query_string, blocked_users)
            winemakers_data = search_users_winemakers(query_string)
            items_out = winemakers_data + users_data
            data = {
                'query': query_string,
                'items': items_out,
            }
            response_data = {'data': data}
            fill_default_response_data(response_data)
            return Response(response_data)

    @swagger_auto_schema(
        request_body=SearchQuerySerialiser,
        operation_summary='Search users.',
        operation_description='The method POST is deprecated for this '
                              'endpoint.',
        deprecated=True,
        security=[]
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '/api/search/posts')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)
