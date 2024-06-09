from datetime import datetime
import pandas as pd
from django.conf import settings

import os
import logging
from pathlib import Path

from django.core.management.base import BaseCommand

from web.utils.filenames import replace_ext_with_jpg, is_image_format
from web.utils.images import make_full_image

log_cmd = logging.getLogger("command")


class Command(BaseCommand):
    args = "images_path: The path to original image"
    help = "Create homothetical full image (max width=760), thumbnail (400x400) and square (260x260) images"

    def add_arguments(self, parser):
        parser.add_argument('input_dir', type=str, help='The input directory')

    def handle(self, *args, **options):
        from PIL import Image

        # hardcoded options
        convert_to_jpg = False
        save_full_image = False

        input_dir = Path(options.get('input_dir'))
        errors = []

        for img_name in os.listdir(input_dir):
            if '_tmb' in img_name or '_square' in img_name:
                continue

            if not is_image_format(img_name):
                print(f'WRONG IMAGE FILE: {img_name}. Skipped.')
                continue

            img_path = os.path.join(input_dir, img_name)

            try:
                pic = Image.open(img_path)
                image_name = img_name

                if convert_to_jpg:
                    image_name = replace_ext_with_jpg(image_name)

                if save_full_image:
                    # full image with max width 760px
                    full_image = make_full_image(pic)
                    filename = image_name
                    new_path = os.path.join(input_dir, filename)
                    full_image.save(new_path, format='jpeg', quality=100)

            except Exception as e:
                print(e)
                print(img_name)
                errors.append(img_name)

        # prepare output directory
        output_dir = Path(settings.APP_ROOT) / 'processed_images'
        output_dir.mkdir(parents=True, exist_ok=True)

        if len(errors) > 0:
            df = pd.DataFrame(errors, columns=["ImageName"])
            df.to_csv(output_dir / f'media_images_{datetime.now()}.csv', index=False)
