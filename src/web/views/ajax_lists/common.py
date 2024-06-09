from __future__ import absolute_import

import logging
import re

from django.utils.translation import ugettext_lazy as _

from web.forms.admin_forms import AjaxListForm
from web.utils.exceptions import WrongParametersError
from web.utils.views_common import (ajax_list_control_parameters_by_form,
                                    get_order_dir, get_search_value)

log = logging.getLogger(__name__)


def ajax_list_get_offsets(start, length, page, limit):
    if limit:
        offset_0 = page * limit - limit
        offset_n = page * limit
    elif start is not None and length is not None:
        offset_0 = start
        offset_n = start + length
    else:
        offset_0 = None
        offset_n = None

    res = (offset_0, offset_n)
    return res


def ajax_list_control_with_search_and_ordering(
    request, col_map, FormClass=AjaxListForm
):
    start = None
    length = None
    search_value = None
    page = None
    limit = None

    order_dir = 'desc'
    order_by = ['-modified_time']

    if request.method == 'POST':
        form = FormClass(request.POST)
        search_value = get_search_value(request)
        order_dir = get_order_dir(request, order_dir)

        if "order[0][column]" in request.POST:
            col = int(request.POST["order[0][column]"])
            if col in col_map and col_map[col]:
                if re.search('status', col_map[col]):
                    order_dir_el = '' if order_dir == 'asc' else '-'
                    order_by = [
                        order_dir_el + 'is_archived',
                        order_dir_el + 'status'
                    ]
                else:
                    order_by = [
                        col_map[col] if order_dir == 'asc' else "-" + col_map[col]  # noqa
                    ]
            else:
                order_by = ['-modified_time']

        if form.is_valid():
            cd = form.cleaned_data
            start = cd['start']
            length = cd['length']
            (
                page, limit, order_by_old, order_dir_old
            ) = ajax_list_control_parameters_by_form(cd)
        else:
            raise WrongParametersError(_("Wrong parameters."), form)

    ret_res = (page, limit, start, length, search_value, order_by)

    return ret_res
