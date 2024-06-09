from django.templatetags.static import static
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from web.utils.time import get_current_date
from web_pro.utils.common import (get_owner_user, get_user_venue,
                                  handle_provided_place_id,
                                  prepare_sidebar_data)
from web_pro.utils.dashboard import (get_latest_food, get_latest_wines,
                                     get_wine_number)


# /pro/dashboard
@login_required(login_url='pro_login')
def dashboard(request, pid=None):
    print(1111)
    res = handle_provided_place_id(request, pid)
    if res['redirect']:
        return res['redirect']
    print(2222)
    sidebar_data = prepare_sidebar_data(request, 'dashboard')
    user = get_owner_user(request)
    venue = get_user_venue(user.id, request)
    cur_date = get_current_date()

    sidebar_data['cur_year'] = cur_date.year

    color_config = {}
    for color in ['red', 'white', 'sparkling', 'pink', 'orange']:
        color_config[color] = {
            'capitalised': _(color.capitalize()),
            'link': reverse(
                'pro_wines', args=[venue.id]
            ) + '?scrollTo=' + color,
            'icon': static('pro_assets/img/wine-icon-{}.png'.format(color)),
            'number': get_wine_number(venue.id, color),
        }

    context = {}
    context.update(sidebar_data)
    context['color_config'] = color_config
    context['latest_wines'] = get_latest_wines(pid)
    context['latest_food'] = get_latest_food(pid)
    context['pid'] = venue.id

    return render(request, "admin/index_pro_dashboard.html", context)
