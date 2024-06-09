from web.constants import PostStatusE, PostTypeE
from web.models import DrankItToo, LikeVote, Post
from web.serializers.comments_likes import (DrankItTooUDSerializer,
                                            LikeVoteUDSerializer)
from web.serializers.users import UserWithVenuesSerializer
from web.serializers.posts import PostUDSerializer

from .model_tools import get_filter_criteria_for_order_last_id
from .views_common import list_last_id, prevent_using_non_active_account


def get_user_data_cd(cd, user, request=None, include_refused_wineposts=False):
    if include_refused_wineposts:
        allowed_wp_statuses = [PostStatusE.PUBLISHED, PostStatusE.DRAFT, PostStatusE.IN_DOUBT,
                               PostStatusE.REFUSED, PostStatusE.BIO_ORGANIC]
    else:
        allowed_wp_statuses = [PostStatusE.PUBLISHED, PostStatusE.DRAFT, PostStatusE.IN_DOUBT,
                               PostStatusE.BIO_ORGANIC]

    prevent_using_non_active_account(user)

    limit_all = cd['limit'] if 'limit' in cd and cd['limit'] else None
    get_likes = cd['get_likes'] if 'get_likes' in cd else False
    get_drank_it_toos = cd['get_drank_it_toos'] if 'get_drank_it_toos' in cd else False
    get_general_posts = cd['get_general_posts'] if 'get_general_posts' in cd else False
    get_wineposts = cd['get_wineposts'] if 'get_wineposts' in cd else False
    get_posts = cd['get_posts'] if 'get_posts' in cd else False
    get_star_reviews = cd['get_star_reviews'] if 'get_star_reviews' in cd else False

    like_last_id = cd['like_last_id'] if 'like_last_id' in cd and cd['like_last_id'] else None
    dit_last_id = cd['dit_last_id'] if 'dit_last_id' in cd and cd['dit_last_id'] else None
    post_last_id = cd['post_last_id'] if 'post_last_id' in cd and cd['post_last_id'] else None
    sr_last_id = cd['sr_last_id'] if 'sr_last_id' in cd and cd['sr_last_id'] else None

    general_post_last_id = None
    winepost_last_id = None

    general_posts_out = []
    wineposts_out = []
    posts_out = []
    star_reviews_out = []
    likes_out = []
    dits_out = []

    general_post_number = Post.active.filter(
        author=user, type=PostTypeE.NOT_WINE,
        status__in=[PostStatusE.DRAFT, PostStatusE.PUBLISHED, PostStatusE.IN_DOUBT]  # noqa
    ).count()

    winepost_number = Post.active.filter(
        author=user, type=PostTypeE.WINE, status__in=allowed_wp_statuses
    ).count()

    post_number = winepost_number + general_post_number

    sr_number = Post.active.filter(
        author=user, type=PostTypeE.WINE, is_star_review=True,
        status=PostStatusE.PUBLISHED
    ).count()

    like_number = user.likevote_number
    dit_number = user.drank_it_too_number

    if get_likes:
        filter_criteria_likes = get_filter_criteria_for_order_last_id("desc", like_last_id, {"author": user})
        likes = LikeVote.active.filter(**filter_criteria_likes).order_by('-created_time').\
            select_related('post', 'place')[0: limit_all]
        like_last_id = list_last_id(likes)
        likes_out = LikeVoteUDSerializer(likes, many=True).data

    if get_drank_it_toos:
        filter_criteria_dits = get_filter_criteria_for_order_last_id("desc", dit_last_id, {"author": user})
        dits = DrankItToo.active.filter(**filter_criteria_dits).order_by('-created_time')[0: limit_all]
        dit_last_id = list_last_id(dits)
        dits_out = DrankItTooUDSerializer(dits, many=True).data

    if get_general_posts or get_wineposts or get_posts:
        filter_criteria_posts = get_filter_criteria_for_order_last_id("desc", post_last_id, {
            "author": user,
            "status__in": allowed_wp_statuses})

        posts = Post.active.filter(**filter_criteria_posts).order_by('-created_time'). \
            select_related('place', 'wine', 'wine__main_image',
                           'wine__author', 'main_image',
                           'author', 'place__main_image', 'place__author')[0: limit_all]
        posts_out = PostUDSerializer(posts, many=True).data

        post_last_id = list_last_id(posts)

        general_posts = Post.active.filter(author=user, type=PostTypeE.NOT_WINE,
                                           status__in=[PostStatusE.DRAFT, PostStatusE.IN_DOUBT,
                                                       PostStatusE.PUBLISHED]).\
            order_by('-created_time').\
            select_related('place', 'main_image', 'author', 'place__main_image', 'place__author')[0: limit_all]

        general_post_last_id = list_last_id(general_posts)
        general_posts_out = PostUDSerializer(general_posts, many=True).data

        wineposts = Post.active.filter(author=user, type=PostTypeE.WINE, status__in=allowed_wp_statuses). \
            order_by('-created_time').select_related(
            'place', 'wine', 'wine__main_image', 'wine__author',
            'main_image', 'author', 'place__main_image', 'place__author')[0: limit_all]
        winepost_last_id = list_last_id(wineposts)
        wineposts_out = PostUDSerializer(wineposts, many=True).data

    if get_star_reviews:
        filter_criteria_srs = get_filter_criteria_for_order_last_id("desc", sr_last_id, {
            "author": user,
            "type": PostTypeE.WINE,
            "is_star_review": True,
            "status": PostStatusE.PUBLISHED})
        star_reviews = Post.active.filter(
            **filter_criteria_srs).order_by('-created_time').\
            select_related('place', 'wine', 'wine__main_image', 'wine__author',
                           'main_image', 'author', 'place__main_image',
                           'place__author')[0: limit_all]
        sr_last_id = list_last_id(star_reviews)
        star_reviews_out = PostUDSerializer(star_reviews, many=True).data

    result_data = {
        'user': UserWithVenuesSerializer(user,
                                         context={'request': request}).data,
        'likes': likes_out,
        'drank_it_toos': dits_out,
        'posts': posts_out,
        'star_reviews': star_reviews_out,

        'likevote_last_id': like_last_id,
        'drank_it_too_last_id': dit_last_id,
        'post_last_id': post_last_id,
        'star_review_last_id': sr_last_id,

        'like_number': like_number,
        'drank_it_too_number': dit_number,
        'star_review_number': sr_number,
        'post_number': post_number,
        'general_posts': general_posts_out,
        'wineposts': wineposts_out,

        'general_post_last_id': general_post_last_id,
        'winepost_last_id': winepost_last_id,
        'general_post_number': general_post_number,
        'winepost_number': winepost_number,
        # 'has_badge': has_badge,
        # 'badge_expiry_date_ms': badge_expiry_date_ms,
        # 'badge_expiry_date': badge_expiry_date,
    }
    return result_data


def get_user_data(request, user, include_refused_wineposts=False):
    cd = request.form.cleaned_data
    return get_user_data_cd(cd, user, request,
                            include_refused_wineposts=include_refused_wineposts)
