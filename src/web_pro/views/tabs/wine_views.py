from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import ugettext_lazy as _

from web_pro.utils.common import (get_color_config, handle_provided_place_id,
                                  prepare_sidebar_data, resolve_url_to_pro_page)
from web_pro.utils.wines import WineModelOperator, get_wine_post_data

template_path = 'admin/wines.html'


# /pro/wines
@login_required(login_url='pro_login')
def wines(request, pid=None):
    res = handle_provided_place_id(request, pid)
    if res['redirect']:
        return res['redirect']

    sidebar_data = prepare_sidebar_data(request, 'wines')

    sidebar_data.update({
        'color_config': get_color_config(),
        'pid': pid,
        'section_titles': {'wines': _('Wines')},
        'you_search_text': _('You search')
    })

    return render(request, template_path, sidebar_data)


# /pro/wines_by_users
@login_required(login_url='pro_login')
def wines_by_users(request, pid=None):
    res = handle_provided_place_id(request, pid)
    if res['redirect']:
        return res['redirect']

    sidebar_data = prepare_sidebar_data(request, 'wines_by_users')

    sidebar_data.update({
        'color_config': get_color_config(), 'pid': pid,
        'section_titles': {'wines': _('Wines')},
        'you_search_text': _('You search')
    })

    return render(request, 'admin/wines_by_users.html', sidebar_data)


# pro/winepost/
@login_required(login_url='pro_login')
def get_wine_post(request, post_id):
    return JsonResponse(get_wine_post_data(post_id, request.user))


# pro/wines/post
@login_required(login_url='pro_login')
def post_wine(request):
    operator = WineModelOperator(request)
    post_type = operator.data.get('postType', [])

    if request.method == 'POST':
        if post_type == 'edit':
            operator.edit_wine_post()

        if post_type == 'delete':
            operator.delete_wine_post()

        if post_type == 'add':
            operator.add_wine_post()

    return redirect(resolve_url_to_pro_page(request, 'pro_wines'))
