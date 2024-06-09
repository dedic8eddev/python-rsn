import json
import logging
import re
from datetime import datetime, timedelta
from functools import wraps

from django import forms
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from jwt_auth.exceptions import AuthenticationFailed
from jwt_auth.mixins import JSONWebTokenAuthMixin
from refreshtoken.models import RefreshToken

from web.constants import ApiErrorCodeE, ApiResultE, ApiResultStatusE
from web.models import UserProfile
from web.utils.exceptions import (ApiError, BadSignatureError, ResultEmpty,
                                  ResultErrorError, ResultErrorWithMsg,
                                  WrongParametersError, get_auth_error)
from web.utils.json_handling import JsonEncoder

log = logging.getLogger(__name__)


def get_lang_from_request_pro(request, default_lang='EN'):
    lang = None
    lang_out = default_lang
    if 'HTTP_ACCEPT_LANGUAGE' in request.META:
        lang_src = request.META['HTTP_ACCEPT_LANGUAGE']
        lang_array = lang_src.split(",")
        if lang_array and lang_array[0]:
            lang = lang_array[0]
    elif 'HTTP_LANG' in request.META and request.META['HTTP_LANG']:
        lang = request.META['HTTP_LANG']

    if lang:
        re_res = re.search('([a-zA-Z]+)', lang)
        if re_res:
            lang = re_res.groups()[0]
            lang_out = lang.upper()
        if lang_out and lang_out not in ['FR', 'EN']:
            lang_out = default_lang
    return lang_out


def get_lang_from_request(request):
    lang = None
    if 'HTTP_ACCEPT_LANGUAGE' in request.META:
        lang_src = request.META['HTTP_ACCEPT_LANGUAGE']
        lang_array = lang_src.split(",")
        if lang_array and lang_array[0]:
            lang = lang_array[0]
    elif 'HTTP_LANG' in request.META and request.META['HTTP_LANG']:
        lang = request.META['HTTP_LANG']
    if request.data and 'lang' in request.data and request.data['lang'] \
            and isinstance(request.data['lang'], str):
        lang = request.data['lang']

    if lang:
        re_res = re.search('([a-zA-Z]+)', lang)
        if re_res:
            lang = re_res.groups()[0]
            return lang.upper()
    return None


# class LazyEncoder(DjangoJSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, Promise):
#             return force_text(obj)
#         return super(LazyEncoder, self).default(obj)

