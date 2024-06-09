from __future__ import absolute_import

import datetime as dt
import json
import logging
import time

import requests
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from web.constants import (DonationFrequencyE, DonationReceiptStatusE,
                           DonationStatusE)
from web.forms.api_forms import AppleDonationsReceiptForm, DonationsClickForm
from web.models import (Donation, DonationReceipt, Place, StatsClick,
                        UserProfile)
from web.utils.api_handling import signed_api
from web.utils.common_userdata import get_user_data
from web.utils.donations import (android_store_donation_recalc_user,
                                 donation_products_android,
                                 donation_products_apple, recalc_for_user,
                                 set_android_code_data)
from web.utils.exceptions import WrongParametersError
from web.utils.sendernotifier import SenderNotifier
from web.utils.views_common import prevent_using_non_active_account

log = logging.getLogger(__name__)


# /api/donations/apple/products
@signed_api(FormClass=None, token_check=True, log_response_data=False)
def get_products_apple(request):
    user = request.user
    prevent_using_non_active_account(user)

    items = {
        'once': [],
        'monthly': [],
    }
    for key, item_data in donation_products_apple[settings.ENV_APPLE].items():
        it_out = {'product_id': key, 'days': item_data['dayspan']}
        if item_data['freq'] == DonationFrequencyE.ONCE:
            items['once'].append(it_out)
        elif item_data['freq'] == DonationFrequencyE.MONTHLY:
            items['monthly'].append(it_out)
    return items


# /api/donations/android/products
@signed_api(FormClass=None, token_check=True, log_response_data=False)
def get_products_android(request):
    user = request.user
    prevent_using_non_active_account(user)

    items = {
        'once': [],
        'monthly': [],
    }
    for key, item_data in donation_products_android.items():
        it_out = {'product_id': key, 'days': item_data['dayspan']}
        if item_data['freq'] == DonationFrequencyE.ONCE:
            items['once'].append(it_out)
        elif item_data['freq'] == DonationFrequencyE.MONTHLY:
            items['monthly'].append(it_out)
    return items


