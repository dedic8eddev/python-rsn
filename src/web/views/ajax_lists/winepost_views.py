import operator
from functools import reduce

from django.contrib.auth.decorators import login_required
from django.db.models import Case, Count, CharField, IntegerField, Q, Value,\
    When
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from web.constants import PostStatusE, PostTypeE, UserTypeE, WinePostListForE
from web.models import Post, Wine, Winemaker
from web.serializers.post_html_serializers import (
    WinepostForRefereeSerializer, WinepostForWinemakerSerializer,
    WinepostForWinepostSerializer, WinepostWithVuforiaSerializer)
from web.utils.views_common import get_current_user
from web.views.ajax_lists.common import (
    ajax_list_control_with_search_and_ordering, ajax_list_get_offsets)
from web.views.ajax_lists.winepost_maps import (
    winepost_items_col_map_for_user, winepost_items_col_map_for_winemaker,
    winepost_items_col_map_for_winepost, winepost_items_col_map_referees,
    winepost_items_col_map_with_vuforia)


def get_winepost_items_common(
    request, filter_criteria=Q(),
    serializer=WinepostWithVuforiaSerializer,
    col_map=winepost_items_col_map_with_vuforia,
):
    page = None
    limit = None
    order_by = ['-modified_time']
    start = None
    length = None
    search_value = None

    (
        page, limit, start, length, search_value, order_by
    ) = ajax_list_control_with_search_and_ordering(
        request,
        col_map=col_map
    )
    (offset_0, offset_n) = ajax_list_get_offsets(start, length, page, limit)

    filter_criteria &= Q(type=PostTypeE.WINE)

    if search_value:
        if search_value.lower() in [
            'draft', 'in doubt', 'natural', 'not natural',
            'bio-organic', 'deleted'
        ]:
            q_search = Q(status_s__icontains=search_value)
        elif search_value.lower() == 'question':
            q_search = Q(wine__winemaker__status=20) & (
                Q(wine__status=10) |
                Q(status=10) |
                Q(status=15)
            )

        else:
            search_filters = {
                Q(title__unaccent__icontains=search_value),
                Q(wine__name__unaccent__icontains=search_value),
                Q(wine__winemaker__name__unaccent__icontains=search_value),
                Q(wine__winemaker__domain__unaccent__icontains=search_value),
                Q(wine__winemaker__region__unaccent__icontains=search_value),
                Q(wine_year=search_value),
                Q(author__username__unaccent__icontains=search_value),
                Q(expert__username__unaccent__icontains=search_value),
                Q(place__name__unaccent__icontains=search_value)
            }

            q_search = reduce(operator.or_, search_filters)

        filter_criteria &= q_search

    qs = Post.objects.annotate(
        status_s=Case(
            When(status=PostStatusE.DRAFT, then=Value("draft")),
            When(status=PostStatusE.IN_DOUBT, then=Value("in doubt")),
            When(status=PostStatusE.PUBLISHED, then=Value("natural")),
            When(status=PostStatusE.REFUSED, then=Value("not natural")),
            When(status=PostStatusE.BIO_ORGANIC, then=Value("bio-organic")),
            When(status=PostStatusE.DELETED, then=Value("deleted")),
            output_field=CharField(),
        )
    ).filter(filter_criteria).order_by(*order_by)

    total_count = qs.count()
    items = qs[offset_0: offset_n]

    items_out = serializer(items, many=True).data

    return JsonResponse({
        "iTotalRecords": total_count,
        "iTotalDisplayRecords": total_count,
        "data": items_out
    })


# /ajax/winepost/items-opti
@csrf_exempt
@login_required
def get_winepost_items_opti(request, list_for):
    print('---------------')
    get_current_user(request)

    if list_for == WinePostListForE.USERS:
        filter_criteria = Q(author__type=UserTypeE.USER)
    elif list_for == WinePostListForE.OWNERS:
        filter_criteria = Q(author__type__in=[
            UserTypeE.OWNER,
        ])
    elif list_for == WinePostListForE.GEOLOCATED:
        filter_criteria = Q(
            place__isnull=False,
            author__type=UserTypeE.USER
        )
    elif list_for == WinePostListForE.ALL:
        filter_criteria = Q()
    else:
        filter_criteria = Q()

    return get_winepost_items_common(
        request,
        serializer=WinepostWithVuforiaSerializer,
        col_map=winepost_items_col_map_with_vuforia(),
        filter_criteria=filter_criteria
    )


