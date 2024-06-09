import json
import requests
import logging
import time
import datetime as dt
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
from web.models import Donation, UserProfile
from web.utils.donations import donation_products_apple, android_get_access_token, recalc_for_user
from web.utils.fetches import fetchalldict
from web.constants import DonationReceiptStatusE, DonationStatusE, DonationFrequencyE


log = logging.getLogger("command")


class Command(BaseCommand):
    args = ""
    help = "updates subscriptions"

    def handle_android(self):
        access_token, at_status, at_status_info = android_get_access_token()
        if at_status != 'OK':
            log.error("update-subs ERROR %s=%s - quitting", at_status_info[0], at_status_info[1])
            return

        url_voided_items = "https://www.googleapis.com/androidpublisher/v3/applications/%(app_id)s/" \
                           "purchases/voidedpurchases?access_token=%(access_token)s" % {
                               'app_id': settings.ANDROID_APP_ID,
                               'access_token': access_token}
        resp = requests.get(url_voided_items)
        resp_json = resp.json()

    def handle_apple(self):
        q_authors = "SELECT DISTINCT author_id FROM web_donationreceipt WHERE is_archived = false AND app_os='apple'"
        with connection.cursor() as cursor:
            cursor.execute(q_authors)
            author_ids = fetchalldict(cursor)

        if not author_ids:
            return

        cnt_ids = len(author_ids)
        for i, author_id in enumerate(author_ids):
            log.debug("updating apple subs for user ID % s (%s / %s) " % (author_id, i + 1, cnt_ids))
            user = UserProfile.active.get(id=author_id['author_id'])
            q_lastrec = "SELECT * FROM web_donationreceipt WHERE author_id = %s AND app_os = 'apple' " \
                        "   ORDER BY created_time DESC LIMIT 1"
            with connection.cursor() as cursor:
                cursor.execute(q_lastrec, [author_id['author_id']])
                rec_items = fetchalldict(cursor)

            for rec_item in rec_items:
                url = settings.URL_APPLE_PROD
                data = {
                    'receipt-data': rec_item['receipt_data'],
                    'password': settings.SECRET_KEY_APPLE,
                }
                data_str = json.dumps(data)
                resp = requests.post(url=url, data=data_str)
                try:
                    resp_json = resp.json()
                except ValueError:
                    log.debug("Can't parse the item ID %s for author ID %s (%s / %s) - A1" %
                              (rec_item['id'], author_id, i + 1, cnt_ids))
                    continue
                except Exception:
                    log.debug("Can't parse the item ID %s for author ID %s (%s / %s) - C3" %
                              (rec_item['id'], author_id, i + 1, cnt_ids))
                    continue

                # This receipt is from the test environment, but it was sent to the production environment
                # for verification. Send it to the test environment instead.
                if 'status' in resp_json and int(resp_json['status']) == 21007:
                    url = settings.URL_APPLE_SANDBOX
                    data = {
                        'receipt-data': rec_item['receipt_data'],
                        'password': settings.SECRET_KEY_APPLE,
                    }
                    data_str = json.dumps(data)
                    resp = requests.post(url=url, data=data_str)
                    resp_json = resp.json()

                if 'status' not in resp_json or resp_json['status'] != 0 or 'receipt' not in resp_json \
                        or 'in_app' not in resp_json['receipt'] or not resp_json['receipt']['in_app'] or \
                        'receipt_creation_date' not in resp_json['receipt'] or \
                        not resp_json['receipt']['receipt_creation_date']:
                    q_upd = "UPDATE web_donationreceipt SET status = %s, modified_time = now() WHERE id = %s"
                    with connection.cursor() as cursor:
                        cursor.execute(q_upd, [DonationReceiptStatusE.FAILED, rec_item['id']])
                    log.debug("APPLE: The receipt with ID %d is BROKEN, FAILED." % rec_item['id'])
                else:
                    rec_date = resp_json['receipt']['receipt_creation_date']
                    rec_date_ms = resp_json['receipt']['receipt_creation_date_ms']
                    log.debug("APPLE: Receipt OK. Starting to read the new receipt, creation date %s, MS: %s",
                              rec_date, rec_date_ms)
                    log.debug("APPLE: Number of items: %d in receipt creation date %s, MS: %s",
                              len(resp_json['receipt']['in_app']), rec_date, rec_date_ms)
                    q_upd = "UPDATE web_donationreceipt SET status = %s, modified_time = now() WHERE id = %s"
                    with connection.cursor() as cursor:
                        cursor.execute(q_upd, [DonationReceiptStatusE.OK, rec_item['id']])

                    base_from_ms = None
                    for i, item in enumerate(resp_json['receipt']['in_app']):
                        date_to_ms = None
                        date_now_ms = int(round(time.time() * 1000))
                        last_updated_date_ms = int(round(time.time() * 1000))
                        last_purchase_date_ms = int(item['purchase_date_ms'])
                        date_from = dt.datetime.fromtimestamp(round(last_purchase_date_ms / 1000))

                        log.debug(
                            "APPLE: Reading the item for product_id: %s transaction_id: %s receipt creation date %s, "
                            "MS: %s", item['product_id'], item['transaction_id'], rec_date, rec_date_ms)
                        if item['product_id'] not in donation_products_apple[settings.ENV_APPLE]:
                            log.debug("APPLE: Item with product_id: %s transaction_id: %s NOT in defined Apple products. "
                                      "Please check the data structure.", item['product_id'], item['transaction_id'])
                            continue

                        ds = Donation.active.filter(app_os='apple', product_id=item['product_id'],
                                                    transaction_id=item['transaction_id'])
                        save_donation = False if ds else True
                        status = DonationStatusE.ACTIVE  # TODO - should it be OK?
                        currency = 'EUR'

                        # getting product definition from donation_products_apple
                        p_def = donation_products_apple[settings.ENV_APPLE][item['product_id']]
                        # product frequency - ONCE or MONTHLY, a very important thing.
                        freq = p_def['freq']

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
                            dayspan_ms = dayspan * 24 * 3600 * 1000
                            date_to_ms = last_purchase_date_ms + dayspan * 24 * 3600 * 1000
                            date_to = dt.datetime.fromtimestamp(int(round(date_to_ms / 1000)))

                            if 'cancellation_date' in item and item['cancellation_date']:
                                log.debug(
                                    "APPLE: The item for product_id: %s transaction_id: %s receipt creation date %s, "
                                    "MS: %s HAS BEEN CANCELLED ON %s - SKIPPING", item['product_id'],
                                    item['transaction_id'],
                                    rec_date, rec_date_ms, item['cancellation_date'])
                                status = DonationStatusE.CANCELED
                            else:
                                if not base_from_ms:
                                    base_from_ms = int(item['purchase_date_ms'])
                        elif freq == DonationFrequencyE.MONTHLY:
                            dayspan = p_def['dayspan']
                            dayspan_ms = dayspan * 24 * 3600 * 1000
                            date_to_ms = int(item['expires_date_ms'])
                            date_to = dt.datetime.fromtimestamp(round(date_to_ms / 1000))
                            p_price = None

                            if 'cancellation_date' in item and item['cancellation_date']:
                                log.debug(
                                    "APPLE: The item for product_id: %s transaction_id: %s receipt creation date %s, "
                                    "MS: %s HAS BEEN CANCELLED ON %s - SKIPPING", item['product_id'],
                                    item['transaction_id'],
                                    rec_date, rec_date_ms, item['cancellation_date'])
                                status = DonationStatusE.CANCELED
                        else:
                            continue

                        if save_donation:
                            d = Donation(
                                author=user,
                                receipt_id=rec_item['id'],
                                app_os='apple',
                                product_id=item['product_id'],
                                transaction_id=item['transaction_id'],
                                is_sandbox=rec_item['is_sandbox'],
                                date_from=date_from,
                                date_to=date_to,
                                frequency=freq,
                                status=status,
                                value=p_price,
                                qty=item['quantity'],
                                currency=currency,
                                resp_item_json=json.dumps(item)
                            )
                            d.save()
                            d.refresh_from_db()
            recalc_for_user(user)

    def handle(self, *args, **options):
        log.debug("updating the subscriptions")
        # self.handle_android()
        self.handle_apple()
