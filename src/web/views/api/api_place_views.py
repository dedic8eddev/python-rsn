from __future__ import absolute_import

import os
import datetime

from django.db.models import Q, Count
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from reports.models import BlockUser
from web.authentication import CustomTokenAuthentication

import json
import logging
import re
from itertools import chain

from django.utils.translation import ugettext_lazy as _

from django.conf import settings
from web.constants import (PlaceStatusE, TimeLineItemTypeE, UserTypeE,
                           VenueWineTypeE, PostTypeE, PlaceSourceInfoE)
from web.forms.api_forms import (PlaceCreateForm,
                                 PlaceDeleteForm, PlaceEditForm,
                                 PlaceFileUploadForm, PlaceListGeoForm,
                                 PlaceOpenClosedStatusForm)
from web.models import Place, PlaceImage, Post, TimeLineItem, UserProfile, LikeVote
from web.serializers.comments_likes import CommentSerializer, \
    LikeVoteSerializer
from web.serializers.common import RandomFoodsWinesGeoSerializer
from web.serializers.places import (FullPlaceSerializer,
                                    MinimalPlaceSerializer,
                                    PlaceWithLocationSerializer,
                                    MinimalPlace2Serializer, PlaceGetSerializer,
                                    WinesForPlaceSerializer)
from web.serializers.posts import FoodPostAPISerializer, WinePostAPISerializer
from web.utils.api_handling import signed_api, fill_default_response_data
from web.utils.api_place_utils import (get_closest_venues, get_food_posts,
                                       get_recent_wine_posts, get_wine_posts)
from web.utils.exceptions import (ResultEmpty, ResultErrorError,
                                  WrongParametersError)
from web.utils.geoloc import get_address_data_for_latlng
from web.utils.pro_utils import get_owner_url_pro
from web.utils.views_common import (prevent_editing_not_own_item,
                                    prevent_using_non_active_account)

# from web.utils.api_user_storage_utils import ApiUserStorageUtils

from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from web.pagination import PlacePagination
from django.contrib.postgres.aggregates import ArrayAgg

# from web.constants import PLACE_IMAGES_LIMIT
log = logging.getLogger(__name__)


# /api/places/delete
@signed_api(
    FormClass=PlaceDeleteForm, token_check=True, json_used=True,
    success_status=200, ensure_ascii=True
)
def delete_place(request):
    user = request.user
    prevent_using_non_active_account(user)
    item = None
    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data
            if cd['place_id']:
                item = Place.active.get(
                    id=cd['place_id'],
                    status__in=[
                        PlaceStatusE.SUBSCRIBER,
                        PlaceStatusE.PUBLISHED,
                        PlaceStatusE.DRAFT,
                        PlaceStatusE.IN_DOUBT
                    ]
                )
            elif cd['tl_id']:
                tl_item = TimeLineItem.active.get(id=cd['tl_id'])
                if tl_item.item_type == TimeLineItemTypeE.PLACE:
                    item = Place.active.get(
                        id=tl_item.cached_item['id'],
                        status__in=[
                            PlaceStatusE.SUBSCRIBER,
                            PlaceStatusE.PUBLISHED,
                            PlaceStatusE.DRAFT,
                            PlaceStatusE.IN_DOUBT
                        ]
                    )
                else:
                    raise ResultErrorError(
                        "wrong item type in TL ITEM - place expected", 102
                    )
            if not item:
                raise ResultErrorError("item to delete was not found", 102)
            prevent_editing_not_own_item(user, item)
            item.archive()
            return {
                'archived_item': FullPlaceSerializer(
                    item, context={'request': request}
                ).data,
            }
        else:
            raise WrongParametersError(_("Wrong parameters."), form)


