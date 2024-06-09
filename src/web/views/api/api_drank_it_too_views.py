from __future__ import absolute_import

import logging

from django.utils.translation import ugettext_lazy as _

from reports.models import BlockUser
from web.constants import PostTypeE, TimeLineItemTypeE
from web.forms.api_forms import (DrankItTooCreateForm, DrankItTooDeleteForm,
                                 DrankItTooListForm)
from web.models import DrankItToo, Post, TimeLineItem, UserProfile, Wine
from web.serializers.comments_likes import DrankItTooSerializer
from web.utils.api_handling import signed_api
from web.utils.exceptions import (ResultEmpty, ResultErrorError,
                                  WrongParametersError)
from web.utils.model_tools import get_filter_criteria_for_order_last_id
from web.utils.views_common import (list_control_parameters_by_form,
                                    list_last_id,
                                    prevent_using_non_active_account)

from .common import get_newest_tl_dict_for_post_and_send_sr_if_needed

log = logging.getLogger(__name__)


# /api/drankittoos/add
@signed_api(FormClass=DrankItTooCreateForm, token_check=True, json_used=True, success_status=200)
def add_drank_it_too(request):
    user = request.user
    prevent_using_non_active_account(user)
    tl_item = None

    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data
            if cd['tl_id']:
                tl_item = TimeLineItem.active.get(id=cd['tl_id'], item_type=TimeLineItemTypeE.POST)
                parent_item = tl_item.get_item()
            elif cd['post_id']:
                parent_item = Post.active.get(id=cd['post_id'], type=PostTypeE.WINE)
            else:
                raise WrongParametersError(_("Wrong parameters - neither post_id nor tl_id provided"), form)

            drank_it_toos = DrankItToo.active.filter(**{'author': user, 'post': parent_item})
            if not drank_it_toos:
                drank_it_too = DrankItToo(**{'author': user, 'post': parent_item})
                drank_it_too.save()
                parent_item.refresh_from_db()
                if tl_item:
                    tl_item.refresh_from_db()

            return get_newest_tl_dict_for_post_and_send_sr_if_needed(request, parent_item)
        else:
            raise WrongParametersError(_("Wrong parameters - form is not valid."), form)


# /api/drankittoos/delete
@signed_api(FormClass=DrankItTooDeleteForm, token_check=True, json_used=True, success_status=200)
def delete_drank_it_too(request):
    user = request.user
    prevent_using_non_active_account(user)
    tl_item = None
    parent_item = None
    if request.method == 'POST':
        form = request.form

        if form.is_valid():
            cd = form.cleaned_data
            if cd['post_id']:
                parent_item = Post.active.get(id=cd['post_id'])
                items = DrankItToo.active.filter(post=parent_item, author=user).order_by('-id')
            elif cd['tl_id']:
                tl_item = TimeLineItem.active.get(id=cd['tl_id'], item_type=TimeLineItemTypeE.POST)
                parent_item = tl_item.get_item()
                items = DrankItToo.active.filter(post=parent_item, author=user).order_by('-id')
            elif cd['drank_it_too_id']:
                items = DrankItToo.active.filter(id=cd['drank_it_too_id'], author=user).order_by('-id')
                if items:
                    parent_item = items[0].get_parent_item()
            else:
                raise WrongParametersError(_("Wrong parameters - neither post_id nor tl_id provided"), form)

            if not items:
                raise ResultErrorError("no item to use")
            if not parent_item:
                raise ResultErrorError("no parent item for this drank it to")

            for item in items:
                item.archive()
                item.refresh_from_db()
            parent_item.refresh_from_db()
            return get_newest_tl_dict_for_post_and_send_sr_if_needed(request, parent_item)


# /api/drankittoos/list
@signed_api(FormClass=DrankItTooListForm, token_check=True, log_response_data=False)
def get_drank_it_toos_list(request):
    user = request.user
    prevent_using_non_active_account(user)
    filter_criteria = {}

    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data
            if cd['post_id']:
                post = Post.active.get(id=cd['post_id'], type=PostTypeE.WINE)
                filter_criteria['post'] = post
            elif cd['user_id']:
                user_item = UserProfile.active.get(id=cd['user_id'])
                filter_criteria['author'] = user_item
            elif cd['username']:
                user_item = UserProfile.active.get(username=cd['username'])
                filter_criteria['author'] = user_item
            elif cd['wine_id']:
                wine_item = Wine.active.get(id=cd['wine_id'])
                filter_criteria['wine'] = wine_item
            else:
                raise WrongParametersError(_("Wrong parameters - post_id, user_id, username or wine_id required"), form)

            (limit, order_dir, last_id, order_by) = list_control_parameters_by_form(cd, default_limit=None)
            filter_criteria = get_filter_criteria_for_order_last_id(order_dir, last_id, filter_criteria)

            # exclude drank it too-s from blocked users
            blocked_users = []
            if user.is_authenticated:
                blocked_users = BlockUser.objects.filter(
                    user=user).values_list('block_user_id')

            items = DrankItToo.active.filter(
                **filter_criteria
            ).exclude(
                author_id__in=blocked_users
            ).order_by(order_by)[0:limit]

            if not items:
                raise ResultEmpty

            last_id = list_last_id(items)
            items_out = DrankItTooSerializer(items, many=True).data

            return {'items': items_out, 'last_id': last_id}