# /ajax/all-referees/
@csrf_exempt
@login_required
def get_all_referee_items(request):
    get_current_user(request)

    filter_criteria = Q(
        is_parent_post=True,
        status=PostStatusE.PUBLISHED
    )

    return get_winepost_items_common(
        request,
        serializer=WinepostForRefereeSerializer,
        col_map=winepost_items_col_map_referees(),
        filter_criteria=filter_criteria
    )


# /ajax/all-star-reviews/
@csrf_exempt
@login_required
def get_all_star_review_items(request):
    get_current_user(request)

    filter_criteria = Q(
        is_star_review=True,
        status=PostStatusE.PUBLISHED
    )

    return get_winepost_items_common(
        request,
        serializer=WinepostForRefereeSerializer,
        col_map=winepost_items_col_map_referees(),
        filter_criteria=filter_criteria
    )


# /ajax/userpost/items/{uid}  - userposts
@csrf_exempt
@login_required
def get_userpost_items(request, uid):
    get_current_user(request)

    filter_criteria = Q(
        Q(author_id=uid) | Q(validated_by_id=uid) |
        Q(expert_id=uid) | Q(last_modifier_id=uid)
    )

    return get_winepost_items_common(
        request,
        serializer=WinepostForRefereeSerializer,
        col_map=winepost_items_col_map_for_user(),
        filter_criteria=filter_criteria
    )


# /ajax/winepost/referee-items/wine/{id}
@csrf_exempt
@login_required
def get_winepost_referee_items_for_wine(request, id):
    get_current_user(request)
    wine = Wine.objects.get(id=id)

    filter_criteria = Q(
        wine=wine,
        is_parent_post=True,
        status=PostStatusE.PUBLISHED
    )

    return get_winepost_items_common(
        request,
        serializer=WinepostForRefereeSerializer,
        col_map=winepost_items_col_map_referees(),
        filter_criteria=filter_criteria
    )


# /ajax/winepost/star-reviews/wine/{id}
@csrf_exempt
@login_required
def get_winepost_star_review_items_for_wine(request, id):
    get_current_user(request)
    wine = Wine.objects.get(id=id)

    filter_criteria = Q(
        wine=wine,
        is_star_review=True,
        status=PostStatusE.PUBLISHED
    )

    return get_winepost_items_common(
        request,
        serializer=WinepostForRefereeSerializer,
        col_map=winepost_items_col_map_referees(),
        filter_criteria=filter_criteria
    )


# /ajax/winepost/referee-items/winepost/{id}
# used for "There is already a similar Parent Post/Referrer"
@csrf_exempt
@login_required
def get_winepost_referee_items_for_winepost(request, id):
    get_current_user(request)
    winepost = Post.objects.get(id=id, type=PostTypeE.WINE)

    filter_criteria = Q(
        wine=winepost.wine,
        is_parent_post=True
    ) & ~Q(id=id, status=PostStatusE.DRAFT)

    return get_winepost_items_common(
        request,
        serializer=WinepostForRefereeSerializer,
        col_map=winepost_items_col_map_referees(),
        filter_criteria=filter_criteria
    )


# /ajax/winepost/referee/items/winemaker/{id}
@csrf_exempt
@login_required
def get_winepost_referee_items_for_winemaker(request, id):
    get_current_user(request)
    winemaker = Winemaker.active.get(id=id)

    filter_criteria = Q(
        wine__winemaker=winemaker,
        status=PostStatusE.PUBLISHED
    )

    return get_winepost_items_common(
        request,
        serializer=WinepostForWinemakerSerializer,
        filter_criteria=filter_criteria,
        col_map=winepost_items_col_map_for_winemaker(),
    )


