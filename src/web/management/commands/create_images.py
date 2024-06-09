import logging
from pathlib import Path

from django.core.management.base import BaseCommand

from web.utils.filenames import replace_ext_with_jpg
from web.utils.images import make_full_image

log_cmd = logging.getLogger("command")


class Command(BaseCommand):
    args = "images_path: The path to original image"
    help = "Create homothetical full image (max width=760), thumbnail (400x400) and square (260x260) images"

    def add_arguments(self, parser):
        parser.add_argument('image_path', type=str, help='The path to original image')

    def handle(self, *args, **options):
        from PIL import Image

        # hardcoded options
        convert_to_jpg = True

        img_path = Path(options.get('image_path'))

        pic = Image.open(img_path)
        image_name = img_path.name

        if convert_to_jpg:
            image_name = replace_ext_with_jpg(image_name)

        full_image = make_full_image(pic)
        filename = image_name
        full_image.save(filename, format='jpeg')
