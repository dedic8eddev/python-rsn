import datetime as dt

from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from web.constants import UserStatusE, UserTypeE
from web.forms.admin_forms import (AdminUserProfileForm,
                                   ResetUserPasswordConfirmationForm)
from web.models import Place, UserImage, UserProfile
from web.serializers.users import RightPanelUserSerializer
from web.utils.exceptions import NotPermittedError
from web.utils.message_utils import EmailCollection
from web.utils.pro_utils_cms import update_owner_venue
from web.utils.views_common import prevent_using_non_active_account
from web.views.admin.common import get_c


# /users
@login_required
def users(request):
    c = get_c(
        request=request, active='list_users',
        path='/users', add_new_url='add_user'
    )

    return render(request, "lists/users.html", c)


# /user/add
@csrf_protect
@login_required
def add_user(request):
    bc_path = [
        ('/', 'Home'),
        (reverse('list_users'), 'users'),
        (reverse('add_user'), 'add')
    ]

    c = get_c(
        request=request, active='list_users', path=None, bc_path_alt=bc_path
    )

    user = UserProfile(
        author=c['current_user'],
        status=UserStatusE.ACTIVE,
        lang='FR'
    )

    if request.method == 'POST':
        form = AdminUserProfileForm(
            request.POST, request.FILES, instance=user
        )

        if form.is_valid():
            cd = form.cleaned_data
            images = request.FILES.getlist('image_avatar')

            if cd['password_plain']:
                user.set_password(cd['password_plain'])

            user.save()
            user.refresh_from_db()

            if user.type == UserTypeE.OWNER:
                update_owner_venue(user, cd['place'])
                m = 'Activation email sent for owner (new user {}).'
                messages.add_message(
                    request,
                    messages.INFO,
                    m.format(user.username)
                )
                EmailCollection().send_activation_email(user)

            if images:
                user_image = UserImage(image_file=images[0], user=user)
                user_image.save()
                user.image = user_image
                user.save()
                user.refresh_from_db()

            if cd['subscription']:
                place = cd['place']
                subscription = cd['subscription']
                place.subscription = subscription
                place.save()

            return redirect('edit_user', user.id)

    else:
        form = AdminUserProfileForm(instance=user)

    c["form"] = form
    c["user"] = user
    c["is_new"] = True
    c['current_status'] = UserStatusE.names[
        user.status
    ] if user.status in UserStatusE.names else None
    c["action_url"] = reverse('add_user')
    c["user_is_admin"] = True if (user.type in [
        UserTypeE.ADMINISTRATOR, UserTypeE.EDITOR
    ]) else False
    c["pdg_title"] = '[New User]'

    opts_in = UserStatusE.names

    c["pdg_options"] = [
        {
            'value': UserStatusE.ACTIVE,
            'name': opts_in[UserStatusE.ACTIVE],
            'class': 'btincluded',
            'selclass': 'included'
        },
        {
            'value': UserStatusE.BANNED,
            'name': opts_in[UserStatusE.BANNED],
            'class': 'onhold',
            'selclass': 'onhold'
        },
        {
            'value': UserStatusE.INACTIVE,
            'name': opts_in[UserStatusE.INACTIVE],
            'class': 'btrefused',
            'selclass': 'refused'
        },
    ]

    return render(request, "edit/user.html", c)


# right-panel/user-by-email
class UserByEmailList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RightPanelUserSerializer
    queryset = UserProfile.active.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['email', 'username']


