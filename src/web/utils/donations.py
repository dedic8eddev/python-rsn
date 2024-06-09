import datetime as dt
import json
import logging
import math
import time

import requests
from django.conf import settings

from web.constants import DonationFrequencyE, DonationStatusE
from web.models import Donation, DonationReceipt, UserProfile
from web.utils.filenames import (get_local_file_contents,
                                 replace_file_in_local_path)

from .exceptions import ResultErrorWithMsg
from .model_tools import load_json, load_json_if_str

log = logging.getLogger(__name__)


donation_products_apple = {
    'dev': {
        "digital.raisin.non.renewing.subscription.development.tip1": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 1.99,
            "currency": "EUR",
            "dayspan": 183,
        },
        "digital.raisin.non.renewing.subscription.development.tip2": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 4.99,
            "currency": "EUR",
            "dayspan": 183,
        },
        "digital.raisin.non.renewing.subscription.development.tip3": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 8.99,
            "currency": "EUR",
            "dayspan": 183,
        },
        "digital.raisin.non.renewing.subscription.development.tip4": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 13.99,
            "currency": "EUR",
            "dayspan": 183,
        },

        "digital.raisin.non.renewing.subscription.development.tip5": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 21.99,
            "currency": "EUR",
            "dayspan": 183,
        },
        "digital.raisin.non.renewing.subscription.development.tip6": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 39.99,
            "currency": "EUR",
            "dayspan": 183,
        },
        "digital.raisin.non.renewing.subscription.development.tip7": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 74.99,
            "currency": "EUR",
            "dayspan": 183,
        },
        "digital.raisin.non.renewing.subscription.development.tip8": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 129.99,
            "currency": "EUR",
            "dayspan": 183,
        },

        "digital.raisin.non.renewing.subscription.development.tip9": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 299.99,
            "currency": "EUR",
            "dayspan": 183,
        },
        "digital.raisin.non.renewing.subscription.development.tip10": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 449.99,
            "currency": "EUR",
            "dayspan": 183,
        },


        # ----- AUTO RENEWABLE -----
        "digital.raisin.auto.renewable.subscription.development.tip1": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 0.99,
            "currency": "EUR",
            "dayspan": 30,
        },
        "digital.raisin.auto.renewable.subscription.development.tip2": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 1.79,
            "currency": "EUR",
            "dayspan": 30,
        },
        "digital.raisin.auto.renewable.subscription.development.tip3": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 4.49,
            "currency": "EUR",
            "dayspan": 30,
        },
        "digital.raisin.auto.renewable.subscription.development.tip4": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 6.99,
            "currency": "EUR",
            "dayspan": 30,
        },

        "digital.raisin.auto.renewable.subscription.development.tip5": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 8.99,
            "currency": "EUR",
            "dayspan": 30,
        },
        "digital.raisin.auto.renewable.subscription.development.tip6": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 13.49,
            "currency": "EUR",
            "dayspan": 30,
        },
        "digital.raisin.auto.renewable.subscription.development.tip7": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 17.99,
            "currency": "EUR",
            "dayspan": 30,
        },
        "digital.raisin.auto.renewable.subscription.development.tip8": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 22.49,
            "currency": "EUR",
            "dayspan": 30,
        },

        "digital.raisin.auto.renewable.subscription.development.tip9": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 39.99,
            "currency": "EUR",
            "dayspan": 30,
        },

        "digital.raisin.auto.renewable.subscription.development.tip10": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 44.99,
            "currency": "EUR",
            "dayspan": 30,
        },
    },

    'prod': {
        "digital.raisin.non.renewing.subscription.tip1": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 1.99,
            "currency": "EUR",
            "dayspan": 183,
        },
        "digital.raisin.non.renewing.subscription.tip2": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 4.99,
            "currency": "EUR",
            "dayspan": 183,
        },
        "digital.raisin.non.renewing.subscription.tip3": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 8.99,
            "currency": "EUR",
            "dayspan": 183,
        },
        "digital.raisin.non.renewing.subscription.tip4": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 13.99,
            "currency": "EUR",
            "dayspan": 183,
        },

        "digital.raisin.non.renewing.subscription.tip5": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 21.99,
            "currency": "EUR",
            "dayspan": 183,
        },
        "digital.raisin.non.renewing.subscription.tip6": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 39.99,
            "currency": "EUR",
            "dayspan": 183,
        },
        "digital.raisin.non.renewing.subscription.tip7": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 74.99,
            "currency": "EUR",
            "dayspan": 183,
        },
        "digital.raisin.non.renewing.subscription.tip8": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 129.99,
            "currency": "EUR",
            "dayspan": 183,
        },

        "digital.raisin.non.renewing.subscription.tip9": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 299.99,
            "currency": "EUR",
            "dayspan": 183,
        },
        "digital.raisin.non.renewing.subscription.tip10": {  # miesiąc
            "freq": DonationFrequencyE.ONCE,
            "price": 449.99,
            "currency": "EUR",
            "dayspan": 183,
        },

        # ----- AUTO RENEWABLE -----
        "digital.raisin.auto.renewable.subscription.tip1": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 0.99,
            "currency": "EUR",
            "dayspan": 30,
        },
        "digital.raisin.auto.renewable.subscription.tip2": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 1.79,
            "currency": "EUR",
            "dayspan": 30,
        },
        "digital.raisin.auto.renewable.subscription.tip3": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 4.49,
            "currency": "EUR",
            "dayspan": 30,
        },
        "digital.raisin.auto.renewable.subscription.tip4": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 6.99,
            "currency": "EUR",
            "dayspan": 30,
        },
        "digital.raisin.auto.renewable.subscription.tip5": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 8.99,
            "currency": "EUR",
            "dayspan": 30,
        },
        "digital.raisin.auto.renewable.subscription.tip6": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 13.49,
            "currency": "EUR",
            "dayspan": 30,
        },
        "digital.raisin.auto.renewable.subscription.tip7": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 17.99,
            "currency": "EUR",
            "dayspan": 30,
        },
        "digital.raisin.auto.renewable.subscription.tip8": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 22.49,
            "currency": "EUR",
            "dayspan": 30,
        },
        "digital.raisin.auto.renewable.subscription.tip9": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 39.99,
            "currency": "EUR",
            "dayspan": 30,
        },
        "digital.raisin.auto.renewable.subscription.tip10": {  # miesiąc
            "freq": DonationFrequencyE.MONTHLY,
            "price": 44.99,
            "currency": "EUR",
            "dayspan": 30,
        },
    },
}


