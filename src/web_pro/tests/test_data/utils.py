import os
import base64

from PIL import Image
import tempfile
from django.utils.six import BytesIO

from django.core.files.base import ContentFile

from django.core.files.uploadedfile import TemporaryUploadedFile, SimpleUploadedFile, UploadedFile

from raisin.settings import BASE_DIR
from web.tests.api.utils import assert_response_status_code


class Utils:
    def setup(self):
        raise NotImplemented

    def assert_post_response(self, client, payload, status_code):
        response = client.post(self.url, payload, format='multipart')
        assert_response_status_code(response, status_code)


def get_image():
    image_dir = os.path.join(BASE_DIR, 'web_pro/tests/test_data/images/test_image.png')
    return SimpleUploadedFile('test_image.jpg', open(image_dir, 'rb').read(), 'image/png')


def get_image_name(payload):
    image = payload.pop('imageFile', None)
    if image:
        return image.name.split('.')[0]
    return None
