from __future__ import absolute_import

import base64
import datetime as dt
import json
import logging
import uuid

from django.apps import apps
from django.conf import settings
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from jwt_auth import settings as jwt_settings
from rest_framework import status as http_status
from refreshtoken.models import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from reports.models import BlockUser
from web.constants import (ApiErrorCodeE, UserStatusE, UserTypeE,
                           ValidationErrorE, PushNotifyTypeE)
from web.forms.api_forms import (FileUploadForm, NotificationListForm,
                                 RefreshTokenForm, UpdatePushFieldsForm,
                                 UpdateUserLangForm,
                                 UserProfileCreateForm, UserProfileForm,
                                 UserProfileOptionsForm)
from web.forms.common import ResetUserPasswordForm
from web.models import (Comment, DrankItToo, LikeVote, Post, UserImage,
                        UserNotification, UserProfile, Wine)
from web.serializers.comments_likes import (UserNotificationAsPlaceSerializer,
                                            UserNotificationAsPostSerializer,
                                            UserNotificationSerializer)
from web.serializers.users import UserSerializer, \
    UserProfileAnyOptionsSerializer
from web.utils.api_handling import get_lang_from_request, signed_api, \
    fill_default_response_data
from web.utils.api_user_storage_utils import ApiUserStorageUtils
from web.utils.common_userdata import get_user_data, get_user_data_cd
from web.utils.exceptions import (ApiError, ResultEmpty, ResultErrorError,
                                  WrongParametersError, get_auth_error)
from web.utils.message_utils import EmailCollection
from web.utils.model_tools import get_filter_criteria_for_order_last_id
from web.utils.views_common import (list_control_parameters_by_form,
                                    list_last_id,
                                    prevent_using_non_active_account)
from web.authentication import CustomTokenAuthentication


log = logging.getLogger(__name__)
log_app_ios_check = logging.getLogger("app_ios_check")


# tool methods for user actions ------------------------------------------------
# gets the user profile data to display, including likes, drank it toos etc.
# does a Basic authentication ---------------------------------------


def basic_authenticate_test(request):
    # copied and refactored from rest_framework.authentication.py
    HTTP_HEADER_ENCODING = 'iso-8859-1'
    auth = request.META.get('HTTP_AUTHORIZATION', b'')
    if isinstance(auth, type('')):
        # Work around django test client oddness
        auth = auth.encode(HTTP_HEADER_ENCODING)
    auth = auth.split()

    if not auth or auth[0].lower() != b'basic':
        msg = _('Invalid request. No credentials provided.')
        # raise WrongAuthError(msg, 99)
        raise ApiError(ApiErrorCodeE.WRONG_AUTH_CREDENTIALS_NOT_PROVIDED)

    if len(auth) == 1:
        msg = _('Invalid basic header. No credentials provided.')
        # raise WrongAuthError(msg, 99)
        raise ApiError(ApiErrorCodeE.WRONG_AUTH_CREDENTIALS_NOT_PROVIDED)
    elif len(auth) > 2:
        msg = _('Invalid basic header. Credentials string should not contain spaces.')
        raise ApiError(ApiErrorCodeE.WRONG_AUTH_CREDENTIALS_MALFORMED_SPACES)
    try:
        auth_parts = base64.b64decode(auth[1]).decode(HTTP_HEADER_ENCODING).partition(':')
    except (TypeError, UnicodeDecodeError):
        msg = _('Invalid basic header. Credentials not correctly base64 encoded.')
        # raise WrongAuthError(msg, 99)
        raise ApiError(ApiErrorCodeE.WRONG_AUTH_CREDENTIALS_MALFORMED_BASE64)

    userid, password = auth_parts[0], auth_parts[2]
    model = apps.get_model(settings.AUTH_USER_MODEL)
    credentials = {
        model.USERNAME_FIELD: userid,
        'password': password
    }

    credentials_test = {"%s__iexact" % model.USERNAME_FIELD: userid}
    credentials_test_email = {"email__iexact": userid}

    users_test = UserProfile.objects.filter(**credentials_test_email)
    if not users_test:
        users_test = UserProfile.objects.filter(**credentials_test)

    if not users_test:
        msg = _('Invalid username/password.')
        raise ApiError(msg, ApiErrorCodeE.WRONG_AUTH_DOES_NOT_EXIST)

    user_test = users_test[0]

    dt_now = dt.datetime.now()
    dt_back = dt_now - dt.timedelta(minutes=settings.FAILED_ATTEMPTS_BLOCKER_MIN)
    if user_test.last_failed_attempt_time and user_test.last_failed_attempt_time > dt_back \
            and user_test.failed_attempts_no >= settings.MAX_FAILED_ATTEMPTS:
        msg = _('Max failed attempts reached.')
        raise ApiError(msg, ApiErrorCodeE.MAX_FAILED_ATTEMPTS_REACHED)

    user = authenticate(**credentials)
    # authentication has FAILED - invalid username/email or password
    if user is None:
        msg = _('Invalid username/password.')
        raise ApiError(msg, ApiErrorCodeE.WRONG_AUTH_INVALID_CREDENTIALS, {"user_id": user_test.id})

    if not user.is_active:
        msg = _('User inactive or deleted.')
        raise ApiError(msg, ApiErrorCodeE.WRONG_AUTH_INACTIVE_OR_DELETED)

    user.failed_attempts_no = 0
    user.last_failed_attempt_time = None
    user.save()
    user.refresh_from_db()

    return user