donation_products_android = {
    'com.raisin.raisin.tip1': {
        'freq': DonationFrequencyE.ONCE,
        'dayspan': 30,
        'price': 1,
        "currency": "EUR",
    },
    'com.raisin.raisin.tip2': {
        'freq': DonationFrequencyE.ONCE,
        'dayspan': 30,
        'price': 2,
        "currency": "EUR",
    },
    'com.raisin.raisin.tip5': {
        'freq': DonationFrequencyE.ONCE,
        'dayspan': 30,
        'price': 5,
        "currency": "EUR",
    },
    'com.raisin.raisin.tip10': {
        'freq': DonationFrequencyE.ONCE,
        'dayspan': 30,
        'price': 10,
        "currency": "EUR",
    },
    'com.raisin.raisin.tip20': {
        'freq': DonationFrequencyE.ONCE,
        'dayspan': 30,
        'price': 20,
        "currency": "EUR",
    },
    'com.raisin.raisin.tip50': {
        'freq': DonationFrequencyE.ONCE,
        'dayspan': 30,
        'price': 50,
        "currency": "EUR",
    },
    'com.raisin.raisin.tip100': {
        'freq': DonationFrequencyE.ONCE,
        'dayspan': 30,
        'price': 100,
        "currency": "EUR",
    },
    'com.raisin.raisin.tip200': {
        'freq': DonationFrequencyE.ONCE,
        'dayspan': 30,
        'price': 200,
        "currency": "EUR",
    },
    'com.raisin.raisin.tip300': {
        'freq': DonationFrequencyE.ONCE,
        'dayspan': 30,
        'price': 300,
        "currency": "EUR",
    },
    'com.raisin.raisin.tip_max': {
        'freq': DonationFrequencyE.ONCE,
        'dayspan': 30,
        'price': 350,
        "currency": "EUR",
    },

    'com.raisin.raisin.sub1': {
        'freq': DonationFrequencyE.MONTHLY,
        'dayspan': 30,
        'price': 1,
        "currency": "EUR",
    },
    'com.raisin.raisin.sub2': {
        'freq': DonationFrequencyE.MONTHLY,
        'dayspan': 30,
        'price': 2,
        "currency": "EUR",
    },
    'com.raisin.raisin.sub5': {
        'freq': DonationFrequencyE.MONTHLY,
        'dayspan': 30,
        'price': 5,
        "currency": "EUR",
    },
    'com.raisin.raisin.sub10': {
        'freq': DonationFrequencyE.MONTHLY,
        'dayspan': 30,
        'price': 10,
        "currency": "EUR",
    },
    'com.raisin.raisin.sub20': {
        'freq': DonationFrequencyE.MONTHLY,
        'dayspan': 30,
        'price': 20,
        "currency": "EUR",
    },
    'com.raisin.raisin.sub50': {
        'freq': DonationFrequencyE.MONTHLY,
        'dayspan': 30,
        'price': 50,
        "currency": "EUR",
    },
    'com.raisin.raisin.sub100': {
        'freq': DonationFrequencyE.MONTHLY,
        'dayspan': 30,
        'price': 100,
        "currency": "EUR",
    },
    'com.raisin.raisin.sub200': {
        'freq': DonationFrequencyE.MONTHLY,
        'dayspan': 30,
        'price': 200,
        "currency": "EUR",
    },
    'com.raisin.raisin.sub300': {
        'freq': DonationFrequencyE.MONTHLY,
        'dayspan': 30,
        'price': 300,
        "currency": "EUR",
    },
    'com.raisin.raisin.sub_max': {
        'freq': DonationFrequencyE.MONTHLY,
        'dayspan': 30,
        'price': 350,
        "currency": "EUR",
    },
}

