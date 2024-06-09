from __future__ import absolute_import

import datetime as dt
import json
import logging

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from reports.models import BlockUser
from web.authentication import CustomTokenAuthentication

from web.constants import (AppEnvE, PlaceStatusE, PostStatusE, PostTypeE,
                           TimeLineItemTypeE, UserStatusE, UserTypeE,
                           WinemakerStatusE, WineStatusE,
                           get_post_status_for_wine_status)
from web.forms.api_forms import (FileUploadForm,
                                 GeneralPostCreateForm, GeneralPostEditForm,
                                 PostDeleteForm, PostListForm,
                                 WinepostCreateForm, WinepostCreateNewForm,
                                 WinepostEditForm)
from web.models import (Comment, DrankItToo, LikeVote, Place, Post, PostImage,
                        TimeLineItem, TotalStats, UserProfile, Wine, WineImage,
                        Winemaker, get_parent_post_for_wine,
                        select_star_review_for_winepost)
from web.serializers.comments_likes import (CommentSerializer,
                                            DrankItTooSerializer,
                                            LikeVoteSerializer)
from web.serializers.posts import FullPostSerializer, PostGetSerializer, \
    VuforiaScansCountSerializer
from web.utils.api_handling import signed_api, fill_default_response_data
from web.utils.exceptions import (ResultEmpty, ResultErrorError,
                                  WrongParametersError)
from web.utils.model_object_tools import archive_images_fn
from web.utils.model_tools import (get_filter_criteria_for_order_last_id,
                                   make_winepost_title)
from web.utils.pro_utils import get_owner_currency
from web.utils.views_common import (is_privileged_account,
                                    list_control_parameters_by_form,
                                    list_last_id, prevent_editing_not_own_item,
                                    prevent_using_non_active_account)
from web.utils.yearly_data import update_yearly_data_with_parent_post

log = logging.getLogger(__name__)
log_add_wp = logging.getLogger("add_wp_log")


def save_vuf_wine_data(vuf_wine_id, post):
    vuf_wines = Wine.objects.filter(id=vuf_wine_id)
    if vuf_wines:
        vuf_wine = vuf_wines[0]
        vuf_post = get_parent_post_for_wine(vuf_wine)
        # there is parent post for vuf_wine - GOOD! Setting it as matched
        if vuf_post:
            post.vuf_match_wine = vuf_wine
            post.vuf_match_post = vuf_post
            post.save()
            post.refresh_from_db()
        # there is NO parent post for vuf_wine - NOT GOOD!
        # But there is ref_image which
        # contains post - GOOD! Using this post from ref_image
        elif vuf_wine.ref_image and vuf_wine.ref_image.post:
            vuf_post = vuf_wine.ref_image.post
            post.vuf_match_wine = vuf_wine
            post.vuf_match_post = vuf_post
            post.save()
            post.refresh_from_db()
        # neither parent post, nor post for ref_image - quite BAD!
        # But checking further...
        else:
            vuf_posts = Post.objects.filter(wine=vuf_wine)
            # other posts (non-parent, non-referrer) exist for this wine
            # SECOND BEST! using the first of those as "matched"
            if vuf_posts:
                vuf_post = vuf_posts[0]
                post.vuf_match_wine = vuf_wine
                post.vuf_match_post = vuf_post
                post.save()
                post.refresh_from_db()


# /api/posts/delete
@signed_api(
    FormClass=PostDeleteForm, token_check=True,
    json_used=True, success_status=200
)
def delete_post(request):
    user = request.user
    prevent_using_non_active_account(user)
    item = None

    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data
            if cd['post_id']:
                item = Post.active.get(id=cd['post_id'])
            elif cd['tl_id']:
                tl_item = TimeLineItem.active.get(id=cd['tl_id'])
                if tl_item.item_type == TimeLineItemTypeE.POST:
                    item = Post.active.get(id=tl_item.cached_item['id'])
                else:
                    raise ResultErrorError(
                        "wrong item type in TL ITEM - post expected", 102
                    )

            if not item:
                raise ResultErrorError("item to delete was not found", 102)
            prevent_editing_not_own_item(user, item)

            if item.type == PostTypeE.WINE and item.is_parent_post and \
                    settings.MOVE_PARENT_POSTS_ON_APP_DELETE and \
                    settings.ADMIN_PROFILE_USERNAME:
                admin_profiles = UserProfile.active.filter(
                    username=settings.ADMIN_PROFILE_USERNAME)
                if admin_profiles:
                    admin_profile = admin_profiles[0]
                    item.author = admin_profile
                    item.save()
                    item.delete_related_items()
                    item.delete_from_timeline()
                else:
                    item.archive()
            else:
                item.archive()
                item.refresh_from_db()

            item_dict = FullPostSerializer(
                item, context={'request': request, 'include_wine_data': True}
            ).data

            return {'archived_item': item_dict}
        else:
            raise WrongParametersError(_("Wrong parameters."), form)


