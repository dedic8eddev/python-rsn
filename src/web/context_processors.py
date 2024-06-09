from django.conf import settings
from web.version import VERSION_NAME, VERSION_NUMBER
from web_pro.utils.common import get_final_user_lang
from web.views.admin.common import get_main_menu
from django.urls import resolve


def version_processor(request):
    return {
        'version_name': VERSION_NAME,
        'version_number': VERSION_NUMBER,
        'display_pro_version': settings.DEBUG
    }


def user_lang_processor(request):
    if not request.user.is_authenticated:
        return {
            'user_lang': 'EN'
        }
    else:
        return {
            'user_lang': get_final_user_lang(request.user, request)
        }


def main_menu_processor(request):
    current_url = resolve(request.path_info).url_name
    return {
        'main_menu': get_main_menu(),
        'active': current_url
    }


def site_url_images_processor(request):
    from django.conf import settings
    site_url_images = '{}://{}/'.format(
        'https',
        # 's3.eu-central-1.amazonaws.com',
        settings.AWS_STORAGE_BUCKET_NAME
    )
    return {'SITE_URL_IMAGES': site_url_images}
