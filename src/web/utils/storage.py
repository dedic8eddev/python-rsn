import io
import subprocess
from abc import ABC

from django.contrib.staticfiles.storage import StaticFilesStorage
from storages.backends.s3boto3 import S3Boto3Storage
from storages.utils import get_available_overwrite_name

from web.utils.filenames import (get_extension, format_image_filename,
                                 replace_ext_with_jpg)
from web.utils.images import (make_full_image, open_or_convert, image_formats)
from web.version import VERSION_NUMBER


class HashPathStaticFilesStorage(StaticFilesStorage):
    def url(self, name):
        base_url = super(HashPathStaticFilesStorage, self).url(name)

        if not base_url.endswith('js') and not base_url.endswith('css'):
            return base_url

        # Fix for Docker. Docker container don't include git files.
        try:
            last_commit = subprocess.check_output(
                'git rev-parse --short HEAD', shell=True
            ).decode('utf-8').replace('\n', '')

            the_hash = 'v' + VERSION_NUMBER + 'uq=' + last_commit
        except subprocess.CalledProcessError:
            the_hash = 'v' + VERSION_NUMBER + 'uq=' + "git_commit"

        if "?" in base_url:
            return "%s&%s" % (base_url, the_hash)

        return "%s?%s" % (base_url, the_hash)


class MediaStorage(S3Boto3Storage, ABC):
    location = 'media'
    default_acl = 'public-read'
    file_overwrite = False

    def _save(self, name, content):
        if hasattr(content, 'content_type') and content.content_type.startswith('image/gif'):  # noqa
            return super()._save(name, content)
        elif hasattr(content, 'content_type') and content.content_type.startswith('image/'):  # noqa
            return self.generate_thumbnails(name, content)
        elif name.split('.')[-1] in image_formats:
            return self.generate_thumbnails(name, content)
        else:
            return super()._save(name, content)

    def _save_image(self, picture, filename):
        fh = self.open(filename, 'wb')
        sfile = io.BytesIO()

        picture.save(sfile, format='jpeg')

        fh.write(sfile.getvalue())
        fh.close()

    def generate_thumbnails(self, name, content, convert_to_jpg=True):
        """
        Generate four types of images:
            - homothetical full image with max width 760px
            - homothetical horizontal image with max width 1200px
            - homothetical poster image with max width 650px
            - thumbnail image 400x400px
            - square image 260x260px
        All images stores in AWS S3 bucket

        :param name - The image file name
        :param content - The content of the image
        :param convert_to_jpg - Optional, whether to convert image to .jpg
        :param crop_transparency - Optional, whether to crop image transparency
        :param save_full_image - Whether to persist full image changes
        :param save_thumb_image - Whether to persist thumb image changes
        :param save_square_image - Whether to persist square image changes
        :param save_horizontal_image - Whether to persist horizontal image
        changes
        :param save_poster_image - Whether to persist poster image changes
        """
        # extension = get_extension(name).lower()
        extension = get_extension(name)
        pic = open_or_convert(content, extension)

        image_name = name
        if convert_to_jpg:
            image_name = replace_ext_with_jpg(name)

        full_image = make_full_image(pic)
        filename = format_image_filename(image_name)
        self._save_image(full_image, filename)

        return image_name

    def get_available_name(self, name, max_length=None):
        """Overwrite existing file with the same name if Vuforia."""
        name = self._clean_name(name)
        if name.startswith('vuforia/'):
            return get_available_overwrite_name(name, max_length)
        return super().get_available_name(name, max_length)
