from django.contrib import auth
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import translation
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

from web.forms.admin_forms import ResetUserPasswordConfirmationForm
from web.models import UserProfile
from web.utils.exceptions import NotPermittedError
from web.utils.tokens import CommonTokenGenerator
from web.utils.views_common import prevent_using_non_active_account


@csrf_protect
@never_cache
def pro_reset_password_confirm(request, uid, token):
    password_reset_tmpl = 'user/reset-password.html'
    auth.logout(request)

    error_message = None
    is_finished = False
    is_canceled = False

    bc_path = [
        (reverse('pro_reset_password_confirm', args=[uid, token]), 'Password reset')  # noqa
    ]

    c = {'bc_path': bc_path}
    try:
        uid_decoded = urlsafe_base64_decode(uid).decode('UTF-8')
        user = UserProfile.objects.get(pk=uid_decoded)

        prevent_using_non_active_account(user)

        language = user.lang if user.lang else 'EN'
        translation.activate(language)  # does not work here because
        # language is overriden in layout.html

        if not default_token_generator.check_token(user, token):
            pass
            # noqa raise NotPermittedError("Token for password update to your account (%s) has expired" % user.username)

        if request.method == 'POST':
            form = ResetUserPasswordConfirmationForm(request.POST)

            if form.is_valid():
                cd = form.cleaned_data
                user.set_password(cd['password1'])
                user.save()
                is_finished = True
        else:
            form = ResetUserPasswordConfirmationForm()
        c["form"] = form
        c['uid'] = uid
        c['token'] = token
        c['is_finished'] = is_finished
        c['is_canceled'] = is_canceled
        c['user'] = user
        c['user_lang'] = language
        c['error_message'] = error_message
    except NotPermittedError as e:
        error_message = e
        c['error_message'] = error_message
    except Exception as e:
        error_message = e
        c['error_message'] = error_message

    c['first_time'] = False
    return render(request, password_reset_tmpl, c)


@csrf_protect
@never_cache
def pro_set_password(request, uid, token):
    auth.logout(request)

    uid_decoded = urlsafe_base64_decode(uid).decode('UTF-8')
    user = UserProfile.objects.get(pk=uid_decoded)

    token_generator = CommonTokenGenerator()
    if not token_generator.check_token(user, token):
        return redirect('reset_password_login_screen')

    form = ResetUserPasswordConfirmationForm(request.POST)

    if request.method == 'POST' and form.is_valid():
        user.set_password(form.cleaned_data['password1'])
        user.is_confirmed = True
        user.save()
        user.refresh_from_db()
        auth.login(request, user)

        return redirect('pro_dashboard')

    if request.method == 'GET':
        form.errors['password1'], form.errors['password2'] = None, None

    context = {
        'form': form,
        'uid': uid,
        'token': token,
        'user': user,
        'first_time': True,
    }

    return render(request, 'user/reset-password.html', context)
