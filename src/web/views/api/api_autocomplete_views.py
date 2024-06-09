from __future__ import absolute_import

import logging

from django.db.models import Q, Count, OuterRef, Subquery
from django.utils.translation import ugettext_lazy as _
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from web.api_filters.search_filters import AutocompleteSearchFilter
from web.api_paginations.autocomplete import AutocompletePagination
from web.authentication import CustomTokenAuthentication
from rest_framework.authentication import SessionAuthentication
from web.constants import (AutocompleteQueryType, PlaceStatusE, UserStatusE,
                           UserTypeE, WinemakerStatusE, WineStatusE, PostTypeE, PostStatusE)
from web.forms.common import AutocompleteQueryForm
from web.models import Place, UserProfile, Wine, Winemaker, Post
from web.serializers.places import FullPlaceSerializer
from web.serializers.posts import WineWithYearSerializer
from web.serializers.users import UserSerializer
from web.serializers.winemakers import LongWinemakerSerializerLegacy
from web.utils.api_handling import signed_api
from web.utils.exceptions import WrongParametersError

log = logging.getLogger(__name__)


# /api/autocomplete/winemaker
class AutocompleteWinemakerAPIListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = (CustomTokenAuthentication, SessionAuthentication)
    queryset = Winemaker.active.filter(
        status__in=[WinemakerStatusE.VALIDATED, WinemakerStatusE.IN_DOUBT, WinemakerStatusE.BIO_ORGANIC],
        author__status__in=[UserStatusE.ACTIVE, UserStatusE.INACTIVE]
    )
    filter_backends = [AutocompleteSearchFilter]
    search_fields = ['*name']
    serializer_class = LongWinemakerSerializerLegacy
    pagination_class = AutocompletePagination

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('author', 'author__image', 'last_modifier', 'last_modifier__image', 'main_image').\
            annotate(
            total_wine_number_annotated=Count('wines', filter=Q(
                wines__status=WineStatusE.VALIDATED,
                wines__is_archived=False), distinct=True),
            total_wine_post_number_annotated=Count('wines__posts', filter=Q(
                wines__posts__status=PostStatusE.PUBLISHED,
                wines__posts__type=PostTypeE.WINE,
                wines__posts__wine__status=WineStatusE.VALIDATED), distinct=True)
        )
        return qs

    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '/api/autocomplete/wine')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)


# /api/autocomplete/domain
@signed_api(
    FormClass=AutocompleteQueryForm, token_check=True, log_response_data=False
)
def autocomplete_domain(request):
    form = request.form

    if request.method == 'POST':
        if form.is_valid():
            cd = request.form.cleaned_data
            q_criteria = Q(author__status__in=[
                UserStatusE.ACTIVE,
                UserStatusE.INACTIVE
            ], status__in=[
                WineStatusE.VALIDATED,
                WineStatusE.BIO_ORGANIC,
                WineStatusE.IN_DOUBT
            ])
            query = cd['query']

            if cd.get('query_type') == AutocompleteQueryType.STARTS:
                q_criteria &= Q(domain__unaccent__istartswith=query)
            if cd.get('query_type') == AutocompleteQueryType.ENDS:
                q_criteria &= Q(domain__unaccent__iendswith=query)
            else:  # CONTAINS - default value
                q_criteria &= Q(domain__unaccent__icontains=query)

            items = Winemaker.active.filter(q_criteria).all()
            items_out = LongWinemakerSerializerLegacy(items, many=True).data

        return {
            'items': items_out,
            'query': query,
        }
    else:
        raise WrongParametersError(_("Wrong parameters."), form)


# /api/autocomplete/wine
class AutocompleteWineAPIListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = (CustomTokenAuthentication, SessionAuthentication)
    queryset = Wine.active.filter(
        author__status__in=[UserStatusE.ACTIVE, UserStatusE.INACTIVE],
        status__in=[WineStatusE.VALIDATED, WineStatusE.BIO_ORGANIC, WineStatusE.IN_DOUBT]
    )
    filter_backends = [AutocompleteSearchFilter]
    search_fields = ['*name']
    serializer_class = WineWithYearSerializer
    pagination_class = AutocompletePagination

    def get_queryset(self):
        qs = super().get_queryset()
        parent_post = Post.active.filter(wine=OuterRef('pk'), is_parent_post=True)

        qs = qs.select_related('author', 'winemaker', 'main_image')\
            .annotate(
            wine_post_number_annotated=Count(
                'posts', filter=Q(posts__type=PostTypeE.WINE, posts__status=PostStatusE.PUBLISHED), distinct=True
            ),
            total_star_review_number_annotated=Count(
                'posts', filter=Q(posts__type=PostTypeE.WINE, posts__status=PostStatusE.PUBLISHED,
                                  posts__is_star_review=True), distinct=True
            ),
            wine_trade=Subquery(parent_post.values('wine_trade')[:1]),
            parent_post_status=Subquery(parent_post.values('status')[:1])
        )
        return qs

    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '/api/autocomplete/wine')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)


# /api/autocomplete/place
@signed_api(
    FormClass=AutocompleteQueryForm, token_check=True,
    log_response_data=False, ensure_ascii=False
)
def autocomplete_place(request):
    form = request.form

    if request.method == 'POST':
        if form.is_valid():
            cd = request.form.cleaned_data
            q_criteria = Q(status__in=[
                PlaceStatusE.SUBSCRIBER,
                PlaceStatusE.PUBLISHED,
                PlaceStatusE.DRAFT,
                PlaceStatusE.IN_DOUBT
            ])
            query = cd['query']

            if cd.get('query_type') == AutocompleteQueryType.STARTS:
                q_criteria &= Q(name__unaccent__istartswith=query)
            if cd.get('query_type') == AutocompleteQueryType.ENDS:
                q_criteria &= Q(name__unaccent__iendswith=query)
            else:  # CONTAINS - default value
                q_criteria &= Q(name__unaccent__icontains=query)

            items = Place.active.filter(q_criteria).all()
            items_out = FullPlaceSerializer(
                items, many=True, context={'request': request}
            ).data

        return {
            'items': items_out,
            'query': query,
        }
    else:
        raise WrongParametersError(_("Wrong parameters."), form)


# /api/autocomplete/username
@signed_api(
    FormClass=AutocompleteQueryForm, token_check=True, log_response_data=False
)
def autocomplete_username(request):
    form = request.form

    if request.method == 'POST':
        if form.is_valid():
            cd = request.form.cleaned_data
            q_criteria = Q(status__in=[
                UserStatusE.ACTIVE,
                UserStatusE.INACTIVE
            ], type=UserTypeE.USER)
            query = cd['query']

            if cd.get('query_type') == AutocompleteQueryType.STARTS:
                q_criteria &= Q(username__unaccent__istartswith=query)
            if cd.get('query_type') == AutocompleteQueryType.ENDS:
                q_criteria &= Q(username__unaccent__iendswith=query)
            else:  # CONTAINS - default value
                q_criteria &= Q(username__unaccent__icontains=query)

            items = UserProfile.active.filter(q_criteria).all()
            items_out = UserSerializer(
                items, many=True, context={'request': request}
            ).data

        return {
            'items': items_out,
            'query': query,
        }
    else:
        raise WrongParametersError(_("Wrong parameters."), form)
