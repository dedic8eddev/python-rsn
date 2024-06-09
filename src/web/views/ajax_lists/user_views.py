from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from web.constants import UserStatusE, UserTypeE
from web.models import UserProfile
from web.views.ajax_lists.common import (
    ajax_list_control_with_search_and_ordering, ajax_list_get_offsets)
from web.views.ajax_lists.formatting import format_img_html


def format_users_default(items, user):
    items_out = []
    for item in items:
        img_html = '<div style="margin-left:50px; text-align: left; " class="picture-bigger">'  # noqa

        img_html += format_img_html(
            item.image, item.username,
            side_size=40, img_class="avatar",
            img_style="margin-left:10px; margin-right:10px;"
        )

        img_html += '<a href="{href}" title="{username}">{username}</a>'.format(
            href=reverse("edit_user", args=[item.id]), username=item.username
        )

        if item.status == UserStatusE.BANNED:
            img_html += '<i class="fa fa-lock activebblue"></i>'
        img_html += "</div>"

        full_name_html = '<a href="{href}" title="{full_name}">{full_name}</a>'.format(
            href=reverse("edit_user", args=[item.id]),
            full_name=item.full_name if item.full_name else ''
        )

        type_text = UserTypeE.names[item.type] if item.type in UserTypeE.names else ''

        if item.id != user.id and item.status != UserStatusE.BANNED:
            act = '<a data-original-title="Edit" href="{}" title="" class="btn btn-xs btn-outline btn-success ' \
                  'add-tooltip"> <i class="fa fa-pencil"></i></a>&nbsp;&nbsp; ' \
                  '<a data-original-title="Ban user" href="#" title="" class="btn btn-xs btn-outline btn-info ' \
                  'add-tooltip" id="ban_user_{}"  data-placement="top">' \
                  '<i class="fa fa-lock"></i></a>'
            action_edit = reverse('edit_user', kwargs={'id': item.id})
            action_ban = item.id
            actions_html = act.format(action_edit, action_ban)

            cb = '<input id="colors-{}-toggle-1" name="ids" value="{}" type="checkbox">'
            checkbox_html = cb.format(item.id, item.id)
        else:
            act = '<a data-original-title="Edit" href="{}" title="" class="btn btn-xs btn-outline btn-success ' \
                  'add-tooltip">' \
                  '<i class="fa fa-pencil"></i></a>&nbsp;&nbsp;'
            actions_html = act.format(
                reverse('edit_user', kwargs={'id': item.id})
            )

            cb = '<input id="colors-{}-toggle-1" name="ids" value="{}" type="checkbox" disabled="disabled">'  # noqa
            checkbox_html = cb.format(item.id, item.id)

        datetime_html = '<span class="date_space">{}</span><span>{}</span>'.format(
            item.modified_time.strftime('%d %b %Y'),
            item.modified_time.strftime('%H:%M')
        )

        item_out = {
            'checkbox_id': checkbox_html,
            'img_html': img_html,
            'full_name': full_name_html,
            'email': item.email,
            'post_number': item.posts_authored.count(),
            'star_review_number': item.posts_authored.filter(
                is_star_review=True, is_archived=False
            ).count(),
            'account_created': datetime_html,
            'type_text': type_text,
            'lang': item.lang,
            'actions': actions_html,
        }

        items_out.append(item_out)

    return items_out


# /ajax/user/items
@csrf_exempt
@login_required
def get_user_items(request):
    col_map = {
        0: 'id',
        1: 'username',
        2: 'full_name',
        3: 'email',

        4: 'all_posts_number',
        5: 'star_review_number',
        6: 'modified_time',
        7: 'type',

        8: 'lang',
        9: None,  # actions
    }

    (
        page, limit, start, length, search_value, order_by
    ) = ajax_list_control_with_search_and_ordering(
        request, col_map=col_map
    )

    (offset_0, offset_n) = ajax_list_get_offsets(start, length, page, limit)

    filters = Q()

    if search_value is not None:
        search_filters = Q(
            username__unaccent__icontains=search_value
        ) | Q(
            full_name__unaccent__icontains=search_value
        ) | Q(
            email__unaccent__icontains=search_value
        )

        filters = search_filters

    filters &= ~(
        Q(username__istartswith='genowner__') |
        Q(username__istartswith='testuser')
    )

    qs = UserProfile.objects.annotate(
        all_posts_number=Count('posts_authored__id'),
    ).filter(filters).order_by(
        *order_by
    ).select_related('author').prefetch_related(
        'posts_authored',
        'like_votes_authored',
        'comments_authored',
        'drank_it_toos_authored',
    )

    total_count = qs.count()
    users = qs[offset_0:offset_n]

    return JsonResponse({
        "iTotalRecords": total_count,
        "iTotalDisplayRecords": total_count,
        "data": format_users_default(users, request.user)
    })
