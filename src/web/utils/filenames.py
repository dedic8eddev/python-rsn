import tempfile
import os
import re
from pathlib import Path
from uuid import uuid4
from datetime import date
# from django.conf import settings
from unidecode import unidecode
from web.utils.images import image_formats
from django.utils.text import slugify


def get_max_id(model):
    try:
        return model.objects.values('id').order_by('-id').first()['id'] + 1
    except Exception:
        return 1


def strip_spaces(filename):
    filename = re.sub(' ', '_', filename)

    return filename


def format_image_filename(name, suffix=''):
    """
    Format image file name with suffix at the end.
    Append the suffix to the end image filename.

    Return:
        - str, updated image filename
    """
    file_name, extension = os.path.splitext(name)
    return f'{file_name}{suffix}{extension}'


def file_exists(file_path):
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return True
    return False


def _mkdir_if_not_exists(dir_path):
    path_obj = Path(dir_path)
    if not path_obj.exists():
        path_obj.mkdir(parents=True)
    elif not path_obj.is_dir():
        raise FileExistsError(
            "path {} exists and it's not a directory".format(dir_path)
        )

    return dir_path


def create_dir_if_not_exists(dir_path):
    _mkdir_if_not_exists(dir_path)
    return dir_path


def get_local_file_contents(path, mode='r'):
    if not os.path.exists(path):
        return None
    with open(path, mode) as f:
        data = f.read()
    f.close()
    return data


def is_image_format(name):
    """
    Check whether image file name is in supported images formats
    :param name - The image filename
    """
    img_format = get_extension(name)
    if img_format.strip('.').lower() not in image_formats:
        return False
    return True


def replace_file_in_local_path(path, data):
    if os.path.exists(path):
        os.remove(path)
    f = open(path, 'w')
    f.write(data)
    f.close()


def get_extension(filename):
    _, ext = os.path.splitext(filename)
    return ext


def update_filename(instance, filename):
    filename = unidecode(strip_spaces(filename))

    if re.search(r"[^a-zA-Z/0-9-._]", filename, re.IGNORECASE):
        filename = re.sub(r"[^a-zA-Z/0-9-._]", '-', filename)

    if (
        instance.__class__.__name__ == 'WineListFile'
    ):
        winelist = instance.winelist
        if instance.winelist.is_temp:
            file_path = os.path.join(
                instance.SUB_PATH, 'temp', winelist.temp_parent_id, filename
            )
        else:
            file_path = os.path.join(
                instance.SUB_PATH,
                str(winelist.place_id) if winelist.place_id else 'alone',
                filename
            )
    elif (
            instance.__class__.__name__ == 'VuforiaImage'
    ):
        file_path = os.path.join(instance.SUB_PATH, filename)
    else:
        ext = filename.split('.')[-1]
        if not instance.pk:  # random name for each new file
            filename = '{}.{}'.format(uuid4().hex, ext)
        file_path = os.path.join(instance.SUB_PATH, filename)

    return file_path


def update_event_gif_filename(instance, filename):
    filename = unidecode(strip_spaces(filename))
    ext = filename.split('.')[-1]
    pk = instance.id
    if not pk:
        pk = get_max_id(instance._meta.model)
    filename = f"{slugify(instance.title)}-{pk}-{str(date.today())}_animated.{ext}"
    file_path = os.path.join('events/gif/', filename)
    return file_path


def update_news_gif_filename(instance, filename):
    filename = unidecode(strip_spaces(filename))

    if re.search(r"[^a-zA-Z/0-9-._]", filename, re.IGNORECASE):
        filename = re.sub(r"[^a-zA-Z/0-9-._]", '-', filename)

    file_path = os.path.join('news/gif/', filename)

    return file_path


def update_event_poster_filename(instance, filename):
    filename = unidecode(strip_spaces(filename))
    ext = filename.split('.')[-1]
    pk = instance.id
    if not pk:
        pk = get_max_id(instance._meta.model)
    filename = f"{slugify(instance.title)}-{pk}-{str(date.today())}.{ext}"
    file_path = os.path.join('events/poster/', filename)
    return file_path


def update_news_poster_filename(instance, filename):
    filename = unidecode(strip_spaces(filename))
    if re.search(r"[^a-zA-Z/0-9-._]", filename, re.IGNORECASE):
        filename = re.sub(r"[^a-zA-Z/0-9-._]", '-', filename)
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(instance.name.replace(" ", "-").lower() + "-" + str(date.today()), ext)
    file_path = os.path.join('news/poster/', filename)
    return file_path


def get_vuforia_image_filename(wine_id, winepost_id, ext):
    ext = ext.strip('.')
    dest_filename = "{}--{}.{}".format(wine_id, winepost_id, ext)
    return dest_filename


def replace_ext_with_jpg(original_name):
    ext = get_extension(original_name)

    if not ext:
        return f"{original_name}.jpg"

    return original_name.replace(ext, '.jpg')


def get_temp_filename(suffix=".jpg", delete=True):
    """
    Create temporary file with suffix and get the filename path
    """
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=delete) as fh:
        return fh.name


def get_news_image_filename(instance, filename):
    ext = filename.split('.')[-1]
    pk = instance.pk if instance.pk else instance.max_id
    filename_ = f'{instance.slug}-{pk}.{ext}'
    return f'{instance.SUB_PATH}{filename_}'


def get_event_image_filename(instance, filename):
    ext = filename.split('.')[-1]
    filename_ = f'{instance.slug}.{ext}'
    return f'{instance.SUB_PATH}{filename_}'