def signed_api(
    FormClass=None, token_check=True,
    log_response_data=False, remove_headers_for_rack=False,
    success_status=200, json_used=True, ensure_ascii=True
):
    """
    Requests have extra fields before the actual function is called: (Mean => Adding requests extra fields... ??)
     - now, data, form, cd
     - user, if token_check is True
    """

    def _decorator(f):
        @csrf_exempt
        @wraps(f)
        def _replacement(request, pk=None):
            response_data = {}
            try:
                log.info("++request %s", f.__name__)
                # api_token_valid_to = None
                request.now = datetime.now()

                # workaround for the bug from line  267 of script lib/python3.4/site-packages/django/http/request.py
                # The problem was, that when no CONTENT_LENGTH attribute was set, it was passed to int() function
                # as an empty string, which caused error. Simply adding "0" at the beginning of the expression
                # would be OK, but manual hacking of Django libraries is NOT a good idea, so I found this workaround
                # here :) (Django 1.10, Python 3.4/3.5)
                if not request.META.get("CONTENT_LENGTH"):
                    request.META['CONTENT_LENGTH'] = 0

                log.info("request body: %s", request.body)

                if json_used and request.body.decode('utf-8'):
                    try:
                        request.data = json.loads(request.body.decode('utf-8'))
                    except ValueError:
                        log.error("Error in json: %s", request.body.decode('utf-8'))
                        raise ApiError("Json decoding error", ApiResultE.INVALID_DATA)
                else:
                    # log.debug(UserTypeE.ADMIN)
                    request.data = {}
                log.debug("request data: %s", request.data)
                if token_check:
                    request.user, request.ts = handle_token(request)
                    # if not request.user.user_type == user_type:
                    #     code = ApiResultE.NOT_A_USER
                    #     msg = "User bad type"
                    #     raise ApiError(msg, code)

                response_ready = False
                if FormClass is not None:
                    form = FormClass(request.data)
                    # TODO: w sumie nie wiem czy to potrzebne , request=request)
                    # ale mozliwe ze inny rodzaj forma to potrzebuje
                    if not form.is_valid():
                        # try to catch creating object with used id.
                        # If so, no error ocures
                        try:
                            ferr = form.errors.as_data()
                            code = ferr['id'][0].code
                            if code == 'unique':
                                response_ready = True
                                response_data = None
                        except KeyError:
                            pass

                        if not response_ready:
                            handle_error(request, form)

                    request.form = form
                    request.cd = form.cleaned_data
                if pk is not None:
                    request.pk = pk
                with transaction.atomic():
                    if not response_ready:
                        response_data = f(request)  # may raise an ApiError

                    status_code = ApiResultStatusE.STATUS_OK

                    # response for SUCCESSFUL resolution
                    response_data = {
                        'data': response_data,
                        'success': True,
                        'status': status_code
                    }
            except BadSignatureError:  # raised by check_signed_request
                status_code = ApiResultStatusE.WRONG_AUTH
                response_data = {
                    # "errorCode": ApiResultE.BAD_SIGNATURE,
                    # "errorMessage": "Bad signature",
                    'success': False,
                    'status': status_code,
                    'errors': [
                        {
                            'type': 'general',
                            "messages": [_("Wrong authorization.")]
                        }
                    ]
                }
                log.error("BadSignatureError caught: %s", response_data)
            except ApiError as e:
                errorCode = e.args[1]
                errors_general = None
                errors_info = []

                lang = get_lang_from_request(request)
                if errorCode == ApiErrorCodeE.WRONG_AUTH_INVALID_CREDENTIALS:
                    status_code = ApiResultStatusE.WRONG_AUTH
                    errors_general = get_auth_error(errorCode, lang)
                    user_info = e.args[2]
                    user_test = UserProfile.objects.get(id=user_info['user_id'])
                    dt_now = datetime.now()
                    dt_back = dt_now - timedelta(minutes=settings.FAILED_ATTEMPTS_BLOCKER_MIN)

                    # blocker did not exist or has expired - set it up
                    if not user_test.last_failed_attempt_time or user_test.last_failed_attempt_time < dt_back:
                        user_test.last_failed_attempt_time = datetime.now()
                        user_test.failed_attempts_no = 0
                        user_test.save()
                        user_test.refresh_from_db()

                    if user_test.failed_attempts_no is not None:
                        user_test.failed_attempts_no += 1
                    else:
                        user_test.failed_attempts_no = 1
                    user_test.last_failed_attempt_time = datetime.now()
                    user_test.save()
                    user_test.refresh_from_db()
                elif errorCode == ApiErrorCodeE.MAX_FAILED_ATTEMPTS_REACHED:
                    status_code = ApiResultStatusE.WRONG_AUTH
                    errors_general = get_auth_error(errorCode, lang)
                elif errorCode == ApiErrorCodeE.WRONG_AUTH_INVALID_TOKEN:
                    status_code = ApiResultStatusE.WRONG_AUTH
                    errors_general = get_auth_error(errorCode, lang)
                elif errorCode == ApiErrorCodeE.WRONG_AUTH_DOES_NOT_EXIST:
                    status_code = ApiResultStatusE.WRONG_AUTH
                    errors_general = get_auth_error(errorCode, lang)
                elif errorCode == ApiErrorCodeE.WRONG_AUTH_CREDENTIALS_NOT_PROVIDED:
                    status_code = ApiResultStatusE.WRONG_AUTH
                    errors_general = get_auth_error(errorCode, lang)
                elif errorCode == ApiErrorCodeE.WRONG_AUTH_CREDENTIALS_MALFORMED_SPACES:
                    status_code = ApiResultStatusE.WRONG_AUTH
                    errors_general = get_auth_error(errorCode, lang)
                elif errorCode == ApiErrorCodeE.WRONG_AUTH_CREDENTIALS_MALFORMED_BASE64:
                    status_code = ApiResultStatusE.WRONG_AUTH
                    errors_general = get_auth_error(errorCode, lang)
                elif errorCode == ApiErrorCodeE.RESULT_ALREADY_EXISTS:
                    status_code = ApiResultStatusE.RESULT_ALREADY_EXISTS
                    errors_general = get_auth_error(errorCode, lang)
                elif errorCode == ApiErrorCodeE.RESULT_ALREADY_EXISTS_USERNAME:
                    status_code = ApiResultStatusE.RESULT_ALREADY_EXISTS_USERNAME
                    errors_general = get_auth_error(errorCode, lang)
                elif errorCode == ApiErrorCodeE.RESULT_ALREADY_EXISTS_EMAIL:
                    status_code = ApiResultStatusE.RESULT_ALREADY_EXISTS_EMAIL
                    errors_general = get_auth_error(errorCode, lang)
                elif errorCode == ApiErrorCodeE.WRONG_AUTH_INACTIVE_OR_DELETED:
                    status_code = ApiResultStatusE.WRONG_AUTH
                    errors_general = get_auth_error(errorCode, lang)
                elif errorCode == ApiErrorCodeE.INVALID_USERNAME_SYNTAX:
                    status_code = ApiResultStatusE.WRONG_PARAMETERS
                    errors_general = get_auth_error(errorCode, lang)
                elif errorCode == ApiErrorCodeE.INVALID_USERNAME_SYNTAX:
                    status_code = ApiResultStatusE.WRONG_PARAMETERS
                    errors_general = get_auth_error(errorCode, lang)
                elif errorCode == ApiErrorCodeE.INVALID_REGISTER:
                    status_code = ApiResultStatusE.WRONG_PARAMETERS
                    errors_info = e.args[2] if len(e.args) >= 3 else {}
                elif errorCode == ApiErrorCodeE.USER_NOT_FOUND:
                    status_code = ApiResultStatusE.WRONG_PARAMETERS
                    errors_info = e.args[2] if len(e.args) >= 3 else {}
                # used for checking forms, since each form-related error has its own code and we need to know
                # that SOMETHING is wrong with a form (eg. WRONG_PARAMETERS)
                elif len(e.args) >= 4:
                    status_code = e.args[3]
                else:
                    status_code = ApiResultStatusE.RESULT_ERROR
                if not errors_general:
                    if status_code == ApiResultStatusE.WRONG_PARAMETERS:
                        errors_general = _("Wrong parameters.")
                    else:  # including ApiResultStatusE.RESULT_ERROR
                        errors_general = _("An error has occurred: %s" % str(e))

                if not errors_info:
                    errors_info = [
                        {
                            'type': 'general',
                            "messages": [errors_general]
                        }
                    ]
                    if len(e.args) >= 3:
                        response_data["field"] = e.args[2]

                response_data = {
                    # "errorCode": errorCode,
                    # "errorMessage": e.args[0],
                    'success': False,
                    'status': status_code,
                    'errors': errors_info,
                }
                log.error("ApiError caught: %s", response_data)
            except AuthenticationFailed as e:
                lang = get_lang_from_request(request)
                status_code = ApiResultStatusE.WRONG_AUTH

                response_data = {
                    "status": status_code,
                    'success': False,
                    'errors': [
                        {
                            'type': 'general',
                            # "messages": [_("Wrong authorization.")]
                            "messages": [get_auth_error(ApiErrorCodeE.WRONG_AUTH_INVALID_TOKEN, lang)]
                        }
                    ]
                }
                if len(e.args) >= 3:
                    response_data["field"] = e.args[2]
                log.error("ApiError caught: %s", response_data)
            except RefreshToken.DoesNotExist as e:
                status_code = ApiResultStatusE.WRONG_AUTH
                lang = get_lang_from_request(request)
                response_data = {
                    "status": status_code,
                    'success': False,
                    'errors': [
                        {
                            'type': 'general',
                            # "messages": [_("Wrong authorization.")]
                            "messages": [get_auth_error(ApiErrorCodeE.WRONG_AUTH_INVALID_TOKEN, lang)]
                        }
                    ]
                }
                if len(e.args) >= 3:
                    response_data["field"] = e.args[2]
                log.error("ApiError caught: %s", response_data)

            except WrongParametersError as e:
                status_code = ApiResultStatusE.WRONG_PARAMETERS

                response_data = {
                    # "errorCode": ApiResultE.INTERNAL_ERROR,
                    # "errorMessage": str(e),
                    'success': False,
                    'status': status_code
                }

                if len(e.args) >= 2 and (isinstance(e.args[1], forms.Form) or isinstance(e.args[1], forms.ModelForm)):
                    ferr = e.args[1].errors
                    ferr_out = [
                        {
                            "type": "field",
                            "field": field,
                            "messages": field_errors
                        } for field, field_errors in ferr.items()
                    ]
                    response_data['errors'] = ferr_out
                else:
                    response_data['errors'] = [
                        {
                            'type': 'general',
                            "messages": [_("Wrong parameters.")]
                        }
                    ]
                log.exception("Exception caught: %s", response_data)
            except ResultErrorError as e:
                status_code = ApiResultStatusE.RESULT_ERROR
                d_error = e.args[0]
                d_errordesc = ""
                if len(e.args) > 1:
                    d_errordesc = e.args[1]

                response_data = {
                    # "errorCode": ApiResultE.INTERNAL_ERROR,
                    # "errorMessage": str(e),
                    'success': False,
                    'status': status_code,
                    'errors': [
                        {
                            'type': 'general',
                            "messages": [_("An error has occurred: %s" % str(e)), ]
                        },
                    ],
                }
                log.exception("Exception caught: %s", response_data)
            except ResultErrorWithMsg as e:
                status_code = ApiResultStatusE.WRONG_PARAMETERS
                d_error = e.args[0]
                d_errordesc = ""
                if len(e.args) > 1:
                    d_errordesc = e.args[1]

                response_data = {
                    # "errorCode": ApiResultE.INTERNAL_ERROR,
                    "error": d_error,
                    "error_details": d_errordesc,
                    'success': False,
                    'status': status_code,
                    'errors': [
                        {
                            'type': 'general',
                            "messages": [_("An error has occurred: %s" % str(e)), ]
                        },
                    ],
                }
                log.exception("Exception caught: %s", response_data)
            except ResultEmpty:
                status_code = ApiResultStatusE.RESULT_EMPTY

                # response for SUCCESSFUL resolution
                response_data = {
                    'data': response_data,
                    'success': True,
                    'status': status_code
                }
            except Exception as e:
                status_code = ApiResultStatusE.RESULT_ERROR

                response_data = {
                    # "errorCode": ApiResultE.INTERNAL_ERROR,
                    # "errorMessage": str(e),
                    'success': False,
                    'status': status_code,
                    'errors': [
                        {
                            'type': 'general',
                            "messages": [_("An error has occurred: %s" % str(e)), ]
                        },
                    ],
                }
                log.exception("Exception caught: %s", response_data)
            finally:
                # fill_default_response_data(response_data, api_token_valid_to)
                fill_default_response_data(response_data)
                # log.debug("response dataXXXX: %s", response_data)
                if log_response_data:
                    log.debug("response data: %s", response_data)
                else:
                    log.debug("response data logging suppressed")

            response_status = success_status
            if response_data['success'] is False:
                response_status = 400

            sresp = signed_response(response_data, response_status, ensure_ascii)
            if remove_headers_for_rack:
                # RemoveHeadersMiddleware will remove unneeded headers so rack can fit them in its buffer.
                sresp.remove_headers_for_rack = True
            log.info("--request %s", f.__name__)
            return sresp

        return _replacement

    return _decorator