# ----------------------------------  USER-related API views  -------------------------------------------
# /api/refresh-token
@signed_api(FormClass=RefreshTokenForm, token_check=False)
def refresh_refresh_token(request):
    jwt_payload_handler = settings.JWT_PAYLOAD_HANDLER
    jwt_encode_handler = jwt_settings.JWT_ENCODE_HANDLER
    jwt_response_payload_handler = settings.JWT_RESPONSE_PAYLOAD_HANDLER

    refresh_token = request.form.cleaned_data['refresh_token']

    try:
        refresh_token = RefreshToken.objects.select_related('user').get(key=refresh_token)
    except RefreshToken.DoesNotExist:
        msg = _('Invalid token.')
        # raise WrongAuthError(msg, 97)
        raise ApiError(msg, ApiErrorCodeE.WRONG_AUTH_INVALID_TOKEN)

    request.refresh_token = refresh_token.key
    user = refresh_token.user

    prevent_using_non_active_account(user)

    payload = jwt_payload_handler(user)
    token = jwt_encode_handler(payload)
    response_data = jwt_response_payload_handler(token, user, request)
    return response_data


# /api/sign-in
# /api/users/login
@signed_api(FormClass=None, token_check=False, ensure_ascii=False)
def create_refresh_token(request):
    user = basic_authenticate_test(request)
    prevent_using_non_active_account(user)

    jwt_payload_handler = settings.JWT_PAYLOAD_HANDLER
    jwt_encode_handler = jwt_settings.JWT_ENCODE_HANDLER
    jwt_response_payload_handler = settings.JWT_RESPONSE_PAYLOAD_HANDLER

    refresh_token = RefreshToken(
        user=user,
        app=uuid.uuid4(),
    )

    refresh_token.save()
    request.refresh_token = refresh_token.key

    payload = jwt_payload_handler(user)
    token = jwt_encode_handler(payload)
    response_data = jwt_response_payload_handler(token, user, request)

    ApiUserStorageUtils.clear_value_by_token(token, user.id, 'api_user_venues')

    return response_data


# /api/sign-out
# /api/users/logout
@signed_api(FormClass=RefreshTokenForm, token_check=False)
def delete_refresh_token(request):
    refresh_token = request.form.cleaned_data['refresh_token']

    if not refresh_token:
        raise WrongParametersError(_("No refresh token provided"))

    try:
        refresh_token = RefreshToken.objects.select_related('user').get(key=refresh_token)
    except RefreshToken.DoesNotExist:
        msg = _('Invalid token.')
        # raise WrongAuthError(msg, 97)
        raise ApiError(msg, ApiErrorCodeE.WRONG_AUTH_INVALID_TOKEN)

    refresh_token.delete()
    return None


