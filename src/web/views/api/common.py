from web.models import TimeLineItem, select_star_review_for_winepost
from web.constants import PostTypeE
from web.utils.exceptions import ResultErrorError
from web.serializers.timeline import TimeLineItemSerializer


def get_newest_tl_dict_for_post_and_send_sr_if_needed(request, post):
    parent_item_field = 'post_item'
    tl_items = TimeLineItem.active.filter(**{parent_item_field: post}). \
        order_by('-id')
    if not tl_items:
        raise ResultErrorError("no TL item for the parent item - %s with id: %d" %
                               (parent_item_field, post.id))
    if post.type == PostTypeE.WINE:
        select_star_review_for_winepost(post)
    return TimeLineItemSerializer(tl_items[0], context={
        'request': request,
        'include_wine_data': True,
        'include_winemaker_data': True,
    }).data