def save_donation_apple(user, cd):
    dt_now_ts = time.time()
    dt_now_ms = round(dt_now_ts * 1000)

    app_os = 'apple'
    dr = DonationReceipt(
        author=user,
        app_os=app_os,
        # product_id=cd['product_id'],
        # qty=cd['qty'] if cd['qty'] else 1,
        # transaction_id=cd['transaction_id'],
        is_sandbox=cd['is_sandbox'],
        receipt_data=cd['receipt_data']
    )

    url = settings.URL_APPLE_PROD
    data = {
        'receipt-data': cd['receipt_data'],
        'password': settings.SECRET_KEY_APPLE,
    }
    data_str = json.dumps(data)
    resp = requests.post(url=url, data=data_str)
    resp_json = resp.json()

    # This receipt is from the test environment, but it was sent to the production environment for verification.
    # Send it to the test environment instead.
    if 'status' in resp_json and int(resp_json['status']) == 21007:
        log.debug("21007 - REDRIECTING to SANDBOX")
        url = settings.URL_APPLE_SANDBOX
        data = {
            'receipt-data': cd['receipt_data'],
            'password': settings.SECRET_KEY_APPLE,
        }
        data_str = json.dumps(data)
        resp = requests.post(url=url, data=data_str)
        resp_json = resp.json()

    dr.provider_response = resp_json
    log.debug("APPLE: The new receipt has been retrieved")
    if 'status' not in resp_json or resp_json['status'] != 0 or 'receipt' not in resp_json \
            or 'in_app' not in resp_json['receipt'] or not resp_json['receipt']['in_app'] or \
            'receipt_creation_date' not in resp_json['receipt'] or not resp_json['receipt']['receipt_creation_date']:
        dr.status = DonationReceiptStatusE.FAILED
        dr.save()
        dr.refresh_from_db()
        log.debug("APPLE: The new receipt is BROKEN, FAILED.")
    else:
        rec_date = resp_json['receipt']['receipt_creation_date']
        rec_date_ms = resp_json['receipt']['receipt_creation_date_ms']
        log.debug("APPLE: Receipt OK. Starting to read the new receipt, creation date %s, MS: %s",
                  rec_date, rec_date_ms)
        log.debug("APPLE: Number of items: %d in receipt creation date %s, MS: %s",
                  len(resp_json['receipt']['in_app']), rec_date, rec_date_ms)
        dr.status = DonationReceiptStatusE.OK
        dr.save()
        dr.refresh_from_db()

        # base_from_ms = None
        for i, item in enumerate(resp_json['receipt']['in_app']):
            log.debug("APPLE: Reading the item for product_id: %s transaction_id: %s receipt creation date %s, MS: %s",
                      item['product_id'], item['transaction_id'], rec_date, rec_date_ms)
            if item['product_id'] not in donation_products_apple[settings.ENV_APPLE]:
                log.debug("APPLE: Item with product_id: %s transaction_id: %s NOT in defined Apple products. "
                          "Please check the data structure.", item['product_id'], item['transaction_id'])
                continue

            ds = Donation.active.filter(app_os=app_os, product_id=item['product_id'],
                                        transaction_id=item['transaction_id'])
            save_donation = False if ds else True
            status = DonationStatusE.ACTIVE  # TODO - should it be OK?
            currency = 'EUR'
            # getting product definition from donation_products_apple
            p_def = donation_products_apple[settings.ENV_APPLE][item['product_id']]
            # product frequency - ONCE or MONTHLY, a very important thing.
            freq = p_def['freq']

            date_to_ms = None
            # date_now_ms = int(round(time.time() * 1000))
            # last_updated_date_ms = int(round(time.time() * 1000))
            last_purchase_date_ms = int(item['purchase_date_ms'])
            date_from = dt.datetime.fromtimestamp(round(last_purchase_date_ms / 1000))
            purchase_date_ms = int(item['purchase_date_ms'])

            # "ONCE" products - a number of days will be added to the badge validity, based on the price of the
            # purchased product. It works independently from the "MONTHLY" products, which are NOT used for
            # calculation here.
            if freq == DonationFrequencyE.ONCE:
                log.debug("APPLE: Item with product_id: %s transaction_id: %s is of 'ONCE' type.",
                          item['product_id'], item['transaction_id'])

                # setting the last update (current timestamp in miliseconds ) and last purchase
                # (purchase_date_ms from item) dates, as well as date_from in object format

                p_price = p_def['price']
                # calculation of dayspan based on product price
                # dayspan = math.ceil(365 / (BASE_PRICE_APPLE / p_price))
                dayspan = p_def['dayspan']

                if settings.ENV_APPLE == 'dev':
                    time_diff_ms = dayspan * 5 * 60 * 1000
                else:
                    time_diff_ms = dayspan * 24 * 3600 * 1000
                dayspan_ms = time_diff_ms
                date_to_ms = last_purchase_date_ms + time_diff_ms
                date_to = dt.datetime.fromtimestamp(int(round(date_to_ms / 1000)))

                if 'cancellation_date' in item and item['cancellation_date']:
                    log.debug(
                        "APPLE: The item for product_id: %s transaction_id: %s receipt creation date %s, "
                        "MS: %s HAS BEEN CANCELLED ON %s - SKIPPING", item['product_id'], item['transaction_id'],
                        rec_date, rec_date_ms, item['cancellation_date'])
                    status = DonationStatusE.CANCELED
            elif freq == DonationFrequencyE.MONTHLY:
                dayspan = p_def['dayspan']
                dayspan_ms = dayspan * 24 * 3600 * 1000
                # date_to_ms = int(item['purchase_date_ms']) + dayspan * 24 * 3600 * 1000
                date_to_ms = int(item['expires_date_ms'])
                date_to = dt.datetime.fromtimestamp(round(date_to_ms / 1000))
                p_price = p_def['price']
                if 'cancellation_date' in item and item['cancellation_date']:
                    log.debug(
                        "APPLE: The item for product_id: %s transaction_id: %s receipt creation date %s, "
                        "MS: %s HAS BEEN CANCELLED ON %s - SKIPPING", item['product_id'], item['transaction_id'],
                        rec_date, rec_date_ms, item['cancellation_date'])
                    status = DonationStatusE.CANCELED
            else:
                continue

            if save_donation:
                extra_json = {
                    'purchase_date_ms': purchase_date_ms,
                    'expiry_date_ms': date_to_ms,
                    'dayspan_ms': dayspan_ms,
                    'dayspan': dayspan,
                    'rec_date': rec_date,
                    'rec_date_ms': dt_now_ms,
                }
                d = Donation(
                    author=user,
                    receipt=dr,
                    app_os=app_os,
                    product_id=item['product_id'],
                    transaction_id=item['transaction_id'],
                    is_sandbox=cd['is_sandbox'],
                    date_from=date_from,
                    date_to=date_to,
                    frequency=freq,
                    status=status,
                    value=p_price,
                    qty=item['quantity'],
                    currency=currency,
                    resp_item_json=json.dumps(item),
                    extra_json=extra_json
                )
                d.save()
                d.refresh_from_db()
    recalc_for_user(user)


