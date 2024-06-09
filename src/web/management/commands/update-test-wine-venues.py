import logging
from django.db import connection
from django.core.management.base import BaseCommand
from web.models import Place, Post
from web.constants import PostTypeE
from web.utils.fetches import fetchalldict


log = logging.getLogger("command")


class Command(BaseCommand):
    args = ""
    help = "TEST WINES FOR VENUES"

    def get_places_without_posts_type(self, type):
        query = "SELECT p.id FROM web_place p WHERE p.is_archived != true AND p.id NOT IN ( " \
                "    SELECT wpv.place_id from web_post_venues wpv INNER JOIN web_post wp ON wp.id=wpv.post_id " \
                "        WHERE wp.type=%(type)s);"

        params = {'type': type}
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            items = fetchalldict(cursor)
            item_ids = [item['id'] for item in items]
            places = Place.active.filter(id__in=item_ids)
            return places

    def handle(self, *args, **options):
        i = 0
        pq = 1
        i = 0
        pq = 1
        posts_foods = Post.active.filter(type=PostTypeE.FOOD)
        cnt_posts_foods = posts_foods.count()
        places_not_food = self.get_places_without_posts_type(PostTypeE.FOOD)
        if places_not_food:
            cnt_places = len(places_not_food)
            log.debug("CNT PLACES WITHOUT FOODS: %s" % cnt_places)
            for place in places_not_food:
                log.debug("place W/O FOOD ID: %s NAME: %s (%s / %s) POST I: %s" % (place.id, place.name, pq,
                                                                                   cnt_places, i))
                for j in range(0, 25):
                    ij = i + j
                    if ij >= cnt_posts_foods:
                        i = 0
                        ij = i + j
                    post = posts_foods[ij]
                    log.debug("==== FOOD POST ID: %s TITLE: %s " % (post.id, post.title))
                    if place not in post.venues.all():
                        post.venues.add(place)
                        post.debug_save()
                    i += 1
                pq += 1