BASE_PRICE_APPLE = 10
BASE_PRICE_ANDROID = 10

for i, item in donation_products_apple['dev'].items():
    if item['freq'] == DonationFrequencyE.ONCE:
        price = item['price']
        dayspan = math.ceil(365 / (BASE_PRICE_APPLE / price))
        donation_products_apple['dev'][i]['dayspan'] = dayspan
for i, item in donation_products_apple['prod'].items():
    if item['freq'] == DonationFrequencyE.ONCE:
        price = item['price']
        dayspan = math.ceil(365 / (BASE_PRICE_APPLE / price))
        donation_products_apple['prod'][i]['dayspan'] = dayspan


for i, item in donation_products_android.items():
    if item['freq'] == DonationFrequencyE.ONCE:
        price = item['price']
        dayspan = math.ceil(365 / (BASE_PRICE_ANDROID / price))
        donation_products_android[i]['dayspan'] = dayspan


def set_android_code_data(code):
    replace_file_in_local_path(settings.ANDROID_CODE_PATH, code)


def get_android_code_data():
    return get_local_file_contents(settings.ANDROID_CODE_PATH)


def set_android_refresh_token_data(token_data_dict):
    token_data_dict['created_at_ts'] = time.time()
    token_data_str = json.dumps(token_data_dict)
    replace_file_in_local_path(settings.ANDROID_REFRESH_TOKEN_PATH, token_data_str)


def get_android_refresh_token_data():
    data = get_local_file_contents(settings.ANDROID_REFRESH_TOKEN_PATH)
    if data:
        return load_json(data, None)
    return data


