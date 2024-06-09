from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from web.constants import CalEventStatusE
from web.forms.admin_forms import AjaxListForm
from web.models import CalEvent
from web.utils.exceptions import WrongParametersError
from web.utils.model_tools import cut_string, strip_tags
from web.utils.upload_tools import aws_url
from web.utils.views_common import get_search_value, get_sorting
from web.views.ajax_lists.common import ajax_list_control_parameters_by_form


# /ajax/event/items
@csrf_exempt
@login_required
def get_event_items(request):
    page = None
    limit = None
    order_dir = 'desc'
    order_by = '-modified_time'

    start = None
    length = None
    search_value = None
    col_map = {
        0: 'id',
        1: None,
        2: 'external_created_time',  # published AT
        3: 'start_date',
        4: 'external_author_name',  # author img
        5: 'title',  # event title
        6: 'description',  # description
        7: 'status',  # status
        8: None,  # geolocation
        9: None,  # geolocation
        10: None,  # geolocation
        11: None,  # geolocation
    }

    if request.method == 'POST':
        form = AjaxListForm(request.POST)
        search_value = get_search_value(request)
        order_by = get_sorting(request, col_map, order_by, order_dir)
        if form.is_valid():
            cd = form.cleaned_data
            start = cd['start']
            length = cd['length']
            (page, limit, order_by_old, order_dir_old) = ajax_list_control_parameters_by_form(cd)  # noqa
        else:
            raise WrongParametersError(_("Wrong parameters."), form)

    filter_criteria = Q()

    if search_value is not None:
        filter_criteria = (
            Q(description__unaccent__icontains=search_value) |
            Q(title__unaccent__icontains=search_value) |
            Q(loc_name__unaccent__icontains=search_value) |
            Q(author__username__unaccent__icontains=search_value) |
            Q(external_author_name__unaccent__icontains=search_value)
        )

        if search_value.upper() in CalEventStatusE.names_human:
            filter_criteria |= Q(
                status=CalEventStatusE.names_human[search_value.upper()]
            )

        date_formats = ['%b %Y', '%B %Y', '%b %y', '%B %y']
        match_date = None
        for date_format in date_formats:
            try:
                match_date = datetime.strptime(search_value, date_format)
                break
            except ValueError:
                pass

        if match_date:
            filter_criteria = Q(
                start_date__month=match_date.month,
                start_date__year=match_date.year
            )

    if limit:
        offset_0 = page * limit - limit
        offset_n = page * limit
    elif start is not None and length is not None:
        offset_0 = start
        offset_n = start + length
    else:
        offset_0 = None
        offset_n = None

    qs = CalEvent.active.filter(filter_criteria)

    total_count = qs.count()
    events = qs.order_by(order_by)[offset_0:offset_n]
    items_out = []

    for event in events:
        event_link = reverse('edit_event', args=[event.id])

        desc_text = strip_tags(event.description)
        desc_html = '<a href="{}">{}</a>[{}]'.format(
            event_link, cut_string(desc_text, 382), len(event.description if event.description else '')
        )

        title_html = '<a href="{}">{}</a>'.format(event_link, event.title)

        button_format = '<button class="btn btn-xs {}">{}</button>'
        if event.status == CalEventStatusE.DRAFT:
            status_text = button_format.format('onhold', 'DRAFT')
        elif event.status == CalEventStatusE.PUBLISHED:
            status_text = button_format.format('published', 'Published')
        else:
            status_text = ""

        img_template = '<a href="{}" data-toggle="lightbox"><img width="70" height="70" src="{}" /></a>'  # noqa
        img_html = img_template.format(
            aws_url(event.image), aws_url(event.image, thumb=True)
        )

        author_template = '<img width="35" height="35" src="{}" data-src="{}" alt="{}">'  # noqa
        if event.author:
            author_img_html = author_template.format(
                aws_url(event.author.image, thumb=True),
                aws_url(event.author.image, thumb=True),
                event.author.username
            )
        else:
            author_img_html = event.external_author_name

        geoloc = event.loc_name

        checkbox_template = '<input id="colors-%d-toggle-1" name="ids" value="{id}" type="checkbox">'  # noqa
        checkbox = checkbox_template.format(id=event.id)

        item_out = {
            'checkbox_id': checkbox,
            'event_img_html': img_html,
            'author_img_html': author_img_html,
            'title': title_html,
            'description': desc_html,
            'status': status_text,
            'geoloc': geoloc,
            'comment_number': event.comment_number,
            'likevote_number': event.likevote_number,
            'attn_number': event.attendees.count(),
            'date': event.start_date.strftime(
                '%d %b %Y, %H:%M'
            ) if event.start_date else None
        }

        published_at = event.published_at if event.published_at else event.external_created_time  # noqa

        if published_at:
            item_out['external_created_time'] = published_at.strftime(
                '%d %b %Y, %H:%M'
            )

        items_out.append(item_out)

    return JsonResponse({
        "data": items_out,
        "iTotalRecords": total_count,
        "iTotalDisplayRecords": total_count,
    })