# /api/places/place
class PlaceGetView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = (CustomTokenAuthentication,)

    @swagger_auto_schema(
        query_serializer=PlaceGetSerializer,
        security=[],
        operation_summary='Return information about place by place_id.',
        operation_description='Return information about place by place_id.'
    )
    def get(self, request, format=None):
        serializer = PlaceGetSerializer(data=request.query_params)
        # prevent_using_non_active_account(user)
        offset_0 = 0
        offset_n = 5
        if serializer.is_valid():
            validated_data = serializer.validated_data
            place_id = validated_data.get('place_id')
            places = Place.active.filter(
                id=place_id,
                status__in=[
                    PlaceStatusE.SUBSCRIBER,
                    PlaceStatusE.PUBLISHED,
                    PlaceStatusE.DRAFT,
                    PlaceStatusE.IN_DOUBT
                ]
            )
            if not places.exists():
                raise ResultEmpty

            place = places.first()
            if place.status not in [PlaceStatusE.PUBLISHED,
                                    PlaceStatusE.SUBSCRIBER]:
                raise ResultErrorError("Place is not validated yet.", 102)

            blocked_users = []
            if request.user.is_authenticated:
                blocked_users = BlockUser.objects.filter(
                    user=request.user).values_list('block_user_id')
            likevotes = LikeVote.active.filter(
                place=place
            ).exclude(  # likevotes from blocked users
                author_id__in=blocked_users
            ).order_by(
                '-created_time')[offset_0: offset_n]
            comments = place.comments.filter(
                is_archived=False
            ).exclude(
                author_id__in=blocked_users
            ).order_by(
                '-created_time'
            ).select_related('author')[offset_0: offset_n]

            likevote_last_id = likevotes[
                len(likevotes) - 1].id if likevotes else None  # noqa
            comment_last_id = comments[
                len(comments) - 1].id if comments else None  # noqa
            comments_out = []
            likevotes_out = []

            if comments:
                comments_out = CommentSerializer(comments, many=True).data
            if likevotes:
                likevotes_out = LikeVoteSerializer(likevotes, many=True).data

            place_out = FullPlaceSerializer(
                place, context={'request': request}
            ).data

            place_images = list(PlaceImage.objects.filter(place_id=place_id, is_archived=False,
                                                          image_area__isnull=False)
                                .order_by('image_area', 'abstractimage_ptr_id', )
                                .values_list('image_file', flat=True))
            base_url = "https://{0}{1}".format(os.getenv("RAISIN_AWS_STORAGE_BUCKET_NAME"), settings.MEDIA_URL)
            if len(place_images) > 0:
                place_out['images'] = ["{0}{1}".format(base_url, x) for x in place_images]

            formitable_url = None
            owner = UserProfile.objects.filter(id=place_out['venue_owner_id']).last()
            if owner:
                formitable_url = owner.formitable_url
            if formitable_url == '':
                formitable_url = None
            place_out['formitable_url'] = formitable_url

            place_out['i_like_it'] = request.user.__str__() in [x['author'] for x in likevotes_out]

            food_posts_count, food_posts = get_food_posts(request, place)

            wine_posts_result = {}

            for wp_type in [
                VenueWineTypeE.WHITE,
                VenueWineTypeE.RED,
                VenueWineTypeE.PINK,
                VenueWineTypeE.ORANGE,
                VenueWineTypeE.SPARKLING
            ]:
                wine_posts_count, wine_posts = get_wine_posts(
                    request, place, limit=None, wp_type=wp_type,
                    minimal=True
                )

                wine_posts_result[wp_type] = {
                    'count': wine_posts_count, 'items': wine_posts
                }

            data = {
                'owner_url_pro': get_owner_url_pro(request.user, place),
                'place': place_out,
                'likevotes': likevotes_out,
                'comments': comments_out,
                'likevote_last_id': likevote_last_id,
                'comment_last_id': comment_last_id,
                'wines': wine_posts_result,
                'foods': {
                    'count': food_posts_count,
                    'items': food_posts
                },
            }
            response_data = {'data': data}
            fill_default_response_data(response_data)
            return Response(response_data)

        return Response()

    @swagger_auto_schema(
        request_body=PlaceGetSerializer,
        operation_summary='Return information about place by place_id.',
        operation_description='The method POST is deprecated for this '
                              'endpoint.',
        deprecated=True,
        security=[]
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '/api/places/place')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)


