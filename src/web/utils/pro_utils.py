from django.conf import settings


def get_owner_currency(owner_user):
    return owner_user.currency.upper() if owner_user.currency else 'EUR'


def get_owner_url_pro(request_user, place):
    owner_url_pro = '/pro/dashboard/%s' % place.id
    url = "%s/%s" % (settings.SITE_URL.rstrip('/'), owner_url_pro.lstrip('/'))

    return url
