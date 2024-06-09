from jwt_auth.exceptions import AuthenticationFailed
from rest_framework import authentication
from jwt_auth.mixins import JSONWebTokenAuthMixin
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import NotAuthenticated


class CustomTokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        try:
            token_auth = JSONWebTokenAuthMixin()
            user, auth = token_auth.authenticate(request)
            return user, auth
        except AuthenticationFailed:
            return None
        except NotAuthenticated:
            return None


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening
