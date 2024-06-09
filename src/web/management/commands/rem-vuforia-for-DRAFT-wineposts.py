import logging
from django.core.management.base import BaseCommand

from web.models import Post, PostStatusE

# removes vuforia images for existing wineposts with DRAFT status
# actually this script just re-saves DRAFT wineposts
# launching overridden Post.save() logic

log = logging.getLogger("command")


class Command(BaseCommand):
    args = ""
    help = "removes vuforia images for existing wineposts with DRAFT status"

    def handle(self, *args, **options):
        log.debug("Fetching wineposts to be cleaned from Vuforia targets ...")
        draft_posts = Post.active.filter(status=PostStatusE.DRAFT,
                                         ref_image__vuforia_deleted=False)
        log.debug(f"{draft_posts.count()} wineposts found.")
        for post in draft_posts:
            post.save()  # there is already logic to clean DRAFT winepost in
            # overridden Post.save() method
        log.debug("Vuforia targets for DRAFT wineposts will be deleted "
                  f"approximately in {draft_posts.count()/100} minutes")
        # VWS targets will be removed by delete_images() celery task