def android_get_access_token():
    # we check whether token exists
    token_data = get_android_refresh_token_data()
    if not token_data or 'access_token' not in token_data or 'token_type' not in token_data or \
            'expires_in' not in token_data or 'refresh_token' not in token_data or 'created_at_ts' not in token_data \
            or not token_data['access_token'] or not token_data['token_type'] or not token_data['expires_in'] \
            or not token_data['refresh_token'] or not token_data['created_at_ts']:
        code = get_android_code_data()
        if not code:
            log.debug("ANDROID - No refresh token and no code. must_redirect=1")
            return None, "error", ["must_redirect", 1]
        log.debug("ANDROID - No refresh token - using the code %s ", code)
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.ANDROID_CLIENT_ID,
            "client_secret": settings.ANDROID_GOOGLE_SECRET_KEY,
            "redirect_uri": settings.ANDROID_REDIRECT_URI,
        }
        resp = requests.post("https://accounts.google.com/o/oauth2/token", data=data)
        resp_json = resp.json()
        log.debug("ANDROID - authorization response: %s", resp_json)
        # {
        #     "access_token": "ya29.ZStBkRnGyZ2mUYOLgls7QVBxOg82XhBCFo8UIT5gM",  # used for accessing the APIs
        #     "token_type": "Bearer",
        #     "expires_in": 3600,
        #     "refresh_token": "1/zaaHNytlC3SEBX7F2cfrHcqJEa3KoAHYeXES6nmho"     # used for refreshing the access token
        # }
        if resp_json and 'access_token' in resp_json and 'token_type' in resp_json and 'expires_in' in resp_json \
                and 'refresh_token' in resp_json \
                and resp_json['access_token'] and resp_json['token_type'] and resp_json['expires_in'] \
                and resp_json['refresh_token']:
            log.debug("ANDROID - setting refresh token - token data: %s ", resp_json)
            set_android_refresh_token_data(resp_json)
            token_data = get_android_refresh_token_data()
        else:   # {'error': 'invalid_grant', 'error_description': 'Code was already redeemed.'}
            log.debug("ANDROID - code %s was already redeemed. must_redirect=2", code)
            return None, "error", ["must_redirect", 2]

    dt_now_ts = time.time()
    dt_expires_at_ts = token_data['created_at_ts'] + token_data['expires_in']
    if dt_expires_at_ts > dt_now_ts:
        access_token = token_data['access_token']
    else:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": token_data['refresh_token'],
            "client_id": settings.ANDROID_CLIENT_ID,
            "client_secret": settings.ANDROID_GOOGLE_SECRET_KEY,
        }
        log.debug("ANDROID - authorization using refresh_token %s", token_data['refresh_token'])
        resp = requests.post("https://accounts.google.com/o/oauth2/token", data=data)
        resp_json = resp.json()
        log.debug("ANDROID - authorization using refresh_token %s - response %s",
                  token_data['refresh_token'], resp_json)
        if resp_json and 'access_token' in resp_json and 'token_type' in resp_json and 'expires_in' in resp_json \
                and resp_json['access_token'] and resp_json['token_type'] and resp_json['expires_in']:
            access_token = resp_json['access_token']
            token_data['access_token'] = access_token
            token_data['expires_in'] = resp_json['expires_in']
            token_data['token_type'] = resp_json['token_type']
            set_android_refresh_token_data(token_data)
            log.debug("ANDROID - authorization using refresh_token %s OK - storing token.", token_data['refresh_token'])
        else:
            log.debug("ANDROID - authorization ERROR, must_redirect=3")
            return None, "error", ["must_redirect", 3]

    return access_token, "OK", []


def android_get_provider_response_for_receipt(rec_json_text):
    dec_status, dec_details = android_decode_receipt(rec_json_text)
    if dec_status == "OK":
        rec_user, rec_prod_id, rec_freq, rec_purchase_token, rec_api_prod_type = dec_details
    else:
        raise ResultErrorWithMsg(*dec_details)
    resp_json = android_get_provider_response(rec_api_prod_type=rec_api_prod_type,
                                              rec_prod_id=rec_prod_id,
                                              rec_purchase_token=rec_purchase_token)
    return resp_json


def android_get_provider_response(rec_api_prod_type, rec_prod_id, rec_purchase_token):
    # ====== GET ANDROID PURCHASE INFO FROM GOOGLE ======
    # https://developers.google.com/android-publisher/api-ref/purchases/{api_prod_type}/get
    access_token, at_status, at_status_info = android_get_access_token()
    if not access_token and at_status == 'error' and at_status_info:
        raise ResultErrorWithMsg(*at_status_info)

    app_id = settings.ANDROID_APP_ID
    url_prod = "https://www.googleapis.com/androidpublisher/v3/applications/%(app_id)s/purchases/%(api_prod_type)s" \
               "/%(product_id)s/tokens/%(product_token)s?access_token=%(access_token)s" % {
                   "app_id": app_id,
                   "api_prod_type": rec_api_prod_type,
                   "product_id": rec_prod_id,
                   "product_token": rec_purchase_token,
                   "access_token": access_token}

    resp = requests.get(url_prod)
    try:
        resp_json = resp.json()
        log.debug("ANDROID - getting response for URL prod %s: %s", url_prod, resp_json)
    except ValueError:
        raise ResultErrorWithMsg("google_api_error", "1a")
    except Exception:
        raise ResultErrorWithMsg("google_api_error", "1b")

    if resp.status_code != 200:
        raise ResultErrorWithMsg("google_api_error", "1c")
    # ====== /GET ANDROID PURCHASE INFO FROM GOOGLE ======
    return resp_json


