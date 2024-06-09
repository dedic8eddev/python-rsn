import logging

import pyheif
from django.conf import settings
from PIL import Image, ImageOps

log = logging.getLogger(__name__)

image_formats = [
    'jpeg', 'jpg', 'gif', 'bmp', 'png', 'tga', 'raw', 'ico', 'webp',
    'tif', 'tiff', 'pic', 'pcx', 'heic'
]

icon_manager_formats = [
    'css', 'doc', 'htm', 'mov', 'pdf', 'ppt', 'txt', 'xls', 'avi', 'dll',
    'eps', 'mp3', 'psd', 'wav', 'zip', 'xlsx', 'docx'
]

THUMBNAIL_WIDTH = 400
THUMBNAIL_HEIGHT = 400
SQUARE_WIDTH = 260
SQUARE_HEIGHT = 260
FULL_IMAGE_WIDTH = 5000
HORIZONTAL_EVENT_IMAGE_WIDTH = 1200
POSTER_EVENT_IMAGE_WIDTH = 650

SITE_URL_IMAGES = '{}://{}/'.format(
    'https',
    # 's3.eu-central-1.amazonaws.com',
    settings.AWS_STORAGE_BUCKET_NAME
)


def convert_to_rgb(image):
    """Converts to RGB images from RGBA and LA modes."""
    if image.mode in ('P', 'CMYK'):
        image = image.convert('RGB')
        return image

    if image.mode not in ['RGBA', 'LA']:
        return image

    background = Image.new("RGB", image.size, (255, 255, 255))
    background.paste(image, mask=image.split()[3])

    return background


def is_landscape(pic):
    """
    Check whether pic is in landscape orientation
    """
    width, height = pic.size
    return width > height


def crop_transparent_square(pic, tn_size):
    """ Adds transparent border to images and crops to square. """
    width, height = pic.size
    background = Image.new('RGBA', (tn_size, tn_size), (255, 255, 255, 0))

    paste_x = int((tn_size - width) / 2)
    paste_y = int((tn_size - height) / 2)

    background.paste(pic, (paste_x, paste_y))

    return background


def crop_center(pil_img, crop_width, crop_height):
    """
    Crop the central area of the image

    :param pil_img: The image
    :param crop_width: The crop image width
    :param crop_height: The crop image height
    """
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))


def crop_max_square(pil_img):
    """
    Crop the largest size square of image
    """
    return crop_center(pil_img, min(pil_img.size), min(pil_img.size))


def make_thumbnail(pic, width=THUMBNAIL_WIDTH, crop_transparency=False):
    """
    Make image with new thumbnail width.

    :param pic - The picture from which you need to make a thumbnail
    :param width - New required image width
    :param crop_transparency - Optional attribute, whether to crop image transparency if any
    """
    try:
        image = ImageOps.exif_transpose(pic)
    except Exception as e:
        log.info(e)
        image = pic.copy()

    # optionally remove transparent from any side if any
    if crop_transparency:
        image = image.crop(image.getbbox())

    # make centered crop of the image with the largest size
    image = crop_max_square(image)

    # resize to new image thumbnail size
    image = image.resize((width, width))

    return convert_to_rgb(image)


def h_transformation(pic, new_width):
    """
    Make homothetical copy of input image

    :param pic - The original image
    :param new_width - New requested homothetical image width
    """
    result = pic.copy()
    result = convert_to_rgb(ImageOps.exif_transpose(result))
    result.thumbnail((new_width, pic.height))

    return result


def make_h_thumbnail(pic):
    return h_transformation(pic, THUMBNAIL_WIDTH)


def make_full_image(pic, max_width=FULL_IMAGE_WIDTH):
    """
    Make full image from original

    :param pic - The original image
    :param max_width - The max width allowed for full image
    """
    # get image width
    width, _ = pic.size

    # image width is smaller than max width, return image as it is
    # in short, this means: smaller images are not resized (no width, no height issue)
    if width <= max_width:
        return h_transformation(pic, new_width=width)

    # make homothetical image with MAIN_IMAGE_WIDTH, keeping aspect ratio
    return h_transformation(pic, new_width=max_width)


def open_or_convert(content, ext):
    if ext != '.heic':
        return Image.open(content)

    content.file.seek(0)
    i = pyheif.read_heif(content.file)
    pi = Image.frombytes(
        mode=i.mode, size=i.size, data=i.data
    )

    return pi
