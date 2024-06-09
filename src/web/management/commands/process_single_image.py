from pathlib import Path

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand

from web.utils.filenames import is_image_format
from web.utils.storage import MediaStorage
from web.utils.upload_tools import aws_url
from web.management.commands.process_images import Command as ImageProcessor


class Command(BaseCommand):
    args = ""
    help = "Re-process full, thumbs and square images"

    # create instance of MediaStorage to handle storing images into AWS S3 bucket
    storage = MediaStorage(bucket=settings.AWS_STORAGE_BUCKET_NAME)

    # list of of rows of different image type urls
    rows = []

    def add_arguments(self, parser):
        # Positional Argument
        parser.add_argument('model', type=str,
                            help='Define model alias, one of: event, vuforia, wine, winemaker, user, post, place')
        parser.add_argument('db_name', type=str, help='Image name in DB')

        # Flag argument
        parser.add_argument('--crop_transparency', action='store_true', help='Whether to crop image transparency')
        parser.add_argument('--full_images', action='store_true', help='Whether to persist full image changes')
        parser.add_argument('--thumb_images', action='store_true', help='Whether to persist thumb image changes')
        parser.add_argument('--square_images', action='store_true', help='Whether to persist square image changes')
        parser.add_argument('--convert_to_jpg', action='store_true', help='Whether to convert to jpg format')

    def handle(self, *args, **options):
        """
        Re-process thumbs images for specified model

        Example:

            python manage.py process_images place
            python manage.py process_images place --crop_transparency --thumb_images
        """
        # get model alias
        # places/24---f33ab1ea-acd7-11e6-835b-040164388201.jpg
        model_name = options.get('model')
        db_name = options.get('db_name')
        crop_transparency = options.get('crop_transparency', False)
        full_image = options.get('full_images')
        thumb_image = options.get('thumb_images')
        square_image = options.get('square_images')
        convert_to_jpg = options.get('convert_to_jpg')

        # do processing only for active images (skip archived)
        model = ImageProcessor.get_image_model(model_name=model_name)

        img = model.objects.filter(image_file=db_name).first()

        self.stdout.write(f"Start processing '{db_name}' image")
        self.stdout.write(f"\t-crop transparency: {crop_transparency}")
        self.stdout.write(f"\t-convert to jpg: {convert_to_jpg}")
        self.stdout.write(f"\t-process full images: {full_image}")
        self.stdout.write(f"\t-process thumb images: {thumb_image}")
        self.stdout.write(f"\t-process square images: {square_image}")

        if not full_image and not thumb_image and not square_image:
            self.stdout.write("Nothing to process, please select one+ of the options: '--full_images', "
                              "'--thumb_images', '--square_images'"
                              )
            return

        # process images in parallel
        # return errors dataframe(arg, exc) if any issues occurred during processing
        self.process_image(image=img, crop_transparency=crop_transparency, full_image=full_image,
                           thumb_image=thumb_image, square_image=square_image)

        # prepare output directory
        output_dir = Path(settings.APP_ROOT) / 'processed_images'
        output_dir.mkdir(parents=True, exist_ok=True)

        # export success results
        if len(self.rows) > 0:
            df = pd.DataFrame(self.rows, columns=["db_name", "full", "thumb", "square"])
            df.to_csv(output_dir / f'single_{model_name}_image_urls.csv', index=False)

    def process_image(self, image, crop_transparency=False, full_image=False, thumb_image=True, square_image=True,
                      convert_to_jpg=False):
        """
        Process single image

        :param image - Image to process
        :param crop_transparency - Whether to crop image transparency
        :param full_image - Whether to persist full image changes
        :param thumb_image - Whether to persist thumb image changes
        :param square_image - Whether to persist square image changes
        :param convert_to_jpg - Whether to convert image to jpg format

        Return:
            - image name
            - updated image list urls
            - error image list urls if any
        """
        row = []

        original_name = str(image.image_file)

        # skip not supported images formats
        if not is_image_format(original_name):
            return original_name

        image_name = self.storage.generate_thumbnails(
            name=original_name,
            content=image.image_file,
            convert_to_jpg=convert_to_jpg,
            crop_transparency=crop_transparency,
            save_full_image=full_image,
            save_thumb_image=thumb_image,
            save_square_image=square_image
        )

        # append DB image name
        row.append(original_name)

        # append full image aws url
        row.append(aws_url(image=image_name))

        # append thumb image aws url
        row.append(aws_url(image=image_name, thumb=True))

        # append square image aws url
        row.append(aws_url(image=image_name, square=True))

        self.rows.append(row)
        return image_name