# /api/user/
# /api/users/profile/own/get
@signed_api(FormClass=UserProfileOptionsForm, token_check=True)
def get_user_own(request):
    user = request.user

    return get_user_data(request, user, include_refused_wineposts=True)


# /api/user/
# /api/users/profile/any/get
class UserProfileAnyView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CustomTokenAuthentication]

    @swagger_auto_schema(
        query_serializer=UserProfileAnyOptionsSerializer,
        operation_summary='Return user profile by user_id or username',
        operation_description='Return user profile by user_id or username',
        security=[]
    )
    def get(self, request, format=None):
        user_id = request.query_params.get('user_id')
        username = request.query_params.get('username')

        if username:
            user = UserProfile.active.get(username=username)
        elif user_id:
            user = UserProfile.active.get(id=user_id)
        else:
            raise WrongParametersError(
                _("neither username nor user_id provided")
            )

        if not user:
            raise ResultErrorError(_("no user found"))

        if str(user.id) == settings.ERASED_USER_UUID:
            return Response(data=_("this user has already been deleted"),
                            status=http_status.HTTP_409_CONFLICT)
            # raise ResultErrorError(_("this user has already been deleted"))

        # *** 'Blocked User' check
        # anonymous user is able to see all User Profiles
        if not request.user.is_authenticated:
            pass
        # if user A (block_user / target) was blocked by user B (blocker)
        elif BlockUser.objects.filter(user=request.user, block_user=user):
            return Response(data=_("this user has already been blocked by "
                                   "requester"),
                            status=http_status.HTTP_404_NOT_FOUND)

        if user.id == request.user.id:
            include_refused_wineposts = True
        else:
            include_refused_wineposts = False

        serializer = UserProfileAnyOptionsSerializer(data=request.query_params)
        if serializer.is_valid(raise_exception=True):
            validated_data = serializer.validated_data
            data = get_user_data_cd(
                validated_data,
                user,
                request,
                include_refused_wineposts=include_refused_wineposts
            )

            response_data = {'data': data}
            fill_default_response_data(response_data)
            return Response(response_data)

    @swagger_auto_schema(
        request_body=UserProfileAnyOptionsSerializer,
        operation_summary='Return user profile by user_id or username',
        operation_description='The method POST is deprecated for this '
                              'endpoint.',
        deprecated=True,
        security=[]
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '/api/users/profile/any/get')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)


# /api/users/profile/own/delete
@signed_api(FormClass=None, token_check=True)
def delete_user_own(request):
    user = request.user
    if user.is_archived:
        raise ResultErrorError("user is already deleted")

    # archives (marks as archived/deleted) all objects created by user except other users
    # Winemaker.active.filter(author=user).archive()
    posts = Post.active.filter(author=user)
    wines = Wine.active.filter(author=user)
    comments = Comment.active.filter(author=user)
    likes = LikeVote.active.filter(author=user)
    dits = DrankItToo.active.filter(author=user)
    if posts:
        for post in posts:
            post.archive()

    if wines:
        for wine in wines:
            wine.archive()

    if comments:
        for comment in comments:
            comment.archive()

    if likes:
        for like in likes:
            like.archive()

    if dits:
        for dit in dits:
            dit.archive()

    tokens = RefreshToken.objects.filter(user=user)

    # clears all refresh tokens for the user to be deleted (physically deleted)
    if tokens:
        for token in tokens:
            token.delete()

    # deletes (archives) the user
    user.archive()

    return {}


