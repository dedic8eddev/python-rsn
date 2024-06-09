import traceback
import logging
from django.http import JsonResponse
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR

from rest_framework.views import exception_handler
from django.conf import settings
from web.constants import ApiErrorCodeE

log = logging.getLogger()


class ResultEmpty(Exception):  # not an error, but a condition using exceptions anyway
    pass


class BadSignatureError(Exception):
    pass


class ApiError(Exception):
    pass  # 1st arg is a message, 2nd a code, 3rd (optional) - error_details


class WrongParametersError(Exception):
    pass  # 1st arg is a message, 2 - form data


# class WrongAuthError(Exception):
#     pass  # 1st arg is a message, 2nd a code, 3rd (optional) - error_details


class ResultErrorError(Exception):
    pass  # 1st arg is a message, 2nd a code, 3rd (optional) - error_details


class NotPermittedError(Exception):
    pass


class ActivationError(Exception):
    pass


class ResultErrorWithMsg(Exception):
    pass   # 1st arg is a message, 2 - form data


def get_auth_error(api_error_code, lang=None):
    msgs_langs = {
        'EN': {
            ApiErrorCodeE.WRONG_AUTH_INVALID_CREDENTIALS: "Email or username and password are not matching.",
            ApiErrorCodeE.WRONG_AUTH_DOES_NOT_EXIST: "Could not find an account with that username.",
            ApiErrorCodeE.WRONG_AUTH_CREDENTIALS_NOT_PROVIDED: 'Invalid request. No credentials provided.',
            ApiErrorCodeE.RESULT_ALREADY_EXISTS_USERNAME: "This username already exists.",
            ApiErrorCodeE.RESULT_ALREADY_EXISTS_EMAIL: "This email is already registered.",
            ApiErrorCodeE.WRONG_AUTH_CREDENTIALS_MALFORMED_SPACES: "Invalid basic header. Credentials string should not contain spaces.",
            ApiErrorCodeE.WRONG_AUTH_CREDENTIALS_MALFORMED_BASE64: "WRONG_AUTH_CREDENTIALS_MALFORMED_BASE64",
            ApiErrorCodeE.WRONG_AUTH_INACTIVE_OR_DELETED: "User inactive or deleted.",
            ApiErrorCodeE.WRONG_AUTH_INVALID_TOKEN: "Token is invalid.",
            ApiErrorCodeE.MAX_FAILED_ATTEMPTS_REACHED: "Error: too many failed attempts. Please, try again in %s minutes." % settings.FAILED_ATTEMPTS_BLOCKER_MIN,
            ApiErrorCodeE.INVALID_USERNAME_SYNTAX: "Enter a valid username. This value may contain only letters, numbers, and _/- character.",
            ApiErrorCodeE.INVALID_EMAIL_SYNTAX: "Enter a valid email address.",
            ApiErrorCodeE.FIELD_IS_REQUIRED: "This field is required.",
            ApiErrorCodeE.USER_NOT_FOUND: "User not found.",
        },
        'FR': {
            ApiErrorCodeE.WRONG_AUTH_INVALID_CREDENTIALS: "Le nom d'utilisateur et le mot de passe ne correspondent pas.",
            ApiErrorCodeE.WRONG_AUTH_DOES_NOT_EXIST: "Impossible de trouver un compte avec ce nom d'utilisateur.",
            ApiErrorCodeE.WRONG_AUTH_CREDENTIALS_NOT_PROVIDED: "Requête invalide. Aucune information d'identification fournie.",
            ApiErrorCodeE.RESULT_ALREADY_EXISTS_USERNAME: "Cet identifiant existe déjà.",
            ApiErrorCodeE.RESULT_ALREADY_EXISTS_EMAIL: "Cet identifiant existe déjà.",
            ApiErrorCodeE.WRONG_AUTH_CREDENTIALS_MALFORMED_SPACES: "En-tête invalide. La chaîne de caractères d'identification ne doit pas contenir d'espaces.",
            ApiErrorCodeE.WRONG_AUTH_INACTIVE_OR_DELETED: "Utilisateur inactif ou supprimé.",
            ApiErrorCodeE.WRONG_AUTH_INVALID_TOKEN: "Token invalide.",
            ApiErrorCodeE.MAX_FAILED_ATTEMPTS_REACHED: "Erreur: trop de tentatives infructueuses. Veuillez réessayer dans %s minutes." % settings.FAILED_ATTEMPTS_BLOCKER_MIN,
            ApiErrorCodeE.INVALID_USERNAME_SYNTAX: "Entrez un nom d'utilisateur valide. Cette valeur ne peut contenir que des lettres, des chiffres et des caractères _ / -.",
            ApiErrorCodeE.INVALID_EMAIL_SYNTAX: "Entrez une adresse email valide.",
            ApiErrorCodeE.FIELD_IS_REQUIRED: "Ce champ est requis.",
            ApiErrorCodeE.USER_NOT_FOUND: "Utilisateur non trouvé.",
        },
        'JA': {
            ApiErrorCodeE.WRONG_AUTH_INVALID_CREDENTIALS: "電子メールまたはユーザー名とパスワードが一致しません。",
            ApiErrorCodeE.WRONG_AUTH_DOES_NOT_EXIST: "そのユーザー名のアカウントが見つかりませんでした。",
            ApiErrorCodeE.WRONG_AUTH_CREDENTIALS_NOT_PROVIDED: "無効なリクエストです。認証情報が提供されていません。",
            ApiErrorCodeE.RESULT_ALREADY_EXISTS_USERNAME: "このユーザー名は既に存在します。",
            ApiErrorCodeE.RESULT_ALREADY_EXISTS_EMAIL: "このユーザー名は既に存在します。",
            ApiErrorCodeE.WRONG_AUTH_CREDENTIALS_MALFORMED_SPACES: "無効な基本ヘッダーです。認証情報文字列はスペースを含んではいけません。",
            ApiErrorCodeE.WRONG_AUTH_INACTIVE_OR_DELETED: "ユーザーが非アクティブまたは削除されました。",
            ApiErrorCodeE.WRONG_AUTH_INVALID_TOKEN: "トークンが無効です",
            ApiErrorCodeE.MAX_FAILED_ATTEMPTS_REACHED: "エラー：失敗した試行が多すぎます。 %s分後にもう一度お試しください。" %
                                                       settings.FAILED_ATTEMPTS_BLOCKER_MIN,
            ApiErrorCodeE.INVALID_USERNAME_SYNTAX: "有効なユーザー名を入力してください。 この値には、文字、数字、および__ /文字のみを含めることができます。",
            ApiErrorCodeE.INVALID_EMAIL_SYNTAX: "有効なメールアドレスを入力してください。",
            ApiErrorCodeE.FIELD_IS_REQUIRED: "この項目は必須です。",
            ApiErrorCodeE.USER_NOT_FOUND: "ユーザーが見つかりません。",
        },
        'IT': {
            ApiErrorCodeE.WRONG_AUTH_INVALID_CREDENTIALS: "Email o username e password non corrispondono.",
            ApiErrorCodeE.WRONG_AUTH_DOES_NOT_EXIST: "Impossibile trovare un account con quel nome utente.",
            ApiErrorCodeE.WRONG_AUTH_CREDENTIALS_NOT_PROVIDED: "Richiesta non valida. Non sono state fornite credenziali.",
            ApiErrorCodeE.RESULT_ALREADY_EXISTS_USERNAME: "Questo username esiste già.",
            ApiErrorCodeE.RESULT_ALREADY_EXISTS_EMAIL: "Questo indirizzo email è già stato registrato.",
            ApiErrorCodeE.WRONG_AUTH_CREDENTIALS_MALFORMED_SPACES: "Intestazione non valida. La stringa delle credenziali non deve contenere spazi.",
            ApiErrorCodeE.WRONG_AUTH_INACTIVE_OR_DELETED: "Utente inattivo o cancellato.",
            ApiErrorCodeE.WRONG_AUTH_INVALID_TOKEN: "Il token non è valido.",
            ApiErrorCodeE.MAX_FAILED_ATTEMPTS_REACHED: "Errore: troppi tentativi falliti. Riprovare tra %s minuti." % settings.FAILED_ATTEMPTS_BLOCKER_MIN,
            ApiErrorCodeE.INVALID_USERNAME_SYNTAX: "Inserire un nome utente valido. Questo valore può contenere solo lettere, numeri e il carattere _/-.",
            ApiErrorCodeE.INVALID_EMAIL_SYNTAX: "Inserisci un indirizzo email valido.",
            ApiErrorCodeE.FIELD_IS_REQUIRED: "Questo campo è obbligatorio.",
            ApiErrorCodeE.USER_NOT_FOUND: "Utente non trovato.",
        },
    }

    if lang and lang in ['EN', 'FR', 'JA', 'ES', 'IT', 'DE'] and lang in msgs_langs and api_error_code in msgs_langs[lang]:
        msg = msgs_langs[lang][api_error_code]
        return msg
    elif api_error_code in msgs_langs['EN']:
        return msgs_langs['EN'][api_error_code]

    return 'Authorization failed.' + str(api_error_code)


def custom_exception_handler(exc, context):
    """
    Custom exception handler.
    Handle default rest framework exceptions and unexpected server exceptions
    Included logging of all exceptions with full traceback history

    Return:
        Response object {
            'detail': <message>,
            'status_code': <status code>
        }
    """
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    full_traceback = traceback.format_exc()
    # Now add the HTTP status code to the response.
    # default rest framework error handling
    if response is not None:
        response.data['status_code'] = response.status_code
        # logs detail data from the exception being handled
        # if 400 <= response.status_code < 500:
        #     log.warning(f"Original error detail and callstack: {exc}")
        #     log.warning(full_traceback)

        if 500 <= response.status_code:
            log.error(f"Original error detail and callstack: {exc}")
            log.error(full_traceback)
    else:
        # unexpected server error handling
        error_data = {
            'detail': f'{type(exc).__name__}: {exc}',
            'status_code': HTTP_500_INTERNAL_SERVER_ERROR
        }
        # returns a JsonResponse
        response = JsonResponse(error_data, safe=False, status=500)
        # logs detail data from the exception being handled
        log.error(f"Original error detail and callstack: {exc}")
        log.error(full_traceback)

    return response
