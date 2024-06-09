from django.core.management.base import BaseCommand
from news.models import LPB, News, Quote, WebsitePage, FeaturedVenue, Cheffe, Testimonial
from web.models import Place, Wine, Winemaker, Post
from web.utils.files import execute_task


class Command(BaseCommand):
    args = ""
    help = "Recreating all type of slugs"

    def add_arguments(self, parser):
        parser.add_argument('model', type=str,
                            help='Define model alias, one of: news, place, featured_venue,\
                                quote, lpb, website_page or all')

    def handle(self, *args, **options):
        """
        Re-process thumbs images for specified model

        Example:

            python manage.py slugging place
        """
        model_name = options.get('model')
        models = self.get_model(model_name=model_name)
        for m in models:
            items = m.objects.all()
            items_count = len(items)
            self.stdout.write(f"Start processing {items_count} items of {m.__name__} model.")
            self.stdout.write(f"\t-total amount: {items_count}")
            execute_task(
                task=self.make_slugs,
                iterator=items
            )

        self.stdout.write('Slugging names is DONE!')

    @staticmethod
    def get_model(model_name):
        """
        Get image model factory method
        """
        model_name = model_name.lower()
        if model_name == "all":
            return [News, Place, Quote, LPB, WebsitePage, FeaturedVenue, Cheffe, Testimonial]
        elif model_name == 'news':
            return [News]
        elif model_name == 'place':
            return [Place]
        elif model_name == 'featured_venue':
            return [FeaturedVenue]
        elif model_name == 'quote':
            return [Quote]
        elif model_name == 'lpb':
            return [LPB]
        elif model_name == 'cheffe':
            return [Cheffe]
        elif model_name == 'testimonial':
            return [Testimonial]
        elif model_name == 'website_page':
            return [WebsitePage, ]
        elif model_name == 'wine_maker':
            return [Winemaker, ]
        elif model_name == 'wine':
            return [Wine, ]
        elif model_name == 'post':
            return [Post, ]
        else:
            raise ValueError('Invalid model name')

    def make_slugs(self, instance):
        instance.save()
        return True
