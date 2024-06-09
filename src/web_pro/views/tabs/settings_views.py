from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from web.utils.form_tools import validate_password
from web_pro.utils.common import (get_owner_user, handle_provided_place_id,
                                  prepare_sidebar_data)
from web_pro.utils.settings import SettingsOperator


# pro/settings
@login_required(login_url='pro_login')
def pro_settings(request, pid=None):
    res = handle_provided_place_id(request, pid)
    if res['redirect']:
        return res['redirect']

    operator = SettingsOperator(request)
    sidebar_data = prepare_sidebar_data(request, 'settings')
    if operator.get_phone_number():
        sidebar_data['phone_number'] = operator.get_phone_number()
    else:
        sidebar_data['phone_number'] = _('None')
    sidebar_data['pid'] = pid

    return render(request, "admin/settings.html", sidebar_data)


# pro/settings-password
@login_required(login_url='pro_login')
def pro_settings_password(request, pid=None):
    if request.method != 'POST':
        raise Http404

    res = handle_provided_place_id(request, pid)
    if res['redirect']:
        return res['redirect']

    user = get_owner_user(request)
    current_password = request.POST["old_password"]
    new_password = request.POST["new_password"]
    password_errors = []

    if not user.check_password(current_password):
        password_errors.append(_('The current password does not match.'))

    try:
        validate_password({'pwd': new_password}, 'pwd')
    except ValidationError as e:
        password_errors.append(e.message + '.')

    if not password_errors:
        user.set_password(new_password)
        user.save()
        user.refresh_from_db()
        update_session_auth_hash(request, user)

    sidebar_data = prepare_sidebar_data(request, 'settings')
    sidebar_data['password_errors'] = password_errors
    sidebar_data['pid'] = pid

    return render(request, "admin/settings.html", sidebar_data)


# /pro/settings/owner-details
@login_required(login_url='pro_login')
def update_owner_details(request):
    operator = SettingsOperator(request)
    operator.update_owner_details()

    return JsonResponse({'result': 'done'})


@login_required(login_url='pro_login')
def update_company_details(request):
    operator = SettingsOperator(request)
    operator.update_company_details()

    return JsonResponse({'result': 'done'})
