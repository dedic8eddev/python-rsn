import requests
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from news.models import FeaturedVenueImage, NewsImage, QuoteImage, TestimonialImage, CheffeImage

from web.models import (PlaceImage, PostImage, VuforiaImage, EventImage,
                        CalEvent, WineImage, WinemakerImage, UserImage)
from web.utils.filenames import is_image_format
from web.utils.files import execute_task
from web.utils.storage import MediaStorage
from web.utils.upload_tools import aws_url


class Command(BaseCommand):
    args = ""
    help = "Re-process full, thumbs, square, horizontal, poster images"

    # create instance of MediaStorage to handle storing images into AWS S3 bucket
    storage = MediaStorage(bucket=settings.AWS_STORAGE_BUCKET_NAME)

    # list of rows of different image type urls
    rows = []

    def add_arguments(self, parser):
        # Positional Argument
        parser.add_argument('model', type=str,
                            help='Define model alias, one of: event, '
                                 'event_poster, vuforia, wine, winemaker, '
                                 'user, post, featured_venue, '
                                 'place, news, quote')
        # Optional argument
        parser.add_argument('--start', type=int, default=None, help='Use both start and limit args to restrict the quantity of images being procesed')  # noqa
        parser.add_argument('--limit', type=int, default=None, help='Use both start and limit args to restrict the quantity of images being procesed')  # noqa

        # Flag argument
        parser.add_argument('--crop_transparency', action='store_true', help='Whether to crop image transparency')
        parser.add_argument('--convert_to_jpg', action='store_true', help='Whether to convert image to jpg')
        parser.add_argument('--full_images', action='store_true', help='Whether to persist full image changes')
        parser.add_argument('--thumb_images', action='store_true', help='Whether to persist thumb image changes')
        parser.add_argument('--square_images', action='store_true', help='Whether to persist square image changes')
        parser.add_argument('--archived', action='store_true', help='Whether to process archived only images')
        parser.add_argument('--horizontal_images', action='store_true', help='Whether to persist horizontal image changes')  # noqa
        parser.add_argument('--poster_images', action='store_true', help='Whether to persist poster image changes')
        parser.add_argument('--analyze', action='store_true', help='Check if thumbnail and square images in use for given model')  # noqa

    def handle(self, *args, **options):
        """
        Re-process thumbs images for specified model

        Example:

            python manage.py process_images place
            python manage.py process_images place --crop_transparency --thumb_images
            python manage.py process_images event --start=0 --limit=5 --square_images
            python manage.py process_images event --start=0 --limit=5 --analyze
        """
        # get model alias
        model_name = options.get('model')
        crop_transparency = options.get('crop_transparency', False)
        full_image = options.get('full_images')
        thumb_image = options.get('thumb_images')
        square_image = options.get('square_images')
        convert_to_jpg = options.get('convert_to_jpg')
        archived = options.get('archived')
        horizontal_image = options.get('horizontal_images')
        poster_image = options.get('poster_images')
        start = options.get('start')
        limit = options.get('limit')
        analyze = options.get('analyze')

        # do processing only for active images (skip archived)
        model = self.get_image_model(model_name=model_name)

        if archived:
            images = model.objects.filter(is_archived=True).all()
        else:
            images = model.active.all()

        if type(start) == int and limit:
            images = images.order_by('id')[start:limit]

        images_count = len(images)

        self.stdout.write(f"Start processing {images_count} of {model_name} images")
        self.stdout.write(f"\t-crop transparency: {crop_transparency}")
        self.stdout.write(f"\t-convert images to jpg: {convert_to_jpg}")
        self.stdout.write(f"\t-process full images: {full_image}")
        self.stdout.write(f"\t-process thumb images: {thumb_image}")
        self.stdout.write(f"\t-process square images: {square_image}")
        self.stdout.write(f"\t-process horizontal images: {horizontal_image}")
        self.stdout.write(f"\t-process poster images: {poster_image}")
        self.stdout.write(f"\t-analyze images: {analyze}")

        if not full_image and not thumb_image and not square_image and not \
                horizontal_image and not poster_image and not analyze:
            self.stdout.write("Nothing to process, please select one+ of the options: '--full_images', "
                              "'--thumb_images', '--square_images', "
                              "'--horizontal_images', '--poster_images' or "
                              "select '--analyze' option to check thumbnails and square images for given model"
                              )
            return

        # process images in parallel
        # return errors dataframe(arg, exc) if any issues occurred during processing

        if analyze:
            errors_df = execute_task(
                task=self.analyze_image,
                iterator=images
            )
        else:
            errors_df = execute_task(
                task=self.process_image,
                iterator=images,
                crop_transparency=crop_transparency,
                full_image=full_image,
                thumb_image=thumb_image,
                square_image=square_image,
                horizontal_image=horizontal_image,
                poster_image=poster_image,
                convert_to_jpg=convert_to_jpg
            )

        # prepare output directory
        output_dir = Path(settings.APP_ROOT) / 'processed_images'
        output_dir.mkdir(parents=True, exist_ok=True)

        # export success results
        if len(self.rows) > 0:
            df = pd.DataFrame(self.rows, columns=["db_name",
                                                  "creation datetime",
                                                  "full", "thumb", "square",
                                                  "horizontal", "poster"])

            if archived:
                file_name = f'archived_{model_name}_images_urls.csv'
            else:
                file_name = f'{model_name}_images_urls.csv'
            df.to_csv(output_dir / file_name, index=False)

        # export errors results
        if len(errors_df) > 0:
            errors_df.rename(columns={"arg": "db_name"}, inplace=True)

            if not analyze:
                errors_df['full'] = errors_df['db_name'].apply(lambda x: aws_url(x))
                errors_df['thumb'] = errors_df['db_name'].apply(lambda x: aws_url(x, thumb=True))
                errors_df['square'] = errors_df['db_name'].apply(lambda x: aws_url(x, square=True))
                errors_df['horizontal'] = errors_df['db_name'].apply(lambda x: aws_url(x, horizontal=True))
                errors_df['poster'] = errors_df['db_name'].apply(lambda x: aws_url(x, poster=True))

            if archived:
                errors_file_name = f'archived_{model_name}_images_errors.csv'
            else:
                errors_file_name = f'{model_name}_images_errors.csv'
            errors_df.to_csv(output_dir / errors_file_name, index=False)

        self.stdout.write(f"{model_name.capitalize()} images processed:")
        self.stdout.write(f"\t-total amount: {images_count}")
        self.stdout.write(f"\t-processed successfully: {len(self.rows)}")
        self.stdout.write(f"\t-unprocessed: {len(errors_df)}")
        self.stdout.write('Reprocessing images is DONE!')

    @staticmethod
    def get_image_model(model_name):
        """
        Get image model factory method
        """
        model_name = model_name.lower()
        # handle post images
        if model_name == 'post':
            return PostImage

        # handle place images
        elif model_name.lower() == 'place':
            return PlaceImage

        # handle vuforia images
        elif model_name == 'vuforia':
            return VuforiaImage

        # handle event horizontal visuals
        elif model_name == 'event':
            return EventImage

        # handle event poster visuals
        elif model_name == 'event_poster':
            return CalEvent

        # handle wine images
        elif model_name == 'wine':
            return WineImage

        # handle winemaker images
        elif model_name == 'winemaker':
            return WinemakerImage

        # handle user images
        elif model_name == 'user':
            return UserImage
        # handle featured venues images
        elif model_name == 'featured_venue':
            return FeaturedVenueImage
        # handle news images
        elif model_name == 'news':
            return NewsImage
        elif model_name == 'quote':
            return QuoteImage
        elif model_name == 'cheffe':
            return CheffeImage
        elif model_name == 'testimonial':
            return TestimonialImage
        # unsupported images type
        else:
            raise ValueError('Invalid model name')

    def process_image(self, image, crop_transparency=False, full_image=False,
                      thumb_image=True, square_image=True,
                      horizontal_image=True, poster_image=True,
                      convert_to_jpg=True):
        """
        Process single image

        :param image - Image to process
        :param crop_transparency - Whether to crop image transparency
        :param full_image - Whether to persist full image changes
        :param thumb_image - Whether to persist thumb image changes
        :param square_image - Whether to persist square image changes
        :param horizontal_image - Whether to persist horizontal image changes
        :param poster_image - Whether to persist poster image changes
        :param convert_to_jpg - Whether to convert image to jpg

        Return:
            - image name
            - updated image list urls
            - error image list urls if any
        """
        row = []

        if type(image) == CalEvent:
            content = image.poster_image_file
        else:
            content = image.image_file

        # skip not supported images formats
        original_name = str(content)
        if not is_image_format(original_name):
            return original_name

        image_name = self.storage.generate_thumbnails(
            name=original_name,
            content=content,
            convert_to_jpg=convert_to_jpg,
            crop_transparency=crop_transparency,
            save_full_image=full_image,
            save_thumb_image=thumb_image,
            save_square_image=square_image,
            save_horizontal_image=horizontal_image,
            save_poster_image=poster_image
        )

        # if we convert image extension, we need also to update image in the DB
        if convert_to_jpg:
            if type(image) == CalEvent:
                image.poster_image_file = image_name
            else:
                image.image_file = image_name
            image.save()

        # append DB image name
        row.append(original_name)

        # append creation datetime
        row.append(image.created_time)

        # append full image aws url
        row.append(aws_url(image=image_name))

        # append thumb image aws url
        row.append(aws_url(image=image_name, thumb=True))

        # append square image aws url
        row.append(aws_url(image=image_name, square=True))

        # append horizontal image aws url
        row.append(aws_url(image=image_name, horizontal=True))

        # append poster image aws url
        row.append(aws_url(image=image_name, poster=True))

        self.rows.append(row)
        return image_name

    def image_url_check(self, image, suffix=''):
        original_image_name = image.image_file.name
        image_name = original_image_name
        image_url = "https://{0}{1}{2}".format(
            settings.AWS_STORAGE_BUCKET_NAME,
            settings.MEDIA_URL,
            image_name
        )
        with requests.get(image_url) as r:
            if r.status_code == 200:
                return 'OK'
            else:
                return 'FAIL'

    def analyze_image(self, image):
        row = [str(image), image.created_time]

        # get and append full image check result
        full_image_check_result = self.image_url_check(image)
        row.append(full_image_check_result)

        # get and append thumbnail image check result
        thumbnail_image_check_result = self.image_url_check(image,
                                                            suffix='_tmb')
        row.append(thumbnail_image_check_result)

        # get and append square image check result
        square_image_check_result = self.image_url_check(image,
                                                         suffix='_square')
        row.append(square_image_check_result)

        # get and append horizontal image check result
        horizontal_image_check_result = self.image_url_check(
            image, suffix='_horizontal')
        row.append(horizontal_image_check_result)

        # get and append poster image check result
        poster_image_check_result = self.image_url_check(image,
                                                         suffix='_poster')
        row.append(poster_image_check_result)

        self.rows.append(row)
        return image.image_file.name
