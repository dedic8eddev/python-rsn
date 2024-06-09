from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from web.constants import PlaceStatusE
from web.forms.admin_forms import AjaxListForm
from web.models import Comment
from web.utils.exceptions import WrongParametersError
from web.utils.model_tools import cut_string
from web.utils.upload_tools import aws_url
from web.utils.views_common import (get_current_user, get_search_value,
                                    get_sorting)
from web.views.ajax_lists.common import ajax_list_control_parameters_by_form
from web.views.ajax_lists.formatting import format_user_html


# /ajax/est-com/items
@csrf_exempt
@login_required
def get_est_com_items(request):
    get_current_user(request)

    filter_criteria = {}
    page = None
    limit = None
    order_dir = 'desc'
    order_by = '-modified_time'

    start = None
    length = None
    search_value = None
    col_map = {
        0: None,  # 'id',
        1: 'modified_time',
        2: 'author__username',  # author img
        3: None,  # 'place__main_image',  # place img
        4: 'place__name',  # place name
        5: 'description',  # description
        6: 'place__status',  # description
    }

    if request.method == 'POST':
        form = AjaxListForm(request.POST)
        search_value = get_search_value(request)
        order_by = get_sorting(request, col_map, order_by, order_dir)
        if form.is_valid():
            cd = form.cleaned_data
            start = cd['start']
            length = cd['length']
            (
                page, limit, order_by_old, order_dir_old
            ) = ajax_list_control_parameters_by_form(cd)
        else:
            raise WrongParametersError(_("Wrong parameters."), form)

    filter_criteria = Q()
    if search_value is not None:
        filter_criteria = Q(
            description__unaccent__icontains=search_value
        ) | Q(
            place__name__unaccent__icontains=search_value
        ) | Q(
            author__username__unaccent__icontains=search_value
        )

    total_count = Comment.objects.filter(
        filter_criteria
    ).exclude(place=None).count()

    if limit:
        offset_0 = page * limit - limit
        offset_n = page * limit
    elif start is not None and length is not None:
        offset_0 = start
        offset_n = start + length
    else:
        offset_0 = None
        offset_n = None

    items = Comment.objects.filter(
        filter_criteria
    ).exclude(place=None).select_related(
        'place', 'place__main_image', 'author', 'author__image'
    ).order_by(order_by)[offset_0:offset_n]

    items_out = []

    for item in items:
        ph = '<a href="{}" data-toggle="lightbox" data-title="{}"><img width="35" height="35" data-src="{}" alt="{}"/></a>'  # noqa
        place_img_html = ph.format(
            aws_url(item.place.main_image), item.place.name,
            aws_url(item.place.main_image), item.place.name
        )

        desc_html = '<a href="{}">{}</a>'.format(
            reverse('view_comment', args=[item.id]),
            cut_string(item.description, 382) + "[{}]".format(
                len(item.description)
            )
        )

        if int(item.place.status) == PlaceStatusE.IN_DOUBT:
            status_text = '<button class="btn btn-xs indoubt">in doubt</button>'  # noqa
        elif int(item.place.status) == PlaceStatusE.DRAFT:
            status_text = '<button class="btn btn-xs onhold">DRAFT</button>'
        elif int(item.place.status) == PlaceStatusE.PUBLISHED:
            status_text = '<button class="btn btn-xs published">Published</button>'  # noqa
        elif int(item.place.status) == PlaceStatusE.SUBSCRIBER:
            status_text = '<button class="btn btn-xs subscriber">Subscriber</button>'  # noqa
        elif int(item.place.status) == PlaceStatusE.CLOSED:
            status_text = '<button class="btn btn-xs delete">Closed</button>'  # noqa
        elif int(item.status) == PlaceStatusE.ELIGIBLE:
            status_text = '<button class="btn btn-xs eligible">Eligible</button>'  # noqa
        elif int(item.status) == PlaceStatusE.NOT_ELIGIBLE:
            status_text = '<button class="btn btn-xs noteligible">Not Eligible</button>'  # noqa
        elif int(item.status) == PlaceStatusE.IN_REVIEW:
            status_text = '<button class="btn btn-xs inreview">In Review</button>'  # noqa
        elif int(item.status) == PlaceStatusE.TO_PUBLISH:
            status_text = '<button class="btn btn-xs topublish">To Publish</button>'  # noqa
        else:
            status_text = ""

        cb = '<input id="colors-{}-toggle-1" name="ids" value="{}" type="checkbox">'  # noqa

        item_out = {
            'checkbox_id': cb.format(item.id, item.id),
            'date': item.modified_time.strftime('%d %b %Y %H:%M'),
            'author_img_html': format_user_html(item.author),
            'place_img_html': place_img_html,
            'place_name': '<a href="{}">{}</a>'.format(
                reverse('edit_place', args=[item.place_id]),
                item.place.name
            ),
            'description': desc_html,
            'place_status': status_text,
        }
        items_out.append(item_out)

    return JsonResponse({
        "data": items_out,
        "iTotalRecords": total_count,
        "iTotalDisplayRecords": total_count,
    })
