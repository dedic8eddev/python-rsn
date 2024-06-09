import os

from celery.utils.log import get_task_logger
from django.db.models import Q

from my_celery.celery_app import app
from web.constants import PlaceStatusE, PostTypeE, PostStatusE, WineListStatusE
from web.models import Place, Post, WineListFile
from web.utils.ocr.db import (fetch_validated_winemakers,
                              fetch_validated_wines_with_wms)
from web.utils.ocr_tools import get_text_rows, get_score
from web.utils.vuforia_models import (create_vuforia_images_for_post_and_wine,
                                      delete_vuforia_image,
                                      fetch_vuforia_images_dirty,
                                      fetch_vuforia_images_to_delete,
                                      fetch_vuforia_images_to_rate,
                                      update_dirty_image, update_image_rating)


logger = get_task_logger(__name__)

BATCH = 100


@app.task
def add_vuforia_child_posts():
    logger.info(
        "Checking for CHILD POST IMAGES to be sent to Vuforia "
        "for rating and then removed."
    )

    posts = Post.active.filter(
        type=PostTypeE.WINE, is_parent_post=False, ref_image=None
    ).exclude(
        main_image=None
    ).exclude(
        status=PostStatusE.DRAFT
    )[:BATCH]

    ids = posts.values_list('id', flat=True)
    posts_count = posts.count()

    msg = "{} Child post(s) to be sent to Vuforia found: {}"
    logger.info(msg.format(posts_count, ids))

    if posts_count == 0:
        return

    for i, post in enumerate(posts):
        msg = "Adding vuforia image for child post {}/{} ID {} wine ID {} name: {}" # noqa
        logger.info(msg.format(
            i + 1, posts_count, post.id, post.wine.id, post.wine.name
        ))

        create_vuforia_images_for_post_and_wine(
            post, only_from_post=True, for_child_post=True
        )


@app.task
def add_vuforia_parent_posts():
    logger.info("Fetching PARENT POST IMAGES to be sent to Vuforia")

    posts = Post.active.filter(
        Q(ref_image=None) | Q(wine__ref_image=None),
        type=PostTypeE.WINE, is_parent_post=True
    ).exclude(
        main_image=None, wine__main_image=None
    ).exclude(
        status=PostStatusE.DRAFT
    )[:BATCH]

    posts_count = posts.count()

    ids = posts.values_list('id', flat=True)
    msg = "{} Parent post(s) to be sent to Vuforia found: {}"
    logger.info(msg.format(posts_count, ids))

    if posts_count == 0:
        return

    for i, post in enumerate(posts):
        msg = "Adding vuforia image for parent post {}/{} ID {} wine ID {} name: {}" # noqa
        logger.info(msg.format(
            i + 1, posts_count, post.id, post.wine.id, post.wine.name
        ))

        create_vuforia_images_for_post_and_wine(post)


@app.task
def delete_images():
    logger.info("Fetching vuforia images to be DELETED")

    images, images_count = fetch_vuforia_images_to_delete(BATCH)
    logger.info("{} Vuforia image(s) to be DELETED found".format(images_count))

    if images_count == 0:
        return

    for i, image in enumerate(images):
        msg = "DELETING image ({} / {}) with id {} target_id: {} FROM VUFORIA"
        logger.info(msg.format(i + 1, images_count, image.id, image.target_id))

        delete_vuforia_image(image)


@app.task
def update_ratings():
    logger.info("Fetching vuforia images with update_rating=true")

    images, images_count = fetch_vuforia_images_to_rate(10)
    logger.info("{} Vuforia image(s) with update_rating found".format(
        images_count
    ))

    if images_count == 0:
        logger.info("UPDATE RATINGS: EMPTY RESULT")

    for i, image in enumerate(images):
        msg = "Getting image rating for image ID ({}/{}) {} target ID {}"
        logger.info(msg.format(i + 1, images_count, image.id, image.target_id))

        update_image_rating(image)


@app.task
def update_dirty_images():
    logger.info("Fetching vuforia images with is_dirty=true")

    images, images_count = fetch_vuforia_images_dirty(BATCH)
    logger.info(f"{images_count} Vuforia image(s) with is_dirty=True found.")

    if images_count == 0:
        return

    for i, image in enumerate(images):
        msg = "Updating dirty Image ({} / {}) with id {} name: {} target_id: {} "
        logger.info(msg.format(i + 1, images_count, image.id, image.get_name(), image.target_id))
        update_dirty_image(image)


@app.task
def ocr_recognize(wl_file_id):
    wl_file = WineListFile.active.get(id=wl_file_id)
    logger.info("OCR-ing image file: {} ".format(
        str(wl_file.image_file))
    )

    try:
        text_rows = get_text_rows(wl_file.image_file)
        wl_file.item_text_rows = text_rows
        wl_file.save()

    except Exception as e:
        wl_file.winelist.status = WineListStatusE.FAILED
        wl_file.winelist.save()
        logger.error("Result for file {}: FAILED: {}".format(
            str(wl_file.image_file), e)
        )


@app.task
def ocr_calculate_and_save_user_edited_text(wl_file_id,
                                            new_exclusion_word_row=None):
    winemakers = fetch_validated_winemakers()
    wines_with_wms = fetch_validated_wines_with_wms()
    wines = wines_with_wms['items']
    wines_by_wm = wines_with_wms['items_by_wm']

    wl_file = WineListFile.active.get(id=wl_file_id)

    try:
        moderated_indexes = {}
        if wl_file.winelist.total_score_data:
            for item in wl_file.winelist.total_score_data.get('rows_out'):
                if item.get('moderated'):
                    moderated_indexes.update({item['ind']: item['status']})
        text_rows = wl_file.item_text_rows
        score = get_score(text_rows, winemakers=winemakers, wines=wines,
                          wines_by_wm=wines_by_wm,
                          moderated_indexes=moderated_indexes,
                          new_exclusion_word_row=new_exclusion_word_row)

        score['file'] = os.path.basename(wl_file.image_file.name)
        wl_file.winelist.total_score_data = score
        wl_file.winelist.status = WineListStatusE.OK
        wl_file.winelist.save()

        logger.info("Result for file {}: {}%".format(
            str(wl_file.image_file), score['score_percent'])
        )
    except Exception as e:
        wl_file.winelist.status = WineListStatusE.FAILED
        wl_file.winelist.save()
        logger.error("Result for file {}: FAILED: {}".format(
            str(wl_file.image_file), e)
        )


@app.task
def update_places_timezones():
    logger.info("Updating places with timezones")
    places = Place.active.filter(
        tz_name__isnull=True,
        status__in=[PlaceStatusE.PUBLISHED, PlaceStatusE.SUBSCRIBER]
    )
    logger.info("Found {} places without timezones".format(places.count()))
    for place in places:
        tz_id = place.update_timezone()
        logger.info(
            "Updated timezone for place ID: {} NAME: {} TIMEZONE: {}"
            .format(place.id, place.name, tz_id))