# /api/places/place/add
@signed_api(
    FormClass=None, token_check=True, json_used=False,
    success_status=200, ensure_ascii=True
)
def add_place(request):
    user = request.user
    prevent_using_non_active_account(user)
    if request.method == 'POST':
        form1 = PlaceFileUploadForm(request.POST, request.FILES)
        files = request.FILES.getlist('images')
        if form1.is_valid():
            # done this way to enable form validation despite the lack of
            # "data" field - I want to return field validation information at
            # all times (no "data" field = all fields non-valid)
            try:
                data_json = json.loads(form1.cleaned_data['data'])
            except ValueError:
                data_json = {}

            form2 = PlaceCreateForm(data_json)
            if form2.is_valid():
                cd = form2.cleaned_data
                full_street_address = "%s %s" % (
                    cd['street_address'],
                    str(cd['house_number'])
                ) if cd['house_number'] else cd['street_address']
                place = Place(
                    author=user,
                    name=cd['name'],
                    type=cd['type'],

                    is_bar=cd['is_bar'],
                    is_restaurant=cd['is_restaurant'],
                    is_wine_shop=cd['is_wine_shop'],

                    description=cd['description'],
                    street_address=cd['street_address'],
                    full_street_address=full_street_address,

                    house_number=cd['house_number'],
                    zip_code=cd['zip_code'],
                    city=cd['city'],
                    country=str(cd['country']),
                    country_iso_code=str(
                        cd['country_iso_code']
                    ) if cd['country_iso_code'] else None,
                    is_30_p_natural_already=(True if ('is_30_p_natural_already' in cd and cd['is_30_p_natural_already'])
                                             else False),
                    phone_number=cd['phone_number'],
                    website_url=cd['website_url'],
                    email=cd['email'],
                    latitude=cd['latitude'],
                    longitude=cd['longitude'],
                    pin_latitude=cd['latitude'],
                    pin_longitude=cd['longitude'],

                    social_facebook_url=cd['social_facebook_url'],
                    social_twitter_url=cd['social_twitter_url'],
                    social_instagram_url=cd['social_instagram_url'],
                    status=PlaceStatusE.DRAFT,
                    src_info=PlaceSourceInfoE.SUBMITTED_ON_APP
                )

                if str(cd['latitude']) and str(cd['longitude']):
                    address_data_latlng = get_address_data_for_latlng(
                        cd['latitude'], cd['longitude']
                    )
                    if address_data_latlng['country']:
                        place.country = address_data_latlng['country']
                    if address_data_latlng['iso']:
                        place.country_iso_code = address_data_latlng['iso']
                    if address_data_latlng['city'] and address_data_latlng['quality'] < 3:  # noqa
                        place.city = address_data_latlng['city']
                    if address_data_latlng['state'] and address_data_latlng['quality'] < 3:  # noqa
                        place.state = address_data_latlng['state']

                place.save(update_timezone=True)
                place.refresh_from_db()

                if files:
                    ordering = 0
                    file_main = files.pop(0)
                    main_image = PlaceImage(image_file=file_main, place=place, author=user, ordering=ordering)
                    main_image.save()
                    # make_image_prefixed(main_image) - was it naming feature?
                    # upload_to_bucket(main_image)
                    place.main_image = main_image
                    place.save()
                    place.refresh_from_db()
                    ordering += 1
                    for file_item in files:
                        image = PlaceImage(image_file=file_item, place=place, author=user, ordering=ordering)
                        image.save()
                        # upload_to_bucket(image)
                        # make_image_prefixed(image) - was it naming feature?
                        ordering += 1

                place.refresh_from_db()
                place.update_user_mentions(
                    cd['mentions'] if cd['mentions'] else None, save_item=True
                )

                return FullPlaceSerializer(place, context={
                    'request': request
                }).data
            else:
                raise WrongParametersError(_("Wrong parameters."), form2)
        raise WrongParametersError(_("Wrong parameters."), form1)


