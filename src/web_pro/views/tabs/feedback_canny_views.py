from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from web.models import Place
from web_pro.utils.common import (create_canny_token, get_canny_boards,
                                  handle_provided_place_id,
                                  prepare_sidebar_data)


# pro/feedback
@login_required(login_url='pro_login')
def get_feedback_canny(request, pid=None):
    res = handle_provided_place_id(request, pid)
    owner = Place.objects.get(pk=pid).owner
    owner_lang = owner.get_lang()

    if res['redirect']:
        return res['redirect']

    context = prepare_sidebar_data(request, 'feedback')
    context['canny_boards'] = get_canny_boards(owner_lang)
    context['pid'] = pid
    context['user_sso_token'] = create_canny_token(owner, owner_lang)

    return render(request, "admin/feedback-canny.html", context)
