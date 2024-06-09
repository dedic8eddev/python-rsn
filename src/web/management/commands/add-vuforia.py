import logging
import time
from django.core.management.base import BaseCommand
from django.db.models import Q
from web.models import Post
from web.utils.vuforia_models import create_vuforia_images_for_post_and_wine
from web.constants import PostTypeE


log_cmd = logging.getLogger("command")


class Command(BaseCommand):
    SLEEP_INTERVAL_EMPTY = 5
    SLEEP_INTERVAL_BATCH = 1
    MAX_ITEMS_PER_BATCH = 100
    args = ""
    help = "Creates the Vuforia images for posts that don't have them and sets them " \
           "for sending via bg-vuforia by setting is_dirty to true"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        while True:
            log_cmd.info("Vuforia: ---- Fetching vuforia images with is_dirty=true")
            q_criteria = Q(**{"type": PostTypeE.WINE}) & Q(**{"is_parent_post": True})
            q_criteria &= (Q(**{"ref_image": None}) | Q(**{"wine__ref_image": None}))
            exc_criteria = (Q(**{"main_image": None}) & Q(**{"wine__main_image": None}))

            posts = Post.active.filter(q_criteria).exclude(exc_criteria)[0:self.MAX_ITEMS_PER_BATCH]

            if not posts:
                log_cmd.info("ADD-VUFORIA: SLEEPING FOR %s seconds after EMPTY RESULT" % self.SLEEP_INTERVAL_BATCH)
                time.sleep(self.SLEEP_INTERVAL_EMPTY)
                continue

            for post in posts:
                create_vuforia_images_for_post_and_wine(post)
                log_cmd.info("ADD-VUFORIA: adding vuforia image for post ID %s wine ID %s name: %s" %
                             (post.id, post.wine.id, post.wine.name))
            log_cmd.info("ADD-VUFORIA: SLEEPING FOR %s seconds after SENDING BATCH " % self.SLEEP_INTERVAL_BATCH)
            time.sleep(self.SLEEP_INTERVAL_BATCH)