# /api/places/place/edit
@signed_api(
    FormClass=None, token_check=True, json_used=False,
    success_status=200, ensure_ascii=True
)
def edit_place(request):
    user = request.user
    prevent_using_non_active_account(user)
    if request.method == 'POST':
        form1 = PlaceFileUploadForm(request.POST, request.FILES)
        if form1.is_valid():
            # done this way to enable form validation despite the lack of
            # "data" field - I want to return field validation information at
            # all times (no "data" field = all fields non-valid)
            try:
                data_json = json.loads(form1.cleaned_data['data'])
            except ValueError:
                data_json = {}

            form2 = PlaceEditForm(data_json)
            place = None
            if form2.is_valid():
                cd = form2.cleaned_data
                if cd['place_id']:
                    place = Place.active.get(
                        id=cd['place_id'],
                        status__in=[
                            PlaceStatusE.SUBSCRIBER,
                            PlaceStatusE.PUBLISHED,
                            PlaceStatusE.DRAFT,
                            PlaceStatusE.IN_DOUBT
                        ]
                    )
                elif cd['tl_id']:
                    tl_item = TimeLineItem.active.get(id=cd['tl_id'])

                    if tl_item.item_type == TimeLineItemTypeE.PLACE:
                        place = Place.active.get(
                            id=tl_item.cached_item['id'],
                            status__in=[
                                PlaceStatusE.SUBSCRIBER,
                                PlaceStatusE.PUBLISHED,
                                PlaceStatusE.DRAFT,
                                PlaceStatusE.IN_DOUBT
                            ]
                        )
                    else:
                        raise ResultErrorError(
                            "wrong item type in TL ITEM - place expected", 102
                        )
                if not place:
                    raise ResultErrorError("place to edit was not found", 102)

                place.name = cd['name']
                place.description = cd['description']
                place.is_bar = cd['is_bar']
                place.is_restaurant = cd['is_restaurant']
                place.is_wine_shop = cd['is_wine_shop']

                full_street_address = "%s %s" % (
                    cd['street_address'],
                    str(cd['house_number'])
                ) if cd['house_number'] else cd['street_address']
                place.street_address = cd['street_address']
                place.full_street_address = full_street_address
                place.house_number = cd['house_number']
                place.zip_code = cd['zip_code']

                place.city = cd['city']
                place.country = str(cd['country'])
                place.country_iso_code = str(
                    cd['country_iso_code']
                ) if cd['country_iso_code'] else None

                place.phone_number = cd['phone_number']
                place.website_url = cd['website_url']
                place.email = cd['email']

                place.latitude = cd['latitude']
                place.longitude = cd['longitude']
                place.pin_latitude = cd['latitude']
                place.pin_longitude = cd['longitude']

                if str(cd['latitude']) and str(cd['longitude']):
                    address_data_latlng = get_address_data_for_latlng(
                        cd['latitude'], cd['longitude']
                    )
                    if address_data_latlng['country']:
                        place.country = address_data_latlng['country']
                    if address_data_latlng['iso']:
                        place.country_iso_code = address_data_latlng['iso']
                    if address_data_latlng['city'] and address_data_latlng['quality'] < 3:  # noqa
                        place.city = address_data_latlng['city']
                    if address_data_latlng['state'] and address_data_latlng['quality'] < 3:  # noqa
                        place.state = address_data_latlng['state']

                place.social_facebook_url = cd['social_facebook_url']
                place.social_twitter_url = cd['social_twitter_url']
                place.social_instagram_url = cd['social_instagram_url']
                place.status = PlaceStatusE.DRAFT
                place.delete_related_items()
                place.save(update_timezone=True)
                place.refresh_from_db()

                place.update_user_mentions(
                    cd['mentions'] if cd['mentions'] else None, save_item=True
                )
                return FullPlaceSerializer(place, context={'request': request})
            else:
                raise WrongParametersError(_("Wrong parameters."), form2)
        raise WrongParametersError(_("Wrong parameters."), form1)


# /api/places/place/all-wines
class WinesForPlaceView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        security=[],
        query_serializer=WinesForPlaceSerializer,
        operation_summary='Return wines for place by place_id and type.',
        operation_description='The method POST is deprecated for this '
                              'endpoint.',
    )
    def get(self, request, format=None):
        serializer = WinesForPlaceSerializer(data=request.query_params)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            venue = Place.active.get(id=validated_data.get('place_id'))
            data = get_wine_posts(
                request, venue, validated_data.get('limit'), validated_data.get('type')
            )[1]
            response_data = {'data': data}
            fill_default_response_data(response_data)
            return Response(response_data)

    @swagger_auto_schema(
        security=[],
        request_body=WinesForPlaceSerializer,
        deprecated=True,
        operation_summary='Return wines for place by place_id and type.',
        operation_description='The method POST is deprecated for this '
                              'endpoint.',
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '/api/places/place/all-wines')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)


