from __future__ import absolute_import

import logging

from django.utils.translation import ugettext_lazy as _
from packaging import version

from web.forms.api_forms import AppAndroidCheckForm
from web.settings import get_android_settings, get_ios_settings
from web.utils.api_handling import signed_api, fill_default_response_data
from web.utils.exceptions import WrongParametersError
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from web.serializers.api_version import APIVersionSerializer


log = logging.getLogger(__name__)
log_app_ios_check = logging.getLogger("app_ios_check")

log = logging.getLogger(__name__)


# /api/app/ios/check
class AppIOSVersion(APIView):
    permission_classes = [AllowAny]
    sett = get_ios_settings()

    @swagger_auto_schema(
        query_serializer=APIVersionSerializer,
        operation_summary='Return information about iOS application version.',
        operation_description='Return information about iOS application '
                              'version.',
        security=[]
    )
    def get(self, request, format=None):
        serializer = APIVersionSerializer(data=request.query_params)
        if serializer.is_valid(raise_exception=True):
            app_ver = serializer.validated_data.get('app_version')
            build_ver = serializer.validated_data.get('build_version')

            obj_app_version = version.parse(app_ver)
            obj_newest_app_version = version.parse(
                self.sett['ios_newest_app_version']
            )
            obj_min_app_version = version.parse(
                self.sett['ios_min_app_version']
            )
            upgrade_required = False
            if obj_app_version < obj_min_app_version:
                upgrade_required = True

            new_updates_available = False
            if obj_app_version < obj_newest_app_version:
                new_updates_available = True

            lm = "/api/app/ios/check - provided app_ver: {} build ver: {}. UPGRADE REQUIRED: {} NEW UPDATES AVAILABLE: {}"  # noqa
            log_app_ios_check.debug(lm.format(
                app_ver, build_ver, upgrade_required, new_updates_available
            ))
            data = {
                "upgrade_required": upgrade_required,
                "new_updates_available": new_updates_available,
                "newest_app_version": self.sett['ios_newest_app_version'],
            }
            # support old implementation
            response_data = {'data': data}
            fill_default_response_data(response_data)
            return Response(response_data)

    @swagger_auto_schema(
        request_body=APIVersionSerializer,
        operation_summary='Return information about iOS application version.',
        operation_description='The method POST is deprecated for this '
                              'endpoint.',
        deprecated=True,
        security=[]
    )
    def post(self, request, format=None):
        log.warning('The POST method Is deprecated for the endpoint '
                    '/api/app/ios/check')
        request.query_params._mutable = True
        for key, value in request.data.items():
            request.query_params[key] = value
        request.query_params._mutable = False
        return self.get(request, format)


# /api/app/android/check
@signed_api(FormClass=AppAndroidCheckForm, token_check=False, json_used=True)
def app_android_check(request):
    form = request.form
    upgrade_required = False
    new_updates_available = False
    sett = get_android_settings()

    if request.method == 'POST':
        if form.is_valid():
            cd = form.cleaned_data
            model_ver = int(cd['model_version'])
            # app_ver = cd['app_version']
            # build_ver = cd['build_version']
            if model_ver < sett['android_min_model_version']:
                upgrade_required = True

            lm = "/api/app/android/check - provided model_ver: {}. UPGRADE REQUIRED: {} NEW UPDATES AVAILABLE: {}"  # noqa
            log_app_ios_check.debug(lm.format(
                model_ver, upgrade_required, new_updates_available
            ))

            return {
                "upgrade_required": upgrade_required,
                "min_build_version": sett['android_min_build_version'],
                # "new_updates_available": new_updates_available,
            }

    raise WrongParametersError(_("Wrong parameters."), form)