# /api/users/register
# @signed_api(FormClass=UserProfileCreateForm, token_check=False, success_status=200, ensure_ascii=False)
@signed_api(FormClass=None, json_used=True, token_check=False, success_status=200, ensure_ascii=False)
def create_user_profile(request):
    form = UserProfileCreateForm(data=request.data)

    if form.is_valid():
        cd = form.cleaned_data
        email = cd['email']
        username = cd['username']

        user = UserProfile(
            email=email,
            username=username,
            # full_name=form.cleaned_data['full_name'],
            type=UserTypeE.USER,
            status=UserStatusE.ACTIVE,
            is_confirmed=False,
            notify_likes=True,
            notify_drank_it_toos=True,
            notify_comments=True,
            notify_wine_reviewed=True,
        )
        user.set_password(form.cleaned_data['password'])
        user.save()

        jwt_payload_handler = settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = jwt_settings.JWT_ENCODE_HANDLER
        jwt_response_payload_handler = settings.JWT_RESPONSE_PAYLOAD_HANDLER

        refresh_token = RefreshToken(
            user=user,
            app=uuid.uuid4(),
        )
        refresh_token.save()
        request.refresh_token = refresh_token.key

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        response_data = jwt_response_payload_handler(token, user, request)
        return response_data
    else:
        ferr = form.errors.as_data()
        res = []
        api_error_code_main = ApiErrorCodeE.INVALID_REGISTER
        for field, error_list in ferr.items():
            for error_obj in error_list:
                code = error_obj.code
                if code in [ValidationErrorE.INVALID_USERNAME]:
                    api_error_code = ApiErrorCodeE.INVALID_USERNAME_SYNTAX
                    desc = get_auth_error(api_error_code, get_lang_from_request(request))
                elif code == 'invalid' and field == 'email':
                    api_error_code = ApiErrorCodeE.INVALID_EMAIL_SYNTAX
                    desc = get_auth_error(api_error_code, get_lang_from_request(request))
                elif code == 'required':
                    api_error_code = ApiErrorCodeE.FIELD_IS_REQUIRED
                    desc = get_auth_error(api_error_code, get_lang_from_request(request))
                elif code == 'api_error_code' and code in ApiErrorCodeE.values:
                    api_error_code = code
                    desc = get_auth_error(code, get_lang_from_request(request))
                else:
                    desc = _(str(error_obj))
                res.append({
                    'field': field,
                    'messages': [desc],
                    'type': 'field',
                })
        raise ApiError("error", api_error_code_main, res)
        # return res


# /api/users/push/update
@signed_api(FormClass=UpdatePushFieldsForm, token_check=True, json_used=True)
def update_push_data(request):
    user = request.user
    form = request.form

    prevent_using_non_active_account(user)

    if request.method == 'POST':
        if form.is_valid():
            cd = form.cleaned_data
            user.push_user_id = cd['push_user_id']
            user.push_user_token = cd['push_user_token']

            user.save()
            user.refresh_from_db()

            return UserSerializer(user).data

    raise WrongParametersError(_("Wrong parameters."), form)


# /api/users/profile/own/update
@signed_api(FormClass=None, token_check=True, json_used=False)
def update_user_profile_own(request):
    user = request.user
    prevent_using_non_active_account(user)
    if request.method == 'POST':
        form1 = FileUploadForm(request.POST, request.FILES)
        files = request.FILES.getlist('images')
        if form1.is_valid():
            try:
                data_json = json.loads(form1.cleaned_data['data'])
            except ValueError:
                data_json = {}

            # we are only interested in ONE file here, if there would be more, we should have used "for" loop
            if files:
                user_image = UserImage(image_file=files[0], user=user, author=user)
                user_image.save()
                user.image = user_image
                user.save()

            if data_json:
                form2 = UserProfileForm(data_json, instance=user, allNonRequired=True)
                if form2.is_valid():
                    cd = form2.cleaned_data
                    selected_fields = data_json.keys()
                    if cd['password']:
                        user.set_password(form2.cleaned_data['password'])
                    user.save(update_fields=selected_fields)
                    user.refresh_from_db()

            return UserSerializer(user).data
        raise WrongParametersError(_("Wrong parameters."), form1)


