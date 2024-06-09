from django.db.models import Q

from web.constants import PostTypeE, UserTypeE, WineColorE
from web.models import Place, Post
from web.serializers.wineposts import FoodPostSerializer, WinePostSerializer


def get_wine_number(pid, color):
    qs = Post.active.filter(
        type=PostTypeE.WINE,
        wine_id__isnull=False,
        place_id=pid
    )

    try:
        place = Place.objects.get(pk=pid)
    except Place.DoesNotExist:
        return Post.objects.none()

    qs = qs.filter(
        Q(author=place.owner) | Q(author__type=UserTypeE.ADMINISTRATOR)
    )

    if color == 'sparkling':
        qs = qs.filter(wine__is_sparkling=True)
    else:
        qs = qs.filter(
            wine__color=WineColorE.reverse_names[color.upper()]
        )

    return qs.count()


def get_latest_wines(pid):
    qs = Post.active.filter(
        type=PostTypeE.WINE,
        wine_id__isnull=False,
        place_id=pid
    ).order_by('-modified_time')

    try:
        place = Place.objects.get(pk=pid)
    except Place.DoesNotExist:
        return Post.objects.none()

    qs = qs.filter(
        Q(author=place.owner) | Q(author__type=UserTypeE.ADMINISTRATOR)
    )

    qs = qs[:3]

    return [WinePostSerializer(w).data for w in qs]


def get_latest_food(pid):
    qs = Post.active.filter(
        type=PostTypeE.FOOD,
        place_id=pid
    ).order_by('-modified_time')

    try:
        place = Place.active.get(pk=pid)
    except Place.DoesNotExist:
        return Post.objects.none()

    qs = qs.filter(
        Q(author=place.owner) | Q(author__type=UserTypeE.ADMINISTRATOR)
    )

    col1 = qs[:3]
    col2 = qs[3:6]

    return {
        'col1': [FoodPostSerializer(f).data for f in col1],
        'col2': [FoodPostSerializer(f).data for f in col2]
    }
