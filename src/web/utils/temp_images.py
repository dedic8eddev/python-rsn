import io
import logging
import os
import re
from pathlib import Path

import pyheif
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from unidecode import unidecode

from web.utils.filenames import (file_exists, get_extension,
                                 format_image_filename, replace_ext_with_jpg,
                                 strip_spaces)
from web.utils.images import image_formats, make_thumbnail
from web.utils.upload_tools import aws_url

log = logging.getLogger(__name__)


def _get_media_file_path_temp(filename, dir_name, category_dir_name):
    file_path = os.path.join(
        _get_media_dir_temp(dir_name, category_dir_name),
        filename
    )

    return file_path


def _get_media_dir_temp(dir_name, category_dir_name):
    dir_path = os.path.join(
        settings.MEDIA_TEMP_ROOT, category_dir_name, dir_name
    )

    return dir_path


def get_media_url_temp(filename, dir_name, category_dir_name, absolute=True):
    if absolute:
        return "{}/{}".format(
            settings.SITE_URL.rstrip('/'),
            os.path.join(
                settings.MEDIA_URL_TEMP,
                category_dir_name,
                dir_name,
                filename
            ).lstrip('/')
        )

    return os.path.join(settings.MEDIA_URL_TEMP, category_dir_name, filename)


def listdir(path):
    """
    :param path:
    :return: [dirs], [files]
    """
    dirs = []
    files = []
    items = os.listdir(path)
    for item in items:
        item_path = os.path.join(path, item)
        if os.path.isfile(item_path):
            files.append(item)
        else:
            dirs.append(item)
    return dirs, files


def create_temp_directory_if_not_exists(dir_name, category_dir_name):
    dir_name = str(dir_name)
    dir_path = _get_media_dir_temp(dir_name, category_dir_name)
    path_obj = Path(dir_path)

    if not path_obj.exists():
        path_obj.mkdir(parents=True)
    elif not path_obj.is_dir():
        raise FileExistsError(
            "path %s exists and it's not a directory" % dir_path
        )

    return dir_path


def handle_temp_upload(file, dir_name, category_dir_name):
    filename = unidecode(strip_spaces(file.name))
    image_filepath = _get_media_file_path_temp(
        format_image_filename(filename, ''), dir_name, category_dir_name
    )
    extension = get_extension(filename).lower().strip('.')

    if extension == 'heic':
        i = pyheif.read_heif(file)
        jpg_img = Image.frombytes(mode=i.mode, size=i.size, data=i.data)
        image_filepath = replace_ext_with_jpg(image_filepath)
        filename = replace_ext_with_jpg(filename)
        extension = '.jpeg'
        fh = open(image_filepath, 'wb')
        jpg_img.save(fh, format='jpeg')
        fh.close()
        image_file = jpg_img
    else:
        dest = open(image_filepath, 'wb+')
        for chunk in file.chunks():
            dest.write(chunk)
        dest.close()
        image_file = Image.open(image_filepath)

    if extension not in image_formats:
        return image_filepath

    thumb_filepath = _get_media_file_path_temp(
        format_image_filename(filename, '_tmb'), dir_name, category_dir_name
    )

    pic = image_file
    thumbnail = make_thumbnail(pic)
    fh = open(thumb_filepath, 'wb')
    sfile = io.BytesIO()
    format = (extension if extension != 'jpg' else 'jpeg')
    thumbnail.save(sfile, format=format)
    fh.write(sfile.getvalue())
    fh.close()

    return image_filepath


