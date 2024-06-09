import logging

from django.core.management.base import BaseCommand

from web.models import Post
from web.models.images import VuforiaImage

log_cmd = logging.getLogger("command")


class Command(BaseCommand):
    help = "Uploads the Vuforia images for given posts split by whitespaces " \
           "by setting is_dirty to true"
    # example: python3 manage.py add-vuforia-selectively 16 30 60

    def add_arguments(self, parser):
        # Positional Argument
        parser.add_argument('post_ids',
                            nargs='+',
                            type=int,
                            help='Define a list of winepost IDs to be '
                                 'uploaded.')

    @staticmethod
    def log_vuf(message):
        log_cmd.info("Add selected posts to Vuforia: ---- {}".format(message))

    def handle(self, *args, **options):
        post_ids = options.get('post_ids')
        ref_images_list = Post.active.filter(
            id__in=post_ids, is_parent_post=True
        ).values_list('ref_image', flat=True
                      )
        VuforiaImage.active.filter(id__in=ref_images_list).update(
            is_dirty=True)
        self.log_vuf('Done')
