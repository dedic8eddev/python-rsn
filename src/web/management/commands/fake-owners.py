import logging

from django.core.management.base import BaseCommand
from django.db import connection

from web.models import Place, Post
from web.utils.fetches import fetchalldict

kw_log = logging.getLogger("command_keywords")


class Command(BaseCommand):
    args = ""
    help = "fakes the owners for non-owner venues"

    def handle(self, *args, **options):
        query = "SELECT x.* FROM web_post_venues x " \
                "    INNER JOIN web_post wp on wp.id=x.post_id"
        with connection.cursor() as cursor:
            cursor.execute(query)
            res = fetchalldict(cursor)

            for i, item in enumerate(res):
                place_id = item['place_id']
                post_id = item['post_id']
                place = Place.objects.get(id=place_id)
                # if not place.owner:
                #     username = 'genowner__%s' % place_id
                #     email = 'genowner__%s@example.com' % place_id
                #     owner = UserProfile(
                #         username=username,
                #         email=email,
                #         status=UserStatusE.ACTIVE,
                #         type=UserTypeE.OWNER,
                #     )
                #     owner.set_password('abcdEFGH1234')
                #     owner.save()
                #     owner.refresh_from_db()
                #     place.owner = owner
                #     place.save_only()
                #     place.refresh_from_db()

                post = Post.objects.get(id=post_id)
                post.venue = place
                post.debug_save()
