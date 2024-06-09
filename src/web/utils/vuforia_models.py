import base64
import io

from celery.utils.log import get_task_logger
from django.core.files.base import ContentFile
from django.db.models import Q
from PIL import Image

from web.models import Post, VuforiaImage, Wine
from web.utils.filenames import get_extension, get_vuforia_image_filename
from web.services.vuforia import VuforiaService
from web.utils.upload_tools import load_image_data
from my_celery.task_helpers import add_new_image, update_existing_image


"""
this file has been created separately to avoid circular imports from
models (vuforia.py is used in models)
"""

logger = get_task_logger(__name__)


def create_vuforia_images_for_post_and_wine(post,
                                            only_from_post=False,
                                            for_child_post=False):
    if post.is_archived:
        return

    if post.wine.ref_image and post.ref_image:
        return

    vuforia_image = VuforiaImage.objects.filter(
        wine=post.wine, post=post,
        vuforia_deleted=False, delete_from_vuforia=False,
        is_archived=False
    ).first()

    if not vuforia_image:
        if post.wine.main_image and not only_from_post:
            vuforia_image = create_from_x_image(post.wine.main_image, post,
                                                for_child_post)

        if post.main_image:
            vuforia_image = create_from_x_image(post.main_image, post,
                                                for_child_post)

    if not vuforia_image:
        return

    if not only_from_post:
        post.wine.ref_image = vuforia_image
        post.wine.debug_save()
        post.wine.refresh_from_db()

    post.ref_image = vuforia_image
    post.debug_save()
    post.refresh_from_db()


def _create_update_vuforia_image(user, image_file, size, wine, post):
    width, height = size

    VuforiaImage.objects.filter(wine=wine, post=post).update(
        delete_from_vuforia=True,
        is_archived=True
    )

    image_data = {
        'author': user,
        'width': width,
        'height': height,
        'ordering': 0,
        'post': post,
        'wine': wine,
        'image_file': image_file,
        'is_dirty': True
    }

    image = VuforiaImage(**image_data)
    image.save()
    image.refresh_from_db()

    return image


def create_vuforia_image_from_file(user, file, wine, post):
    image_file = Image.open(file)

    file.name = get_vuforia_image_filename(
        wine.id, post.id, get_extension(file.name)
    )

    return _create_update_vuforia_image(
        user, file, image_file.size, wine, post
    )


def create_from_b64_data(user, b64_data, wine, post):
    prefix, img_data = b64_data.split(',')
    img_data = base64.b64decode(img_data)
    buf = io.BytesIO(img_data)

    image_file = Image.open(buf)
    size = image_file.size

    ext = image_file.format.lower()
    new_file = ContentFile(img_data)
    new_file.content_type = 'image/{}'.format(ext)
    new_file.name = get_vuforia_image_filename(wine.id, post.id, ext)

    return _create_update_vuforia_image(user, new_file, size, wine, post)


def create_from_x_image(src_image, winepost, for_child_post=False):
    if not for_child_post:
        VuforiaImage.objects.filter(wine=winepost.wine, post=winepost).update(
            delete_from_vuforia=True,
            is_archived=True
        )

    try:
        image = src_image.duplicate(
            winepost,
            extra_data={
                'author': src_image.author,
                'width': src_image.width,
                'height': src_image.height,
                'ordering': 0,
                'post': winepost,
                'wine': winepost.wine,
                'is_dirty': True,
                'for_child_post': for_child_post,
            },
            for_vuforia=True
        )
    # if src_image.url does not exist
    except (FileNotFoundError, IOError) as file_error:
        msg = "ERROR: {}. Image ID: {} Type: {}"
        logger.error(msg.format(str(file_error), src_image.id, type(src_image)))
        if winepost.wine.main_image == src_image:
            winepost.wine.main_image = None
            winepost.wine.save()
        elif winepost.main_image == src_image:
            winepost.main_image = None
            winepost.save()

        return

    except Exception as e:
        msg = "ERROR: {}. Image ID: {} Type: {}"
        logger.error(msg.format(str(e), src_image.id, type(src_image)))

        return

    return image


def _mark_deleted(image_id, for_child_post=False):
    try:
        image = VuforiaImage.objects.get(pk=image_id)
    except VuforiaImage.DoesNotExist:
        return False

    image.vuforia_deleted = True
    image.delete_from_vuforia = False
    image.save()

    if not for_child_post:
        Post.objects.filter(ref_image_id=image_id).update(ref_image_id=None)
        Wine.objects.filter(ref_image_id=image_id).update(ref_image_id=None)

    return True