# /api/donations/apple/receipt
@signed_api(FormClass=AppleDonationsReceiptForm, token_check=True, log_response_data=False)
def donations_apple_receipt(request):
    user = request.user
    prevent_using_non_active_account(user)

    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data
            save_donation_apple(user=request.user, cd=cd)
            return get_user_data(request, user, include_refused_wineposts=True)
    raise WrongParametersError(_("Wrong parameters."), form)


# /api/donations/android/receipt
@signed_api(FormClass=None, token_check=True, log_response_data=True, success_status=200)
def donations_android_receipt(request):
    user = request.user
    prevent_using_non_active_account(user)
    android_store_donation_recalc_user(user, request.data)
    return {}

    # dr = DonationReceipt(
    #     author=user,
    #     app_os='android',
    #     # product_id=cd['product_id'],
    #     # qty=cd['qty'] if cd['qty'] else 1,
    #     # transaction_id=cd['transaction_id'],
    #     is_sandbox=True,
    #     receipt_data=json.dumps(request.data),
    #     provider_response=None
    #     # provider_response=request.data
    # )
    # dr.save()
    # dr.refresh_from_db()
    # access_token = None
    # rec_resp_json = request.data
    # atrapa = False
    #
    # # if 'atrapa' in rec_resp_json and rec_resp_json['atrapa']:
    # #     atrapa = True
    # # else:
    # #     atrapa = False
    #
    # log.debug("======== ANDROID receipt for logged-inuser ID: %s, data: %s", user.id, request.data)
    #
    # dec_status, dec_details = android_decode_receipt(rec_resp_json)
    # if dec_status == "OK":
    #     rec_user, rec_prod_id, rec_freq, rec_purchase_token, rec_api_prod_type = dec_details
    # else:
    #     raise ResultErrorWithMsg(*dec_details)
    # don_prod_data = donation_products_android[rec_prod_id]
    #
    # # TODO - check whether rec_user.id matches with the logged-in user ID. I will do it later since for
    # # now it would bring about some problems with testing
    #
    # dt_now_ts = time.time()
    # dt_now_ms = round(dt_now_ts * 1000)
    # dt_now = dt.datetime.fromtimestamp(dt_now_ts)
    #
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
    #
    # log.debug("ANDROID - getting response for URL prod %s: %s", url_prod, resp_json)
    # dr.provider_response = resp_json
    # dr.save()
    # dr.refresh_from_db()
    #
    # if 'orderId' not in resp_json or not resp_json['orderId']:
    #     log.error("ANDROID - no orderId in the provider response. google_api_error=1c")
    #     raise ResultErrorWithMsg("google_api_error", "1c")
    #
    # order_id = resp_json['orderId']
    # log.debug("ANDROID - orderId from provider response is: %s", order_id)
    #
    # if rec_freq == DonationFrequencyE.ONCE:
    #     if 'purchaseTimeMillis' not in resp_json or not resp_json['purchaseTimeMillis'] \
    #             or 'purchaseState' not in resp_json:
    #         log.error("ANDROID - ONCE - purchaseTimeMillis not available in the response. google_api_error=1d")
    #         raise ResultErrorWithMsg("google_api_error", "1d")
    #
    #     purchase_date_ms = int(resp_json['purchaseTimeMillis'])
    #     purchase_status = int(resp_json['purchaseState'])
    #     dayspan = int(don_prod_data['dayspan'])
    #     dayspan_ms = dayspan * 3600 * 24 * 1000
    #     end_date_ms = purchase_date_ms + dayspan_ms
    #
    #     date_from = dt.datetime.fromtimestamp(round(int(purchase_date_ms)/1000))
    #     date_to = dt.datetime.fromtimestamp(round(int(end_date_ms)/1000))
    #     currency = don_prod_data['currency']
    #     if int(purchase_status) == 0:  # 0 - purchased, 1 - cancelled
    #         don_status = DonationStatusE.ACTIVE
    #     else:
    #         don_status = DonationStatusE.CANCELED
    #
    # elif rec_freq == DonationFrequencyE.MONTHLY:
    #     if 'startTimeMillis' not in resp_json or not resp_json['startTimeMillis'] \
    #             or 'expiryTimeMillis' not in resp_json or not resp_json['expiryTimeMillis'] or \
    #             'priceCurrencyCode' not in resp_json or not resp_json['priceCurrencyCode']:
    #         log.error("ANDROID - MONTHLY - startTimeMillis not available in the response. google_api_error=1d")
    #         raise ResultErrorWithMsg("google_api_error", "1e")
    #
    #     purchase_date_ms = int(resp_json['startTimeMillis'])
    #     end_date_ms = int(resp_json['expiryTimeMillis'])
    #     currency = resp_json['priceCurrencyCode']
    #     dayspan_ms = end_date_ms - purchase_date_ms
    #     dayspan = round(dayspan_ms / 3600 / 24 / 1000)
    #     date_from = dt.datetime.fromtimestamp(round(int(purchase_date_ms)/1000))
    #     date_to = dt.datetime.fromtimestamp(round(int(end_date_ms)/1000))
    #
    #     # TODO - IS IT OK?
    #     if 'cancelReason' in resp_json and int(resp_json['cancelReason']) == 0 and \
    #             'cancelSurveryResult' in resp_json and 'cancelSurveryReason' in resp_json['cancelSurveryResult']:
    #         log.debug("ANDROID - MONTHLY - rec_prod_id: %s CANCELLED", rec_prod_id)
    #         don_status = DonationStatusE.CANCELED
    #     else:
    #         log.debug("ANDROID - MONTHLY - rec_prod_id: %s ACTIVE", rec_prod_id)
    #         don_status = DonationStatusE.ACTIVE
    # else:
    #     raise ResultErrorWithMsg("google_api_error", '2')
    #
    # ds = Donation.active.filter(app_os='android', product_id=rec_prod_id,
    #                             transaction_id=order_id)
    #
    # extra_json = {
    #     'purchase_date_ms': purchase_date_ms,
    #     'expiry_date_ms': end_date_ms,
    #     'dayspan_ms': dayspan_ms,
    #     'dayspan': dayspan,
    #     'rec_date': dt_now.strftime(settings.T_FMT),
    #     'rec_date_ms': dt_now_ms,
    # }
    #
    # if not ds:
    #     d = Donation(
    #         author=rec_user,
    #         receipt=dr,
    #         app_os='android',
    #         product_id=rec_prod_id,
    #         transaction_id=order_id,
    #         is_sandbox=False,
    #         date_from=date_from,
    #         date_to=date_to,
    #         frequency=rec_freq,
    #         status=don_status,
    #         value=don_prod_data['price'],
    #         qty=1,
    #         currency=currency,
    #         resp_item_json=json.dumps(resp_json),
    #         extra_json=json.dumps(extra_json)
    #     )
    #     d.save()
    #     d.refresh_from_db()
    # else:
    #     d = ds[0]
    #     if don_status != d.status:
    #         d.status = don_status
    #         d.save()
    #         d.refresh_from_db()
    #
    # recalc_for_user(rec_user)
    # return {}


