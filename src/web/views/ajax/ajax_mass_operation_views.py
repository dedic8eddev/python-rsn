from __future__ import absolute_import

import datetime as dt
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from web.constants import PlaceStatusE, PostStatusE, PostTypeE, WinemakerStatusE
from web.forms.admin_forms import (MassOperationIdsAnyPostForm,
                                   MassOperationIdsCommentForm,
                                   MassOperationIdsEstComForm,
                                   MassOperationIdsEventForm,
                                   MassOperationIdsGeneralpostForm,
                                   MassOperationIdsNewParentPostForm,
                                   MassOperationIdsPlaceForm,
                                   MassOperationIdsUserProfileForm,
                                   MassOperationIdsWineForm,
                                   MassOperationIdsWinemakerForm,
                                   MassOperationIdsWinepostForm)
from web.models import (CalEvent, Comment, Place, Post, UserProfile, Wine,
                        Winemaker, select_star_review_for_winepost)
from web.utils.common_winepost import define_as_children_obj
from web.utils.sendernotifier import SenderNotifier
from web.utils.upload_tools import aws_url
from web.utils.views_common import get_current_user

log = logging.getLogger(__name__)


# ------------------------------------------------ AJAX MASS OPERATIONS ---------------------------------------
# notice: entity class is determined by the mass operation FORM used; all of those are forms with
# ModelMultipleChoiceField, which accepts entity queries, and hence the entities are determines
# ------------------------------------------------ AJAX MASS OPERATIONS ---------------------------------------
# notice: entity class is determined by the mass operation FORM used; all of those are forms with
# ModelMultipleChoiceField, which accepts entity queries, and hence the entities are determines


def select_star_review_if_winepost(item):
    if isinstance(item, Post) and item.type == PostTypeE.WINE and item.wine:
        select_star_review_for_winepost(item)


def mass_operation_publish(request, FormClass, status_published):
    data = {"ids": []}
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            for item in cd['ids']:
                if item.is_archived:
                    continue
                if item.status != status_published:
                    data["ids"].append(item.id)
                    item.publish(modifier_user=request.user)
                    select_star_review_if_winepost(item)
    return {
        "status": "OK",
        "data": data
    }


def mass_operation_unpublish(request, FormClass, status_not_published):
    data = {"ids": []}
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            for item in cd['ids']:
                if item.is_archived:
                    continue
                if item.status != status_not_published or \
                        ((isinstance(item, Post) or isinstance(item, Winemaker) or
                            isinstance(item, Place)) and item.get_in_doubt()):
                    data["ids"].append(item.id)
                    item.unpublish(modifier_user=request.user)
                    select_star_review_if_winepost(item)
    return {
        "status": "OK",
        "data": data
    }


def mass_operation_delete(request, FormClass):
    data = {"ids": []}
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            for item in cd['ids']:
                if not item.is_archived:
                    data["ids"].append(item.id)
                    item.archive(modifier_user=request.user)
                    select_star_review_if_winepost(item)
    return {
        "status": "OK",
        "data": data
    }


def mass_operation_delete_winemaker(request, FormClass):
    data = {"ids": []}
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            for item in cd['ids']:
                if not item.is_archived:
                    data["ids"].append(item.id)
                    item.archive(modifier_user=request.user)
    return {
        "status": "OK",
        "data": data
    }


def mass_operation_undelete(request, FormClass):
    data = {"ids": []}
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            for item in cd['ids']:
                if item.is_archived:
                    data["ids"].append(item.id)
                    item.unarchive(modifier_user=request.user)
    return {
        "status": "OK",
        "data": data
    }


def mass_operation_duplicate(request, FormClass):
    data = {"ids": []}
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            for item in cd['ids']:
                if item.is_archived:
                    continue
                data["ids"].append(item.id)
                item.duplicate()
                select_star_review_if_winepost(item)
    return {
        "status": "OK",
        "data": data
    }


def mass_operation_close_place(request, FormClass):
    data = {"ids": []}
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            for item in cd['ids']:
                data["ids"].append(item.id)
                item.close(modifier_user=request.user)
    return {
        "status": "OK",
        "data": data
    }


