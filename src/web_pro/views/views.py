from django.conf import settings
from django.contrib import auth
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from web.constants import UserTypeE
from web.forms.common import LoginForm, ResetUserPasswordByEmailForm
from web.models import Place, UserProfile
from web.utils.exceptions import ResultErrorError
from web.utils.message_utils import EmailCollection
from web.utils.views_common import prevent_using_non_active_account
from web_pro.constants import NOT_AUTHORIZED_USER_TYPES
from web_pro.utils.common import del_session_pro_place_id, redirect_to_pro_page


def is_proper_user_type(user_obj):
    if user_obj.type not in UserTypeE.values:
        return False

    if user_obj.type in NOT_AUTHORIZED_USER_TYPES:
        return False

    return user_obj


def is_proper_user_type_by_username(username):
    user = UserProfile.active.filter(
        Q(username=username) | Q(email=username)
    ).first()

    if not user:
        return False

    return is_proper_user_type(user)


# /pro/login
@csrf_protect
@never_cache
def pro_login(request):
    c = {
        'username_placeholder': 'placeholder:{}'.format(_('Username or email')),  # noqa
        'password_placeholder': 'placeholder:{}'.format(_('Password'))
    }

    redirect_next = None
    login_tpl = "user/user-login.html"

    if request.user.is_authenticated:
        return redirect_to_pro_page(request, 'pro_dashboard')

    del_session_pro_place_id(request)

    if request.method == 'POST':
        redirect_next = request.GET.get('next', '')
        form = LoginForm(request.POST)
        if form.is_valid():
            if is_proper_user_type_by_username(form.user):
                places_for_owner = Place.active.filter(owner=form.user)
                if not places_for_owner and form.user.type == UserTypeE.OWNER:
                    c["form"] = form
                    c["fatal_error"] = _(
                        'No establishment added to your account - Please contact the administrator: '  # noqa
                    ) + '<a href="mailto:pro@raisin.digital" class="email-login">pro@raisin.digital</a>.'  # noqa
                    return render(request, login_tpl, c)

                auth.login(request, form.user)
                if redirect_next:
                    return redirect(redirect_next)
                else:
                    if request.POST.get('checkbox', None):
                        request.session.set_expiry(0)
                    return redirect_to_pro_page(request, 'pro_dashboard')
        else:
            c["form"] = form
            c["error"] = _("Wrong credentials")

            return render(request, login_tpl, c)
    else:
        form = LoginForm()

    form_reset_password = ResetUserPasswordByEmailForm()

    c["form"] = form
    c["form_reset_password"] = form_reset_password
    c["redirect"] = redirect_next
    c['temporary_access_allowed'] = settings.TEMPORARY_ACCESS_ALLOWED

    return render(request, login_tpl, c)


# /pro/logout
@never_cache
def pro_logout(request):
    auth.logout(request)

    return redirect('pro_login')


# /pro/reset_password
@csrf_exempt
@never_cache
def pro_reset_password_login_screen(request):
    forgot_password_tmpl = 'user/user-recover.html'
    reset_password_sent_tmpl = 'user/user-password-reset-confirm.html'

    if request.method == 'POST':
        form = ResetUserPasswordByEmailForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            email = cd['email']

            user = is_proper_user_type_by_username(email)

            if not user:
                return render(request, reset_password_sent_tmpl)
            try:
                prevent_using_non_active_account(user)
            except ResultErrorError:
                return render(request, reset_password_sent_tmpl)

            EmailCollection().send_reset_password_email(user)

        return render(request, reset_password_sent_tmpl)

    form = ResetUserPasswordByEmailForm()

    email_placeholder = 'placeholder:{}'.format(_('Email'))

    return render(
        request,
        forgot_password_tmpl,
        {'form': form, 'email_placeholder': email_placeholder}
    )
