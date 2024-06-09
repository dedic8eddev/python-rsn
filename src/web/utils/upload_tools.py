import logging
import os
import random
import time
import requests
from PIL import Image
from django.conf import settings
from django.db.models.fields.files import ImageFieldFile
from django.templatetags.static import static

from web.utils.images import SITE_URL_IMAGES, image_formats,\
    THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT, SQUARE_WIDTH, SQUARE_HEIGHT, \
    HORIZONTAL_EVENT_IMAGE_WIDTH, POSTER_EVENT_IMAGE_WIDTH


log = logging.getLogger(__name__)


def get_url_with_random_suffix(url):
    suffix = "%s%s" % (time.time(), random.randint(1, 99999))
    url += "?" + suffix
    return url


def get_file_from_url(image_url):
    suffix = "%s%s" % (time.time(), random.randint(1, 99999))
    image_url += "?" + suffix
    response = requests.get(image_url, allow_redirects=True)
    data = response.content
    return data


def download_to_local(file, path):
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    r = requests.get(aws_url(file.name), stream=True)
    with open(path, 'wb') as fd:
        for chunk in r.iter_content(1024):
            fd.write(chunk)


def load_image_data(image):
    try:
        image.image_file.seek(0)
        contents = image.image_file.read()

        width, height = Image.open(image.image_file).size

        return contents, width, height
    except Exception:
        return None, None, None


def aws_url(image, thumb=False, square=False, horizontal=False, poster=False,
            fallback='assets/img/missing-image.jpg'):
    """
    Generate a complete AWS S3 bucket image url to access image.
    :param image - Image can be a string if selected directly from the database.
    :param thumb - Optional, whether to get thumbnail image url
    :param square - Optional, whether to get square image url
    :param horizontal - Optional, whether to get horizontal (event) image url
    :param poster - Optional, whether to get poster (event) image url
    :param fallback - If not image, return default image url
    """
    if not image:
        return settings.SITE_URL + static(fallback) if fallback is not False else None

    # TODO: A future refactor of AJAX and to_dicts should eliminate this fallback.
    # Image can be a string if selected directly from the database.
    if isinstance(image, ImageFieldFile):
        image_file_name = image.name
    else:
        image_file_name = image if isinstance(image, str) else image.image_file.name

    # get image name and extension
    name, extension = os.path.splitext(image_file_name)

    # image format is not supported
    if extension.strip('.').lower() not in image_formats:
        thumb = False
        square = False
        horizontal = False
        poster = False

    # invalid using of function input parameters, raise an exception
    if thumb + square + horizontal + poster > 1:
        raise ValueError("Rather one of 'thumb' or 'square' or 'horizontal' "
                         "or 'poster' option can be True, not many of them")

    # get correct cloudflare prefix
    if thumb:
        cloudflare_prefix = f'cdn-cgi/image/fit=cover,width={THUMBNAIL_WIDTH},height={THUMBNAIL_HEIGHT}/'
    elif square:
        cloudflare_prefix = f'cdn-cgi/image/fit=cover,width={SQUARE_WIDTH},height={SQUARE_HEIGHT}/'
    elif horizontal:
        cloudflare_prefix = f'cdn-cgi/image/fit=cover,width={HORIZONTAL_EVENT_IMAGE_WIDTH}/'
    elif poster:
        cloudflare_prefix = f'cdn-cgi/image/fit=cover,width={POSTER_EVENT_IMAGE_WIDTH}/'
    else:
        cloudflare_prefix = ''

    filename = f'{name}{extension}'
    return f'{SITE_URL_IMAGES}{cloudflare_prefix}media/{filename}'
