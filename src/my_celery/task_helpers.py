from celery.utils.log import get_task_logger

from web.utils.vuforia_helper import discover_target_ids_by_names
from web.services.vuforia import VuforiaService

logger = get_task_logger(__name__)


def update_existing_image(image, image_data, width, metadata):
    sc, r = VuforiaService().update_target(
        image.target_id, image.get_name(), image_data,
        width, metadata, 1
    )

    if sc == VuforiaService.STATUS_CODE_OK:
        image.is_dirty = False
        image.error = False
        # image.target_id = r['target_id']
        # print("TARGET ID: ", r['target_id'])
        image.update_rating = True
        image.save()

        logger.info(
            "Image with id {} has been successfully updated with "
            "metadata content {}".format(
                image.id, metadata)
        )

        return True

    if sc == VuforiaService.STATUS_CODE_NOT_FOUND and \
            r.get('result_code') == "UnknownTarget":
        image.is_dirty = True
        image.target_id = None
        image.save()

        logger.info(
            "ERROR updating image with id {}, target id {}, target_id deleted,"
            " will be rediscovered from Vuforia. SC: {} JSON: {}"
            .format(image.id, image.target_id, sc, str(r))
        )

    if r.get('result_code') == "BadImage":
        image.error = True
        image.save()

        logger.info(
            "Image with id {} marked as bad image. Consider replacing.".format(
                image.id
            )
        )

    else:
        logger.info(
            "ERROR updating image with id {}, target id {}, will retry later. "
            "SC: {} JSON: {}".format(image.id, image.target_id, sc, str(r))
        )

    return False


def add_new_image(image, image_data, width, metadata):
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
        image.target_id = r['target_id']
        image.update_rating = True
        image.save()

        msg = "Image with ID {} has been added to Vuforia, target_id: {} " \
              "with metadata content: {}"
        logger.info(msg.format(image.id, r['target_id'], metadata))

        return True

    # image already exists, should be updated. Target ID was not set in
    # the image, it must be re-discovered
    if sc == VuforiaService.STATUS_CODE_ALREADY_EXISTS:
        msg = "Image with ID {} already exists in Vuforia, "\
              "but it has no target_id. Trying to discover."
        logger.info(msg.format(image.id))
        target_id = discover_target_ids_by_names(image.id)

        if target_id:
            logger.info(
                "Discovery of target_id for image with ID {} successful. "
                "Target ID: {}. Updating target in Vuforia.".format(
                    image.id, target_id
                )
            )

            image.target_id = target_id
            image.save()

            return update_existing_image(image, image_data, width, metadata)

        else:
            logger.info(
                "Discovery of target_id for image with ID {} "
                "FAILED - no target ID found. Marking image as "
                "broken (error). ".format(image.id)
            )

    elif sc == VuforiaService.STATUS_CODE_BAD_IMAGE:
        logger.info(
            "Image with id {} corrupted or format not supported. Marked as "
            "broken (error)".format(image.id)
        )

    else:
        logger.info(
            "Adding new image with ID {} to Vuforia FAILED, "
            "will be retried later. SC: {} MSG: {} ".format(
                image.id, sc, str(r)
            )
        )

    image.is_dirty = False
    image.error = True
    image.save()

    return False
