from django.core.management.base import BaseCommand
from news.models import (NewsImage, FeaturedVenueImage, QuoteImage,
                         WebsitePageImage, LPBImage, TestimonialImage, CheffeImage)
from web.utils.files import execute_task
from web.models.images import PostImage, PlaceImage, EventImage, WinemakerImage
from django.core.files.base import ContentFile
from web.models.models import CalEvent


class Command(BaseCommand):
    args = ""
    help = "Renaming all images of given models"

    def add_arguments(self, parser):
        parser.add_argument('model', type=str,
                            help='Define model alias, one of: news, place,\
                                featured_venue, quote, lpb, post, website_page or all')
        parser.add_argument('--start_index', type=int,
                            help='Define only if you want to get start index, like number.')
        parser.add_argument('--limit', type=int,
                            help='Define only if you want to limit count. It will work start_index+limit')

    def handle(self, *args, **options):
        """
        Re-process thumbs images for specified model

        Example:
            python manage.py change_filenames news
        """
        # get model alias
        model_name = options.get('model')
        start_index = options.get('start_index', 0)
        limit = options.get('limit', None)
        if model_name != "event":
            models = self.get_model(model_name=model_name)
            for m in models:
                items = m['model'].active.all()
                if limit:
                    items = items[start_index:start_index + limit]
                else:
                    items = items[start_index:]
                items_count = len(items)
                mn = m['model_name']
                self.stdout.write(f"Start processing {items_count} items of {mn} model.")
                self.stdout.write(f"\t-total amount: {items_count}")
                execute_task(
                    task=self.change_filename,
                    iterator=items
                )
        if model_name == "all" or model_name == "event":
            items = CalEvent.active.all()
            items_count = len(items)
            self.stdout.write(f"Start processing {items_count} items of Event Poster and Animated images.")
            self.stdout.write(f"\t-total amount: {items_count}")
            execute_task(
                task=self.change_event_poster_and_animated_filename,
                iterator=items
            )
            items = EventImage.active.all()
            items_count = len(items)
            self.stdout.write(f"Start processing {items_count} items of Event Horizontal images.")
            self.stdout.write(f"\t-total amount: {items_count}")
            execute_task(
                task=self.change_event_poster_and_animated_filename,
                iterator=items
            )
        self.stdout.write('Renaming files is DONE!')

    @staticmethod
    def get_model(model_name):
        """
        Get image model factory method
        """
        model_name = model_name.lower()
        if model_name == "all":
            return [{"model": NewsImage, "model_name": 'news'},
                    {"model": PlaceImage, "model_name": 'place'},
                    {"model": TestimonialImage, "model_name": 'testimonial'},
                    {"model": CheffeImage, "model_name": 'cheffe'},
                    {"model": QuoteImage, "model_name": 'quote'},
                    {"model": LPBImage, "model_name": 'lpb'},
                    {"model": WebsitePageImage, "model_name": 'website_page'},
                    {"model": PostImage, "model_name": 'post'},
                    {"model": FeaturedVenueImage, "model_name": 'featured_venue'},
                    {"model": WinemakerImage, "model_name": 'wine_maker'}]
        elif model_name == 'news':
            return [{"model": NewsImage, "model_name": 'news'}]
        elif model_name == 'place':
            return [{"model": PlaceImage, "model_name": 'place'}]
        elif model_name == 'post':
            return [{"model": PostImage, "model_name": 'post'}]
        elif model_name == 'featured_venue':
            return [{"model": FeaturedVenueImage, "model_name": 'featured_venue'}]
        elif model_name == 'quote':
            return [{"model": QuoteImage, "model_name": 'quote'}]
        elif model_name == 'lpb':
            return [{"model": LPBImage, "model_name": 'lpb'}]
        elif model_name == 'cheffe':
            return [{"model": CheffeImage, "model_name": 'cheffe'}]
        elif model_name == 'testimonial':
            return [{"model": TestimonialImage, "model_name": 'testimonial'}]
        elif model_name == 'website_page':
            return [{"model": WebsitePageImage, "model_name": 'website_page'}]
        elif model_name == 'wine_maker':
            return [{"model": WinemakerImage, "model_name": 'wine_maker'}]
        else:
            raise ValueError('Invalid model name')

    def change_filename(self, instance):
        try:
            img = instance.image_file.read()
            storage, path = instance.image_file.storage, instance.image_file.url
            instance.image_file.save(instance.image_file.name, ContentFile(img))
            storage.delete(path)
        except Exception:
            pass
        return True

    def change_event_poster_and_animated_filename(self, instance):
        try:
            img = instance.poster_image_file.read()
            storage, path = instance.poster_image_file.storage, instance.poster_image_file.url
            instance.poster_image_file.save(instance.poster_image_file.name, ContentFile(img), save=True)
            storage.delete(path)
        except Exception:
            pass
        try:
            img = instance.gif_image_file.read()
            storage, path = instance.gif_image_file.storage, instance.gif_image_file.url
            instance.gif_image_file.save(instance.gif_image_file.name, ContentFile(img), save=True)
            storage.delete(path)
        except Exception:
            pass

        try:
            img = instance.image_file.read()
            storage, path = instance.image_file.storage, instance.image_file.url
            instance.image_file.save(instance.image_file.name, ContentFile(img), save=True)
            storage.delete(path)
        except Exception:
            pass
        return True