def fetch_vuforia_images_to_delete(limit=None):
    qs = VuforiaImage.objects.filter(delete_from_vuforia=True).exclude(vuforia_deleted=True)

    return (qs[:limit], len(qs[:limit])) if limit else (qs, qs.count())


def fetch_vuforia_images_to_rate(limit=None):
    qs = VuforiaImage.objects.filter(update_rating=True).exclude(
        Q(delete_from_vuforia=True) |
        Q(vuforia_deleted=True) |
        Q(error=True)
    )

    return (qs[:limit], len(qs[:limit])) if limit else (qs, qs.count())


def _vuf_update_rating(image_id, tracking_rating, reco_rating):
    try:
        image = VuforiaImage.objects.get(pk=image_id)
    except VuforiaImage.DoesNotExist:
        return False

    image.update_rating = False
    image.rating_tracking = tracking_rating
    image.rating_reco = reco_rating
    image.save()

    if not image.for_child_post:
        return True

    # Mark child post image target to be deleted from Vuforia Web Service
    VuforiaImage.objects.filter(
        post_id=image.post_id,
    ).exclude(
        delete_from_vuforia=True,
        vuforia_deleted=True
    ).update(delete_from_vuforia=True)

    return True


def fetch_vuforia_images_dirty(limit=None):
    # wine.status = 10 - ON HOLD
    # post.status = 10 - DRAFT
    qs = VuforiaImage.objects.filter(is_dirty=True).exclude(
        delete_from_vuforia=True,
        vuforia_deleted=True).exclude(
        error=True).exclude(
        wine__status=10).exclude(
        post__status=10
    )

    return (qs[:limit], len(qs[:limit])) if limit else (qs, qs.count())


def delete_vuforia_image(image):
    sc, r = VuforiaService().delete_target(image.target_id)

    # noqa {'transaction_id': '28796635a8d1482283f44b652fd90683', 'result_code': 'Success'}
    if sc == VuforiaService.STATUS_CODE_OK:
        db_deleted = _mark_deleted(image.id, image.for_child_post)
        if db_deleted:
            logger.info("SUCCESSFULLY marked as deleted in DB")
        else:
            logger.info("FAILED to mark as deleted in DB")

    # noqa {'transaction_id': '8c27fcde9c0941d69a26d301c9e498f2', 'result_code': 'UnknownTarget'}
    elif sc == VuforiaService.STATUS_CODE_NOT_FOUND:
        db_deleted = _mark_deleted(image.id, image.for_child_post)
        msg = "Image was PREVIOUSLY DELETED FROM VUFORIA - Unknown Target. Setting vuforia_deleted = true in DB ({})"  # noqa
        logger.info(msg.format('succeeded' if db_deleted else 'failed'))

    else:
        msg = "Deleting image with from Vuforia FAILED, will be retried later. Status Code: {} Message: {} "  # noqa
        logger.info(msg.format(sc, str(r)))


def update_image_rating(image):
    sc, r = VuforiaService().get_target_by_id(image.target_id)

    # {'status': 'processing',
    # 'transaction_id': '5c02aec2b0e64fb18e4d40c114009467',
    # 'target_record': {'active_flag': True, 'name': '553--568.jpg',
    # 'target_id': '64f8e780ca2b4018a16fe2b3447c6727',
    # 'width': 1024, 'reco_rating': '',
    # 'tracking_rating': 4}, 'result_code': 'Success'}
    msg = "Result of getting image rating for image ID {}: SC: {} "
    logger.info(msg.format(image.id, sc))

    if sc == VuforiaService.STATUS_CODE_OK:
        updated = _vuf_update_rating(
            image.id,
            r['target_record']['tracking_rating'],
            r['target_record']['reco_rating']
        )

        msg = "Modified image rating with id {}: {}"
        logger.info(msg.format(
            image.id,
            'SUCCESS in DB' if updated else 'FAILED in DB'
        ))
    else:
        image.is_dirty = False
        image.error = True
        image.save()

    return sc


def update_dirty_image(image):
    image_data, width, height = load_image_data(image)
    if not image_data:
        logger.info(f"Image with id {image.id} IS BROKEN, sending skipped")

        image.is_dirty = False
        image.error = True
        image.save()

        return

    metadata = {
        'image_id': image.id,
        'post_id': image.post_id,
        'wine_id': image.wine_id,
    }

    if image.target_id:
        logger.info(f"Updating image with id {image.id} name: {image.get_name()} target_id: {image.target_id}")
        update_existing_image(image, image_data, width, metadata)
    else:
        logger.info(f"Adding image with id {image.id} name {image.get_name()} to Vuforia")
        add_new_image(image, image_data, width, metadata)
