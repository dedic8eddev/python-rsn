from pathlib import Path

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand

from web.utils.storage import MediaStorage
from ...models import PlaceImage
from ...utils.files import execute_task
from ...utils.upload_tools import aws_url


class Command(BaseCommand):
    args = ""
    help = "Process images with missing full image extension"

    # create instance of MediaStorage to handle storing images into AWS S3 bucket
    storage = MediaStorage(bucket=settings.AWS_STORAGE_BUCKET_NAME)

    fixed_images = []

    def process_missing_extension_image(self, image):

        image_name = self.storage.generate_thumbnails(
            name=str(image.image_file),
            content=image.image_file,
            convert_to_jpg=True,
            crop_transparency=True,
            save_full_image=True,
            save_thumb_image=True,
            save_square_image=True
        )
        image.image_file = image_name
        self.fixed_images.append([
            image_name,
            aws_url(image_name),
            aws_url(image_name, thumb=True),
            aws_url(image_name, square=True),
        ])
        image.save()

        return image_name

    def add_arguments(self, parser):
        parser.add_argument('file_name', type=str, help="The .csv  file name of 'process_images' command")

    def handle(self, *args, **options):
        """
        Process images with missing extension
        """

        # get filename
        file_name = options.get('file_name')

        input_dir = Path(settings.APP_ROOT) / 'processed_images'
        print(input_dir)

        df = pd.read_csv(input_dir / file_name)
        images_count = len(df)
        images = self.get_images_with_no_extension(df)

        self.stdout.write(f"Start fixing extension for images: {images_count} in {file_name}")
        if not images:
            print("Problem images not found or already fixed")
            print('Done!')
            return

        # process images with missing extension
        errors_df = execute_task(self.process_missing_extension_image, images)

        # prepare output directory
        output_dir = Path(settings.APP_ROOT) / 'processed_images'
        output_dir.mkdir(parents=True, exist_ok=True)

        # export fix results
        df = pd.DataFrame(self.fixed_images, columns=["db_name", "full", "thumb", "square"])
        df.to_csv(output_dir / f'fix_missing_{file_name}', index=False)

        # export errors if any
        if len(errors_df) > 0:
            errors_df.rename(columns={'arg': 'db_name'}, inplace=True)
            errors_df.to_csv(output_dir / f'errors_missing_{file_name}', index=False)

        print('DONE!')

    def get_images_with_no_extension(self, df):
        df['db_name'] = df['thumb_url'].apply(lambda x: x.split('media')[1][1:])
        values = df['db_name'].values
        images = PlaceImage.active.filter(image_file__in=list(values))

        return images
