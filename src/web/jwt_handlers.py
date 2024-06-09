import jwt
import warnings
from datetime import datetime

from django.conf import settings
import logging


log = logging.getLogger(__name__)


def jwt_payload_handler(user):
    username_field = 'username'
    username = user.username

    warnings.warn(
        'The following fields will be removed in the future: '
        '`email` and `user_id`. ',
        DeprecationWarning
    )
    payload = {
        'user_id': str(user.id),
        'email': user.email,
        'http_root': settings.MEDIA_HTTP_ROOT,
        'exp': datetime.utcnow() + settings.JWT_EXPIRATION_DELTA, username_field: username
    }
    return payload


def jwt_decode_handler(token):
    from jwt_auth import settings as jwt_settings

    options = {
        'verify_exp': jwt_settings.JWT_VERIFY_EXPIRATION,
    }

    decode = jwt.decode(
        token,
        jwt_settings.JWT_SECRET_KEY,
        jwt_settings.JWT_VERIFY,
        options=options,
        leeway=jwt_settings.JWT_LEEWAY
    )
    if decode['http_root'] != settings.MEDIA_HTTP_ROOT:
        msg = 'Invalid token header'
        raise Exception(msg)
    return decode


def jwt_get_user_id_payload_handler(user):
    return str(user.id)


def jwt_response_payload_handler(token, user=None, request=None):
    # do not move.
    from web.serializers.users import UserWithVenuesSerializer

    payload = {
        'token': token,
        'user': UserWithVenuesSerializer(user, context={'request': request}
                                         ).data,
        'exp': datetime.utcnow() + settings.JWT_EXPIRATION_DELTA
    }
    try:
        payload['refresh_token'] = request.refresh_token
    except AttributeError:
        payload['refresh_token'] = request.data['refresh_token']
    return payload
