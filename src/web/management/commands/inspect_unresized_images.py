import urllib.request
from pathlib import Path

import pandas as pd
from PIL import Image
from django.conf import settings
from django.core.management.base import BaseCommand

from web.utils.storage import MediaStorage
from ...utils.files import execute_task
from ...utils.images import THUMBNAIL_WIDTH


class Command(BaseCommand):
    args = ""
    help = "Inspect results of 'reprocess_images' cli command"

    # create instance of MediaStorage to handle storing images into AWS S3 bucket
    storage = MediaStorage(bucket=settings.AWS_STORAGE_BUCKET_NAME)

    # list of of rows of different image type urls
    wrong_thumb_rows = []
    wrong_main_rows = []
    missing_thumbs_errors = []

    def inspect_thumb(self, thumb_url):

        aws_img = Image.open(urllib.request.urlopen(thumb_url))
        width, height = aws_img.size

        # image correct, skip it
        if width == THUMBNAIL_WIDTH and height == THUMBNAIL_WIDTH:
            return True

        exc = "Thumb does not resized properly from main image"
        row = [thumb_url, exc]
        self.wrong_thumb_rows.append(row)

    def add_arguments(self, parser):
        parser.add_argument('file_name', type=str)

    def handle(self, *args, **options):
        """
        Inspect not resized thumbs images for specified model
        """

        # get filename
        file_name = options.get('file_name')

        input_dir = Path(settings.APP_ROOT) / 'processed_images'
        print(input_dir)

        df = pd.read_csv(input_dir / file_name)
        images_count = len(df)

        self.stdout.write(f"Start inspecting {images_count} in {file_name}")

        # execute urls inspection in multithreading
        thumbs_urls = df['thumb'].values
        errors_df = execute_task(self.inspect_thumb, iterator=thumbs_urls)

        # prepare output directory
        output_dir = Path(settings.APP_ROOT) / 'processed_images'
        output_dir.mkdir(parents=True, exist_ok=True)

        df = pd.DataFrame(self.wrong_thumb_rows, columns=["thumb_url", "message"])
        df.to_csv(output_dir / f'inspect_{file_name}', index=False)

        if len(errors_df) > 0:
            errors_df.rename(columns={"arg": "thumb_url"}, inplace=True)
            errors_df.to_csv(output_dir / f'inspect_errors_{file_name}', index=False)

        print('DONE!')