def android_decode_receipt(rec_resp_json):
    rec_resp_json = load_json_if_str(rec_resp_json)
    """
    Args:
        rec_resp_json: dict structure containing the following keys:
         productId/subscriptionId (one of those must be present)
         userId
         purchaseToken

    Returns:

    """

    rec_user_id = rec_resp_json['userId']
    rec_purchase_token = rec_resp_json['purchaseToken']

    if 'productId' in rec_resp_json and rec_resp_json['productId']:
        rec_freq = DonationFrequencyE.ONCE
        rec_prod_id = rec_resp_json['productId']
        rec_api_prod_type = "products"
        log.debug("productId: %s - ONCE", rec_resp_json['productId'])
    elif 'subscriptionId' in rec_resp_json and rec_resp_json['subscriptionId']:
        rec_freq = DonationFrequencyE.MONTHLY
        rec_prod_id = rec_resp_json['subscriptionId']
        rec_api_prod_type = "subscriptions"
        log.debug("subscriptionId: %s - MONTHLY", rec_resp_json['subscriptionId'])
    else:
        log.debug("No productId or subscriptionId in receipt. wrong_receipt_data=1a")
        return 'error', ['wrong_receipt_data', '1a']

    if rec_prod_id not in donation_products_android:
        log.debug("Product not available in donation_products_android. wrong_receipt_data=1b")
        return 'error', ['wrong_receipt_data', '1b']

    log.debug("ANDROID - rec_user_id: %s, rec_prod_id: %s", rec_user_id, rec_prod_id)

    try:
        rec_user = UserProfile.active.get(id=rec_user_id)
    except ValueError:
        return 'error', ['wrong_receipt_data', '1c']
    except UserProfile.DoesNotExist:
        return 'error', ['wrong_receipt_data', '1d']

    return 'OK', [rec_user, rec_prod_id, rec_freq, rec_purchase_token, rec_api_prod_type]