# /api/posts/post
class PostView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = (CustomTokenAuthentication,)

    @swagger_auto_schema(
        query_serializer=PostGetSerializer,
        operation_summary='Return info about post by post_id',
        operation_description='Return info about post by post_id',
        security=[]
    )
    def get(self, request, format=None):
        serializer = PostGetSerializer(data=request.query_params)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            post = Post.active.get(id=validated_data.get('post_id'))

            offset_0 = 0
            offset_n = 5

            blocked_users = []
            if request.user.is_authenticated:
                blocked_users = BlockUser.objects.filter(
                    user=request.user).values_list('block_user_id')
            likevotes = LikeVote.active.filter(
                post=post
            ).exclude(  # likevotes from blocked users
                author_id__in=blocked_users
            ).order_by('-created_time')[offset_0: offset_n]
            comments = Comment.active.filter(
                post=post
            ).exclude(  # comments from blocked users
                author_id__in=blocked_users
            ).order_by('-created_time')[offset_0: offset_n]
            drank_it_toos = DrankItToo.active.filter(
                post=post
            ).exclude(  # drank it toos from blocked users
                author_id__in=blocked_users
            ).order_by('-created_time')[offset_0: offset_n]

            likevote_last_id = likevotes[len(likevotes)-1].id if likevotes else None  # noqa
            comment_last_id = comments[len(comments)-1].id if comments else None  # noqa
            drank_it_too_last_id = drank_it_toos[len(drank_it_toos)-1].id if drank_it_toos else None  # noqa

            likevotes_out = LikeVoteSerializer(likevotes, many=True).data
            comments_out = CommentSerializer(comments, many=True).data
            drank_it_toos_out = DrankItTooSerializer(
                drank_it_toos, many=True
            ).data

            post_dict = FullPostSerializer(post, context={
                'request': request,
                'include_wine_data': True,
                'include_winemaker_data': True,
                'fallback_wine_image': True
            }).data

            post_dict['i_like_it'] = request.user.__str__() in [x['author'] for x in likevotes_out]
            post_dict['i_drank_it_too'] = request.user.__str__() in [x['author'] for x in drank_it_toos_out]

            data = {
                'post': post_dict,
                'likevotes': likevotes_out,
                'comments': comments_out,
                'drank_it_toos': drank_it_toos_out,

                'likevote_last_id': likevote_last_id,
                'comment_last_id': comment_last_id,
                'drank_it_too_last_id': drank_it_too_last_id,
            }
            response_data = {'data': data}
            fill_default_response_data(response_data)
            return Response(response_data)

    @swagger_auto_schema(
        request_body=PostGetSerializer,
        operation_summary='Return info about post by post_id',
        operation_description='The method POST is deprecated for this '
                              'endpoint.',
        deprecated=True,
        security=[]
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '/api/posts/post')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)


