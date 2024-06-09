"""
Django settings for raisin project.

Generated by 'django-admin startproject' using Django 1.10.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os
from .settings_common import MEDIA_ROOT, SITE_URL

GOOGLE_APPLICATION_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")  # noqa
GOOGLE_API_KEY = os.getenv("RAISIN_GOOGLE_API_KEY")

PUSH_NOTIFY_APP_ID = os.getenv("RAISIN_PUSH_NOTIFY_APP_ID")
PUSH_NOTIFY_REST_API_KEY = os.getenv("RAISIN_PUSH_NOTIFY_REST_API_KEY")
PUSH_NOTIFY_API_URL = os.getenv("RAISIN_PUSH_NOTIFY_API_URL")

AWS_ACCESS_KEY_ID = os.getenv("RAISIN_AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("RAISIN_AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("RAISIN_AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.getenv("RAISIN_AWS_S3_REGION_NAME")
AWS_S3_CUSTOM_DOMAIN = os.getenv("RAISIN_AWS_S3_CUSTOM_DOMAIN")

# Donations settings
ENV_APPLE = os.getenv("RAISIN_APPLE_ENV")
SECRET_KEY_APPLE = os.getenv("RAISIN_APPLE_SECRET_KEY")
URL_APPLE_SANDBOX = "https://sandbox.itunes.apple.com/verifyReceipt"
URL_APPLE_PROD = "https://buy.itunes.apple.com/verifyReceipt"
BASE_PRICE_APPLE = 10  # price used for calculations (in EUR)
T_FMT = '%Y-%m-%d %H:%M:%S'

# Vuforia settings
VUFORIA_ACCESS_KEY = os.getenv("RAISIN_VUFORIA_ACCESS_KEY")
VUFORIA_SECRET_KEY = os.getenv("RAISIN_VUFORIA_SECRET_KEY")
VUFORIA_URL = "https://vws.vuforia.com"

RAISIN_CHARGEBEE_SITE_API_KEY = os.getenv("RAISIN_CHARGEBEE_SITE_API_KEY")
RAISIN_CHARGEBEE_SITE = os.getenv("RAISIN_CHARGEBEE_SITE")
RAISIN_CHARGEBEE_URL = os.getenv("RAISIN_CHARGEBEE_URL")
RAISIN_CHARGEBEE_CMS_USER_UUID = os.getenv("RAISIN_CHARGEBEE_CMS_USER_UUID")

CANNY_API_KEY_EN = os.getenv("RAISIN_CANNY_API_KEY_EN")
CANNY_API_KEY_FR = os.getenv("RAISIN_CANNY_API_KEY_FR")
CANNY_PRIVATE_KEY_EN = os.getenv("RAISIN_CANNY_PRIVATE_SSO_KEY_EN")
CANNY_PRIVATE_KEY_FR = os.getenv("RAISIN_CANNY_PRIVATE_SSO_KEY_FR")
CANNY_URL = os.getenv("RAISIN_CANNY_URL")