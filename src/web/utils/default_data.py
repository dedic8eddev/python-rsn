from django.conf import settings


def get_erased_user_uid():
    return settings.ERASED_USER_UUID