# /api/places/place/all-foods
class FoodsForPlaceView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        security=[],
        query_serializer=PlaceGetSerializer,
        operation_summary='Return all foods for place by place_id.',
        operation_description='Return all foods for place by place_id.'
    )
    def get(self, request, format=None):
        serializer = PlaceGetSerializer(data=request.query_params)

        if serializer.is_valid():
            validated_data = serializer.validated_data
            venue = Place.active.get(id=validated_data.get('place_id'))
            data = get_food_posts(request, venue)[1]
            response_data = {'data': data}
            fill_default_response_data(response_data)
            return Response(response_data)

    @swagger_auto_schema(
        security=[],
        request_body=PlaceGetSerializer,
        deprecated=True,
        operation_summary='Return all foods for place by place_id.',
        operation_description='The method POST is deprecated for this '
                              'endpoint.',
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '/api/places/place/all-foods')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)


def uniq_chain(*args, **kwargs):
    seen = set()
    for x in chain(*args, **kwargs):
        if x in seen:
            continue
        seen.add(x)
        yield x


# /api/places/place/is-it-an-already-posted-wine
class PostedWineView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, *args, **kwargs):
        wine_name = self.request.query_params.get('wine_name')
        winemaker_name = self.request.query_params.get('winemaker_name')
        place_id = int(self.request.query_params.get('place_id'))

        if not (
                wine_name and
                winemaker_name and
                place_id and place_id > 0
        ):
            return Response(
                {'detail': 'Incorrect query parameters.',
                 'status_code': 400}
            )
        wine_name = wine_name.strip()
        winemaker_name = winemaker_name.strip()
        place = Place.active.get(pk=place_id)
        posts = place.posts
        year = None
        if self.request.query_params.get('year'):
            year = int(self.request.query_params.get('year'))
            if not 1900 < year <= datetime.datetime.now().year:
                return Response(
                    {'detail': 'The year value is not allowed. Use the value '
                               'for the year 1900 to the present.',
                     'status_code': 400}
                )

        if posts and year:
            existed_posts = posts.filter(
                is_archived=False,
                type=PostTypeE.WINE,
                author=place.owner,
                wine__name__unaccent__iexact=wine_name,
                wine__winemaker__name__unaccent__iexact=winemaker_name,
                wine_year=year
            )
        elif posts:
            existed_posts = posts.filter(
                is_archived=False,
                type=PostTypeE.WINE,
                author=place.owner,
                wine__name__unaccent__iexact=wine_name,
                wine__winemaker__name__unaccent__iexact=winemaker_name
            )
        else:
            return Response(
                {'detail': 'There are no wineposts for this place_id.',
                 'status_code': 404}
            )
        if existed_posts:
            return Response({'detail': True, 'status_code': 200})
        else:
            return Response({'detail': False, 'status_code': 200})