def get_current_temp_images(
    dir_name, category_dir_name, temp_image_ordering=None
):
    images = []
    dir_name = str(dir_name)
    dir_path = _get_media_dir_temp(dir_name, category_dir_name)

    if not os.path.exists(dir_path):
        return []

    dirs, files_in = listdir(dir_path)
    files = [item for item in files_in if not re.search(r'_tmb\.', item)]

    for file in files:
        url = get_media_url_temp(file, dir_name, category_dir_name)

        thumb_name = format_image_filename(file, '_tmb')
        thumb_path = _get_media_file_path_temp(
            thumb_name, dir_name, category_dir_name
        )

        if file_exists(thumb_path):
            url = get_media_url_temp(thumb_name, dir_name, category_dir_name)

        images.append({
            'url': url,
            'ident': file,
            # TODO: maybe these will be needed again for file uploads/OCR.
            # 'file_path': _get_media_file_path_temp(
            #   filename, dir_name, category_dir_name
            # ),
            # 'filename': filename,
            # 'basename': get_basename(filename),
            # 'ext': get_extension(filename),
        })

    # leaving ordering as such
    if temp_image_ordering:
        temp_image_ordering_array = temp_image_ordering.split(',')
        ord_last = len(temp_image_ordering_array) - 1
    else:
        temp_image_ordering_array = []
        ord_last = 0

    for image in images:
        if image['ident'] in temp_image_ordering_array:
            order_index = temp_image_ordering_array.index(image['ident'])
            image['ordering'] = order_index
        else:
            ord_last += 1
            image['ordering'] = ord_last

    images_sorted = sorted(images, key=lambda item: item['ordering'])
    return images_sorted


def get_current_images(
    parent_item_id, ParentItemClass, ImageClass, criteria_parent_name
):
    try:
        parent_item = ParentItemClass.active.get(id=parent_item_id)
    except ParentItemClass.DoesNotExist:
        return []

    images_out = []
    filters = {
        criteria_parent_name: parent_item
    }

    if (
        ImageClass.__name__ == 'PlaceImage' and
        parent_item.__class__.__name__ == 'Place'
    ):
        filters['image_area__isnull'] = True

    images = ImageClass.active.filter(**filters).order_by('ordering')

    for image in images:
        # filename = str(image.image_file)
        images_out.append({
            'url': aws_url(image),
            'url_thumb': aws_url(image, thumb=True),
            'ident': image.id,
            'real_name': image.real_name
            # TODO: maybe keep this for non-image files?
            # 'filename': filename,
            # 'basename': get_basename(filename),
            # 'ext': get_extension(filename),
        })
    return images_out


# not cleaned
def move_uploaded_temp_files(
    dir_name, category_dir_name, user, ImageClass, parent_item,
    parent_item_field_name, temp_image_ordering=None
):
    images = get_current_temp_images(dir_name, category_dir_name)
    if not images:
        return

    # left ordering as previously
    if temp_image_ordering:
        temp_image_ordering_array = temp_image_ordering.split(',')
        ord_last = len(temp_image_ordering_array) - 1
    else:
        temp_image_ordering_array = []
        ord_last = 0

    for image in images:
        if image['ident'] in temp_image_ordering_array:
            order_index = temp_image_ordering_array.index(image['ident'])
            image['ordering'] = order_index
        else:
            ord_last += 1
            image['ordering'] = ord_last

    images_sorted = sorted(images, key=lambda item: item['ordering'])
    for image in images_sorted:
        filename = image['ident']

        image_source = _get_media_file_path_temp(
            filename, dir_name, category_dir_name
        )

        if ImageClass.__name__ == 'PlaceImage':
            # prefix place image
            renamed_filename = "{}---{}".format(
                parent_item.id, os.path.basename(filename)
            )

            filename = renamed_filename

        upload_file = SimpleUploadedFile(
            name=filename, content=open(image_source, 'rb').read()
        )

        ext = get_extension(image_source).strip('.').lower()
        if ext in image_formats:
            upload_file.content_type = 'image/' + ext

        create_data = {
            "image_file": upload_file,
            'author': user,
            'ordering': image['ordering'],
            parent_item_field_name: parent_item
        }

        p_img = ImageClass(**create_data)
        p_img.save()
        os.remove(image_source)


def delete_temp_image(filename, dir_name, category_dir_name):
    file_path = _get_media_file_path_temp(
        filename, dir_name, category_dir_name
    )
    os.remove(file_path)