# /api/posts/wine/add
@signed_api(
    FormClass=None, token_check=True, json_used=False, success_status=200
)
def add_winepost(request):
    log.debug("add winepost")
    matching_existing_wine = True
    user = request.user
    prevent_using_non_active_account(user)
    winepost = None
    log_add_wp.debug("ADDDING WINEPOST OLD ")

    if request.method == 'POST':
        form1 = FileUploadForm(request.POST, request.FILES)
        files = request.FILES.getlist('images')
        if form1.is_valid():
            log_add_wp.debug("ADDDING WINEPOST OLD FORM1 VALID")
            try:
                data_json = json.loads(form1.cleaned_data['data'])
            except ValueError:
                data_json = {}

            # -- if data_json: --
            form2 = WinepostCreateForm(data_json)
            if form2.is_valid():
                log_add_wp.debug("ADDDING WINEPOST OLD FORM2 VALID")
                cd = form2.cleaned_data
                place = None
                if cd['place_id']:
                    places = Place.active.filter(
                        pk=cd['place_id'],
                        status__in=[PlaceStatusE.PUBLISHED,
                                    PlaceStatusE.SUBSCRIBER]
                    )
                    if places:
                        place = places[0]

                # find (filter) wine by name
                # if exists (wine_from_db) and our parameters don't differ from wine_from_db:
                #   - add a winepost with relation to the wine from db (status=DRAFT)
                #   - add the images (if any) as post images only, not wine images
                # if the wine does not exist (wine_from_db=None) or our parameters differ from wine_from_db:
                #   - add a new Wine entity item (status=ON_HOLD)
                #   - add images if any provided as wine images only (no need to duplicate them in wine post)
                #   - add winepost with relation to wine (status=DRAFT)
                # BOTH: push winepost to timeline
                exact_wine_found = False
                winemaker = None

                if cd['winemaker_id']:
                    winemaker = Winemaker.active.get(pk=cd['winemaker_id'])
                elif cd['winemaker_name']:
                    winemakers = Winemaker.active.filter(
                        name__unaccent__iexact=cd['winemaker_name'])
                    if winemakers:
                        winemaker = winemakers[0]

                if winemaker:
                    wines_from_db = Wine.active.filter(
                        name__unaccent__iexact=cd['name'],
                        designation__unaccent__iexact=cd['designation'],
                        grape_variety__unaccent__iexact=cd['grape_variety'],
                        region__unaccent__iexact=cd['region'],
                        domain__unaccent__iexact=cd['domain'],
                        color=int(cd['color']) if cd['color'] else None,
                        is_sparkling=cd['is_sparkling'],
                        winemaker=winemaker
                    ).order_by('-id')
                    if wines_from_db:
                        wine_from_db = wines_from_db[0]
                        exact_wine_found = True
                        wp_status = get_post_status_for_wine_status(
                            wine_from_db.status
                        )
                        winepost = Post(
                            author=user,
                            status=wp_status,
                            type=PostTypeE.WINE,
                            title=make_winepost_title(cd['name'], cd['year']),
                            description=cd['description'],
                            grape_variety=cd['grape_variety'],
                            wine=wine_from_db,
                            wine_year=cd['year'],
                            place=place,
                            free_so2=None,
                            total_so2=None
                        )
                        winepost.save()
                        winepost.refresh_from_db()

                # exact wine hasn't been found in DB - adding a new wine
                if not exact_wine_found:
                    matching_existing_wine = False
                    if not winemaker:
                        # I know this is already handled in the form
                        # but I wanted this to be clear here,
                        # eg. if something in the form changed
                        if not cd['winemaker_name']:
                            raise WrongParametersError(
                                "No winemaker data", form2
                            )
                        else:
                            winemaker = Winemaker(
                                name=cd['winemaker_name'],
                                region=cd['region'],
                                domain=cd['domain'],
                                author=user,
                                status=WinemakerStatusE.DRAFT
                            )
                            winemaker.save()
                            winemaker.refresh_from_db()

                    new_wine = Wine(
                        author=user,
                        status=WineStatusE.ON_HOLD,
                        name=cd['name'],
                        domain=cd['domain'],
                        designation=cd['designation'],
                        grape_variety=cd['grape_variety'],
                        region=cd['region'],
                        color=int(cd['color']) if cd['color'] else None,
                        is_sparkling=cd['is_sparkling'],
                        winemaker=winemaker,
                        similiar_wine_exists=cd['similiar_wine_exists'],
                        similiar_wine_id=cd['similiar_wine_id']
                    )
                    new_wine.save()
                    new_wine.refresh_from_db()

                    winepost = Post(
                        author=user,
                        status=PostStatusE.DRAFT,
                        type=PostTypeE.WINE,
                        is_parent_post=True,

                        title=make_winepost_title(cd['name'], cd['year']),
                        description=cd['description'],
                        grape_variety=cd['grape_variety'],
                        wine=new_wine,
                        wine_year=cd['year'],
                        place=place,
                        free_so2=None,
                        total_so2=None
                    )
                    winepost.save()
                    winepost.refresh_from_db()

                if not winepost:
                    return {}

                # handling files for wine or winepost
                if files:
                    file_main = files.pop(0)
                    main_image = PostImage(
                        image_file=file_main, post=winepost, author=user
                    )
                    main_image.save()
                    winepost.main_image = main_image
                    winepost.save()
                    for file_item in files:
                        image = PostImage(
                            image_file=file_item, post=winepost, author=user
                        )
                        image.save()

                if cd['vuf_wine_id']:
                    save_vuf_wine_data(cd['vuf_wine_id'], winepost)
                    winepost.refresh_from_db()

                if cd['foursquare_place_name']:
                    winepost.foursquare_place_name = cd['foursquare_place_name']

                if cd['foursquare_place_url']:
                    winepost.foursquare_place_url = cd['foursquare_place_url']

                if cd['vuf_wine_id'] or cd['is_scanned']:
                    winepost.is_scanned = True
                    winepost.save()
                    winepost.refresh_from_db()

                winepost.push_to_timeline(
                    is_new=True, is_sticky=is_privileged_account(user)
                )
                winepost.update_user_mentions(
                    cd['mentions'] if cd['mentions'] else None,
                    save_item=True
                )
                winepost.refresh_from_db()
                winepost_dict = FullPostSerializer(
                    winepost, context={
                        'request': request,
                        'include_wine_data': True,
                        'include_winemaker_data': True
                    }
                ).data
                winepost_dict['matching_existing_wine'] = matching_existing_wine

                select_star_review_for_winepost(winepost, tested_post=winepost)

                # if event is currently going on
                # and the pinpointed place has free_glass = True:
                if place and place.free_glass:
                    place.free_glass_last_action_date = dt.datetime.now()
                    place.save_keep_modified_dt()
                    place.refresh_from_db()
                    # cur_events = FreeGlassEvent.active.all()
                    # if cur_events:
                    #     cur_event = cur_events[0]
                    #     date_today = dt.date.today()
                    #     if cur_event.start_date.date() <= date_today <= cur_event.end_date.date():
                    #         SenderNotifier().send_with_free_glass(request.user, place)
                return winepost_dict
            else:
                raise WrongParametersError(_("Wrong parameters."), form2)
        raise WrongParametersError(_("Wrong parameters."), form1)


# /api/posts/general/add
@signed_api(
    FormClass=None, token_check=True, json_used=False, success_status=200
)
def add_general_post(request):
    user = request.user

    prevent_using_non_active_account(user)
    place = None

    if request.method == 'POST':
        form1 = FileUploadForm(request.POST, request.FILES)
        files = request.FILES.getlist('images')
        if form1.is_valid():
            try:
                data_json = json.loads(form1.cleaned_data['data'])
            except ValueError:
                data_json = {}

            form2 = GeneralPostCreateForm(data_json)
            if form2.is_valid():
                cd = form2.cleaned_data
                if 'post_type' not in cd or cd['post_type'] not in PostTypeE.reverse_names:  # noqa
                    post_type = PostTypeE.NOT_WINE
                else:
                    post_type = PostTypeE.reverse_names[cd['post_type']]

                general_post = Post(
                    author=user,
                    status=PostStatusE.PUBLISHED,
                    type=post_type,
                    title=cd['title'],
                    description=cd['description'],
                    user_mentions=cd['mentions'] if cd['mentions'] else None
                )

                if cd['place_id']:
                    places = Place.active.filter(
                        pk=cd['place_id'], status__in=[PlaceStatusE.PUBLISHED,
                                                       PlaceStatusE.SUBSCRIBER]
                    )
                    if places:
                        place = places[0]
                        general_post.place = place
                if cd['foursquare_place_name']:
                    general_post.foursquare_place_name = cd['foursquare_place_name']  # noqa
                if cd['foursquare_place_url']:
                    general_post.foursquare_place_url = cd['foursquare_place_url']  # noqa

                general_post.save()
                general_post.refresh_from_db()

                # handling files for general post
                if files:
                    file_main = files.pop(0)
                    main_image = PostImage(
                        image_file=file_main, post=general_post, author=user
                    )
                    main_image.save()
                    general_post.main_image = main_image
                    general_post.save()
                    general_post.refresh_from_db()
                    for file_item in files:
                        image = PostImage(
                            image_file=file_item,
                            post=general_post,
                            author=user
                        )
                        image.save()

                general_post.push_to_timeline(
                    is_new=True, is_sticky=is_privileged_account(user)
                )
                general_post.update_user_mentions(
                    cd['mentions'] if cd['mentions'] else None, save_item=True
                )

                # if event is currently going on and the pinpointed place has free_glass = True:
                if place and place.free_glass:
                    place.free_glass_last_action_date = dt.datetime.now()
                    place.save_keep_modified_dt()
                    place.refresh_from_db()

                general_post.refresh_from_db()

                gp_dict = FullPostSerializer(
                    general_post, context={
                        'request': request,
                        'include_wine_data': True,
                        'include_winemaker_data': True
                    }
                ).data

                return gp_dict
            else:
                raise WrongParametersError(_("Wrong parameters."), form2)

        raise WrongParametersError(_("Wrong parameters."), form1)