def recalc_for_user(rec_user):
    """
    Recalculate donations for user, both for Apple and Android
    Args:
        rec_user:

    Returns:
    """
    log.debug("RECALC FOR USER %s (id: %s) STARTED" % (rec_user.username, rec_user.id))
    dt_now_ts = time.time()
    dt_now_ms = round(dt_now_ts * 1000)

    # get all donations for user, both Apple and Android
    all_ds_for_user = Donation.active.filter(author=rec_user).order_by('created_time')

    for d in all_ds_for_user:
        log.debug("RECALC FOR USER %s DATE FROM %s DATE TO %s " % (rec_user.id, d.date_from, d.date_to))
        if isinstance(d.extra_json, str):
            extra_json = load_json(d.extra_json)
        elif isinstance(d.extra_json, dict):
            extra_json = d.extra_json
        else:
            log.debug("RECALC FOR USER - Bad donation with id %d - extra_json is malformed, incorrect type" % d.id)
            continue

        if 'purchase_date_ms' not in extra_json or not extra_json['purchase_date_ms'] or 'dayspan' not in extra_json \
                or not extra_json['dayspan'] or 'dayspan_ms' not in extra_json or not extra_json['dayspan_ms'] or \
                'expiry_date_ms' not in extra_json or not extra_json['expiry_date_ms']:
            log.debug("RECALC FOR USER - Bad donation with id %d - extra_json is malformed" % d.id)
            continue

        purchase_date_ms = int(extra_json['purchase_date_ms'])
        last_purchase_date_ms = purchase_date_ms
        last_updated_date_ms = int(round(time.time() * 1000))
        # once_exp_test_ms = None
        if d.frequency == DonationFrequencyE.ONCE:
            # if not once_exp_test_ms:
            #     once_exp_test_ms = purchase_date_ms
            # elif once_exp_test_ms < purchase_date_ms:
            #     once_exp_test_ms = purchase_date_ms

            once_exp_test_ms = purchase_date_ms + int(extra_json['dayspan_ms'])
            rec_user.p_once_expiry_date_ms = once_exp_test_ms

            rec_user.p_once_last_updated_date_ms = last_updated_date_ms
            rec_user.p_once_last_purchase_date_ms = purchase_date_ms
            rec_user.save()
            rec_user.refresh_from_db()
            log.debug("RECALC: %s: Item with product_id: %s transaction_id: %s of 'ONCE' type - "
                      "storing the purchase data for user %s ID: %s: "
                      "\nDAYSPAN: %d, "
                      "\np_once_expiry_date_ms: %s - %s, "
                      "\np_once_last_purchase_date_ms: %s - %s, "
                      "\np_once_last_updated_date_ms: %s - %s",
                      d.app_os,
                      d.product_id, d.transaction_id,
                      rec_user.username, rec_user.id,
                      extra_json['dayspan'],
                      rec_user.p_once_expiry_date_ms,
                      dt.datetime.fromtimestamp((int(rec_user.p_once_expiry_date_ms) / 1000)).strftime(
                          settings.T_FMT),
                      rec_user.p_once_last_purchase_date_ms,
                      dt.datetime.fromtimestamp((int(rec_user.p_once_last_purchase_date_ms) / 1000)).strftime(
                          settings.T_FMT),
                      rec_user.p_once_last_updated_date_ms,
                      dt.datetime.fromtimestamp((int(rec_user.p_once_last_updated_date_ms) / 1000)).strftime(
                          settings.T_FMT))
        if d.frequency == DonationFrequencyE.MONTHLY:
            dayspan = extra_json['dayspan']
            # date_to_ms = int(item['purchase_date_ms']) + dayspan * 24 * 3600 * 1000
            date_to_ms = int(extra_json['expiry_date_ms'])
            date_to = dt.datetime.fromtimestamp(round(date_to_ms / 1000))
            p_price = None
            if d.status == DonationStatusE.CANCELED:
                log.debug(
                    "RECALC: %s: The item for product_id: %s transaction_id: %s receipt creation date %s, "
                    "MS: %s HAS BEEN CANCELLED ON %s - SKIPPING", d.app_os, d.product_id, d.transaction_id,
                    extra_json['rec_date'], extra_json['rec_date_ms'], extra_json['rec_date'])
            else:
                m_changed = False
                m_expiry_date_ms = None

                if d.app_os == 'apple':
                    if not rec_user.p_monthly_expiry_date_ms_apple or \
                            rec_user.p_monthly_expiry_date_ms_apple < date_to_ms:
                        rec_user.p_monthly_expiry_date_ms_apple = date_to_ms
                        rec_user.p_monthly_last_updated_date_ms_apple = dt_now_ms
                        rec_user.p_monthly_last_purchase_date_ms_apple = last_purchase_date_ms
                        rec_user.save()
                        rec_user.refresh_from_db()
                        m_changed = True
                        m_expiry_date_ms = rec_user.p_monthly_expiry_date_ms_apple
                elif d.app_os == 'android':
                    if not rec_user.p_monthly_expiry_date_ms_android or \
                            rec_user.p_monthly_expiry_date_ms_android < date_to_ms:
                        rec_user.p_monthly_expiry_date_ms_android = date_to_ms
                        rec_user.p_monthly_last_updated_date_ms_android = dt_now_ms
                        rec_user.p_monthly_last_purchase_date_ms_android = last_purchase_date_ms
                        rec_user.save()
                        rec_user.refresh_from_db()
                        m_changed = True
                        m_expiry_date_ms = rec_user.p_monthly_expiry_date_ms_android
                else:
                    continue

                if m_changed and m_expiry_date_ms:
                    log.debug("RECALC: %s: Item with product_id: %s transaction_id: %s of 'MONTHLY' type - "
                              "storing the purchase data for user %s ID: %s: "
                              "\nDAYSPAN: %d, "
                              "\np_monthly_expiry_date_ms: %s - %s, "
                              "\np_monthly_last_purchase_date_ms: %s - %s, "
                              "\np_monthly_last_updated_date_ms: %s - %s",
                              d.app_os,
                              d.product_id, d.transaction_id,
                              rec_user.username, rec_user.id,
                              dayspan,
                              m_expiry_date_ms,
                              dt.datetime.fromtimestamp((int(m_expiry_date_ms) / 1000)).strftime(
                                  settings.T_FMT),
                              last_purchase_date_ms,
                              dt.datetime.fromtimestamp((int(last_purchase_date_ms) / 1000)).strftime(settings.T_FMT),
                              dt_now_ms,
                              dt.datetime.fromtimestamp((int(dt_now_ms) / 1000)).strftime(settings.T_FMT))

    dates_used = []
    if rec_user.p_monthly_expiry_date_ms_android:
        dates_used.append(rec_user.p_monthly_expiry_date_ms_android)
    if rec_user.p_monthly_expiry_date_ms_apple:
        dates_used.append(rec_user.p_monthly_expiry_date_ms_apple)

    if dates_used:
        dates_used.sort(reverse=True)
        date_to_set = dates_used[0]
    else:
        date_to_set = None

    rec_user.p_monthly_expiry_date_ms = date_to_set
    rec_user.save()
    rec_user.refresh_from_db()


