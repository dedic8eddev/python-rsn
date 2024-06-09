from django.contrib.auth.backends import ModelBackend
from web.models import UserProfile
import logging
from refreshtoken.models import RefreshToken

log = logging.getLogger(__name__)


class EmailModelBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None):
        log.debug("auth")
        user = None
        if (not username) or (not password):
            return None
        users = UserProfile.objects.filter(email__iexact=username)
        if users:
            user = users[0]
        else:
            users = UserProfile.objects.filter(username__iexact=username)
            if users:
                user = users[0]
            else:
                raise RefreshToken.DoesNotExist

        if user and user.check_password(password):
            return user

    def get_user(self, user_id):
        user = None
        try:
            user = UserProfile.objects.get(pk=user_id)
        except UserProfile.DoesNotExist:
            pass
        return user