def is_post_data_different(cd, post):
    posts_to_check = Post.active.filter(
        pk=post.id,
        wine__name__unaccent__iexact=cd['name'],
        wine__domain__unaccent__iexact=cd['domain'],
        wine__region__unaccent__iexact=cd['region'],
        wine__designation__unaccent__iexact=cd['designation'],
        wine__grape_variety__unaccent__iexact=cd['grape_variety'],
        wine__color=cd['color'],
        wine__is_sparkling=cd['is_sparkling']
    )
    if not posts_to_check:
        return True
    else:
        return False


def get_or_create_winemaker_by_name(winemaker_name, cd, user):
    winemakers = Winemaker.active.filter(name__unaccent__iexact=winemaker_name)
    if winemakers:
        winemaker = winemakers[0]
        # description=cd['description'],
        # wine=wine_from_db,
        # wine_year=cd['year'],
        # place=place
    else:
        winemaker = Winemaker(
            name=cd['winemaker_name'],
            region=cd['region'],
            domain=cd['domain'],
            author=user,
            status=WinemakerStatusE.DRAFT
        )
        winemaker.save()
        winemaker.refresh_from_db()
    return winemaker


def get_cloned_winepost_with_new_data(cd, winepost, winemaker):
    new_wine = winepost.wine.clone_as_new_draft()
    new_wine.winemaker = winemaker
    new_wine.status = WineStatusE.ON_HOLD
    new_wine.name = cd['name']
    new_wine.domain = cd['domain'] if cd['domain'] else None
    new_wine.region = cd['region']
    new_wine.designation = cd['designation']
    new_wine.grape_variety = cd['grape_variety']
    new_wine.color = cd['color'] if cd['color'] else None
    new_wine.is_sparkling = cd['is_sparkling']
    new_wine.save()
    new_wine.refresh_from_db()
    winepost.wine = new_wine
    winepost.status = PostStatusE.DRAFT
    winepost.is_parent_post = True
    winepost.save()
    winepost.refresh_from_db()
    return winepost


