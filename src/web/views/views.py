from django.conf import settings
from django.contrib import auth
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from web.forms.common import LoginForm, ResetUserPasswordByEmailUsernameForm
from web.models import UserProfile
from web.utils.exceptions import ResultErrorError
from web.utils.message_utils import EmailCollection
from web.utils.views_common import prevent_using_non_active_account


# /login
@csrf_protect
@never_cache
def login(request):
    c = {}

    redirect_next = None
    login_tpl = "login.html"
    home_page = settings.HOME_PAGE
    print('-------------------------')
    if settings.TEMPORARY_ACCESS_ALLOWED:
        if 'breakin' in request.GET or 'breakin' in request.POST:
            user = UserProfile.active.get(username='admin')
            auth.login(request, user)
            return redirect(home_page)

    if request.user.is_authenticated:
        return redirect(home_page)

    if request.method == 'POST':
        redirect_next = request.GET.get('next', '')
        form = LoginForm(request.POST)
        if form.is_valid():
            auth.login(request, form.user)
            if redirect_next:
                return redirect(redirect_next)
            else:
                return redirect('/')
        else:
            c["form"] = form
            return render(request, login_tpl, c)
    else:
        form = LoginForm()

    form_reset_password = ResetUserPasswordByEmailUsernameForm()

    c["form"] = form
    c["form_reset_password"] = form_reset_password
    c["redirect"] = redirect_next
    c['temporary_access_allowed'] = settings.TEMPORARY_ACCESS_ALLOWED

    return render(request, login_tpl, c)


# /logout
@never_cache
def logout(request):
    auth.logout(request)

    home_page = settings.HOME_PAGE

    return redirect(home_page)


@csrf_exempt
@never_cache
def reset_pasword_login_screen(request):
    if request.method == 'POST':
        form = ResetUserPasswordByEmailUsernameForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            username = cd['username']

            query_params = Q(
                username__iexact=username
            ) | Q(email__exact=username)
            users = UserProfile.active.filter(query_params)

            if not users.exists():
                return JsonResponse({'status': 'ERROR',
                                     'label': "Error occurred",
                                     'message': "User account does not exist"})
            else:
                user = users.first()

                try:
                    prevent_using_non_active_account(user)
                except ResultErrorError as e:
                    return JsonResponse({'status': 'ERROR',
                                         'label': "Error occurred",
                                         'message': e.args[0]})

                EmailCollection().send_reset_password_email(user)

                return JsonResponse({
                    'status': 'OK',
                    'label': "Password reset request sent",
                    'message': "Password reset e-mail message has been sent. "
                    "Please follow the further instructions from the message."
                })

        else:
            return JsonResponse({
                'status': 'ERROR',
                'label': "Error occurred",
                'message': "Username invalid or not provided"
            })
            # auth.logout(request)


def handle_403_not_permitted(request, exception=None):
    return redirect('login')
    # response = render(request, '403.html')
    # response.status_code = 400
    #
    # return response


def handle_404_not_found(request, exception=None):
    response = render(request, 'error.html', {
        'error': '404',
        'message': "Seems you're looking for something that doesn't exist."
    })
    response.status_code = 404

    return response


def handle_500(request):
    message = 'Looks like we have an internal issue, please try ' \
              'again in couple of minutes.'
    response = render(request, 'error.html', {
        'error': '404',
        'message': message
    })
    response.status_code = 500

    return response
