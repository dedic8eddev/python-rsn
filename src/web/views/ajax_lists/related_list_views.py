from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from web.constants import PostTypeE
from web.forms.admin_forms import EventRelatedListForm, PostRelatedListForm
from web.models import (Attendee, CalEvent, Comment, DrankItToo, LikeVote,
                        Place, Post)
from web.serializers.comments_likes import CommentSerializer, LikeVoteSerializer
from web.serializers.events import AttendeeSerializer
from web.serializers.places import PlaceWithExtraDataSerializer


# common function for fetching the list
def post_related_list_common(
    request, post, RelatedEntityClass, form_entity_page_field
):
    page = 1
    limit = None
    offset_0 = None
    offset_n = None

    if request.method == 'POST':
        form = PostRelatedListForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            limit = cd['limit'] if cd['limit'] else limit
            page = cd[form_entity_page_field] if cd[form_entity_page_field] else page  # noqa

    if limit:
        offset_0 = page * limit - limit
        offset_n = page * limit - limit

    # if offsets are not set (limit == None),
    # then we just have [None:None] which is OK
    items = RelatedEntityClass.active.filter(post=post).select_related(
        'post', 'wine', 'author'
    )[offset_0:offset_n]

    if RelatedEntityClass.__name__ == 'Comment':
        return CommentSerializer(
            items, many=True, context={'request': request}
        ).data, len(items)
    else:
        return LikeVoteSerializer(
            items, many=True, context={'request': request}
        ).data, len(items)


# common function for fetching the list
def place_related_list_common(
    request, place, RelatedEntityClass, form_entity_page_field
):
    page = 1
    limit = None
    offset_0 = None
    offset_n = None

    if request.method == 'POST':
        form = PostRelatedListForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            limit = cd['limit'] if cd['limit'] else limit
            page = cd[form_entity_page_field] if cd[form_entity_page_field] else page  # noqa

    if limit:
        offset_0 = page * limit - limit
        offset_n = page * limit - limit

    items = RelatedEntityClass.active.filter(
        place=place
    ).select_related('place', 'author')[offset_0:offset_n]

    if RelatedEntityClass.__name__ == 'Comment':
        return CommentSerializer(items, many=True).data
    else:
        return LikeVoteSerializer(items, many=True).data


# common function for fetching the list - events
def event_related_list_common(
    request, cal_event, RelatedEntityClass, form_entity_page_field
):
    page = 1
    limit = None
    offset_0 = None
    offset_n = None

    if request.method == 'POST':
        form = EventRelatedListForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            limit = cd['limit'] if cd['limit'] else limit
            page = cd[form_entity_page_field] if cd[form_entity_page_field] else page  # noqa

    if limit:
        offset_0 = page * limit - limit
        offset_n = page * limit - limit

    # if offsets are not set (limit == None),
    # then we just have [None:None] which is OK
    items = RelatedEntityClass.active.filter(
        cal_event=cal_event
    ).select_related('cal_event', 'author')[offset_0:offset_n]

    if RelatedEntityClass.__name__ == 'Comment':
        return CommentSerializer(items, many=True).data, len(items)
    elif RelatedEntityClass.__name__ == 'LikeVote':
        return LikeVoteSerializer(items, many=True).data, len(items)
    else:
        return AttendeeSerializer(items, many=True).data, len(items)


# /ajax/winepost/related-lists/{id}
@csrf_exempt
@login_required
def winepost_related_lists(request, id):
    c = {}
    post = Post.objects.get(id=id, type=PostTypeE.WINE)

    comments, comment_number = post_related_list_common(
        request, post, Comment, 'page_comments'
    )

    c["is_new"] = False

    c["post"] = post
    c["comments"] = comments
    c['comment_number'] = comment_number
    c["likevotes"], c["likevote_number"] = post_related_list_common(
        request, post, LikeVote, 'page_likes'
    )
    c["drank_it_toos"], c["drank_it_too_number"] = post_related_list_common(
        request, post, DrankItToo, 'page_drank_it_toos'
    )

    return render(request, "base/elements/edit/winepost.related-lists.html", c)


# /ajax/place/related-lists/{id}
@csrf_exempt
@login_required
def place_related_lists(request, id):
    c = {}
    place = Place.active.get(id=id)

    comments = place_related_list_common(
        request, place, Comment, 'page_comments'
    )

    c["is_new"] = False
    c["place"] = PlaceWithExtraDataSerializer(
        place, context={'request': request}
    ).data
    c["comments"] = comments
    c["likevotes"] = place_related_list_common(
        request, place, LikeVote, 'page_likes'
    )

    return render(request, "base/elements/edit/place.related-lists.html", c)


# /ajax/event/related-lists/{id}
@csrf_exempt
@login_required
def event_related_lists(request, id):
    c = {}
    parent_item = CalEvent.active.get(id=id)

    comments, comment_number = event_related_list_common(
        request, parent_item, Comment, 'page_comments'
    )

    c["is_new"] = False
    c["parent_item"] = parent_item
    c["attendees"], c["attendee_number"] = event_related_list_common(
        request, parent_item, Attendee, 'page_attns'
    )
    c["comments"] = comments
    c["comment_number"] = comment_number
    c["likevotes"], c["likevote_number"] = event_related_list_common(
        request, parent_item, LikeVote, 'page_likes'
    )

    return render(request, "base/elements/edit/event.related-lists.html", c)


# /post/related-lists/{id}
@csrf_exempt
@login_required
def generalpost_related_lists(request, id):
    c = {}
    post = Post.active.get(id=id, type=PostTypeE.NOT_WINE)

    comments, comment_number = post_related_list_common(
        request, post, Comment, 'page_comments'
    )

    c["is_new"] = False
    c["post"] = post
    c["comments"] = comments
    c["comment_number"] = comment_number
    c["likevotes"], c["likevote_number"] = post_related_list_common(
        request, post, LikeVote, 'page_likes'
    )

    return render(
        request, "base/elements/edit/generalpost.related-lists.html", c
    )


# /food/related-lists/{id}
@csrf_exempt
@login_required
def food_related_lists(request, id):
    c = {}
    post = Post.active.get(id=id, type=PostTypeE.FOOD)

    comments, comment_number = post_related_list_common(
        request, post, Comment, 'page_comments'
    )

    c["is_new"] = False
    c["post"] = post
    c["comments"] = comments
    c["comment_number"] = comment_number
    c["likevotes"], c["likevote_number"] = post_related_list_common(
        request, post, LikeVote, 'page_likes'
    )

    return render(
        request, "base/elements/edit/generalpost.related-lists.html", c
    )