# /api/posts/wine/edit
@signed_api(
    FormClass=None, token_check=True, json_used=False, success_status=200
)
def edit_winepost(request):
    user = request.user
    matching_existing_wine = True
    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form1 = FileUploadForm(request.POST, request.FILES)
        files = request.FILES.getlist('images')
        if form1.is_valid():
            request_post = request.POST['data'] if 'data' in request.POST else {}  # noqa
            try:
                data_json = json.loads(form1.cleaned_data['data'])
            except ValueError:
                data_json = {}

            # -- if data_json: --
            form2 = WinepostEditForm(data_json)
            if form2.is_valid():
                cd = form2.cleaned_data
                if cd['post_id']:
                    post = Post.active.get(id=cd['post_id'])
                elif cd['tl_id']:
                    tl_item = TimeLineItem.active.get(id=cd['tl_id'])
                    if tl_item.item_type == TimeLineItemTypeE.POST:
                        post = Post.active.get(id=tl_item.cached_item['id'])
                    else:
                        raise ResultErrorError(
                            "wrong item type in TL ITEM - post expected", 102
                        )

                if post.type != PostTypeE.WINE:
                    raise ResultErrorError(
                        "wrong post stype - winepost expected", 102
                    )
                prevent_editing_not_own_item(user, post)

                place = None
                winemaker = None
                if 'place_id' in request_post:
                    if cd['place_id']:
                        places = Place.active.filter(
                            pk=cd['place_id'],
                            status__in=[PlaceStatusE.PUBLISHED,
                                        PlaceStatusE.SUBSCRIBER]
                        )
                        if places:
                            place = places[0]
                    post.place = place

                # ----------------------------------------------------------------
                if post.is_parent_post:     # Parent Post: just update it and change to DRAFT
                    if 'winemaker_name' in request_post or 'winemaker_id' in request_post:
                        if cd['winemaker_name'] and cd['winemaker_name'] != post.wine.winemaker.name:
                            winemaker = get_or_create_winemaker_by_name(cd['winemaker_name'], cd, user)
                        elif cd['winemaker_id']:
                            winemaker = Winemaker.active.get(pk=cd['winemaker_id'])
                        if winemaker and post.wine.winemaker != winemaker:
                            post.wine.winemaker = winemaker
                            post.status = PostStatusE.DRAFT
                    if is_post_data_different(cd, post):
                        post.status = PostStatusE.DRAFT
                        # matching_existing_wine = False
                    if 'name' in request_post:
                        post.wine.name = cd['name']
                    if 'domain' in request_post:
                        post.wine.domain = cd['domain'] if cd['domain'] else None
                    if 'region' in request_post:
                        post.wine.region = cd['region']
                    if 'designation' in request_post:
                        post.wine.designation = cd['designation']
                    if 'grape_variety' in request_post:
                        post.wine.grape_variety = cd['grape_variety']
                        post.grape_variety = cd['grape_variety']
                    if 'color' in request_post:
                        post.wine.color = cd['color'] if cd['color'] else None
                    if 'is_sparkling' in request_post:
                        post.wine.is_sparkling = cd['is_sparkling']
                    post.wine.save()
                    post.wine.refresh_from_db()
                else:
                    # NON-Parent Post: create new wine, assign to
                    # this post and change the post to DRAFT
                    new_wine = False
                    if 'winemaker_name' in request_post or 'winemaker_id' in request_post:
                        if cd['winemaker_name'] and cd['winemaker_name'] != post.wine.winemaker.name:
                            winemaker = get_or_create_winemaker_by_name(
                                cd['winemaker_name'], cd, user
                            )
                            new_wine = True
                        elif cd['winemaker_id']:
                            winemaker = Winemaker.active.get(pk=cd['winemaker_id'])

                    if not winemaker:
                        winemaker = post.wine.winemaker  # no change in winemaker
                    if is_post_data_different(cd, post):
                        new_wine = True
                    if post.wine.winemaker != winemaker:
                        new_wine = True
                    if new_wine:
                        post = get_cloned_winepost_with_new_data(cd, post, winemaker)

                post.title = make_winepost_title(post.wine.name, cd['year'])
                if 'description' in request_post:
                    post.description = cd['description']

                if 'year' in request_post:
                    post.wine_year = cd['year']

                if 'foursquare_place_name' in request_post and cd['foursquare_place_name']:
                    post.foursquare_place_name = cd['foursquare_place_name']
                if 'foursquare_place_url' in request_post and cd['foursquare_place_url']:
                    post.foursquare_place_url = cd['foursquare_place_url']
                last_modified_time = dt.datetime.now()
                post.modified_time = last_modified_time
                post.save()
                post.refresh_from_db()

                # handling files for wine or winepost
                if files:
                    archive_images_fn(parent_item=post, parent_item_field='post', ImageClass=PostImage)
                    file_main = files.pop(0)
                    # parent post - updating wine images
                    if post.is_parent_post:
                        # exact wine found - add images to winepost (we have wine_from_db)
                        main_image = WineImage(image_file=file_main, wine=post.wine, author=user)
                        main_image.save()
                        post.wine.main_image = main_image
                        post.wine.save()
                        post.wine.refresh_from_db()
                        for file_item in files:
                            image = WineImage(image_file=file_item, wine=post.wine, author=user)
                            image.save()
                    # not a parent post - updating post images
                    else:
                        main_image = PostImage(image_file=file_main, post=post, author=user)
                        main_image.save()
                        post.main_image = main_image
                        post.save()
                        post.refresh_from_db()
                        for file_item in files:
                            image = PostImage(image_file=file_item, post=post, author=user)
                            image.save()

                select_star_review_for_winepost(post, tested_post=post)
                post.refresh_from_db()
                post.update_user_mentions(cd['mentions'] if cd['mentions'] else None, save_item=True)
                post.refresh_from_db()

                if cd['vuf_wine_id']:
                    save_vuf_wine_data(cd['vuf_wine_id'], post)
                post.refresh_from_db()
                if cd['year'] and cd['grape_variety']:
                    yd = {
                        'grape_variety': cd['grape_variety'],
                        'free_so2': '',
                        'total_so2': '',
                    }
                    # we compare grape_variety ONLY, because neither free_so2 nor total_so2
                    # are set in the API
                    update_yearly_data_with_parent_post(post,
                                                        str(cd['year']),
                                                        yd,
                                                        compare_fields=['grape_variety'],
                                                        create_new_wine_if_needed=False)
                    post.refresh_from_db()

                winepost_dict = FullPostSerializer(
                    post, context={
                        'request': request,
                        'include_wine_data': True,
                        'include_winemaker_data': True,
                    }
                ).data
                winepost_dict['matching_existing_wine'] = matching_existing_wine

                return winepost_dict
            else:
                raise WrongParametersError(_("Wrong parameters."), form2)
        raise WrongParametersError(_("Wrong parameters."), form1)


