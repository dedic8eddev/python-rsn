from web.constants import (SettingE, get_setting_field_per_type,
                           get_setting_type_by_key)
from web.models import Setting


def get_setting_by_key(key, default_value=None):
    items = Setting.objects.filter(key=key)
    if not items:
        return default_value
    item = items[0]
    field = get_setting_field_per_type(item.type)
    if not field or not hasattr(item, field) or not getattr(item, field):
        return default_value
    return getattr(item, field)


def set_setting_by_key(key, value):
    s_type = get_setting_type_by_key(key)
    if not s_type:
        return
    field = get_setting_field_per_type(s_type)
    if not field:
        return

    items = Setting.objects.filter(key=key)
    if items:
        item = items[0]
    else:
        item = Setting()
        item.key = key
        item.type = s_type

    setattr(item, field, value)
    item.save()
    item.refresh_from_db()


def get_ios_settings():
    return {
        'ios_min_app_version': get_setting_by_key(
            SettingE.IOS_MIN_APP_VERSION, '2'
        ),
        'ios_newest_app_version': get_setting_by_key(
            SettingE.IOS_NEWEST_APP_VERSION, '4.1.0'
        ),
    }


def get_android_settings():
    return {
        'android_min_model_version': get_setting_by_key(
            SettingE.ANDROID_MIN_MODEL_VERSION, '0'
        ),
        'android_min_build_version': get_setting_by_key(
            SettingE.ANDROID_MIN_BUILD_VERSION, '1.0.0'
        ),
    }