class WinesFoodsClosestVenuesView(APIView):
    permission_classes = [AllowAny]
    lat_paris, lng_paris = 48.879083, 2.388551

    @swagger_auto_schema(
        query_serializer=RandomFoodsWinesGeoSerializer,
        operation_summary='Return list of wines, foods, closest venues',
        operation_description='Return list of wines, foods, closest venues',
        security=[]
    )
    def get(self, request, format=None):

        user = request.user
        owner = user if user.is_authenticated and user.type == UserTypeE.OWNER else None

        # prevent_using_non_active_account(user)
        pairs_final_wines, pairs_final_foods = [], []

        serializer = RandomFoodsWinesGeoSerializer(data=request.query_params)
        msg = "get_wines_foods_closest_venues:: REQUEST METHOD {} REQUEST DATA {}"
        log.debug(msg.format(request.method, request.data))

        if not serializer.is_valid():
            raise WrongParametersError(_("Wrong parameters."), serializer)

        validated_data = serializer.validated_data
        lat = validated_data.get('latitude', self.lat_paris)
        lng = validated_data.get('longitude', self.lng_paris)

        if lat == lng and (lat == 0.0 or lat is None):
            lat, lng = self.lat_paris, self.lng_paris

        limit = validated_data.get('limit', 10)

        wp_venues, fp_venues = get_closest_venues(lat, lng, limit, owner=owner)

        for venue in wp_venues:
            if venue.latest_wp:
                wine_post = Post.objects.get(pk=venue.latest_wp)

                pairs_final_wines.append({
                    'id': venue.id,
                    'venue': PlaceWithLocationSerializer(
                        venue, context={'request': request}
                    ).data,
                    'wine': WinePostAPISerializer(
                        wine_post, context={'request': request}
                    ).data
                })

        for venue in fp_venues:
            if venue.latest_fp:
                food_post = Post.objects.get(pk=venue.latest_fp)

                pairs_final_foods.append({
                    'id': venue.id,
                    'venue': PlaceWithLocationSerializer(
                        venue, context={'request': request}
                    ).data,
                    'food': FoodPostAPISerializer(
                        food_post, context={'request': request}
                    ).data
                })

        venues = sorted(
            uniq_chain(wp_venues, fp_venues),
            key=lambda data: data.distance
        )

        # legacy structure
        data = {
            'wines': pairs_final_wines,
            'foods': pairs_final_foods,
            'venues': PlaceWithLocationSerializer(
                venues[0:limit], many=True, context={'request': request}
            ).data,
            'recent_wine_posts': get_recent_wine_posts(request),
        }
        response_data = {'data': data}
        fill_default_response_data(response_data)
        return Response(response_data)

    @swagger_auto_schema(
        request_body=RandomFoodsWinesGeoSerializer,
        operation_summary='Return list of wines, foods, closest venues.',
        operation_description='The method POST is deprecated for this endpoint.'
                              '/api/places/wines-foods-closest-venues',
        deprecated=True,
        security=[]
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '/api/places/wines-foods-closest-venues')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)


def check_return_images_ios(request):
    if 'HTTP_USER_AGENT' in request.META:
        agent = request.META['HTTP_USER_AGENT']
        x = re.match(r'(.+?)/(.+?)\s', agent)
        y = re.search('iOS', agent)
        if x and y:
            ver = re.sub('[.]', '', x.groups()[1])
            if len(ver) == 3 and int(ver) <= 420:
                return False
            elif len(ver) == 2 and int(ver) <= 42:
                return False
            elif len(ver) == 1:
                return False

    # elif 'x-app-app-version' in request.META:
    #     ver = request.META['x-app-app-version']
    #     ver = re.sub('[.]', '', ver)
    #     if len(ver) == 3 and int(ver) <= 420:
    #         return False
    #     elif len(ver) == 2 and int(ver) <= 42:
    #         return False
    #     elif len(ver) == 1:
    #         return False

    return True


# /api/places/geo = obsolete, deprecated old endpoint
@signed_api(
    FormClass=PlaceListGeoForm, token_check=True,
    log_response_data=False, ensure_ascii=True
)
def get_place_list_geo(request):
    log.debug("REQUEST META FROM LIST GEO %s ", request.META)

    user = request.user
    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form = request.form

        if form.is_valid():
            qs = Place.active.filter(
                status__in=[
                    PlaceStatusE.SUBSCRIBER,
                    PlaceStatusE.PUBLISHED
                ]
            ).prefetch_related('place_images')
            # print(qs.query)
            return {
                'items': MinimalPlaceSerializer(
                    qs, many=True, context={'request': request}
                ).data
            }
    raise WrongParametersError(_("Wrong parameters."), form)