# /api/posts/general/edit
@signed_api(FormClass=None, token_check=True, json_used=False, success_status=200)
def edit_general_post(request):
    user = request.user

    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form1 = FileUploadForm(request.POST, request.FILES)
        files = request.FILES.getlist('images')
        if form1.is_valid():
            try:
                data_json = json.loads(form1.cleaned_data['data'])
            except ValueError:
                data_json = {}

            form2 = GeneralPostEditForm(data_json)
            if form2.is_valid():
                cd = form2.cleaned_data
                if cd['post_id']:
                    post = Post.active.get(id=cd['post_id'])
                elif cd['tl_id']:
                    tl_item = TimeLineItem.active.get(id=cd['tl_id'])
                    if tl_item.item_type == TimeLineItemTypeE.POST:
                        post = Post.active.get(id=tl_item.cached_item['id'])
                    else:
                        raise ResultErrorError("wrong item type in TL ITEM - post expected", 102)

                prevent_editing_not_own_item(user, post)

                post.title = cd['title']
                post.description = cd['description']
                if cd['place_id']:
                    post.place_id = cd['place_id']
                if cd['foursquare_place_name']:
                    post.foursquare_place_name = cd['foursquare_place_name']
                if cd['foursquare_place_url']:
                    post.foursquare_place_url = cd['foursquare_place_url']
                post.save()
                post.refresh_from_db()

                # handling files for general post
                if files:
                    archive_images_fn(parent_item=post, parent_item_field='post', ImageClass=PostImage)
                    file_main = files.pop(0)
                    main_image = PostImage(image_file=file_main, post=post, author=user)
                    main_image.save()
                    post.main_image = main_image
                    post.save()
                    for file_item in files:
                        image = PostImage(image_file=file_item, post=post, author=user)
                        image.save()

                post.update_user_mentions(cd['mentions'] if cd['mentions'] else None, save_item=True)
                post.refresh_from_db()

                post_dict = FullPostSerializer(
                    post, context={
                        'request': request,
                        'include_wine_data': True,
                        'include_winemaker_data': True,
                    }
                ).data

                return post_dict
            else:
                raise WrongParametersError(_("Wrong parameters."), form2)

        raise WrongParametersError(_("Wrong parameters."), form1)


# /api/posts/list
@signed_api(FormClass=PostListForm, token_check=True)
def get_post_list(request):
    user = request.user
    prevent_using_non_active_account(user)
    filter_criteria = {}

    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data

            if cd['type']:
                filter_criteria['type'] = cd['type']
            if cd['post_ids']:
                filter_criteria['id__in'] = cd['post_ids']
            if cd['user_id']:
                user_item = UserProfile.active.get(id=cd['user_id'])
                filter_criteria['author'] = user_item
            if cd['username']:
                user_item = UserProfile.active.get(username=cd['username'])
                filter_criteria['author'] = user_item
            if cd['is_star_review']:
                filter_criteria['is_star_review'] = cd['is_star_review']
            if cd['wine_id']:
                wine_item = Wine.active.get(id=cd['wine_id'])
                filter_criteria['wine'] = wine_item
                filter_criteria['type'] = PostTypeE.WINE

            (limit, order_dir, last_id, order_by) = list_control_parameters_by_form(cd)
            filter_criteria = get_filter_criteria_for_order_last_id(order_dir, last_id, filter_criteria)
            filter_criteria['author__type__in'] = [UserTypeE.USER, UserTypeE.ADMINISTRATOR, UserTypeE.EDITOR]
            filter_criteria['author__status__in'] = [UserStatusE.ACTIVE, UserStatusE.INACTIVE]
            posts = Post.active.filter(**filter_criteria).order_by(order_by)[0:limit]
            if not posts:
                raise ResultEmpty

            last_id = list_last_id(posts)
            posts_out = FullPostSerializer(
                posts, many=True, context={
                    'request': request,
                    'fallback_wine_image': True,
                    'include_wine_data': bool(cd['wine_id']),
                    'include_winemaker_data': bool(cd['wine_id']),
                }
            ).data

            return {'items': posts_out, 'last_id': last_id}


# /api/posts/count-vuforia-scans
class VuforiaScansCountView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        query_serializer=VuforiaScansCountSerializer,
        operation_summary='Return vuforia scans count by wine_id',
        operation_description='The method POST is deprecated for this '
                              'endpoint.',
        security=[]
    )
    def get(self, request, format=None):
        serializer = VuforiaScansCountSerializer(data=request.query_params)

        if serializer.is_valid(raise_exception=True):
            validated_data = serializer.validated_data
            stats_items = TotalStats.objects.all()
            if stats_items.exists():
                stats_item = stats_items[0]
            else:
                stats_item = TotalStats()
            stats_item.vuforia_scans_total += 1
            env = int(validated_data.get('env')) if validated_data.get('env') \
                else None
            if env == AppEnvE.ANDROID:    # Android
                stats_item.vuforia_scans_android += 1
            elif env == AppEnvE.IOS:      # iOS
                stats_item.vuforia_scans_ios += 1

            stats_item.save()
            stats_item.refresh_from_db()

            data = {
                'vuforia_scans_android': stats_item.vuforia_scans_android,
                'vuforia_scans_ios': stats_item.vuforia_scans_ios,
                'vuforia_scans_total': stats_item.vuforia_scans_total,
            }
            response_data = {'data': data}
            fill_default_response_data(response_data)
            return Response(response_data)

    @swagger_auto_schema(
        request_body=VuforiaScansCountSerializer,
        operation_summary='Return vuforia scans count by wine_id',
        operation_description='The method POST is deprecated for this '
                              'endpoint.',
        deprecated=True,
        security=[]
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '/api/posts/count-vuforia-scans')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)


# ====== testing abcd =========

def get_winemaker(cd):
    winemaker = None
    if cd['winemaker_name']:
        log_add_wp.debug("ADDING WINEPOST NEW FORM2 VALIDDDDDDDDDDDDD - WINEMAKER BY NAME")
        winemaker = Winemaker.active.filter(name__unaccent__iexact=cd['winemaker_name']).first()
    elif cd['winemaker_id']:
        log_add_wp.debug("ADDING WINEPOST NEW FORM2 VALIDDDDDDDDDDDDD - WINEMAKER BY ID")
        winemaker = Winemaker.active.get(pk=cd['winemaker_id'])
    return winemaker


