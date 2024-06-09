import logging
import sys
import time

from django.conf import settings
from django.core.management.base import BaseCommand

from web.utils.upload_tools import load_image_data
from web.utils.vuforia_helper import discover_target_ids_by_names
from web.services.vuforia import VuforiaService
from web.utils.vuforia_models import (
    fetch_vuforia_images_dirty,
    fetch_vuforia_images_to_delete,
    fetch_vuforia_images_to_rate,
    _mark_deleted, _vuf_update_rating,
)

log_cmd = logging.getLogger("command")


class Command(BaseCommand):
    auth_failures_cnt = 0
    SLEEP_INTERVAL = 8
    MAX_ITEMS_PER_BATCH = 100
    MAX_AUTH_FAILURES_CNT = 5

    args = ""
    help = "Continuously fetches the vuforia images from vuforia_image table " \
           "with 'is_dirty' set to true and sends them to Vuforia for analysis."

    def add_arguments(self, parser):
        parser.add_argument('--delete_images', action='store_true', help='Whether to delete images')
        parser.add_argument('--update_images', action='store_true', help='Whether to update images')
        parser.add_argument('--update_ratings', action='store_true', help='Whether to update ratings')

    def on_auth_failure(self, sc):
        if sc != VuforiaService.STATUS_CODE_AUTH_ERROR:
            return

        # AuthenticationFailure
        self.auth_failures_cnt += 1
        self.log_vuf(
            "DELETE IMAGE - AUTHENTICATION FAILURE no."
            " {} - increasing the counter".format(self.auth_failures_cnt)
        )

        if self.auth_failures_cnt > self.MAX_AUTH_FAILURES_CNT:
            message = "number of AUTHENTICATION FAILURES {} exceeded the MAX_AUTH_FAILURES_CNT {} - {}"
            action_taken = 'EXITING SCRIPT' if settings.QUIT_ON_MAX_AUTH_FAILURES_CNT else 'DOING NOTHING IN DEV SETTING'  # noqa

            self.log_vuf(
                message.format(
                    self.auth_failures_cnt,
                    self.MAX_AUTH_FAILURES_CNT,
                    action_taken
                )
            )

        if settings.QUIT_ON_MAX_AUTH_FAILURES_CNT:
            sys.exit(1)

    def handle(self, *args, **options):
        delete_images = options.get('delete_images')
        update_images = options.get('update_images')
        update_ratings = options.get('update_ratings')

        while True:
            if delete_images:
                self.delete_images()

            if update_images:
                self.update_dirty_images()

            if update_ratings:
                self.update_ratings()

            self.log_vuf("sleeping for {} after parsing all buffer".format(
                self.SLEEP_INTERVAL
            ))
            time.sleep(self.SLEEP_INTERVAL)

    def log_vuf(self, message):
        log_cmd.info("Vuforia: ---- {}".format(message))

    def delete_images(self):
        self.log_vuf("Fetching vuforia images to be DELETED")
        images, images_count = fetch_vuforia_images_to_delete()
        self.log_vuf("{} Vuforia image(s) to be DELETED found".format(
            images_count
        ))

        for i, image in enumerate(images):
            msg = "DELETING image ({} / {}) with id {} target_id: {} FROM VUFORIA"  # noqa
            self.log_vuf(msg.format(i, images_count, image.id, image.target_id))

            sc, r = VuforiaService().delete_target(image.target_id)

            # noqa {'transaction_id': '28796635a8d1482283f44b652fd90683', 'result_code': 'Success'}
            if sc == VuforiaService.STATUS_CODE_OK:
                db_deleted = _mark_deleted(image.id, image.for_child_post)
                if db_deleted:
                    self.log_vuf("SUCCESSFULLY marked as deleted in DB")
                else:
                    self.log_vuf("FAILED to mark as deleted in DB")

            # noqa {'transaction_id': '8c27fcde9c0941d69a26d301c9e498f2', 'result_code': 'UnknownTarget'}
            elif sc == VuforiaService.STATUS_CODE_NOT_FOUND:
                db_deleted = _mark_deleted(image.id, image.for_child_post)
                msg = "Image was PREVIOUSLY DELETED FROM VUFORIA - Unknown Target. Setting vuforia_deleted = true in DB ({})"  # noqa
                self.log_vuf(msg.format(
                    'succeeded' if db_deleted else 'failed'
                ))

            else:
                msg = "Deleting image with from Vuforia FAILED, will be retried later. Status Code: {} Message: {} "  # noqa
                self.log_vuf(msg.format(sc, str(r)))

            self.on_auth_failure(sc)

    def update_ratings(self):
        self.log_vuf("Fetching vuforia images with update_rating=true")
        images, images_count = fetch_vuforia_images_to_rate(
            self.MAX_ITEMS_PER_BATCH
        )
        self.log_vuf("{} Vuforia image(s) with update_rating found".format(
            images_count
        ))

        for i, image in enumerate(images):
            msg = "Getting image rating for image ID ({}/{}) {} target ID {}"
            self.log_vuf(msg.format(i, images_count, image.id, image.target_id))

            sc, r = VuforiaService().get_target_by_id(image.target_id)

            # {'status': 'processing',
            # 'transaction_id': '5c02aec2b0e64fb18e4d40c114009467',
            # 'target_record': {'active_flag': True, 'name': '553--568.jpg',
            # 'target_id': '64f8e780ca2b4018a16fe2b3447c6727',
            # 'width': 1024, 'reco_rating': '',
            # 'tracking_rating': 4}, 'result_code': 'Success'}
            msg = "Result of getting image rating for image ID {}: SC: {} "
            self.log_vuf(msg.format(image.id, sc))

            if sc == VuforiaService.STATUS_CODE_OK:
                updated = _vuf_update_rating(
                    image.id,
                    r['target_record']['tracking_rating'],
                    r['target_record']['reco_rating']
                )

                self.log_vuf("Modified image rating with id {}: {}".format(
                    image.id,
                    'SUCCESS in DB' if updated else 'FAILED in DB'
                ))

            self.on_auth_failure(sc)

    def update_dirty_images(self):
        self.log_vuf("Fetching vuforia images with is_dirty=true")
        images, images_count = fetch_vuforia_images_dirty(
            self.MAX_ITEMS_PER_BATCH
        )
        self.log_vuf("{} Vuforia image(s) found".format(images_count))

        for i, image in enumerate(images):
            self.log_vuf(
                "Image ({} / {}) with id {} name: {} target_id: {} ".format(
                    i, images_count, image.id,
                    image.get_name(),
                    image.target_id
                )
            )

            image_data, width, height = load_image_data(image)
            if not image_data:
                msg = "Image with id {} IS BROKEN, sending skipped"
                self.log_vuf(msg.format(image.id))

                image.is_dirty = False
                image.error = True
                image.save()

                continue

            metadata = {
                'image_id': image.id,
                'post_id': image.post_id,
                'wine_id': image.wine_id,
            }

            if image.target_id:
                self.log_vuf(
                    "Updating image with id {} name: {} target_id: {} ".format(
                        image.id,
                        image.get_name(),
                        image.target_id
                    )
                )
                self.update_existing_image(image, image_data, width, metadata)
            else:
                self.log_vuf(
                    "Adding image with id {} name {} to Vuforia".format(
                        image.id, image.get_name()
                    )
                )
                self.add_new_image(image, image_data, width, metadata)

    def update_existing_image(self, image, image_data, width, metadata):
        sc, r = VuforiaService().update_target(
            image.target_id, image.get_name(), image_data,
            width, metadata, 1
        )

        if sc == VuforiaService.STATUS_CODE_OK:
            self.log_vuf(
                "Image with id {} has been successfully updated".format(
                    image.id
                )
            )

            image.is_dirty = False
            image.error = False
            image.save()

            return True

        self.log_vuf(
            "ERROR updating image with id {}, target id {}, will retry later. "
            "SC: {} JSON: {}".format(image.id, image.target_id, sc, str(r))
        )
        self.on_auth_failure(sc)

    def add_new_image(self, image, image_data, width, metadata):
        sc, r = VuforiaService().add_target(
            image.get_name(),
            image_data, width, metadata, 1
        )

        # image added OK
        if sc in [
            VuforiaService.STATUS_CODE_OK,
            VuforiaService.STATUS_CODE_TARGET_CREATED
        ]:
            image.is_dirty = False
            image.error = False
            image.save()

            self.log_vuf(f"Image with ID {image.id} has been added to Vuforia, target_id: {r['target_id']}")

            return True

        # image already exists, should be updated. Target ID was not set in
        # the image, it must be re-discovered
        if sc == VuforiaService.STATUS_CODE_ALREADY_EXISTS:
            self.log_vuf(
                f"Image with ID {image.id} already exists in Vuforia, but it has no target_id. Trying to discover."
            )

            target_id = discover_target_ids_by_names(image.id)
            if target_id:
                self.log_vuf(
                    "Discovery of target_id for image with ID {} successful. "
                    "Target ID: {}. Updating target in Vuforia.".format(
                        image.id, target_id
                    )
                )

                sc, r = VuforiaService().update_target(
                    target_id, image.get_name(), image_data,
                    width, metadata, 1
                )

                if sc == VuforiaService.STATUS_CODE_OK:
                    self.log_vuf(
                        "Image with ID {}, target_id {} has been "
                        "successfully updated in Vuforia. ".format(
                            image.id, target_id
                        )
                    )

                    image.is_dirty = False
                    image.error = False
                    image.target_id = target_id
                    image.save()

                    return True

            self.log_vuf(
                "Discovery of target_id for image with ID {} "
                "FAILED - no target ID found. Marking image as "
                "broken (error). ".format(image.id)
            )
            image.is_dirty = False
            image.error = True
            image.save()

            return False

        self.log_vuf(
            "Adding new image with ID {} to Vuforia FAILED, "
            "will be retried later. SC: {} MSG: {} ".format(
                image.id, sc, str(r)
            )
        )

        self.on_auth_failure(sc)
