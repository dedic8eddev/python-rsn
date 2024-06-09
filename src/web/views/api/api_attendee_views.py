from __future__ import absolute_import

import logging

from django.utils.translation import ugettext_lazy as _

from reports.models import BlockUser
from web.forms.api_forms import (AttendeeCreateForm, AttendeeDeleteForm,
                                 AttendeeListForm)
from web.models import Attendee, CalEvent
from web.serializers.events import AttendeeSerializer
from web.utils.api_handling import signed_api
from web.utils.exceptions import (ResultEmpty, ResultErrorError,
                                  WrongParametersError)
from web.utils.model_tools import get_filter_criteria_for_order_last_id
from web.utils.views_common import (list_control_parameters_by_form,
                                    list_last_id,
                                    prevent_using_non_active_account)

log = logging.getLogger(__name__)


# /api/events/attendees/add
@signed_api(
    FormClass=AttendeeCreateForm, token_check=True,
    json_used=True, success_status=200
)
def add_attendee(request):
    user = request.user

    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form = request.form

        if form.is_valid():
            cd = form.cleaned_data

            parent_item = CalEvent.active.get(id=cd['event_id'])
            attns = parent_item.attendees.filter(
                author=user, cal_event=parent_item
            )

            attn = attns.first() if attns.exists() else Attendee(
                author=user, cal_event=parent_item
            )

            attn.is_user_there = bool(cd['is_user_there'])
            attn.is_archived = False
            attn.save()
            attn.refresh_from_db()

            return AttendeeSerializer(attn).data

        else:
            raise WrongParametersError(_("Wrong parameters."), form)


# /api/events/attendees/delete
@signed_api(
    FormClass=AttendeeDeleteForm, token_check=True,
    json_used=True, success_status=200
)
def delete_attendee(request):
    user = request.user

    prevent_using_non_active_account(user)

    parent_item = None

    if request.method == 'POST':
        form = request.form

        if form.is_valid():
            cd = form.cleaned_data

            if cd['event_id']:
                parent_item = CalEvent.active.get(id=cd['event_id'])
                items = parent_item.attendees.filter(
                    author=user
                ).order_by('-id')

            elif cd['attendee_id']:
                items = Attendee.objects.filter(
                    id=cd['attendee_id'], author=user
                ).order_by('-id')

                if items:
                    item = items[0]
                    parent_item = item.cal_event
                    if not parent_item:
                        raise ResultErrorError(
                            "no parent item for like with id %d" % cd['likevote_id']  # noqa
                        )

            else:
                raise WrongParametersError(_("Wrong parameters."), form)

            if not items:
                raise ResultErrorError("no item to use")
            if not parent_item:
                raise ResultErrorError(
                    "no parent item (event) for this attendee it to"
                )

            for item in items:
                item.archive()
                item.refresh_from_db()

            return AttendeeSerializer(items[0]).data


# /api/events/attendees
@signed_api(FormClass=AttendeeListForm, token_check=False)
def get_attendees_list(request):
    user = request.user
    if user.is_authenticated:
        prevent_using_non_active_account(user)

    filter_criteria = {}

    if request.method == 'POST':
        form = request.form

        if form.is_valid():
            cd = form.cleaned_data

            item = CalEvent.active.get(id=cd['event_id'])
            filter_criteria['cal_event'] = item
            (
                limit, order_dir, last_id, order_by
            ) = list_control_parameters_by_form(cd)

            filter_criteria = get_filter_criteria_for_order_last_id(
                order_dir, last_id, filter_criteria
            )

            # exclude attendees who are blocked_users
            blocked_users = []
            if not user.is_authenticated:
                pass
            else:
                blocked_users = BlockUser.objects.filter(
                    user=user).values_list('block_user_id')

            attns = Attendee.active.filter(
                **filter_criteria
            ).exclude(
                author_id__in=blocked_users
            ).order_by(order_by).prefetch_related(
                'author__place_owner'
            )[0:limit]

            if not attns:
                raise ResultEmpty

            last_id = list_last_id(attns)

            attns_out = []

            if attns:
                attns_out = AttendeeSerializer(attns, many=True).data

            return {'attendees': attns_out, 'last_id': last_id}