def handle_error(request, form):
    error_messages = {'error_messages': {
            'null': '1',
            'blank': '2',
            'invalid': '3',
            'invalid_choice': '4',
            'unique': '5',
            'unique_for_date': '6',
            'required': '7',
            'max_length': '8',
            'min_length': '9',
            'max_value': '10',
            'min_value': '11',
            'max_digits': '12',
            'max_decimal_places': '13',
            'max_whole_digits': '14',
            'missing': '15',
            'empty': '16',
            'invalid_list': '17',
            'incomplete': '18',
            'invalid_date': '19',
            'invalid_time': '20',
            'list': '21',
            'invalid_pk_value': '22',
            }}
    ferr = form.errors.as_data()
    if not request.data:
        code = ApiResultE.INVALID_DATA
        msg = "No arguments"

        raise WrongParametersError(msg, form)
        # raise ApiError(msg, code)
        # throw just first error from the list

    # http://stackoverflow.com/questions/17322668/typeerror-dict-keys-object-does-not-support-indexing
    # Exception caught: {'status': 102, 'errorMessage': "'dict_items' object does not support indexing",
    # 'errorCode': 99, 'success': False}
    # Traceback (most recent call last):
    #  File "/var/www/workspaces/raisin/src/web/api_handling.py", line 69, in _replacement
    #    handle_error(request, form)
    #  File "/var/www/workspaces/raisin/src/web/api_handling.py", line 226, in handle_error
    #    first_error = ferr.items()[0][1]
    # TypeError: 'dict_items' object does not support indexing

    # instead of this: first_error = ferr.items()[0][1] in Python 3 we use this:
    first_error = list(ferr.items())[0][1]
    # code = first_error[0].code
    # code = int(error_messages['error_messages'][str(code)])
    msg = str(first_error[0])
    # msg = None
    # field = ferr.items()[0][0]
    # field = list(ferr.items())[0][0]

    raise WrongParametersError(msg, form)
    # raise ApiError(msg, code, field, ApiResultStatusE.WRONG_PARAMETERS)


def handle_token(request):  # changed to JWT token check from jwt_auth
    token_auth = JSONWebTokenAuthMixin()
    user, auth = token_auth.authenticate(request)
    # authenticate already is checking if user.is_active
    return user, None


def signed_response(data, success_status, ensure_ascii=True):
    packed_data = json.dumps(data, cls=JsonEncoder, sort_keys=True, indent=4, ensure_ascii=ensure_ascii)
    response = HttpResponse(packed_data, content_type="application/json", status=success_status)
    return response


def fill_default_response_data(data, success=False):  # , api_token_valid_to):
    # data["server_version"] = 1  #  settings.VERSION
    # data["protocol_version"] = 1
    data["date"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    data["host"] = "localhost"
    if success:
        data['success'] = success