def mass_operation_set_in_doubt(request, FormClass):
    data = {"ids": []}
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            for item in cd['ids']:
                if item.is_archived:
                    continue
                data["ids"].append(item.id)
                item.set_in_doubt(modifier_user=request.user)
    return {
        "status": "OK",
        "data": data
    }


def mass_operation_set_to_investigate(request, form_class):
    """
    Apply mass operation. Possible to pass `form_class` for wineposts and winemakers,
    since both are using same interface.

    :param request: The request object
    :param form_class: The form class, `form.Form`
    """
    data = {"ids": []}
    if request.method == 'POST':
        # from django.http import QueryDict
        # query_dict = QueryDict('ids=410&ids=713')
        # print(query_dict)

        form = form_class(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            for item in cd['ids']:
                if item.is_archived:
                    continue
                data["ids"].append(item.id)

                # Note, to be able to apply the same mass operation call to wineposts & winemakers
                # the item function must be the same name and semantic
                item.set_to_investigate(modifier_user=request.user)
    return {
        "status": "OK",
        "data": data
    }


def mass_operation_set_bio_organic(request, FormClass):
    data = {"ids": []}
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            for item in cd['ids']:
                if item.is_archived:
                    continue
                data["ids"].append(item.id)
                item.set_bio_organic(modifier_user=request.user)
    return {
        "status": "OK",
        "data": data
    }


def mass_operation_refuse(request, FormClass):
    data = {"ids": []}
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            for item in cd['ids']:
                if item.is_archived:
                    continue

                data["ids"].append(item.id)
                item.refuse(modifier_user=request.user)
                select_star_review_if_winepost(item)
    return {
        "status": "OK",
        "data": data
    }


def mass_operation_refuse_winepost(request, FormClass):
    data = {"ids": []}
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            for item in cd['ids']:
                if item.is_archived:
                    continue
                data["ids"].append(item.id)
                item.refuse(modifier_user=request.user)
                select_star_review_if_winepost(item)
    return {
        "status": "OK",
        "data": data
    }


def mass_operation_refuse_winemaker(request, FormClass):
    data = {"ids": []}
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            for item in cd['ids']:
                data["ids"].append(item.id)
                item.refuse(modifier_user=request.user)
    return {
        "status": "OK",
        "data": data
    }


def mass_operation_ban(request, FormClass, user):
    data = {"ids": []}
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            for item in cd['ids']:
                if item.id != user.id:
                    data["ids"].append(item.id)
                    item.ban(modifier_user=request.user)
    return {
        "status": "OK",
        "data": data
    }


def mass_operation_unban(request, FormClass, user):
    data = {"ids": []}
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            for item in cd['ids']:
                if item.id != user.id:
                    data["ids"].append(item.id)
                    item.unban(modifier_user=request.user)

    return {
        "status": "OK",
        "data": data
    }


def mass_operation_ban_comment_author(request, FormClass, user):
    data = {"ids": []}
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            for item in cd['ids']:
                if item.author.id != user.id:
                    data["ids"].append(item.id)
                    item.author.ban(modifier_user=request.user)
    return {
        "status": "OK",
        "data": data
    }


def mass_operation_unban_comment_author(request, FormClass, user):
    data = {"ids": []}
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            for item in cd['ids']:
                if item.author.id != user.id:
                    data["ids"].append(item.id)
                    item.author.unban(modifier_user=request.user)

    return {
        "status": "OK",
        "data": data
    }


# /ajax/places/publish
@csrf_exempt
@login_required
def places_publish(request):
    get_current_user(request)
    result = mass_operation_publish(request, MassOperationIdsPlaceForm, PlaceStatusE.PUBLISHED)
    result['count'] = Place.active.all().count()
    return JsonResponse(result)


# /ajax/places/unpublish
@csrf_exempt
@login_required
def places_unpublish(request):
    get_current_user(request)
    result = mass_operation_unpublish(request, MassOperationIdsPlaceForm, PlaceStatusE.DRAFT)
    result['count'] = Place.active.all().count()
    return JsonResponse(result)


# /ajax/places/delete
@csrf_exempt
@login_required
def places_delete(request):
    get_current_user(request)
    result = mass_operation_delete(request, MassOperationIdsPlaceForm)
    result['count'] = Place.active.all().count()
    return JsonResponse(result)


# /ajax/places/delete
@csrf_exempt
@login_required
def places_close(request):
    get_current_user(request)
    result = mass_operation_close_place(request, MassOperationIdsPlaceForm)
    result['count'] = Place.active.all().count()
    return JsonResponse(result)


# /ajax/wines/delete
@csrf_exempt
@login_required
def wines_delete(request):
    get_current_user(request)
    result = mass_operation_delete(request, MassOperationIdsWineForm)
    result['count'] = Wine.active.all().count()
    return JsonResponse(result)


# /ajax/places/duplicate
@csrf_exempt
@login_required
def places_duplicate(request):
    get_current_user(request)
    result = mass_operation_duplicate(request, MassOperationIdsPlaceForm)
    result['count'] = Place.active.all().count()
    return JsonResponse(result)


# /ajax/winemakers/publish
@csrf_exempt
@login_required
def winemakers_publish(request):
    get_current_user(request)
    result = mass_operation_publish(request, MassOperationIdsWinemakerForm, WinemakerStatusE.VALIDATED)
    result['count'] = Winemaker.active.all().count()
    return JsonResponse(result)


# /ajax/winemakers/unpublish
@csrf_exempt
@login_required
def winemakers_unpublish(request):
    get_current_user(request)
    result = mass_operation_unpublish(request, MassOperationIdsWinemakerForm, WinemakerStatusE.DRAFT)
    result['count'] = Winemaker.active.all().count()
    return JsonResponse(result)


# /ajax/winemakers/set_in_doubt
@csrf_exempt
@login_required
def winemakers_set_in_doubt(request):
    get_current_user(request)
    result = mass_operation_set_in_doubt(request, MassOperationIdsWinemakerForm)
    result['count'] = Winemaker.active.all().count()
    return JsonResponse(result)


# /ajax/winemakers/set_bio_organic
@csrf_exempt
@login_required
def winemakers_set_bio_organic(request):
    get_current_user(request)
    result = mass_operation_set_bio_organic(request, MassOperationIdsWinemakerForm)
    result['count'] = Winemaker.active.all().count()
    return JsonResponse(result)


# /ajax/winemakers/set_to_investigate
@csrf_exempt
@login_required
def winemakers_set_to_investigate(request):
    """
    API to set requested winemakers to 'TO_INVESTIGATE' status
    """
    get_current_user(request)
    result = mass_operation_set_to_investigate(request, MassOperationIdsWinemakerForm)
    result['count'] = Winemaker.active.all().count()
    return JsonResponse(result)


# /ajax/winemakers/delete
@csrf_exempt
@login_required
def winemakers_delete(request):
    get_current_user(request)
    result = mass_operation_delete_winemaker(request, MassOperationIdsWinemakerForm)
    result['count'] = Winemaker.active.all().count()
    return JsonResponse(result)


# /ajax/winemakers/duplicate
@csrf_exempt
@login_required
def winemakers_duplicate(request):
    get_current_user(request)
    result = mass_operation_duplicate(request, MassOperationIdsWinemakerForm)
    result['count'] = Winemaker.active.all().count()
    return JsonResponse(result)


# /ajax/wineposts/publish
@csrf_exempt
@login_required
def wineposts_publish(request):
    get_current_user(request)
    result = mass_operation_publish(request, MassOperationIdsWinepostForm, PostStatusE.PUBLISHED)
    result['count'] = Post.active.filter(type=PostTypeE.WINE).count()
    return JsonResponse(result)


# /ajax/wineposts/unpublish
@csrf_exempt
@login_required
def wineposts_unpublish(request):
    get_current_user(request)
    result = mass_operation_unpublish(request, MassOperationIdsWinepostForm, PostStatusE.DRAFT)
    result['count'] = Post.active.filter(type=PostTypeE.WINE).count()
    return JsonResponse(result)


# /ajax/wineposts/delete
@csrf_exempt
@login_required
def wineposts_delete(request):
    get_current_user(request)
    result = mass_operation_delete(request, MassOperationIdsAnyPostForm)
    result['count'] = Post.active.filter(type=PostTypeE.WINE).count()
    return JsonResponse(result)


# /ajax/wineposts/undelete
@csrf_exempt
@login_required
def wineposts_undelete(request):
    get_current_user(request)
    result = mass_operation_undelete(request, MassOperationIdsAnyPostForm)
    result['count'] = Post.active.filter(type=PostTypeE.WINE).count()
    return JsonResponse(result)


# /ajax/wineposts/refuse
@csrf_exempt
@login_required
def wineposts_refuse(request):
    get_current_user(request)
    result = mass_operation_refuse_winepost(request, MassOperationIdsWinepostForm)
    result['count'] = Post.active.filter(type=PostTypeE.WINE).count()
    return JsonResponse(result)


# /ajax/wineposts/set_in_doubt
@csrf_exempt
@login_required
def wineposts_set_in_doubt(request):
    get_current_user(request)
    result = mass_operation_set_in_doubt(request, MassOperationIdsWinepostForm)
    result['count'] = Post.active.filter(type=PostTypeE.WINE).count()
    return JsonResponse(result)


# /ajax/wineposts/set_to_investigate
@csrf_exempt
@login_required
def wineposts_set_to_investigate(request):
    """
    Set a requested wineposts to 'TO_INVESTIGATE' status
    """
    get_current_user(request)
    result = mass_operation_set_to_investigate(request, form_class=MassOperationIdsWinepostForm)
    result['count'] = Post.active.filter(type=PostTypeE.WINE).count()
    return JsonResponse(result)


# /ajax/wineposts/set_bio_organic
@csrf_exempt
@login_required
def wineposts_set_bio_organic(request):
    get_current_user(request)
    result = mass_operation_set_bio_organic(request, MassOperationIdsWinepostForm)
    result['count'] = Post.active.filter(type=PostTypeE.WINE).count()
    return JsonResponse(result)


# =========================================================================================================

# /ajax/est-com/delete
@csrf_exempt
@login_required
def est_com_delete(request):
    get_current_user(request)

    result = mass_operation_delete(request, MassOperationIdsEstComForm)
    result['count'] = Comment.active.filter().exclude(place=None).count()
    return JsonResponse(result)


# /ajax/est-com/undelete
@csrf_exempt
@login_required
def est_com_undelete(request):
    get_current_user(request)

    result = mass_operation_undelete(request, MassOperationIdsEstComForm)
    result['count'] = Comment.active.filter().exclude(place=None).count()
    return JsonResponse(result)


# /ajax/est-com/ban-user
@csrf_exempt
@login_required
def est_com_ban_user(request):
    user = get_current_user(request)

    result = mass_operation_ban_comment_author(request, MassOperationIdsEstComForm, user)
    result['count'] = Comment.active.filter().exclude(place=None).count()
    return JsonResponse(result)


# /ajax/est-com/ban-user
@csrf_exempt
@login_required
def est_com_unban_user(request):
    user = get_current_user(request)

    result = mass_operation_unban_comment_author(request, MassOperationIdsEstComForm, user)
    result['count'] = Comment.active.filter().exclude(place=None).count()
    return JsonResponse(result)

# =========================================================================================================


# /ajax/places/set_in_doubt
@csrf_exempt
@login_required
def places_set_in_doubt(request):
    get_current_user(request)

    result = mass_operation_set_in_doubt(request, MassOperationIdsPlaceForm)
    result['count'] = Place.active.all().count()
    return JsonResponse(result)


# /ajax/generalposts/publish
@csrf_exempt
@login_required
def generalposts_publish(request):
    get_current_user(request)

    result = mass_operation_publish(request, MassOperationIdsGeneralpostForm, PostStatusE.PUBLISHED)
    result['count'] = Post.active.filter(type=PostTypeE.NOT_WINE).count()
    return JsonResponse(result)


# /ajax/generalposts/unpublish
@csrf_exempt
@login_required
def generalposts_unpublish(request):
    get_current_user(request)

    result = mass_operation_unpublish(request, MassOperationIdsGeneralpostForm, PostStatusE.DRAFT)
    result['count'] = Post.active.filter(type=PostTypeE.NOT_WINE).count()
    return JsonResponse(result)


# /ajax/generalposts/refuse
@csrf_exempt
@login_required
def generalposts_refuse(request):
    get_current_user(request)

    result = mass_operation_delete(request, MassOperationIdsGeneralpostForm)
    result['count'] = Post.active.filter(type=PostTypeE.NOT_WINE).count()
    return JsonResponse(result)


# /ajax/food/publish
@csrf_exempt
@login_required
def food_publish(request):
    get_current_user(request)
    result = mass_operation_publish(request, MassOperationIdsGeneralpostForm, PostStatusE.PUBLISHED)
    result['count'] = Post.active.filter(type=PostTypeE.FOOD).count()
    return JsonResponse(result)


# /ajax/food/unpublish
@csrf_exempt
@login_required
def food_unpublish(request):
    get_current_user(request)

    result = mass_operation_unpublish(request, MassOperationIdsGeneralpostForm, PostStatusE.DRAFT)
    result['count'] = Post.active.filter(type=PostTypeE.FOOD).count()
    return JsonResponse(result)


# /ajax/food/refuse
@csrf_exempt
@login_required
def food_refuse(request):
    get_current_user(request)

    result = mass_operation_delete(request, MassOperationIdsGeneralpostForm)
    result['count'] = Post.active.filter(type=PostTypeE.FOOD).count()
    return JsonResponse(result)


# /ajax/event/publish
@csrf_exempt
@login_required
def event_publish(request):
    get_current_user(request)

    result = mass_operation_publish(request, MassOperationIdsEventForm, PostStatusE.PUBLISHED)
    result['count'] = CalEvent.objects.filter(is_archived=False).count()
    return JsonResponse(result)


# /ajax/event/unpublish
@csrf_exempt
@login_required
def event_unpublish(request):
    get_current_user(request)

    result = mass_operation_unpublish(request, MassOperationIdsEventForm, PostStatusE.DRAFT)
    result['count'] = CalEvent.objects.filter(is_archived=False).count()
    return JsonResponse(result)


# /ajax/event/refuse
@csrf_exempt
@login_required
def event_refuse(request):
    get_current_user(request)

    result = mass_operation_delete(request, MassOperationIdsEventForm)
    result['count'] = CalEvent.objects.filter(is_archived=False).count()
    return JsonResponse(result)


# /ajax/users/ban
@csrf_exempt
@login_required
def users_ban(request):
    user = get_current_user(request)

    result = mass_operation_ban(request, MassOperationIdsUserProfileForm, user)
    result['count'] = UserProfile.active.all().count()
    return JsonResponse(result)


# /ajax/users/unban
@csrf_exempt
@login_required
def users_unban(request):
    user = get_current_user(request)

    result = mass_operation_unban(request, MassOperationIdsUserProfileForm, user)
    result['count'] = UserProfile.active.all().count()
    return JsonResponse(result)


# /ajax/comments/delete
@csrf_exempt
@login_required
def comments_delete(request):
    get_current_user(request)
    print("comments_delete")
    result = mass_operation_delete(request, MassOperationIdsCommentForm)
    result['count'] = None   # Comment.active.all().count()
    return JsonResponse(result)


# /ajax/wineposts/mop-has-children
@csrf_exempt
@login_required
def winepost_has_children(request):
    get_current_user(request)
    wine_name = ""
    wine_author = ""
    wine_author_avatar_url = ""
    wine_author_edit_url = ""
    wine_parent_post_type = ""
    has_children = False
    if request.method == 'POST':
        form = MassOperationIdsNewParentPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            if cd['ids'] and len(cd['ids']) == 1:
                p_id = cd['ids'][0]
                post = p_id
                wine_name = post.wine.name
                wine_author = '@' + post.author.username
                wine_author_edit_url = reverse('edit_user', args=[post.author.id])
                wine_author_avatar_url = aws_url(post.author.image, thumb=True) if post.author else None
                wine_parent_post_type = 'Parent Post' if post.get_is_natural() else "Referrer"
                if post.is_parent_post and post.type == PostTypeE.WINE and post.wine:
                    other_posts = Post.active.filter(wine=post.wine).exclude(id=post.id)
                    if other_posts:
                        has_children = True

    return JsonResponse({
        "has_children": has_children,
        "wine_name": wine_name,
        "wine_author": wine_author,
        "wine_author_avatar_url": wine_author_avatar_url,
        "wine_author_url": wine_author_edit_url,
        "wine_parent_post_type": wine_parent_post_type,
    })


# /ajax/wineposts/mop-define-as-children
@csrf_exempt
@login_required
def wineposts_mop_define_as_children(request):
    user = get_current_user(request)
    data = {"ids": []}
    status = 'error'

    if request.method == 'POST':
        form = MassOperationIdsNewParentPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            for item in cd['ids']:
                data["ids"].append(item.id)
                # define as child to existing winemaker and new_parent_post_id
                if cd['define_as_child'] \
                        and cd['new_parent_post_id'] \
                        and cd['new_parent_post_id'] != item.id:  # we don't want to assign a winepost to itself
                    define_as_children_obj(item, cd['new_parent_post_id'], user)
                    item.refresh_from_db()
                # make NEW parent post under new_winemaker_id
                elif cd['is_parent_post'] and cd['new_winemaker_id']:
                    new_winemaker = Winemaker.objects.get(id=cd['new_winemaker_id'])
                    new_wine = item.wine.duplicate()
                    item.wine = new_wine
                    item.wine.winemaker = new_winemaker
                    # item.wine.domain = new_winemaker.domain
                    item.wine.region = new_winemaker.region
                    item.wine.designation = new_winemaker.region
                    item.wine.grape_variety = item.grape_variety
                    item.wine.save()
                    item.modified_time = dt.datetime.now()
                    item.set_title_winepost()
                    item.is_parent_post = True
                    status = ['Not natural',
                              'Bio-organic',
                              'In doubt',
                              'To investigate']
                    if cd['nat_oth'] and cd['nat_oth'] == 'natural':
                        item.status = PostStatusE.PUBLISHED
                    elif cd['nat_oth'] and cd['nat_oth'] == 'other'\
                            and cd['status'] and cd['status'] in status:
                        if cd['status'] == 'Not natural':
                            item.status = PostStatusE.REFUSED
                        elif cd['status'] == 'Bio-organic':
                            item.status = PostStatusE.BIO_ORGANIC
                        elif cd['status'] == 'In doubt':
                            item.status = PostStatusE.IN_DOUBT
                        elif cd['status'] == 'To investigate':
                            item.status = PostStatusE.TO_INVESTIGATE
                    elif item.status in [PostStatusE.DRAFT, PostStatusE.IN_DOUBT]:
                        item.status = PostStatusE.PUBLISHED
                    elif item.status == PostStatusE.BIO_ORGANIC:
                        item.status = PostStatusE.BIO_ORGANIC
                    elif item.status == PostStatusE.REFUSED:
                        item.status = PostStatusE.REFUSED
                    item.save()
                    item.wine.refresh_from_db()

                    Post.active.filter(
                        wine=item.wine,
                        type=PostTypeE.WINE,
                        is_parent_post=True
                    ).exclude(id=item.id).update(is_parent_post=False)

                    if item.status == PostStatusE.PUBLISHED:
                        item.publish(
                            validated_by=request.user,
                            update_published_time=False
                        )
                    elif item.status == PostStatusE.DRAFT:
                        item.unpublish(modifier_user=request.user)
                    elif item.status == PostStatusE.REFUSED or item.status == PostStatusE.HIDDEN:
                        item.refuse(modifier_user=request.user)
                    elif item.status == PostStatusE.IN_DOUBT:
                        item.set_in_doubt(modifier_user=request.user)
                    elif item.status == PostStatusE.BIO_ORGANIC:
                        item.set_bio_organic(modifier_user=request.user)
                    elif item.status == PostStatusE.TO_INVESTIGATE:
                        item.set_to_investigate(modifier_user=request.user)

                    item.refresh_from_db()

                    # item duplication - turned off on JHBretin's request, however I'm not sure whether he won't be
                    # restoring it as well
                    # new_winemaker = Winemaker.objects.get(id=cd['new_winemaker_id'])
                    # if item.status != PostStatusE.DRAFT:
                    #     new_item = item.duplicate(change_title=True)
                    # else:
                    #     new_item = item.duplicate(change_title=False)
                    # new_item.refresh_from_db()
                    # new_item.wine.winemaker = new_winemaker
                    # new_item.wine.domain = new_winemaker.domain
                    # new_item.wine.region = new_winemaker.region
                    # new_item.wine.designation = new_winemaker.region
                    # new_item.wine.save()
                    #
                    # new_item.set_title_winepost()
                    # new_item.is_parent_post = True
                    # if cd['nat_oth'] and cd['nat_oth'] == 'natural':
                    #     new_item.status = PostStatusE.PUBLISHED
                    # elif cd['nat_oth'] and cd['nat_oth'] != 'natural':
                    #     new_item.status = PostStatusE.REFUSED
                    # elif item.status in [PostStatusE.DRAFT, PostStatusE.IN_DOUBT]:
                    #     new_item.status = PostStatusE.PUBLISHED
                    # elif item.status == PostStatusE.BIO_ORGANIC:
                    #     new_item.status = PostStatusE.BIO_ORGANIC
                    # elif item.status == PostStatusE.REFUSED:
                    #     new_item.status = PostStatusE.REFUSED
                    #
                    # new_item.save()
                    # new_item.wine.refresh_from_db()
                    # item = new_item

                # item.is_parent_post = cd['is_parent_post']
                # item.modified_time = dt.datetime.now()
                # item.save()
                # item.refresh_from_db()
                # if item.is_parent_post:
                #     other_pps = Post.objects.filter(wine=item.wine, is_parent_post=True).exclude(id=item.id)
                #     for other_pp in other_pps:
                #         other_pp.is_parent_post = False
                #         other_pp.save()

                if not item.is_star_review and cd['is_star_review']:
                    item.is_star_review = True
                    item.save()
                    item.refresh_from_db()
                    SenderNotifier().send_star_review_on_winepost(item)
                    other_srs = Post.objects.filter(wine=item.wine, is_star_review=True).exclude(id=item.id)
                    for other_sr in other_srs:
                        other_sr.is_star_review = False
                        other_sr.save()

            status = 'OK'
    result = {
        "status": status,
        "data": data,
        "count": Post.active.filter(type=PostTypeE.WINE).count()
    }
    return JsonResponse(result)


# /ajax/wineposts/mop-move-to-general-post
@csrf_exempt
@login_required
def wineposts_mop_move_to_general_post(request):
    get_current_user(request)
    data = {"ids": []}
    status = 'error'

    if request.method == 'POST':
        form = MassOperationIdsWinepostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            for item in cd['ids']:
                data["ids"].append(item.id)
                item.move_to_general_post()
            status = 'OK'
    result = {
        "status": status,
        "data": data,
        "count": Post.active.filter(type=PostTypeE.WINE).count()
    }
    return JsonResponse(result)


# # /ajax/wineposts/mop-update
# @csrf_exempt
# @login_required
# def wineposts_mop_update(request):
#     user = get_current_user(request)
#     data = {"ids": []}
#     status = 'error'
#
#     if request.method == 'POST':
#         form = MassOperationIdsWinepostExtendedForm(request.POST)
#         if form.is_valid():
#             cd = form.cleaned_data
#             for item in cd['ids']:
#                 data["ids"].append(item.id)
#                 item.is_parent_post = cd['is_parent_post']
#                 item.is_star_review = cd['is_star_review']
#                 item.modified_time = dt.datetime.now()
#                 item.save()
#                 item.refresh_from_db()
#             status = 'OK'
#
#     result = {
#         "status": status,
#         "data": data,
#         "count": Post.active.filter(type=PostTypeE.WINE).count()
#     }
#     return JsonResponse(result)
