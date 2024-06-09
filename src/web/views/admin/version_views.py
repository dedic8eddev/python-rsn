from django.shortcuts import render
from django.urls import reverse

from web.constants import SettingE
from web.forms.admin_forms import VersionSettingsForm
from web.settings import (get_android_settings, get_ios_settings,
                          set_setting_by_key)
from web.views.admin.common import get_c


def edit_version_settings(request):
    bc_path = [
        ('/', 'Home'),
        # (reverse('list_users'), 'users'),
        (reverse('edit_version_settings'), "Update Version Settings"),
    ]

    c = get_c(request=request, active=None, path=None, bc_path_alt=bc_path)

    sett_ios = get_ios_settings()
    sett_android = get_android_settings()
    data_in = {
        'ios_min_app_version': sett_ios['ios_min_app_version'],
        'ios_newest_app_version': sett_ios['ios_newest_app_version'],
        'android_min_model_version': sett_android['android_min_model_version'],
        'android_min_build_version': sett_android['android_min_build_version'],
    }

    if request.method == 'POST':
        form = VersionSettingsForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            set_setting_by_key(
                SettingE.IOS_MIN_APP_VERSION,
                cd['ios_min_app_version']
            )
            set_setting_by_key(
                SettingE.ANDROID_MIN_MODEL_VERSION,
                cd['android_min_model_version']
            )
            set_setting_by_key(
                SettingE.IOS_NEWEST_APP_VERSION,
                cd['ios_newest_app_version']
            )
            set_setting_by_key(
                SettingE.ANDROID_MIN_BUILD_VERSION,
                cd['android_min_build_version']
            )
    else:
        form = VersionSettingsForm(data=data_in)

    c["form"] = form
    c["action_url"] = reverse('edit_version_settings')
    c["pdg_title"] = "Update Version Settings"
    c["pdg_options"] = []

    return render(request, "edit/version-settings.html", c)
