import logging
import random
import datetime as dt
from django.core.management.base import BaseCommand
from django.db.models import Q
from web.models import Post, Place, UserProfile, LikeVote, Comment, MonthlyStatsSubscriberPlace
from web.constants import UserTypeE
from web.utils.time import get_current_date


log_cmd = logging.getLogger("command")


class Command(BaseCommand):
    SLEEP_INTERVAL_EMPTY = 5
    SLEEP_INTERVAL_BATCH = 1
    MAstat_ITEMS_PER_BATCH = 100
    args = ""
    help = "Creates the Vuforia images for posts that don't have them and sets them " \
           "for sending via bg-vuforia by setting is_dirty to true"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        places_owners = Place.active.filter(owner__isnull=False)
        owners = [p.owner for p in places_owners]
        q_query = Q(author__type=UserTypeE.OWNER) | Q(author__in=owners)
        posts = Post.active.filter(q_query)
        log_cmd.debug("Found posts for owners: %s" % posts.count())
        for post in posts:
            inc_taps = random.randint(1, 15)
            inc_imps = random.randint(7, 19)
            post.tap_number += inc_taps
            post.impression_number += inc_imps
            post.debug_save()
            post.refresh_from_db()
            log_cmd.debug("POST ID %s INC TAPS: %s INC IMPRESSIONS: %s. FINAL TAPS: %s FINAL IMPRESSIONS: %s" %
                          (post.id, inc_taps, inc_imps, post.tap_number, post.impression_number))

        for place in places_owners:
            inc_visits = random.randint(3, 19)
            inc_imps = random.randint(5, 21)
            place.visit_number += inc_visits
            place.impression_number += inc_imps
            place.save_only()
            place.refresh_from_db()
            log_cmd.debug("PLACE ID %s INC VISITS: %s INC IMPRESSIONS: %s. FINAL VISITS: %s FINAL IMPRESSIONS: %s" %
                          (place.id, inc_visits, inc_imps, place.visit_number, place.impression_number))

        years = [2019, 2020]
        users = UserProfile.active.all()
        cur_date = get_current_date()
        for year in years:
            for month in range(1, 13):
                if year == cur_date.year and month > cur_date.month:
                    break

                p = Place.active.get(name='Iratze')
                for i in range(0, 40):
                    l = LikeVote(place=p, author=random.choice(users), created_time=dt.datetime.now(),
                                 modified_time=dt.datetime.now())
                    l.save_only()
                    l.refresh_from_db()
                    c = Comment(place=p, author=random.choice(users), created_time=dt.datetime.now(),
                                modified_time=dt.datetime.now(), description="blah blah blah", status=20)
                    c.save_only()
                    c.refresh_from_db()

                stat, created = MonthlyStatsSubscriberPlace.objects.get_or_create(place=p, owner=p.owner, 
                                                                                  year=year, month=month)
                stat.visits_total = random.randint(50, 730)
                stat.imp_home_venues_nearby = random.randint(130, 466)
                stat.imp_home_food = random.randint(144, 499)
                stat.imp_home_wines = random.randint(155, 536)
                stat.imp_map_thumb = random.randint(10, 553)
                stat.imp_venue_images_carousel = random.randint(111, 333)
                stat.imp_venue_food = random.randint(114, 555)
                stat.imp_venue_wines = random.randint(134, 631)
                stat.imp_total = stat.imp_home_venues_nearby + stat.imp_home_food + stat.imp_home_wines + \
                    stat.imp_map_thumb + stat.imp_venue_images_carousel + stat.imp_venue_food + \
                    stat.imp_venue_wines
                stat.tap_venue_website = random.randint(1, 499)
                stat.tap_venue_direction = random.randint(92, 584)
                stat.tap_venue_phone = random.randint(86, 231)
                stat.tap_venue_opening = random.randint(2, 166)
                stat.tap_from_venues_nearby = random.randint(11, 150)
                stat.tap_from_food = random.randint(33, 417)
                stat.tap_from_wines = random.randint(69, 177)
                stat.tap_from_map = random.randint(25, 539)
                stat.tap_from_total = stat.tap_from_venues_nearby + stat.tap_from_food + stat.tap_from_wines + \
                                      stat.tap_from_map
                stat.tap_venue_total = stat.tap_venue_website + stat.tap_venue_direction+ stat.tap_venue_phone + \
                                       stat.tap_venue_opening

                stat.this_week_stats = {
                    'tap_venue_website': stat.tap_venue_website - 10,
                    'tap_venue_direction': stat.tap_venue_direction - 10,
                    'tap_venue_phone': stat.tap_venue_phone - 10,
                    'tap_venue_opening': stat.tap_venue_opening - 10,
                    'tap_from_venues_nearby': stat.tap_from_venues_nearby - 10,
                    'tap_from_food': stat.tap_from_food - 10,
                    'tap_from_wines': stat.tap_from_wines - 10,
                    'tap_from_map': stat.tap_from_map - 10,
                }

                stat.last_week_stats = {
                    'tap_venue_website': stat.tap_venue_website - 20,
                    'tap_venue_direction': stat.tap_venue_direction - 20,
                    'tap_venue_phone': stat.tap_venue_phone - 20,
                    'tap_venue_opening': stat.tap_venue_opening - 20,
                    'tap_from_venues_nearby': stat.tap_from_venues_nearby - 20,
                    'tap_from_food': stat.tap_from_food - 20,
                    'tap_from_wines': stat.tap_from_wines - 20,
                    'tap_from_map': stat.tap_from_map - 20,
                }

                stat.save()
                stat.refresh_from_db()