def get_or_add_winemaker(cd, user):
    created = False
    # NOT SCANNED - added by autocomplete OR as a completely new wine
    winemaker = get_winemaker(cd)
    if not winemaker:
        created = True
        log_add_wp.debug("ADDING WINEPOST NEW FORM2 VALIDDDDDDDDDDDDD - CREATING NEW WINEMAKER")
        winemaker = Winemaker(
            name=cd['winemaker_name'],
            region=cd['region'],
            domain=cd['domain'],
            author=user,
            status=WinemakerStatusE.DRAFT
        )
        winemaker.save()
        winemaker.refresh_from_db()

    return created, winemaker


def add_new_wine(cd, winemaker, user):
    log_add_wp.debug("ADDING WINEPOST NEW FORM2 VALIDDDDDDDDDDDDD - NO WINES FOUND IN DB, ADDING A NEW WINE")
    wine = Wine(
        author=user,
        status=WineStatusE.ON_HOLD,
        name=cd['name'],
        domain=cd['domain'],
        grape_variety=cd['grape_variety'],
        region=cd['region'],
        color=int(cd['color']) if cd['color'] else None,
        is_sparkling=cd['is_sparkling'],
        winemaker=winemaker,
        similiar_wine_exists=cd['similiar_wine_exists'],
        similiar_wine_id=cd['similiar_wine_id'],
        designation=cd['designation'],
        year=cd['year']
    )
    wine.save()
    wine.refresh_from_db()
    return wine


def add_new_winepost(cd, wine, place, files, added_by_scanning, user):
    # adding new winepost, regardless of what way was used to add a wine - scanning or not.
    log_add_wp.debug("ADDING WINEPOST NEW FORM2 VALIDDDDDDDDDDDDD - ADDING A WINEPOST")
    if user.type == UserTypeE.OWNER:
        currency = get_owner_currency(user)
        price = cd['price']
    else:
        currency = ""
        price = None

    winepost = Post(
        author=user,
        status=get_post_status_for_wine_status(wine.status),
        type=PostTypeE.WINE,
        title=make_winepost_title(wine.name, cd['year']),
        description=cd['description'],
        grape_variety=cd['grape_variety'],
        wine=wine,
        wine_year=cd['year'] or wine.year,
        place=place,
        foursquare_place_name=cd['foursquare_place_name'] if cd['foursquare_place_name'] else None,
        foursquare_place_url=cd['foursquare_place_url'] if cd['foursquare_place_url'] else None,
        is_scanned=True if added_by_scanning else False,
        free_so2=None,
        total_so2=None,
        price=price,
        currency=currency
    )

    winepost.save()
    winepost.refresh_from_db()

    # handling files for winepost (only "posted by user" are being created, NOT LABELS)
    if files:
        log_add_wp.debug("ADDING WINEPOST NEW FORM2 VALIDDDDDDDDDDDDD - ADDING FILES FOR WINEPOST")
        file_main = files.pop(0)
        main_image = PostImage(image_file=file_main, post=winepost, author=user)
        main_image.save()
        winepost.main_image = main_image
        winepost.save()
        for file_item in files:
            image = PostImage(image_file=file_item, post=winepost, author=user)
            image.save()

    if added_by_scanning:
        log_add_wp.debug("ADDED BY SCANNING - SAVING VUFORIA DATA")
        save_vuf_wine_data(cd['wine_id'], winepost)
        winepost.refresh_from_db()

    log_add_wp.debug("PUSHING TO TIMELINE")
    winepost.push_to_timeline(is_new=True, is_sticky=is_privileged_account(user))
    log_add_wp.debug("UPDATING USER MENTIONS")
    winepost.update_user_mentions(cd['mentions'] if cd['mentions'] else None, save_item=True)
    log_add_wp.debug("REFRESHING FROM DB")
    winepost.refresh_from_db()

    if cd['year'] and cd['grape_variety']:
        log_add_wp.debug("SETTING YEARLY DATA")
        yd = {
            'grape_variety': cd['grape_variety'],
            'free_so2': '',
            'total_so2': '',
        }
        # we compare grape_variety ONLY, because neither free_so2 nor total_so2
        # are set in the API
        update_yearly_data_with_parent_post(winepost,
                                            str(cd['year']),
                                            yd,
                                            compare_fields=['grape_variety'],
                                            create_new_wine_if_needed=False)
        winepost.refresh_from_db()
        log_add_wp.debug("FINISHED SETTING YEARLY DATA")

    log_add_wp.debug("GETTING ADDED WINEPOST DATA")
    log_add_wp.debug("SELECTING STAR REVIEW FOR A WINEPOST")
    select_star_review_for_winepost(winepost, tested_post=winepost)

    # if event is currently going on and the pinpointed place has free_glass = True:
    if place and place.free_glass:
        log_add_wp.debug("PLACE DATA PROVIDED AND FREE_GLASS FOR A PLACE - CHECKING")
        place.free_glass_last_action_date = dt.datetime.now()
        place.save_keep_modified_dt()
        place.refresh_from_db()
        # cur_events = FreeGlassEvent.active.all()
        # if cur_events:
        #     cur_event = cur_events[0]
        #     date_today = dt.date.today()
        #     if cur_event.start_date.date() <= date_today <= cur_event.end_date.date():
        #         SenderNotifier().send_with_free_glass(request.user, place)
    log_add_wp.debug("::: RETURNING WINEPOST_DICT DATA :::")
    return winepost