# /user/edit/{id}
@login_required
@csrf_protect
def edit_user(request, id):
    user = UserProfile.active.get(id=id)
    place = Place.objects.filter(owner=user).first()
    bc_path = [
        ('/', 'Home'),
        (reverse('list_users'), 'users'),
        (reverse('edit_user', args=[id]), user.full_name),
    ]
    password_changed = False
    c = get_c(
        request=request, active='list_users', path=None, bc_path_alt=bc_path
    )
    form = AdminUserProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=user,
        place=place
    )

    if request.method == 'POST':
        old_type = user.type

        if form.is_valid():
            cd = form.cleaned_data
            images = request.FILES.getlist('image_avatar')
            user.last_modifier = c['current_user']
            last_modified_time = dt.datetime.now()
            user.modified_time = last_modified_time

            if images:
                user_image = UserImage(image_file=images[0], user=user)
                user_image.save()
                user.image = user_image
                user.save()
                user.refresh_from_db()

            if cd['password_plain']:
                user.set_password(cd['password_plain'])
                password_changed = True

            if cd['type'] == UserTypeE.OWNER:
                update_owner_venue(user, cd['place'])

            if cd['customer']:
                user.customer = cd['customer']

            if (
                old_type != UserTypeE.OWNER and
                user.type == UserTypeE.OWNER and
                not user.is_confirmed
            ):
                m = 'Activation email sent for owner (new role of user {}).'
                messages.add_message(
                    request,
                    messages.INFO,
                    m.format(user.username)
                )
                EmailCollection().send_activation_email(user)

            if cd['place']:
                place = cd['place']
                if place.subscription != cd['subscription']:
                    place.subscription = cd['subscription']
                    place.last_modifier = c['current_user']
                    place.expert = c['current_user']
                    place.modified_time = dt.datetime.now()
                    place.save()

            if cd['formitable_url']:
                str_add = '?ft-tag=Raisin'
                formitable_url = cd['formitable_url'].replace(str_add, '')
                user.formitable_url = (formitable_url + str_add)

            user.save()
            return redirect('edit_user', user.id)

    if user.last_modifier:
        c["saved_by"] = user.last_modifier
        c["saved_at"] = user.modified_time
    else:
        c["saved_by"] = user.author
        c["saved_at"] = user.created_time

    c["form"] = form
    c["password_changed"] = password_changed
    c["user"] = user
    c["user_is_admin"] = True if (user.type in [
        UserTypeE.ADMINISTRATOR, UserTypeE.EDITOR
    ]) else False
    c["is_new"] = False
    c['current_status'] = UserStatusE.names[
        user.status
    ] if user.status in UserStatusE.names else None
    c['current_venue'] = Place.objects.filter(owner=user).first()
    c["action_url"] = reverse('edit_user', args=[id])

    if user.full_name:
        full_name = user.full_name
    else:
        full_name = ""

    c["pdg_title"] = full_name + "<i> [" + user.username + "]</i>"

    opts_in = UserStatusE.names
    c["pdg_options"] = [
        {
            'value': UserStatusE.ACTIVE,
            'name': opts_in[UserStatusE.ACTIVE],
            'class': 'btincluded',
            'selclass': 'included'
        },
        {
            'value': UserStatusE.BANNED,
            'name': opts_in[UserStatusE.BANNED],
            'class': 'onhold',
            'selclass': 'onhold'
        },
        {
            'value': UserStatusE.INACTIVE,
            'name': opts_in[UserStatusE.INACTIVE],
            'class': 'btrefused',
            'selclass': 'refused'
        },
    ]

    return render(request, "edit/user.html", c)


@csrf_protect
@never_cache
def reset_password_confirm(request, uid, token):
    auth.logout(request)
    error_message = None
    is_finished = False
    is_canceled = False
    bc_path = [(
        reverse(
            'reset_password_confirm',
            args=[uid, token]
        ),
        'Password reset'
    )]
    c = {'bc_path': bc_path}
    try:
        uid_decoded = urlsafe_base64_decode(uid).decode('UTF-8')
        user = UserProfile.objects.get(pk=uid_decoded)
        prevent_using_non_active_account(user)
        if not default_token_generator.check_token(user, token):
            pass
            # raise NotPermittedError("Token for password update to
            # your account (%s) has expired" % user.username)
        if request.method == 'POST':
            form = ResetUserPasswordConfirmationForm(request.POST)
            if 'cancel' in request.POST:
                is_canceled = True
            else:
                if form.is_valid():
                    cd = form.cleaned_data
                    user.set_password(cd['password1'])
                    if not user.is_confirmed:
                        user.is_confirmed = True
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
        c['error_message'] = error_message
    except NotPermittedError as e:
        error_message = e
        c['error_message'] = error_message
    except Exception as e:
        error_message = e
        c['error_message'] = error_message

    c['first_time'] = False

    return render(request, "user/password_reset.html", c)