# /api/donations/android/callback - callback for Google used in OAuth2 authorization -
# here the android code is being set, based on which the refresh_token will be generated
@signed_api(FormClass=None, token_check=False, log_response_data=True, success_status=200)
def donations_android_callback(request):
    raisin_token = request.GET.get('raisin_token', None)
    if not raisin_token or raisin_token != settings.ANDROID_CALLBACK_SECRET_KEY:
        raise WrongParametersError(_("Wrong parameters."), {})

    code = request.GET.get("code", "")
    if not code:
        raise WrongParametersError(_("Wrong parameters."), {})

    set_android_code_data(code)
    return {}


# /api/donations/android/getpush
@signed_api(FormClass=None, token_check=False, log_response_data=False, success_status=204)
def donations_android_get_push(request):
    token = request.GET.get('token', None)
    if not token or token != settings.ANDROID_CALLBACK_SECRET_KEY:
        raise WrongParametersError(_("Wrong parameters."), {})

    user = UserProfile.active.get(username='admin')
    prevent_using_non_active_account(user)

    dr = DonationReceipt(
        author=user,
        app_os='android',
        # product_id=cd['product_id'],
        # qty=cd['qty'] if cd['qty'] else 1,
        # transaction_id=cd['transaction_id'],
        is_sandbox=False,
        receipt_data=None,
        provider_response=request.data
    )
    dr.save()
    dr.refresh_from_db()

    return {}