# DRF: /api/places/geo
class PlaceListGeoView(ListCreateAPIView):
    """
    Get a places list
    """
    permission_classes = [AllowAny]
    queryset = Place.app_active.all()
    serializer_class = MinimalPlace2Serializer
    pagination_class = PlacePagination
    authentication_classes = (CustomTokenAuthentication,)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('subscription', 'main_image', 'owner')
        qs = qs.annotate(
            test_place_images_with_area=ArrayAgg(
                'place_images__image_file',
                filter=Q(place_images__is_archived=False,
                         place_images__image_area__isnull=False),
                # distinct=True,
                ordering=('place_images__image_area',
                          'place_images__abstractimage_ptr_id',)
            )
        )
        qs = qs.annotate(
            test_place_images_without_area=ArrayAgg(
                'place_images__image_file',
                filter=Q(place_images__is_archived=False,
                         place_images__image_area__isnull=True),
                # distinct=True
                ordering=('place_images__image_area',
                          'place_images__abstractimage_ptr_id',),
            )
        )

        # blocked users
        # blocked_users = []
        # if self.request.user.is_authenticated:
        #     blocked_users = BlockUser.objects.filter(
        #         user=self.request.user
        #     ).values_list('block_user_id', flat=True)
        #
        # if blocked_users:
        #     # exclude like votes from blocked users
        #     qs = qs.annotate(likevotes_count=Count(
        #         'like_votes',
        #         filter=Q(like_votes__is_archived=False),
        #         exclude=Q(author_id__in=blocked_users),
        #         distinct=True
        #     ))
        #
        #     # exclude comments from blocked users
        #     qs = qs.annotate(comments_count=Count(
        #         'comments',
        #         filter=Q(comments__is_archived=False),
        #         exclude=Q(author_id__in=blocked_users),
        #         distinct=True
        #     ))
        # else:
        #     # exclude like votes from blocked users
        #     qs = qs.annotate(likevotes_count=Count('like_votes', distinct=True))
        #
        #     # exclude comments from blocked users
        #     qs = qs.annotate(comments_count=Count('comments', distinct=True))

        return qs

    # may be needed by the old DRF version
    # def list(self, request, *args, **kwargs):
    #     return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


# /api/places/open-closed-status
@signed_api(
    FormClass=PlaceOpenClosedStatusForm, token_check=True,
    log_response_data=False, ensure_ascii=True
)
def get_place_list_open_closed_status(request):
    user = request.user
    prevent_using_non_active_account(user)

    form = request.form
    if request.method == 'POST':
        if form.is_valid():
            cd = form.cleaned_data

            if cd.get('place_id'):
                qs = Place.active.filter(
                    pk=cd['place_id'],
                    status__in=[
                        PlaceStatusE.SUBSCRIBER,
                        PlaceStatusE.PUBLISHED
                    ]
                )
            else:
                qs = Place.active.filter(status__in=[
                    PlaceStatusE.SUBSCRIBER,
                    PlaceStatusE.PUBLISHED
                ])

            if not qs.count():
                raise ResultEmpty

            return {
                'items': MinimalPlaceSerializer(
                    qs, many=True, context={'request': request}
                ).data
            }
    raise WrongParametersError(_("Wrong parameters."), form)


# DRF /api/places/open-closed-status
class PlaceListOpenClosedStatusView(ListCreateAPIView):
    queryset = Place.active.all().order_by('name')
    permission_classes = [IsAuthenticated]
    serializer_class = MinimalPlace2Serializer
    pagination_class = PlacePagination
    authentication_classes = (CustomTokenAuthentication,)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('subscription', 'main_image', 'owner')
        qs = qs.filter(status__in=[
            PlaceStatusE.SUBSCRIBER,
            PlaceStatusE.PUBLISHED
        ])
        qs = qs.annotate(
            test_place_images_with_area=ArrayAgg(
                'place_images__image_file',
                filter=Q(place_images__is_archived=False,
                         place_images__image_area__isnull=False),
                # distinct=True,
                ordering=('place_images__image_area',
                          'place_images__abstractimage_ptr_id',),
            )
        )
        qs = qs.annotate(
            test_place_images_without_area=ArrayAgg(
                'place_images__image_file',
                filter=Q(place_images__is_archived=False,
                         place_images__image_area__isnull=True),
                distinct=True
            )
        )

        # blocked users
        blocked_users = {}
        if self.request.user.is_authenticated:
            blocked_users = BlockUser.objects.filter(
                user=self.request.user).values_list('block_user_id')

        # exclude like votes from blocked users
        qs = qs.annotate(likevotes_count=Count(
            'like_votes',
            filter=Q(like_votes__is_archived=False),
            exclude=Q(author_id__in=blocked_users),
            distinct=True
        )
        )

        # exclude comments from blocked users
        qs = qs.annotate(comments_count=Count(
            'comments',
            filter=Q(comments__is_archived=False),
            exclude=Q(author_id__in=blocked_users),
            distinct=True
        )
        )
        return qs

    # may be needed by the old DRF version
    # def list(self, request, *args, **kwargs):
    #     return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