@signed_api(FormClass=ResetUserPasswordForm, token_check=False, ensure_ascii=False)
def reset_password(request):
    form = request.form
    if form.is_valid():
        lang = get_lang_from_request(request)
        username = form.cleaned_data['username']
        # will throw DoesNotExist error catched by api_handling if user does not exist, it was intended so
        users = UserProfile.active.filter(email__iexact=username)
        if not users:
            users = UserProfile.active.filter(username__iexact=username)
        if not users:
            res = []
            api_error_code = ApiErrorCodeE.USER_NOT_FOUND
            res.append({
                'field': 'username',
                'messages': [get_auth_error(api_error_code, lang)],
                'type': 'field',
            })
            raise ApiError("error", api_error_code, res)
        user = users[0]
        prevent_using_non_active_account(user)
        EmailCollection().send_reset_password_email(user, lang)

        result_data = {}
        return result_data
    else:
        raise WrongParametersError(_("Wrong parameters."), form)


# /api/notifications/list
@signed_api(FormClass=NotificationListForm, token_check=True, log_response_data=False)
def get_notifications_list(request):
    """
    Get a serialized list of user notifications:
        - post: `UserNotificationAsPostSerializer`
        - place: `UserNotificationAsPlaceSerializer`

    API URL: /api/notifications/list
    Request params:
        - last_id: Optional
        - limit: Optional
        - order: Optional
        - order_by: Optional
    """
    user = request.user
    prevent_using_non_active_account(user)
    filter_criteria = {"user_dest": user}
    blocked_users = BlockUser.objects.filter(
        user=request.user).values_list('block_user_id')
    notifications_from_blocked_users_criteria = {
        "user_id__in": blocked_users
    }
    self_notifications_criteria = {
        "user": user,
        "type__in": [PushNotifyTypeE.NOTIFY_LIKE_WINEPOST,
                     PushNotifyTypeE.NOTIFY_COMMENT_PLACE,
                     PushNotifyTypeE.NOTIFY_COMMENT_WINEPOST,
                     PushNotifyTypeE.NOTIFY_DRANK_IT_TOO,
                     PushNotifyTypeE.NOTIFY_LIKE_PLACE]
    }
    form = request.form

    # result notification items
    items = []

    if request.method == 'POST':
        if form.is_valid():
            cd = form.cleaned_data
            (limit, order_dir, last_id, order_by) = list_control_parameters_by_form(cd)
            filter_criteria = get_filter_criteria_for_order_last_id(order_dir, last_id, filter_criteria)

            # query 'limit' user notifications
            notifications = UserNotification.active.filter(
                **filter_criteria
            ).exclude(
                **notifications_from_blocked_users_criteria
            ).exclude(
                **self_notifications_criteria
            ).order_by(order_by)[0:limit]

            # not notification found
            if not notifications:
                raise ResultEmpty

            last_id = list_last_id(notifications)
            for notification in notifications:
                # serialize place notification item
                if notification.place:
                    item = UserNotificationAsPlaceSerializer(notification).data

                # serialize place notification item
                elif notification.post:
                    item = UserNotificationAsPostSerializer(notification).data

                # otherwise, default case: serialize as user notification
                else:
                    item = UserNotificationSerializer(notification).data

                items.append(item)

            return {'items': items, 'last_id': last_id}
    else:
        raise WrongParametersError(_("Wrong parameters."), form)


# /api/users/lang/update
@signed_api(FormClass=UpdateUserLangForm, token_check=True, json_used=True)
def update_lang_data(request):
    user = request.user
    form = request.form
    prevent_using_non_active_account(user)
    if request.method == 'POST':
        if form.is_valid():
            cd = form.cleaned_data
            user.lang = cd['lang'].upper() if cd['lang'] else None
            user.save()
            user.refresh_from_db()
            return UserSerializer(user).data
    raise WrongParametersError(_("Wrong parameters."), form)