def get_wine_if_exists(cd, winemaker, user):
    wine_criteria = {
        'name__unaccent__iexact': cd['name'],
        'grape_variety__unaccent__iexact': cd['grape_variety'],
        'region__unaccent__iexact': cd['region'],
        'domain__unaccent__iexact': cd['domain'],
        'color': int(cd['color']) if cd['color'] else None,
        'is_sparkling': cd['is_sparkling'],
        # 'designation__unaccent__iexact': cd['designation'],  # NOT USED ANYMORE, we use region only
        'winemaker': winemaker,
    }
    if cd['wine_id']:
        wine_criteria['id'] = cd['wine_id']
        log_add_wp.debug("ADDING WINEPOST NEW FORM2 VALIDD - WINE_ID PROVIDED: %s, CHECKING", cd['wine_id'])

    wine = Wine.active.filter(**wine_criteria).order_by('-id').first()
    if wine:
        log_add_wp.debug("ADDING WINEPOST NEW FORM2 VALIDD - EXACT WINES WERE FOUND IN DB")
    return wine


def check_if_scanned_wine_matches(cd, wine):
    winemaker = None
    check_winemaker = False
    if cd['winemaker_name'] or cd['winemaker_id']:
        check_winemaker = True

    if check_winemaker:
        winemaker = get_winemaker(cd)
        if not winemaker or winemaker != wine.winemaker:
            return False

    wine_criteria = {
        'id': wine.id,
    }
    if cd['name']:
        wine_criteria['name__unaccent__iexact'] = cd['name']
    if cd['grape_variety']:
        wine_criteria['grape_variety__unaccent__iexact'] = cd['grape_variety']
    # it's an issue when this data doesn't match for some wines
    # the issue should be investigated
    # if cd['region']:
    #     wine_criteria['region__unaccent__iexact'] = cd['region']
    if cd['domain']:
        wine_criteria['domain__unaccent__iexact'] = cd['domain']
    if cd['color']:
        wine_criteria['color'] = int(cd['color'])
    if cd['is_sparkling'] in [True, False]:
        wine_criteria['is_sparkling'] = cd['is_sparkling']

    wine_test = Wine.active.filter(**wine_criteria).first()
    if not wine_test:
        return False

    return True


# ====== /testing abcd =========


# /api/posts/wine/addnew
@signed_api(FormClass=None, token_check=True, json_used=False, success_status=200)
def add_winepost_new(request):
    log_add_wp.debug("ADDDING WINEPOST NEW ")
    log.debug("add winepost")
    matching_existing_wine = True
    added_by_scanning = False
    user = request.user
    prevent_using_non_active_account(user)
    winepost = None

    if not request.method == 'POST':
        raise WrongParametersError(_("Wrong parameters."), None)

    form1 = FileUploadForm(request.POST, request.FILES)
    files = request.FILES.getlist('images')
    if not form1.is_valid():
        raise WrongParametersError(_("Wrong parameters."), form1)
    try:
        data_json = json.loads(form1.cleaned_data['data'])
    except ValueError:
        data_json = {}

    log_add_wp.debug("ADDDING WINEPOST NEW - FORM1 VALID ")
    # -- if data_json: --
    form2 = WinepostCreateNewForm(data_json)
    if form2.is_valid():
        cd = form2.cleaned_data
        log_add_wp.debug("ADDDING WINEPOST NEW - FORM2 VALID, CD CD CD %s " % str(cd))
        # log_add_wp.debug("ADD WINEPOST NEWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW - "
        #           "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCDDDDDDDDDD %s" % str(cd))
        place = None
        if cd['place_id']:
            place = Place.active.filter(pk=cd['place_id'],
                                        status__in=[PlaceStatusE.PUBLISHED,
                                                    PlaceStatusE.SUBSCRIBER]
                                        ).first()

        # IS SCANNED WITHOUT A WINE - incomplete data
        if cd['is_scanned'] and ('wine_id' not in cd or not cd['wine_id']):
            log_add_wp.debug("ADDING WINEPOST NEW FORM2 VALIDDDDDDDDDDDDD - ERROR ADDING BY SCANNING - NO wine_id")
            raise WrongParametersError(_("Wrong parameters."), form1)
        # IS SCANNED - VUFORIA WINE
        elif cd['is_scanned'] and cd['wine_id']:
            log_add_wp.debug("BY SCANNING")
            added_by_scanning = True
            wine = Wine.active.get(id=cd['wine_id'])
            scanned_matches = check_if_scanned_wine_matches(cd, wine)
            if scanned_matches:
                matching_existing_wine = True
            else:
                matching_existing_wine = False
                wm_created, winemaker = get_or_add_winemaker(cd, user)
                wine = add_new_wine(cd, winemaker, user)
        else:
            wine = None
            # NOT SCANNED - added by autocomplete OR as a completely new wine
            winemaker = get_winemaker(cd)
            # if there is no winemaker, it means exact wine could not exist
            if winemaker:
                log_add_wp.debug("ADDING WINEPOST NEW FORM2 VALIDDDDDDDDDDDDD - SEARCHING FOR WINE IN DB")
                wine = get_wine_if_exists(cd, winemaker, user)

            if wine:
                matching_existing_wine = True
            else:
                matching_existing_wine = False
                wm_created, winemaker = get_or_add_winemaker(cd, user)
                wine = add_new_wine(cd, winemaker, user)

        winepost = add_new_winepost(cd, wine, place, files, added_by_scanning, user)
        winepost_dict = FullPostSerializer(
            winepost, context={
                'request': request,
                'include_wine_data': True,
                'include_winemaker_data': True
            }
        ).data

        winepost_dict['matching_existing_wine'] = matching_existing_wine
        return winepost_dict
    raise WrongParametersError(_("Wrong parameters."), form1)
