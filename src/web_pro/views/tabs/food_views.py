from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from web_pro.utils.common import (handle_provided_place_id,
                                  prepare_sidebar_data, redirect_to_pro_page)
from web_pro.utils.food import FoodModelOperator

template_path = "admin/food.html"


# pro/food
@login_required(login_url='pro_login')
def food(request, pid=None):
    res = handle_provided_place_id(request, pid)
    if res['redirect']:
        return res['redirect']
    sidebar_data = prepare_sidebar_data(request, 'food')

    food_config = {}
    for color in ['food']:
        food_config[color] = {
            'capitalised': _('🍲 Posted Food'),
            'icon': 'pro_assets/img/food/food-void-min.png',
        }

    sidebar_data.update({
        'food_config': food_config,
        'pid': pid,
        'section_titles': {'food': _('🍲 Posted Food')},
        'you_search_text': _('You search')
    })

    return render(request, template_path, sidebar_data)


# pro/food/post
@login_required(login_url='pro_login')
def post_food(request):
    operator = FoodModelOperator(request)
    post_type = operator.data.get('postType', [])

    if request.method == 'POST':
        if post_type == 'edit':
            operator.edit_food_post()

        if post_type == 'delete':
            operator.delete_food_post()

        if post_type == 'add':
            operator.add_food_post()

    return redirect_to_pro_page(request, 'pro_food')
