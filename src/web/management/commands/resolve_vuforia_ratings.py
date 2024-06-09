import logging
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand

from web.models import VuforiaImage
from web.services.vuforia import VuforiaService
from web.utils.files import execute_task
from web.utils.upload_tools import aws_url
from web.utils.vuforia_models import update_image_rating, update_dirty_image

log = logging.getLogger("command")


def update_rating_by_target_id(image):
    # attempt to update image rating by target_id
    # call GET request to vuforia service and update image information in DB
    status_code = update_image_rating(image)

    # if status_code is not OK, means that target_id stored in DB is broken
    # in this case set target_id to None and add this image as new target
    if status_code != VuforiaService.STATUS_CODE_OK:
        image.target_id = None

        # mark 'is_dirty' to be inserted to vuforia service db as new image
        image.is_dirty = True

        # mark 'update_rating' to be updated by periodic celery tasks
        image.update_rating = True

        image.error = False
        image.vuforia_deleted = False
        image.delete_from_vuforia = False

        image.save()


def resolve_images_ratings_with_targets(persist=False):
    """
    Get images and update ratings from vuforia service for images with:
        - rating_tracking is null
        - is_archived is False
        - target_id is not null
    """

    log.info("Get vuforia images with no 'rating_tracking' AND with 'target_id'")

    queryset = VuforiaImage.objects.filter(
        is_archived=False,
        target_id__isnull=False,
        rating_tracking__isnull=True,
        post_ref_image__is_parent_post=True
    )

    count = queryset.count()
    log.info(f"Found {count} vuforia images with targets AND without ratings")

    if count == 0:
        return

    df = pd.DataFrame(
        list(queryset.values('id', 'post_id', 'wine_id', 'rating_reco', 'rating_tracking', 'image_file', 'target_id'))
    )
    df['url'] = df['image_file'].apply(lambda x: aws_url(x))

    # prepare output directory
    output_dir = Path(settings.APP_ROOT) / 'vuforia_ratings'
    output_dir.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_dir / 'vuforia_unrated_images.csv', index=False)

    if persist:
        # process images in parallel
        errors_df = execute_task(
            task=update_rating_by_target_id,
            iterator=queryset
        )

        # if any errors during ratings handling found, export to .csv file for further analysis
        if len(errors_df) > 0:
            errors_df.rename(columns={"arg": "message"}, inplace=True)
            errors_df.to_csv(output_dir / 'vuforia_update_ratings_errors.csv', index=False)


def resolve_images_ratings_with_no_target(persist=False):
    log.info("Get vuforia images with no ratings and None target_id for parent posts only")

    queryset = VuforiaImage.objects.filter(
        is_archived=False,
        target_id__isnull=True,
        rating_tracking__isnull=True,
        post_ref_image__is_parent_post=True
    )

    count = queryset.count()
    log.info(f"{count} Vuforia image(s) with no ratings and None target_id for parent posts found.")

    if count == 0:
        return

    # prepare output directory
    output_dir = Path(settings.APP_ROOT) / 'vuforia_ratings'
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(
        list(queryset.values('id', 'post_id', 'wine_id', 'rating_reco', 'rating_tracking', 'image_file', 'target_id'))
    )
    df.to_csv(output_dir / 'vuforia_unrated_no_target_id_images.csv', index=False)

    if persist:
        # add new targets or update existed
        # this is time cost operation, run in parallel to speedup
        execute_task(
            task=update_dirty_image,
            iterator=queryset
        )


class Command(BaseCommand):
    SLEEP_INTERVAL_EMPTY = 5
    SLEEP_INTERVAL_BATCH = 1
    MAX_ITEMS_PER_BATCH = 100
    args = ""
    help = "Resolve vuforia image ratings"

    def add_arguments(self, parser):
        parser.add_argument('--persist', action='store_true', help='Whether to process image manipulations')

    def handle(self, *args, **options):
        persist = options.get('persist')

        # first step is to handle all images without ratings but with target_id to avoid duplicates
        # get image by target_id and update ratings info
        # if request status is on 'OK' then target_id set to None to be added further as new image
        resolve_images_ratings_with_targets(persist)

        # resolve images with no ratings and no target_id for parent posts only
        # if new image --> add
        # if existed --> update
        resolve_images_ratings_with_no_target(persist)