# /ajax/winepost/star-reviews/winemaker/{id}
@csrf_exempt
@login_required
def get_winepost_star_review_items_for_winemaker(request, id):
    get_current_user(request)
    winemaker = Winemaker.active.get(id=id)

    filter_criteria = Q(
        wine__winemaker=winemaker,
        status=PostStatusE.PUBLISHED,
        is_star_review=True
    )

    return get_winepost_items_common(
        request,
        serializer=WinepostForWinemakerSerializer,
        filter_criteria=filter_criteria,
        col_map=winepost_items_col_map_for_winemaker(),
    )


# /ajax/winepost/items/winemaker/{id}
@csrf_exempt
@login_required
def get_winepost_items_for_winemaker(request, id):
    get_current_user(request)
    winemaker = Winemaker.active.get(id=id)
    serializer = WinepostForWinemakerSerializer

    filter_criteria = Q(
        wine__winemaker=winemaker,
        type=PostTypeE.WINE,
        author__type__in=[
            UserTypeE.USER, UserTypeE.ADMINISTRATOR, UserTypeE.OWNER
        ]
    )

    (
        page, limit, start, length, search_value, order_by
    ) = ajax_list_control_with_search_and_ordering(
        request,
        col_map=winepost_items_col_map_for_winemaker()
    )
    (offset_0, offset_n) = ajax_list_get_offsets(start, length, page, limit)

    if search_value:
        if search_value.lower() in [
            'draft', 'in doubt', 'natural', 'not natural',
            'bio-organic', 'deleted'
        ]:
            q_search = Q(status_s__icontains=search_value)
        elif search_value.lower() == 'question':
            q_search = Q(wine__winemaker__status=20) & (
                Q(wine__status=10) |
                Q(status=10) |
                Q(status=15)
            )

        else:
            search_filters = {
                Q(title__unaccent__icontains=search_value),
                Q(wine__name__unaccent__icontains=search_value),
                Q(wine__winemaker__name__unaccent__icontains=search_value),
                Q(wine__winemaker__domain__unaccent__icontains=search_value),
                Q(wine__winemaker__region__unaccent__icontains=search_value),
                Q(wine_year=search_value),
                Q(author__username__unaccent__icontains=search_value),
                Q(expert__username__unaccent__icontains=search_value),
                Q(place__name__unaccent__icontains=search_value)
            }

            q_search = reduce(operator.or_, search_filters)

        filter_criteria &= q_search

    qs = Post.active.annotate(
        status_s=Case(
            When(status=PostStatusE.DRAFT, then=Value("draft")),
            When(status=PostStatusE.IN_DOUBT, then=Value("in doubt")),
            When(status=PostStatusE.PUBLISHED, then=Value("natural")),
            When(status=PostStatusE.REFUSED, then=Value("not natural")),
            When(status=PostStatusE.BIO_ORGANIC, then=Value("bio-organic")),
            When(status=PostStatusE.DELETED, then=Value("deleted")),
            output_field=CharField(),
        )
    ).filter(filter_criteria).order_by(*order_by)

    qs = qs.annotate(
        wine_parent_posts_count=Count(
            Case(When(wine__posts__is_parent_post=True, then=1),
                 output_field=IntegerField(),
                 )
        )
    ).filter(Q(wine_parent_posts_count=0) | Q(is_parent_post=True))

    total_count = qs.count()
    items = qs[offset_0: offset_n]

    items_out = serializer(items, many=True).data

    return JsonResponse({
        "iTotalRecords": total_count,
        "iTotalDisplayRecords": total_count,
        "data": items_out
    })


# /ajax/winepost/items/winepost-vuforia/{id}
@csrf_exempt
@login_required
def get_winepost_items_for_winepost_vuforia(request, id):
    get_current_user(request)
    winepost = Post.objects.get(id=id, type=PostTypeE.WINE)

    filter_criteria = Q(
        wine_id=winepost.wine_id
    ) & ~Q(pk=id)

    return get_winepost_items_common(
        request,
        serializer=WinepostForWinepostSerializer,
        filter_criteria=filter_criteria,
        col_map=winepost_items_col_map_for_winepost(),
    )
