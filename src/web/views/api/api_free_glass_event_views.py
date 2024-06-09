from __future__ import absolute_import

import datetime as dt
import logging

import django.db.utils
import psycopg2
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from web.constants import PlaceStatusE
from web.forms.api_forms import (GotFreeGlassCreateForm, GotFreeGlassDeleteForm,
                                 GotFreeGlassGetForm, GotFreeGlassListForm)
from web.models import FreeGlassEvent, GetMyFreeGlass, GotFreeGlass, Place
from web.serializers.comments_likes import GetMyFreeGlassSerializer
from web.utils.api_handling import signed_api
from web.utils.exceptions import ResultEmpty, WrongParametersError
from web.utils.model_tools import get_filter_criteria_for_order_last_id
from web.utils.sendernotifier import SenderNotifier
from web.utils.views_common import (list_control_parameters_by_form,
                                    list_last_id,
                                    prevent_using_non_active_account)

log = logging.getLogger(__name__)


@signed_api(FormClass=None, token_check=False)
def get_free_glass_event(request):
    evts = FreeGlassEvent.active.all()
    if evts and evts[0].start_date and evts[0].end_date:
        evt = evts[0]
    else:
        return {}

    date_now = timezone.now().date()

    date_event_start = evt.start_date.date() if evt.start_date else None
    date_event_end = evt.end_date.date() if evt.end_date else None
    announcement_date = evt.announcement_date.date() if evt.announcement_date else None

    days_to_event_start = (date_event_start - date_now).days if date_event_start else None
    days_to_event_end = (date_event_end - date_now).days if date_event_end else None
    days_to_announcement = (announcement_date - date_now).days if announcement_date else None

    show_full_screen = True if announcement_date and date_event_end and (announcement_date <= date_now <=
                                                                         date_event_end) else False

    return {
        'name': evt.name,
        'start_date': date_event_start,
        'end_date': date_event_end,
        'announcement_date': announcement_date,
        'days_to_event_start': days_to_event_start,
        'days_to_event_end': days_to_event_end,
        'days_to_announcement': days_to_announcement,
        'show_full_screen': show_full_screen,
    }


# /api/free-glass-events/get-my/add
@signed_api(FormClass=GotFreeGlassCreateForm, token_check=True, json_used=True, success_status=200)
def add_get_my_free_glass(request):
    user = request.user
    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data
            place = Place.active.get(id=cd['place_id'],
                                     status__in=[PlaceStatusE.PUBLISHED,
                                                 PlaceStatusE.SUBSCRIBER,
                                                 PlaceStatusE.DRAFT,
                                                 PlaceStatusE.IN_DOUBT],
                                     free_glass=True)
            item = GetMyFreeGlass(
                place=place,
                author=request.user)
            item.save()
            item.refresh_from_db()

            place.free_glass_last_action_date = dt.datetime.now()
            # place.modified_time = place.modified_time
            place.save_keep_modified_dt()
            place.refresh_from_db()
            return GetMyFreeGlassSerializer(item).data
        else:
            raise WrongParametersError(_("Wrong parameters."), form)


# /api/free-glass-events/get-my/check
@signed_api(FormClass=GotFreeGlassGetForm, token_check=True)
def get_get_my_free_glass(request):
    user = request.user
    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data
            place = Place.active.get(id=cd['place_id'])
            items = GetMyFreeGlass.active.filter(place=place, author=request.user)
            if items:
                return {'place_i_getmy': True}
            else:
                return {'place_i_getmy': False}
    raise WrongParametersError(_("Wrong parameters."), form)


# /api/free-glass-events/i-got/add
@signed_api(FormClass=GotFreeGlassCreateForm, token_check=True, json_used=True, success_status=200)
def add_got_free_glass(request):
    user = request.user
    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data
            place = Place.active.get(id=cd['place_id'],
                                     status__in=[PlaceStatusE.PUBLISHED,
                                                 PlaceStatusE.SUBSCRIBER,
                                                 PlaceStatusE.DRAFT,
                                                 PlaceStatusE.IN_DOUBT],
                                     free_glass=True)

            # old_items = GotFreeGlass.active.filter(place=place, author=request.user)
            # old_items = None
            # if old_items:
            #     item = old_items[0]
            # else:

            already_added_error = False
            item = GotFreeGlass(
                place=place,
                author=request.user
            )
            try:
                item.save()
            except django.db.utils.IntegrityError:
                already_added_error = True
            except psycopg2.IntegrityError:
                already_added_error = True
            except Exception:
                already_added_error = True

            if already_added_error:
                return GetMyFreeGlassSerializer(item).data
            else:
                item.refresh_from_db()
                place.free_glass_last_action_date = dt.datetime.now()
                place.save_keep_modified_dt()
                place.refresh_from_db()
                cur_events = FreeGlassEvent.active.all()
                if cur_events:
                    cur_event = cur_events[0]
                    date_today = dt.date.today()
                    if cur_event.start_date.date() <= date_today <= cur_event.end_date.date():
                        SenderNotifier().send_with_free_glass(request.user, place)

            return GetMyFreeGlassSerializer(item).data
        else:
            raise WrongParametersError(_("Wrong parameters."), form)


# /api/free-glass-events/i-got/del
@signed_api(FormClass=GotFreeGlassDeleteForm, token_check=True, json_used=True, success_status=200)
def delete_got_free_glass(request):
    user = request.user
    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data
            if cd['place_id']:
                place = Place.active.get(id=cd['place_id'])
                items = GotFreeGlass.active.filter(place=place, author=request.user)
                if items:
                    items[0].archive()
                    items[0].refresh_from_db()
            elif cd['id']:
                items = GotFreeGlass.active.filter(id=cd['id'])
                if items:
                    items[0].archive()
                    items[0].refresh_from_db()

            return {}

    raise WrongParametersError(_("Wrong parameters."), form)


# /api/free-glass-events/i-got/check
@signed_api(FormClass=GotFreeGlassGetForm, token_check=True)
def get_i_got_free_glass(request):
    user = request.user
    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data
            place = Place.active.get(id=cd['place_id'])
            items = GotFreeGlass.active.filter(place=place, author=request.user)
            if items:
                return {'i_got_free_glass': True}
            else:
                return {'i_got_free_glass': False}

    raise WrongParametersError(_("Wrong parameters."), form)


# /api/free-glass-events/list
@signed_api(FormClass=GotFreeGlassListForm, token_check=True, log_response_data=False)
def get_got_free_glass_list(request):
    user = request.user
    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form = request.form

        if form.is_valid():
            cd = form.cleaned_data
            place = Place.active.get(id=cd['place_id'])

            (limit, order_dir, last_id, order_by) = list_control_parameters_by_form(cd, default_limit=None)
            filter_criteria = {'place': place, 'author': request.user}
            filter_criteria = get_filter_criteria_for_order_last_id(order_dir, last_id, filter_criteria)
            items = GotFreeGlass.active.filter(**filter_criteria).order_by(order_by)[0:limit]
            if not items:
                raise ResultEmpty

            last_id = list_last_id(items)
            likevotes_out = GetMyFreeGlassSerializer(items, many=True).data
            return {'likes': likevotes_out, 'last_id': last_id}
    raise WrongParametersError(_("Wrong parameters."), form)