def android_store_donation_recalc_user(user, rec_resp_json):
    rec_resp_json = load_json_if_str(rec_resp_json)
    """

    Args:
        user:
        rec_resp_json: dict structure containing the following keys:
         productId
         userId
         purchaseToken
    Returns:

    """
    dr = DonationReceipt(
        author=user,
        app_os='android',
        # product_id=cd['product_id'],
        # qty=cd['qty'] if cd['qty'] else 1,
        # transaction_id=cd['transaction_id'],
        is_sandbox=True,
        receipt_data=json.dumps(rec_resp_json),
        provider_response=None
        # provider_response=request.data
    )
    dr.save()
    dr.refresh_from_db()
    access_token = None
    # rec_resp_json = request.data
    atrapa = False
    # if 'atrapa' in rec_resp_json and rec_resp_json['atrapa']:
    #     atrapa = True
    # else:
    #     atrapa = False

    log.debug("======== ANDROID receipt for logged-inuser ID: %s, data: %s", user.id, rec_resp_json)

    # decode receipt data (receipt_data field in DonationReceipt = web_donationreceipt),
    # including - if possible - userId. TODO - This should be handled also for cases when there is no
    #
    dec_status, dec_details = android_decode_receipt(rec_resp_json)
    if dec_status == "OK":
        rec_user, rec_prod_id, rec_freq, rec_purchase_token, rec_api_prod_type = dec_details
    else:
        raise ResultErrorWithMsg(*dec_details)
    don_prod_data = donation_products_android[rec_prod_id]

    # TODO - check whether rec_user.id matches with the logged-in user ID. I will do it later since for
    # now it would bring about some problems with testing

    dt_now_ts = time.time()
    dt_now_ms = round(dt_now_ts * 1000)
    dt_now = dt.datetime.fromtimestamp(dt_now_ts)
    resp_json = android_get_provider_response_for_receipt(rec_resp_json)
    # # ====== GET ANDROID PURCHASE INFO FROM GOOGLE ======
    # # https://developers.google.com/android-publisher/api-ref/purchases/{api_prod_type}/get
    # access_token, at_status, at_status_info = android_get_access_token()
    # if not access_token and at_status == 'error' and at_status_info:
    #     raise ResultErrorWithMsg(*at_status_info)
    #
    # app_id = settings.ANDROID_APP_ID
    # url_prod = "https://www.googleapis.com/androidpublisher/v3/applications/%(app_id)s/purchases/%(api_prod_type)s" \
    #            "/%(product_id)s/tokens/%(product_token)s?access_token=%(access_token)s" % {
    #                "app_id": app_id,
    #                "api_prod_type": rec_api_prod_type,
    #                "product_id": rec_prod_id,
    #                "product_token": rec_purchase_token,
    #                "access_token": access_token}
    # resp = requests.get(url_prod)
    # try:
    #     resp_json = resp.json()
    # except ValueError:
    #     raise ResultErrorWithMsg("google_api_error", "1a")
    # except Exception:
    #     raise ResultErrorWithMsg("google_api_error", "1b")
    # # ====== /GET ANDROID PURCHASE INFO FROM GOOGLE ======

    dr.provider_response = resp_json
    dr.save()
    dr.refresh_from_db()

    if 'orderId' not in resp_json or not resp_json['orderId']:
        log.debug("ANDROID - no orderId in the provider response. google_api_error=1c")
        raise ResultErrorWithMsg("google_api_error", "1c")

    order_id = resp_json['orderId']
    log.debug("ANDROID - orderId from provider response is: %s", order_id)

    if rec_freq == DonationFrequencyE.ONCE:
        if 'purchaseTimeMillis' not in resp_json or not resp_json['purchaseTimeMillis'] \
                or 'purchaseState' not in resp_json:
            log.debug("ANDROID - ONCE - purchaseTimeMillis not available in the response. google_api_error=1d")
            raise ResultErrorWithMsg("google_api_error", "1d")

        purchase_date_ms = int(resp_json['purchaseTimeMillis'])
        purchase_status = int(resp_json['purchaseState'])
        dayspan = int(don_prod_data['dayspan'])
        dayspan_ms = dayspan * 3600 * 24 * 1000
        end_date_ms = purchase_date_ms + dayspan_ms
        date_from = dt.datetime.fromtimestamp(round(int(purchase_date_ms)/1000))
        date_to = dt.datetime.fromtimestamp(round(int(end_date_ms)/1000))
        currency = don_prod_data['currency']
        if int(purchase_status) == 0:  # 0 - purchased, 1 - cancelled
            don_status = DonationStatusE.ACTIVE
        else:
            don_status = DonationStatusE.CANCELED
    elif rec_freq == DonationFrequencyE.MONTHLY:
        if 'startTimeMillis' not in resp_json or not resp_json['startTimeMillis'] \
                or 'expiryTimeMillis' not in resp_json or not resp_json['expiryTimeMillis'] or \
                'priceCurrencyCode' not in resp_json or not resp_json['priceCurrencyCode']:
            log.debug("ANDROID - MONTHLY - startTimeMillis not available in the response. google_api_error=1d")
            raise ResultErrorWithMsg("google_api_error", "1e")

        purchase_date_ms = int(resp_json['startTimeMillis'])
        end_date_ms = int(resp_json['expiryTimeMillis'])
        currency = resp_json['priceCurrencyCode']
        dayspan_ms = end_date_ms - purchase_date_ms
        dayspan = round(dayspan_ms / 3600 / 24 / 1000)
        date_from = dt.datetime.fromtimestamp(round(int(purchase_date_ms)/1000))
        date_to = dt.datetime.fromtimestamp(round(int(end_date_ms)/1000))

        # TODO - IS IT OK?
        if 'cancelReason' in resp_json and int(resp_json['cancelReason']) == 0 and \
                'cancelSurveryResult' in resp_json and 'cancelSurveryReason' in resp_json['cancelSurveryResult']:
            log.debug("ANDROID - MONTHLY - rec_prod_id: %s CANCELLED", rec_prod_id)
            don_status = DonationStatusE.CANCELED
        else:
            log.debug("ANDROID - MONTHLY - rec_prod_id: %s ACTIVE", rec_prod_id)
            don_status = DonationStatusE.ACTIVE
    else:
        raise ResultErrorWithMsg("google_api_error", '2')

    ds = Donation.active.filter(app_os='android', product_id=rec_prod_id,
                                transaction_id=order_id)
    extra_json = {
        'purchase_date_ms': purchase_date_ms,
        'expiry_date_ms': end_date_ms,
        'dayspan_ms': dayspan_ms,
        'dayspan': dayspan,
        'rec_date': dt_now.strftime(settings.T_FMT),
        'rec_date_ms': dt_now_ms,
    }
    if not ds:
        d = Donation(
            author=rec_user,
            receipt=dr,
            app_os='android',
            product_id=rec_prod_id,
            transaction_id=order_id,
            is_sandbox=False,
            date_from=date_from,
            date_to=date_to,
            frequency=rec_freq,
            status=don_status,
            value=don_prod_data['price'],
            qty=1,
            currency=currency,
            resp_item_json=json.dumps(resp_json),
            extra_json=json.dumps(extra_json)
        )
        d.save()
        d.refresh_from_db()
    else:
        d = ds[0]
        if don_status != d.status:
            d.status = don_status
            d.save()
            d.refresh_from_db()

    recalc_for_user(rec_user)
