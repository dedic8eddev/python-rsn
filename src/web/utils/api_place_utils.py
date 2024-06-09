from __future__ import absolute_import

import datetime as dt
import json
import logging
import os

from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db.models import (Case, Exists, IntegerField, OuterRef, Q,
                              Subquery,
                              Value, When)

from my_chargebee.models import Subscription
from web.constants import (PostStatusE, PostTypeE, UserTypeE,
                           venue_wine_type_to_color_is_sparkling)
from web.models import Place, Post
from web.serializers.posts import (FoodPostAPISerializer, FullPostSerializer,
                                   MinimalWinePostAPISerializer,
                                   WinePostAPISerializer)
from web.utils.time import get_datetime_from_string

log = logging.getLogger(__name__)


# THIS IS "POSTED BY USERS" in the Application
# (lowest row under leftmost icon "Two bottles")
def get_recent_wine_posts(request, limit=None):
    if not limit:
        limit = 10

    recent_wine_posts = Post.active.filter(
        type=PostTypeE.WINE,
        place__isnull=False,
        place__subscription__isnull=False,
        place__subscription__status__in=[
            Subscription.ACTIVE, Subscription.IN_TRIAL
        ],
        author__type=UserTypeE.USER,
        status=PostStatusE.PUBLISHED
    ).order_by('-modified_time')[0:limit]

    return FullPostSerializer(
        recent_wine_posts, many=True, context={
            'request': request,
            'include_wine_data': True,
            'include_winemaker_data': True
        }
    ).data


def get_food_posts(request, place, limit=None):
    if request.user.is_authenticated:
        food_posts = Post.active.annotate(
            is_my_property=Case(
                When(place__owner=request.user, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).filter(
            place=place,
            type=PostTypeE.FOOD,
            status=PostStatusE.PUBLISHED
        ).order_by('-is_my_property', '-created_time')
    else:
        food_posts = Post.active.filter(
            place=place,
            type=PostTypeE.FOOD,
            status=PostStatusE.PUBLISHED
        ).order_by('-created_time')
    food_posts_count = food_posts.count()
    food_posts = FoodPostAPISerializer(
        food_posts, many=True, context={'request': request}
    ).data

    if limit:
        food_posts = food_posts[0:limit]
        food_posts_count = len(food_posts)

    return food_posts_count, food_posts


def get_wine_posts(request, place, limit=None, wp_type=None, minimal=False):
    if wp_type and wp_type in venue_wine_type_to_color_is_sparkling:
        color, is_sparkling = venue_wine_type_to_color_is_sparkling[wp_type]
    else:
        color, is_sparkling = None, False

    filters = {
        'place': place,
        'type': PostTypeE.WINE
    }

    if color:
        filters['wine__color'] = color
        # this will exclude all sparking wines from any other colors tab
        filters['wine__is_sparkling'] = False

    if is_sparkling:
        filters['wine__is_sparkling'] = True
    if request.user.is_authenticated:
        wine_posts = Post.active.annotate(
            is_my_property=Case(
                When(place__owner=request.user, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).filter(**filters).order_by('-is_my_property', '-created_time')
    else:
        wine_posts = Post.active.filter(**filters).order_by('-created_time')

    wine_posts_count = wine_posts.count()
    if minimal:
        wine_posts = MinimalWinePostAPISerializer(
            wine_posts, many=True, context={'request': request}
        ).data
    else:
        wine_posts = WinePostAPISerializer(
            wine_posts, many=True, context={'request': request}
        ).data

    if limit:
        wine_posts = wine_posts[0:limit]
        wine_posts_count = len(wine_posts)

    return wine_posts_count, wine_posts


def get_closest_venues(lat, lng, limit=10, owner=None, user=None):
    log.debug("CLOSEST VENUES - LAT %s LNG %s " % (lat, lng))
    ref_location = Point(float(lng), float(lat), srid=4326)

    wp_qs = fp_qs = Place.app_active.annotate(
        distance=Distance("point", ref_location)
    )

    wp_filters = fp_filters = Q(
        subscription__isnull=False,
        subscription__status__in=[Subscription.ACTIVE, Subscription.IN_TRIAL]
    )

    if owner:
        wp_qs = wp_qs.annotate(
            is_my_property=Case(
                When(owner_id=owner.id, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        )

        fp_qs = fp_qs.annotate(
            is_my_property=Case(
                When(owner_id=owner.id, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        )

    non_archived_wineposts = Post.active.filter(
        Q(
            place_id=OuterRef('pk'),
            type=PostTypeE.WINE,
            wine__is_archived=False,
            wine__winemaker__is_archived=False,
        ) & (
            Q(main_image_id__isnull=False) |
            Q(wine__main_image_id__isnull=False)
        )
    ).order_by('-created_time')

    non_archived_foodposts = Post.active.filter(
        place_id=OuterRef('pk'),
        type=PostTypeE.FOOD,
        main_image_id__isnull=False
    ).order_by('-created_time')

    fp_qs = fp_qs.annotate(
        latest_fp=Subquery(non_archived_foodposts.values('id')[:1]),
        has_non_archived_foodposts=Exists(non_archived_foodposts)
    )

    wp_qs = wp_qs.annotate(
        latest_wp=Subquery(non_archived_wineposts.values('id')[:1]),
        has_non_archived_wineposts=Exists(non_archived_wineposts),
    )

    wp_filters &= Q(has_non_archived_wineposts=True)
    fp_filters &= Q(has_non_archived_foodposts=True)

    wp_qs = wp_qs.filter(wp_filters)
    fp_qs = fp_qs.filter(fp_filters)

    if owner:
        wp_qs = wp_qs.order_by('-is_my_property', 'distance')
        fp_qs = fp_qs.order_by('-is_my_property', 'distance')
    else:
        wp_qs = wp_qs.order_by('distance')
        fp_qs = fp_qs.order_by('distance')

    return wp_qs[0:limit], fp_qs[0:limit]


def save_cached_place_ocs(items_out):
    file_path_abs = os.path.join(
        settings.MEDIA_ROOT, 'data', 'open-closed-status.txt'
    )
    data_out = {
        'modified_time': dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'items': items_out,
    }
    json_txt = json.dumps(data_out)
    with open(file_path_abs, 'w') as f:
        f.write(json_txt)
    f.close()


# TODO - for now it's not used but it might be useful when there's more places;
# we're still saving the OCS
# TODO - with save_cached_place_ocs
def get_cached_place_ocs_if_available():
    dt_now = dt.datetime.now()
    file_path_abs = os.path.join(
        settings.MEDIA_ROOT, 'data', 'open-closed-status.txt'
    )
    if not os.path.exists(file_path_abs):
        return None

    with open(file_path_abs) as f:
        data = f.read()
    f.close()
    if not data:
        return None
    try:
        data_json = json.loads(data)
    except json.JSONDecodeError:
        return None
    except ValueError:
        return None
    except Exception:
        return None
    if (
        not data_json or
        'modified_time' not in data_json or
        not data_json['modified_time']
    ):
        return None
    mod_dt = get_datetime_from_string(
        data_json['modified_time']
    )  # '%Y-%m-%dT%H:%M:%S'
    if not mod_dt and mod_dt < dt_now - dt.timedelta(minutes=5):
        return None
    return data_json