# /api/donations/checknotify
@signed_api(FormClass=None, token_check=False, log_response_data=False, success_status=200)
def donations_checknotify(request):
    user = UserProfile.active.get(username='admin')
    prevent_using_non_active_account(user)

    token = request.GET.get('token', None)
    pwd = request.GET.get('pwd', None)
    pid = request.GET.get('pid', None)
    if not token or not pwd or pwd != 'pr0sz3w3Jsc':
        raise WrongParametersError(_("Wrong parameters."), {})

    if pid:
        place = Place.active.get(id=pid)
    else:
        places = Place.active.filter(free_glass=True)
        if not places:
            raise WrongParametersError(_("Wrong parameters."), {})
        place = places[0]

    SenderNotifier().send_with_free_glass_test(user, place, token)
    return {}


# /api/donations/click
@signed_api(FormClass=DonationsClickForm, token_check=True, log_response_data=False)
def donations_click(request):
    user = request.user
    prevent_using_non_active_account(user)

    click_notify_config = [{'op': 'mod_0', 'val': 20}, ]
    # place = None
    # wm = None

    if request.method == 'POST':
        form = request.form
        if form.is_valid():
            cd = form.cleaned_data

            stat_items = StatsClick.objects.filter(author=user)
            if stat_items:
                item = stat_items[0]
            else:
                item = StatsClick(author=user)

            if 'place_id' in cd and cd['place_id']:
                # place = Place.objects.get(id=cd['place_id'])
                item.place_clicks += 1
                this_clicks = item.place_clicks
            elif 'winemaker_id' in cd and cd['winemaker_id']:
                # wm = Winemaker.objects.get(id=cd['winemaker_id'])
                item.wm_clicks += 1
                this_clicks = item.wm_clicks
            else:
                # SHOULD NEVER HAPPEN because of precautions taken in DonationsClickForm,
                # but still the code is more clear with it
                raise WrongParametersError(_("Wrong parameters."), {})

            item.total_clicks += 1
            item.save()
            item.refresh_from_db()

            show_screen = False
            hb = user.get_has_badge()
            if not hb:
                for cl_item in click_notify_config:
                    if cl_item['op'] == 'eq' and this_clicks == int(cl_item['val']):
                        show_screen = True
                    if cl_item['op'] == 'gt' and this_clicks > int(cl_item['val']):
                        show_screen = True
                    if cl_item['op'] == 'mod_0' and (this_clicks % int(cl_item['val']) == 0):
                        show_screen = True

            # if show_screen:
            #     SenderNotifier().send_with_free_glass_click(user, place, wm)

            return {"show_screen": show_screen}
    raise WrongParametersError(_("Wrong parameters."), {})
