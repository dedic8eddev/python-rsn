import logging
import time

from django.core.management.base import BaseCommand

from web.constants import PostTypeE
from web.models import Post
from web.utils.vuforia_models import create_vuforia_images_for_post_and_wine

log_cmd = logging.getLogger("command")


class Command(BaseCommand):
    SLEEP_INTERVAL = 5
    MAX_ITEMS_PER_BATCH = 100
    args = ""
    help = "Creates the Vuforia images for CHILD posts, only to rate them " \
           "and remove them again. They will be sent via bg-vuforia by " \
           "setting is_dirty to true, then rated and removed " \
           "from Vuforia. Those Vuforia images will stay in the system " \
           "though to be used in the list."

    def add_arguments(self, parser):
        pass

    def log_vuf(self, message):
        log_cmd.info("Add Vuforia child posts: ---- {}".format(message))

    def handle(self, *args, **options):
        while True:
            self.log_vuf(
                "Checking for CHILD POST IMAGES to be sent to Vuforia for rating and then removed."  # noqa
            )

            posts = Post.active.filter(
                type=PostTypeE.WINE, is_parent_post=False, ref_image=None
            ).exclude(
                main_image=None
            )[0:self.MAX_ITEMS_PER_BATCH]

            for post in posts:
                create_vuforia_images_for_post_and_wine(
                    post, only_from_post=True
                )

                msg = "Adding vuforia image for post ID {} wine ID {} name: {}"
                self.log_vuf(msg.format(post.id, post.wine.id, post.wine.name))

            log_cmd.info("Sleeping for {} seconds after sending batch".format(
                self.SLEEP_INTERVAL
            ))

            time.sleep(self.SLEEP_INTERVAL)
