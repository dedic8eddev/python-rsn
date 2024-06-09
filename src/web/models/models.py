import logging
import uuid
from datetime import datetime, date, time

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import ValidationError

from django.db.models import JSONField
from django.contrib.contenttypes.fields import GenericRelation
from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.gis.db.models import PointField
from django.contrib.gis.geos import Point
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.db.models import Q
import six
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from django.shortcuts import reverse

import web.utils.views_common
from web.constants import (CalEventTypeE, DonationFrequencyE,
                           DonationReceiptStatusE, DonationStatusE,
                           ParentItemTypeE, PlaceStatusE, PlaceTypeE,
                           PostStatusE, PostTypeE, PushNotifyTypeE, StatusE,
                           SysMessageStatusE, SysMessageTypeE,
                           TimeLineItemTypeE,
                           UserStatusE, UserTypeE, UserOriginE,
                           WineColorE, WineListStatusE, WinemakerStatusE,
                           WinemakerTypeE, WineStatusE, wm_type_statuses,
                           PLACE_GEO_CACHE_KEY,
                           get_wine_status_for_winemaker_status)
from web.helpers.places import PlaceHelper
from web.helpers.winemakers import WinemakerHelper
from web.helpers.wineposts import WinepostHelper
from web.utils.filenames import update_filename, update_event_gif_filename, update_event_poster_filename
from web.utils.geoloc import get_timezone_id_by_lat_lng
from web.utils.mentions import update_user_mentions_fn
from web.utils.model_object_tools import (archive_fn, author_has_badge_data,
                                          duplicate_fn, duplicate_images_fn,
                                          get_parent_item_fn,
                                          get_parent_item_type_fn)
from web.utils.model_tools import (beautify_place_name, generate_key,
                                   load_json_if_str,
                                   strip_leading_zero_ret_int_or_zero)
from web.utils.sendernotifier import SenderNotifier
from web.utils.time import (dt_from_str_pendulum, dt_to_str_pendulum,
                            get_datetime_from_string, get_dt_now_pendulum,
                            pendulum_datetime)
from web.utils.upload_tools import aws_url
from web.utils.vuforia import vuf_set_images_to_delete_for_wine
from web.utils import json_handling
from web.validators import (RaisinASCIIUsernameValidator,
                            RaisinUnicodeUsernameValidator)
from web.utils.default_data import get_erased_user_uid


log = logging.getLogger(__name__)
# MAX_DAYS_OPEN_SEARCH = 7
MAX_DAYS_OPEN_SEARCH = 1
WEEK_DAYS = {
    '1': 'Monday',
    '2': 'Tuesday',
    '3': 'Wednesday',
    '4': 'Thursday',
    '5': 'Friday',
    '6': 'Saturday',
    '7': 'Sunday'
}


def is_diff_enough(winner_post, old_sr_post, sr_log):
    winner_item_pts_data = calculate_post_points(winner_post, sr_log)
    old_sr_pts_data = calculate_post_points(old_sr_post, sr_log)

    winner_item_pts = winner_item_pts_data['total_pts']
    old_sr_pts = old_sr_pts_data['total_pts']

    is_enough = True if winner_item_pts - old_sr_pts >= settings.SR_MIN_DIFF else False  # noqa
    sr_log.debug("winner item points %f, old sr points %f, IS ENOUGH: %s " % (
        winner_item_pts, old_sr_pts, is_enough
    ))

    return is_enough


def get_parent_post_for_winepost(winepost):
    if winepost.is_parent_post:
        return winepost
    else:
        pp_items = Post.active.filter(wine=winepost.wine, is_parent_post=True)
        if pp_items:
            return pp_items[0]
    return None


def get_parent_post_for_wine(wine):
    pp_items = Post.active.filter(wine=wine, is_parent_post=True)
    if pp_items:
        return pp_items[0]
    return None


def calculate_post_points(post, sr_log):
    likevote_number = post.likevote_number
    comment_number = post.comment_number
    drank_it_too_number = post.drank_it_too_number

    pt_data = {
        'pt_comm_no': comment_number * settings.SR_WEIGHT_COMMENT_NUMBER,
        'pt_like_no': likevote_number * settings.SR_WEIGHT_LIKEVOTE_NUMBER,
        'pt_dit_no': drank_it_too_number * settings.SR_WEIGHT_DRANK_IT_TOO_NUMBER,  # noqa
        'pt_img': 0.0,
        'pt_relev': 0.0,
        'pt_desc_len': 0.0
    }

    if post.main_image:
        pt_data['pt_img'] = 1 * settings.SR_WEIGHT_IMAGE

    post_description_length = 0
    if post.description:
        post_description_length = len(str(post.description.strip()))
        pt_data['pt_desc_len'] = post_description_length * settings.SR_WEIGHT_DESCRIPTION_LENGTH  # noqa

        keywords_found = 0

        for keyword in settings.RELEVANCY_KEYWORDS:
            if post.description.find(keyword) >= 0:
                keywords_found += 1

        pt_data['pt_relev'] = keywords_found * settings.SR_WEIGHT_RELEVANCY_KEYWORD  # noqa

    tpl = "post %d (%s) for wine %s. Pt comment no: %f, pt like no: %f, " \
          "pt dit no: %f, pt img: %f, pt relevancy: %f, pt desc length: %f "
    sr_log.debug(
        tpl % (
            post.id, post.title, post.wine.name, pt_data['pt_comm_no'],
            pt_data['pt_like_no'], pt_data['pt_dit_no'], pt_data['pt_img'],
            pt_data['pt_relev'], pt_data['pt_desc_len']
        )
    )
    sr_log.debug("==== post %d (%s) DESCRIPTION LENGTH: %s" % (
        post.id, post.title, post_description_length
    ))

    total_points = 0.0
    for key, value in pt_data.items():
        total_points += value

    pt_data['total_pts'] = total_points
    return pt_data


def find_star_review_for_wine(wine, tested_post=None):
    sr_log = logging.getLogger("command_star_reviews")

    sr_log.debug("==========\nSearching for star review for WINE: %s" % wine)

    q_all = Q(wine=wine) & Q(type=PostTypeE.WINE) & Q(
        status=PostStatusE.PUBLISHED
    ) & Q(author__type=UserTypeE.USER)

    # if we are testing a particular post,
    # we only get the current star review (if exists) and this post.
    if tested_post:
        q_all &= Q(is_star_review=True) | Q(id=tested_post.id)

    all_published_posts = Post.active.filter(q_all)

    if not all_published_posts:
        sr_log.debug("no published posts for wine: %s, skipping" % wine)
        return False

    posts_to_sort = []

    for post in all_published_posts:

        post_accepted = False
        pt_data = calculate_post_points(post, sr_log)

        if settings.SR_STRATEGY == settings.SR_STRATEGY_MIN_INDIVIDUAL_POINTS:
            if (
                pt_data['pt_comm_no'] >= settings.SR_MIN_POINTS_COMMENT_NUMBER and  # noqa
                pt_data['pt_like_no'] >= settings.SR_MIN_POINTS_LIKEVOTE_NUMBER and  # noqa
                pt_data['pt_dit_no'] >= settings.SR_MIN_POINTS_DRANK_IT_TOO_NUMBER and  # noqa
                pt_data['pt_desc_len'] >= settings.SR_MIN_POINTS_DESCRIPTION_LENGTH and  # noqa
                pt_data['pt_relev'] >= settings.SR_MIN_POINTS_RELEVANCY
            ):
                post_accepted = True

        elif settings.SR_STRATEGY == settings.SR_STRATEGY_MIN_TOTAL_POINTS:
            if pt_data['total_pts'] >= settings.SR_MIN_TOTAL_POINTS:
                post_accepted = True
        else:
            post_accepted = True

        if not post.description or (post.description and len(post.description) < settings.SR_MIN_DESCRIPTION_LENGTH):
            post_accepted = False

        if post_accepted:
            post_to_sort = {
                'total_points': pt_data['total_pts'],
                'id': post.id,
                'title': post.title,
                'post_obj': post
            }

            posts_to_sort.append(post_to_sort)

        tpl = "post %d (%s) for wine %s total points: %f MIN TOTAL POINTS REQUIRED: %f accepted: %d"  # noqa
        sr_log.debug(tpl % (
            post.id, post.title, post.wine.name, pt_data['total_pts'],
            settings.SR_MIN_TOTAL_POINTS, post_accepted
        ))

    if not posts_to_sort:
        sr_log.debug(
            "no posts found able to become star reviews for wine: %s, skipping" % wine  # noqa
        )
        return False
    else:
        items_sorted = sorted(
            posts_to_sort,
            key=lambda item: item['total_points'],
            reverse=True
        )
        winner_item = items_sorted[0]
        old_srs = Post.active.filter(wine=wine, is_star_review=True)
        if old_srs:
            old_sr = old_srs[0]
            if old_sr.id != winner_item['id'] and not is_diff_enough(winner_item['post_obj'], old_sr, sr_log):
                return False

        sr_log.debug("\n\n=========================================")
        sr_log.debug(
            "setstarreviews: WINE: %s (id: %d)" % (wine.name, wine.id)
        )
        sr_log.debug(
            "setstarreviews - new star review - winning item: %s (id: %d)" % (
                winner_item['title'], winner_item['id']
            )
        )
        sr_log.debug(
            "setstarreviews - setting new star review for this wine - post id: %d title: %s" % (  # noqa
                winner_item['id'], winner_item['title']
            )
        )

        sr_log.debug("\n\n===========================================")
        winner_item_obj = winner_item['post_obj']
        return winner_item_obj


def unset_old_star_reviews(wine, this_post=None):
    if this_post:
        star_reviews = Post.active.filter(
            wine=wine,
            type=PostTypeE.WINE,
            is_star_review=True,
            is_star_discovery=False,  # we don't touch STAR_DISCOVERIES!
            status=PostStatusE.PUBLISHED
        ).exclude(id=this_post.id)
    else:
        star_reviews = Post.active.filter(
            wine=wine,
            type=PostTypeE.WINE,
            is_star_review=True,
            is_star_discovery=False,  # we don't touch STAR_DISCOVERIES!
            status=PostStatusE.PUBLISHED
        )
    if star_reviews:
        for star_review in star_reviews:
            star_review.is_star_review = False
            star_review.save()
            star_review.refresh_from_db()


def select_star_review_for_winepost(winepost, tested_post=None):
    sr_log = logging.getLogger("command_star_reviews")
    sr_log.debug("SELECT STAR REVIEW FOR WINEPOST %s %s " % (
        winepost.id, winepost.title
    ))
    if not settings.SR_CALCULATE:
        return False

    # we don't want to grant star review anew to the
    # post which already IS a star review
    if tested_post and tested_post.is_star_review:
        return False

    winner_item_obj0 = find_star_review_for_wine(
        winepost.wine, tested_post=winepost
    )

    with transaction.atomic():
        if winner_item_obj0 and winner_item_obj0.id == winepost.id:
            winner_item_obj = Post.active.select_for_update().get(id=winepost.id)  # noqa
            unset_old_star_reviews(winepost.wine, winepost)
            was_star_review = True if winner_item_obj.is_star_review else False
            winner_item_obj.is_star_review = True
            winner_item_obj.save()
            winner_item_obj.refresh_from_db()
            # winner_item_obj.wine.star_review_number = 1
            winner_item_obj.wine.save()
            winner_item_obj.wine.refresh_from_db()
            if not was_star_review:
                SenderNotifier().send_star_review_on_winepost(winner_item_obj)


# =============================================================================
# =============================================================================
# ============ MANAGER AND MODEL CLASSES ======================================
class UniqueSlugModel(models.Model):
    slug = models.SlugField(blank=True, max_length=255, null=True, unique=True)

    class Meta:
        abstract = True


class ArchivingManager(models.Manager):
    """
    Manage only active objects (not archived)
    """
    def get_queryset(self):
        queryset = super(ArchivingManager, self).get_queryset()
        queryset = queryset.filter(is_archived=False)

        return queryset


class ArchivingUserManager(UserManager):
    def get_queryset(self):
        q = super().get_queryset()
        q = q.filter(is_archived=False)
        return q


class AppWinepostManager(ArchivingManager):
    """
    Manage active wineposts for the mobile application
    """
    def get_queryset(self):
        queryset = super(AppWinepostManager, self).get_queryset()
        queryset = queryset.filter(
            status__in=WinepostHelper.app_winepost_display_statuses,
            type=PostTypeE.WINE,
            wine_id__isnull=False,
            wine__color__isnull=False
        )

        return queryset


class AppWinemakerManager(ArchivingManager):
    """
    Manage active winemakers for the mobile application
    """
    def get_queryset(self):
        queryset = super(AppWinemakerManager, self).get_queryset()
        queryset = queryset.filter(
            status__in=WinemakerHelper.app_winemaker_display_statuses
        )

        return queryset


class AppPlaceManager(ArchivingManager):
    """
    Manage active places for the mobile application
    """
    def get_queryset(self):
        queryset = super(AppPlaceManager, self).get_queryset()
        queryset = queryset.filter(status__in=PlaceHelper.app_place_display_statuses)

        return queryset


class UserProfile(AbstractUser):
    USERNAME_FIELD_2 = 'email'
    username_validator_raisin = RaisinUnicodeUsernameValidator() if six.PY3 else RaisinASCIIUsernameValidator()  # noqa
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_(
            'Required. 150 characters or fewer. Letters, digits and -/_ only.'
        ),
        validators=[username_validator_raisin],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )

    objects = UserManager()
    active = ArchivingUserManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=40, default=generate_key)

    # push_fields are for push notifications
    push_user_id = models.CharField(max_length=255, null=True, blank=True)
    push_user_token = models.CharField(max_length=255, null=True, blank=True)

    created_time = models.DateTimeField(default=datetime.now, null=False)
    modified_time = models.DateTimeField(default=datetime.now, null=True)
    last_failed_attempt_time = models.DateTimeField(
        default=datetime.now, null=True
    )
    failed_attempts_no = models.IntegerField(default=0, null=True)

    secondary_emails = ArrayField(
        models.EmailField(blank=True),
        size=10, blank=True, null=True
    )

    full_name = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(null=True, blank=True, max_length=170)

    # 10 - User, 20 - Editor, 30 - Administrator
    type = models.IntegerField(choices=UserTypeE.pairs, null=False)
    origin = models.IntegerField(choices=UserOriginE.pairs, null=True)

    status = models.IntegerField(choices=UserStatusE.pairs, null=False)
    is_archived = models.BooleanField(default=False, null=False)
    is_confirmed = models.BooleanField(default=False)

    def has_active_subscription(self):
        if self.customer and self.customer.has_active_subscription():
            return True

        return False

    # ---- monthly subscriptions ----
    # TODO - should I keep or remove this field?? Discuss.
    is_owner = models.BooleanField(default=False)
    customer = models.ForeignKey(
        'my_chargebee.Customer', null=True, on_delete=models.SET_NULL
    )
    # ---- /monthly subscriptions ----

    author = models.ForeignKey(
        "UserProfile", related_name="userprof_author", null=True,
        on_delete=models.CASCADE
    )
    last_modifier = models.ForeignKey(
        'UserProfile', null=True, related_name='userprof_last_modifier',
        on_delete=models.CASCADE
    )

    website_url = models.CharField(max_length=255, null=True, blank=True)
    image = models.ForeignKey('UserImage', null=True,
                              on_delete=models.SET_NULL)
    company_image = models.ForeignKey(
        'UserImage', related_name="company_image", null=True,
        on_delete=models.CASCADE
    )
    # TODO: remove wine_post_number and post_number
    # ToDo: remove comment_number, likevote_number, drank_it_too_number
    wine_post_number = models.IntegerField(default=0)
    comment_number = models.IntegerField(default=0)
    post_number = models.IntegerField(default=0)
    likevote_number = models.IntegerField(default=0)
    drank_it_too_number = models.IntegerField(default=0)
    star_review_number = models.IntegerField(default=0)

    activation_reminder_sent_number = models.IntegerField(default=0)
    activation_reminder_sent_last_date = models.DateTimeField(null=True)

    notify_likes = models.BooleanField(default=False)
    notify_drank_it_toos = models.BooleanField(default=False)
    notify_comments = models.BooleanField(default=False)
    notify_wine_reviewed = models.BooleanField(default=False)

    has_badge = models.BooleanField(default=False)
    has_p_once = models.BooleanField(default=False)
    has_p_monthly = models.BooleanField(default=False)
    badge_expiry_date_ms = models.BigIntegerField(null=True)
    badge_last_updated_date_ms = models.BigIntegerField(null=True)
    badge_last_purchase_date_ms = models.BigIntegerField(null=True)

    p_once_expiry_date_ms = models.BigIntegerField(null=True)
    p_once_last_updated_date_ms = models.BigIntegerField(null=True)
    p_once_last_purchase_date_ms = models.BigIntegerField(null=True)

    p_monthly_expiry_date_ms = models.BigIntegerField(null=True)
    p_monthly_expiry_date_ms_apple = models.BigIntegerField(null=True)
    p_monthly_expiry_date_ms_android = models.BigIntegerField(null=True)
    p_monthly_last_updated_date_ms = models.BigIntegerField(null=True)
    p_monthly_last_updated_date_ms_apple = models.BigIntegerField(null=True)
    p_monthly_last_updated_date_ms_android = models.BigIntegerField(null=True)
    p_monthly_last_purchase_date_ms = models.BigIntegerField(null=True)
    p_monthly_last_purchase_date_ms_apple = models.BigIntegerField(null=True)
    p_monthly_last_purchase_date_ms_android = models.BigIntegerField(null=True)
    lang = models.TextField(blank=True, null=True)
    currency = models.CharField(max_length=5, null=True)
    # assume that one user - one place - one 'formitable_url'
    formitable_url = models.CharField(max_length=255, null=True, blank=True)
    formitable_uid = models.CharField(max_length=255, null=True, blank=True)

    @property
    def author_username(self):
        return self.author.username if self.author else ""

    @property
    def author_image(self):
        return self.author.image if self.author else None

    def is_banned(self):
        return self.status == UserStatusE.BANNED

    def ban(self, modifier_user=None):
        self.status = UserStatusE.BANNED
        if modifier_user:
            self.last_modifier = modifier_user
            self.modified_time = datetime.now()
        self.save()

        timeline_items_to_delete = TimeLineItem.active.filter(user_item=self)
        for timeline_item_to_delete in timeline_items_to_delete:
            timeline_item_to_delete.archive()

    def unban(self, modifier_user=None):
        self.status = UserStatusE.ACTIVE
        if modifier_user:
            self.last_modifier = modifier_user
            self.modified_time = datetime.now()
        self.save()

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.full_name

    def get_name(self):
        return self.username or self.full_name

    def has_badge_data(self):
        has_badge, badge_expiry_date_ms = author_has_badge_data(
            p_once_expiry_date_ms=self.p_once_expiry_date_ms,
            p_monthly_expiry_date_ms=self.p_monthly_expiry_date_ms)
        return has_badge, badge_expiry_date_ms

    def get_has_badge(self):
        return self.has_badge_data()[0]

    def get_badge_expiry_date_ms(self):
        return self.has_badge_data()[1]

    def get_currency(self):
        return self.currency if self.currency else 'EUR'

    def get_total_wine_posts_number(self):
        return Post.objects.filter(type=PostTypeE.WINE, author=self).count()

    def get_images(self):
        return {
            'image': aws_url(self.image),
            'company_image': aws_url(self.company_image),
            'image_thumb': aws_url(self.image, thumb=True),
            'company_image_thumb': aws_url(self.company_image, thumb=True)
        }

    def get_lang(self):
        return self.lang.upper() if self.lang and isinstance(
            self.lang, str
        ) else None

    archive = archive_fn

    def update_wine_post_number(self):
        self.wine_post_number = Post.active.filter(author=self, type=PostTypeE.WINE).count()
        self.save()

    def update_general_post_number(self):
        self.post_number = Post.active.filter(author=self, type=PostTypeE.NOT_WINE).count()
        self.save()

    def update_star_review_number(self):
        self.star_review_number = Post.active.filter(author=self, is_star_review=True).count()
        self.save()

    def get_absolute_url(self):
        return reverse('edit_user', kwargs={'id': self.id})

    @property
    def absolute_url(self):
        return self.get_absolute_url()

    def __repr__(self):
        return self.get_full_name()

    def __str__(self):
        return self.get_full_name()


class Place(UniqueSlugModel, models.Model):
    """
        Stores a single place entry

        Model Relations:
            :model:`my_chargebee.Subscription`
            :model:`UserProfile`
            :model:`PlaceImage`
            :model:`PlaceOpeningHoursWeek`
    """

    objects = models.Manager()
    active = ArchivingManager()
    app_active = AppPlaceManager()

    # record data:
    # noqa id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_time = models.DateTimeField(default=datetime.now, null=False)
    modified_time = models.DateTimeField(default=datetime.now, null=True)
    last_wl_an_time = models.DateTimeField(default=None, null=True)
    total_wl_score = models.FloatField(default=0.0, null=True)

    status = models.IntegerField(null=False)  # StatusE.xxxx (published, draft)
    in_doubt = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False, null=False)
    is_expert_modified = models.BooleanField(default=False, db_index=True)
    wl_added = models.BooleanField(default=False, null=False)
    secondary_emails = ArrayField(
        models.EmailField(blank=True),
        size=10, blank=True, null=True
    )

    # ---- monthly subscriptions ----
    # TODO - REMOVE THE is_venue FIELD.
    # It's no longer needed since we have the "owner" field.
    # TODO - is_venue will always be set to True if "owner" is not null
    is_venue = models.BooleanField(default=False)
    tz_name = models.TextField(null=True)
    tz_offset = models.TextField(null=True)
    tz_dst = models.BooleanField(default=False)
    subscription = models.ForeignKey(
        'my_chargebee.Subscription', null=True, on_delete=models.SET_NULL
    )
    # ---- /monthly subscriptions ----

    validated_at = models.DateTimeField(null=True)
    validated_by = models.ForeignKey(
        'UserProfile', null=True, related_name='place_validated_by',
        on_delete=models.SET_NULL
    )
    team_comments = models.TextField(blank=True, null=True)

    # main data fields
    external_id = models.CharField(max_length=128, null=True)
    name = models.CharField(max_length=128)
    type = models.IntegerField(null=True, choices=PlaceTypeE.pairs)

    description = models.TextField(blank=True)
    user_mentions = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )

    # address/phone data:
    street_address = models.TextField(blank=True, null=True)
    full_street_address = models.TextField(blank=True, null=True)

    house_number = models.CharField(max_length=10, null=True)
    zip_code = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=128, null=True)
    osm_city_name = models.CharField(max_length=255, blank=True)
    osm_country_name = models.CharField(max_length=255, blank=True)
    new_city = models.ForeignKey('cities.City', null=True,
                                 related_name="places",
                                 blank=True, on_delete=models.PROTECT)
    district = models.ForeignKey('cities.District', null=True, blank=True,
                                 related_name='places',
                                 on_delete=models.PROTECT)
    country = models.CharField(max_length=128, null=True, blank=True)
    state = models.CharField(max_length=128, null=True, blank=True)
    country_iso_code = CountryField(
        null=True, blank=True, blank_label='(select country)'
    )
    phone_number = models.CharField(max_length=50, null=True)
    website_url = models.CharField(max_length=255, null=True)
    email = models.EmailField(max_length=255, null=True)

    latitude = models.FloatField(default=0, null=True)
    longitude = models.FloatField(default=0, null=True)
    point = PointField(geography=True, default='POINT(0.0 0.0)')

    pin_latitude = models.FloatField(default=0, null=True)
    pin_longitude = models.FloatField(default=0, null=True)

    country_old = models.CharField(max_length=128, null=True, blank=True)
    country_iso_code_old = models.CharField(
        null=True, blank=True, max_length=3
    )
    city_old = models.CharField(null=True, blank=True, max_length=128)

    # social sites
    social_facebook_url = models.CharField(max_length=255, null=True)
    social_twitter_url = models.CharField(max_length=255, null=True)
    social_instagram_url = models.CharField(max_length=255, null=True)

    sticker_sent = models.BooleanField(default=False, null=False)
    sticker_sent_dates = ArrayField(models.DateField(),
                                    blank=True,
                                    null=True)
    free_glass = models.BooleanField(default=False, null=False)
    free_glass_signup_date = models.DateTimeField(null=True, default=None)
    free_glass_last_action_date = models.DateTimeField(null=True, default=None)

    is_wine_shop = models.BooleanField(default=False, null=False)
    is_restaurant = models.BooleanField(default=False, null=False)
    is_bar = models.BooleanField(default=False, null=False)
    is_30_p_natural_already = models.BooleanField(default=False, null=False)

    opening_hours = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )
    closing_dates = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )

    # relations:
    current_opening_hours = models.ForeignKey(
        'PlaceOpeningHoursWeek', null=True,
        related_name='current_opening_hours',
        on_delete=models.CASCADE
    )

    # author
    author = models.ForeignKey('UserProfile',
                               on_delete=models.SET(get_erased_user_uid()))
    owner = models.ForeignKey(
        'UserProfile', related_name="place_owner", null=True, blank=True,
        on_delete=models.SET_NULL
    )
    last_modifier = models.ForeignKey(
        'UserProfile', null=True, related_name='place_last_modifier',
        on_delete=models.SET_NULL
    )
    expert = models.ForeignKey(
        'UserProfile', null=True, related_name='place_expert',
        on_delete=models.SET_NULL
    )

    # opening_hours - many-to-one, done on PlaceOpeningHoursWeek (many) side
    # images - many-to-one, done on PlaceImage (many) side
    # main_image - image
    main_image = models.ForeignKey(
        'PlaceImage', related_name='main_image', blank=True, null=True,
        on_delete=models.CASCADE
    )

    comment_number = models.IntegerField(default=0)  # ToDo: computable field
    likevote_number = models.IntegerField(default=0)  # ToDo: computable field
    impression_number = models.IntegerField(default=0)
    visit_number = models.IntegerField(default=0)

    # Venue's tab: complementary info:
    missing_info = models.BooleanField(default=False)
    # PlaceSubscrTypeE.xxxx
    type_sub = models.IntegerField(blank=True, null=True)
    media_post_date = models.DateField(blank=True, null=True)
    media_post_url = models.URLField(blank=True, null=True)

    # PlaceSourceInfoE.xxxx
    src_info = models.IntegerField(blank=True, null=True)  # the way a place
    reports = GenericRelation('reports.Report', related_query_name='places')
    # was added into CMS
    # owner properties

    @property
    def display_full_address(self):
        address = self.street_address
        if self.zip_code:
            address += f", {self.zip_code} {self.city}"
        else:
            address += f", {self.city}"
        if self.country:
            address += f", {self.country}"
        return address

    @property
    def owner_username(self):
        return self.owner.username if self.owner else None

    @property
    def owner_identifier(self):
        return self.owner_id if self.owner else None

    @property
    def owner_image(self):
        return self.owner.image if self.owner else None

    # last_modifier properties
    @property
    def last_modifier_username(self):
        return self.last_modifier.username if self.last_modifier else None

    @property
    def last_modifier_identifier(self):
        return self.last_modifier_id if self.last_modifier else None

    @property
    def last_modifier_image(self):
        return self.last_modifier.image if self.last_modifier else None

    # expert properties
    @property
    def expert_username(self):
        return self.expert.username if self.expert else None

    @property
    def expert_identifier(self):
        return self.expert_id if self.expert else None

    @property
    def expert_image(self):
        return self.expert.image if self.expert else None

    def get_i_like_it(self, user):
        """
        Get user I like it
        """
        if not user or user.is_anonymous:
            return False

        return LikeVote.objects.filter(place=self, author=user).exists()

    def get_status_in_doubt(self):
        return PlaceStatusE.IN_DOUBT

    def get_in_doubt(self):
        return True if self.status == self.get_status_in_doubt() else False

    def set_in_doubt(self, modifier_user=None):
        self.status = PlaceStatusE.IN_DOUBT

        # disabled on request by JHB 06.06.2022
        # self.delete_related_items()

        if modifier_user:
            self.last_modifier = modifier_user
            self.modified_time = datetime.now()
            if modifier_user.type == UserTypeE.ADMINISTRATOR:
                self.expert = modifier_user
        self.save()
        self.refresh_from_db()

    update_user_mentions = update_user_mentions_fn

    def update_timezone(self):
        tz_id = None
        if self.latitude and self.longitude:
            tz_id = get_timezone_id_by_lat_lng(self.latitude, self.longitude)
        elif self.pin_latitude and self.pin_longitude:
            tz_id = get_timezone_id_by_lat_lng(
                self.pin_latitude, self.pin_longitude
            )
        if tz_id:
            self.tz_name = tz_id
            super(Place, self).save()
            return tz_id

    def clear_cached(self):
        """
        Clear cached place if any
        """
        place_cache_key = PLACE_GEO_CACHE_KEY.format(self.id)
        cached_value = cache.get(place_cache_key)
        if cached_value:
            cache.delete(place_cache_key)
            log.info(f"Cache deleted '{place_cache_key}' for the place with id={self.id}. Place name: {self.name}.")

    def save(
        self, update_timezone=False, modified_time=True,
        last_modifier=None, *args, **kwargs
    ):
        if last_modifier:
            self.last_modifier = last_modifier
        if modified_time:
            self.modified_time = datetime.now()
        if self.id:
            new_item = False
        else:
            new_item = True

        send_accepted_notification = False

        if not new_item:
            old_version = Place.objects.get(id=self.id)
            if old_version.status in [PlaceStatusE.DRAFT, PlaceStatusE.IN_DOUBT] and \
                    self.status == PlaceStatusE.PUBLISHED or \
                    self.status == PlaceStatusE.SUBSCRIBER:
                send_accepted_notification = True

        self.social_facebook_url = self.social_facebook_url.strip() if self.social_facebook_url else ""  # noqa
        self.social_twitter_url = self.social_twitter_url.strip() if self.social_twitter_url else ""  # noqa
        self.social_instagram_url = self.social_instagram_url.strip() if self.social_instagram_url else ""  # noqa
        self.website_url = self.website_url.strip() if self.website_url else ""
        self.name = beautify_place_name(self.name)

        if not self.longitude:
            self.longitude = 0.0
        if not self.latitude:
            self.latitude = 0.0

        self.point = Point(
            float(self.longitude), float(self.latitude), srid=4326
        )
        super(Place, self).save(*args, **kwargs)
        if send_accepted_notification:
            SenderNotifier().send_accepted_on_place(self)
        if update_timezone:
            self.update_timezone()

    def save_only(self, *args, **kwargs):
        self.modified_time = datetime.now()
        self.name = beautify_place_name(self.name)
        super(Place, self).save(*args, **kwargs)

    def save_keep_modified_dt(self, *args, **kwargs):
        self.name = beautify_place_name(self.name)
        super(Place, self).save(*args, **kwargs)

    def close(self, modifier_user=None):
        self.status = PlaceStatusE.CLOSED

        # disabled on request by JHB 06.06.2022
        # self.delete_related_items()

        if modifier_user:
            self.last_modifier = modifier_user
            self.modified_time = datetime.now()
            if modifier_user.type == UserTypeE.ADMINISTRATOR:
                self.expert = modifier_user
        self.save()
        self.refresh_from_db()

    # ToDo: should be reviewed since PlaceStatusE.SUBSCRIBER taken place
    def publish(
        self, is_new=False, is_sticky=False, msg=None, modifier_user=None
    ):
        self.status = PlaceStatusE.PUBLISHED
        if modifier_user:
            self.last_modifier = modifier_user
            self.modified_time = datetime.now()
            if modifier_user.type == UserTypeE.ADMINISTRATOR:
                self.expert = modifier_user
        self.save()

    def unpublish(
        self, is_new=False, is_sticky=False, msg=None, modifier_user=None
    ):
        self.status = PlaceStatusE.DRAFT

        # disabled on request by JHB 06.06.2022
        # self.delete_related_items()

        if modifier_user:
            self.last_modifier = modifier_user
            self.modified_time = datetime.now()
            if modifier_user.type == UserTypeE.ADMINISTRATOR:
                self.expert = modifier_user
        self.save()
        timeline_items_to_delete = TimeLineItem.active.filter(place_item=self)
        for timeline_item_to_delete in timeline_items_to_delete:
            timeline_item_to_delete.archive()

    def duplicate(self):
        target_parent_item = duplicate_fn(self)
        target_parent_item.name = '[DUPLICATE] %s' % self.name
        target_parent_item.created_time = datetime.now()
        target_parent_item.modified_time = datetime.now()
        target_parent_item.save()
        target_parent_item.refresh_from_db()

        duplicate_images_fn(
            self, target_parent_item=target_parent_item,
            item_id_field='place_images'
        )

        opening_hours_weeks = PlaceOpeningHoursWeek.objects.filter(
            place__id=self.id
        ).filter(is_archived=False)

        if opening_hours_weeks:
            for opening_hours_week in opening_hours_weeks:
                opening_hours_week.duplicate(
                    target_parent_item=target_parent_item
                )

        return target_parent_item

    def archive(self, modifier_user=None):
        archive_fn(self)
        if modifier_user:
            self.last_modifier = modifier_user
            self.modified_time = datetime.now()
            if modifier_user.type == UserTypeE.ADMINISTRATOR:
                self.expert = modifier_user
            self.save_only()

        self.delete_related_items()

        timeline_items_to_delete = TimeLineItem.active.filter(place_item=self)
        for timeline_item_to_delete in timeline_items_to_delete:
            timeline_item_to_delete.archive()

        opening_hours_weeks = PlaceOpeningHoursWeek.objects.filter(
            place__id=self.id
        ).filter(is_archived=False)

        for opening_hours_week in opening_hours_weeks:
            opening_hours_week.archive()

        images = self.place_images.filter(is_archived=False)
        for image in images:
            image.archive()

    def delete_related_items(self):
        place_likes = self.like_votes.filter(is_archived=False)
        for placelike in place_likes:
            placelike.archive()

        place_comments = self.comments.filter(is_archived=False)
        for placecomment in place_comments:
            placecomment.archive()

    def get_main_image(self):
        return aws_url(self.main_image, thumb=True)

    def is_subscriber(self):
        """
        Check whether place is in any of subscription status except 'CANCELED'
        """
        # no subscription
        if not self.subscription:
            return False

        return self.subscription.status in PlaceHelper.place_subscribing_statuses

    def __str__(self):
        return self.name

    @staticmethod
    def get_default_opening_hours():
        res = {
            1: [
                {'fh': "10", 'fm': "00", 'th': "13", 'tm': "00"},
                {'fh': "16", 'fm': "00", 'th': "22", 'tm': "00"}
            ],
            2: [
                {'fh': "10", 'fm': "00", 'th': "13", 'tm': "00"},
                {'fh': "16", 'fm': "00", 'th': "22", 'tm': "00"}
            ],
            3: [
                {'fh': "10", 'fm': "00", 'th': "13", 'tm': "00"},
                {'fh': "16", 'fm': "00", 'th': "22", 'tm': "00"}
            ],
            4: [
                {'fh': "10", 'fm': "00", 'th': "13", 'tm': "00"},
                {'fh': "16", 'fm': "00", 'th': "22", 'tm': "00"}
            ],
            5: [
                {'fh': "10", 'fm': "00", 'th': "13", 'tm': "00"},
                {'fh': "16", 'fm': "00", 'th': "22", 'tm': "00"}
            ],
            6: [
                {'fh': "10", 'fm': "00", 'th': "13", 'tm': "00"},
                {'fh': "16", 'fm': "00", 'th': "22", 'tm': "00"}
            ],
            7: [
                {'fh': "10", 'fm': "00", 'th': "13", 'tm': "00"},
                {'fh': "16", 'fm': "00", 'th': "22", 'tm': "00"}
            ],
        }
        return res

    def opening_hours_defined(self):
        opening_hours = self.opening_hours
        res = load_json_if_str(opening_hours, {})
        if not res or not isinstance(res, dict):
            return False
        for day in range(1, 8):
            day_str = str(day)
            # if day not in opening_hours:
            #     return False
            if opening_hours[day_str]:
                return True
        return False

    def format_closing_dates(self):
        tz_name = 'CET' if not self.tz_name else self.tz_name

        res = load_json_if_str(self.closing_dates, [])
        if not res:
            res = []
        for i, item in enumerate(res):
            if 'd' not in item or not item['d'] or not isinstance(item['d'], str):
                res[i]['d'] = ""
            f_obj = get_datetime_from_string(item['f'])
            t_obj = get_datetime_from_string(item['t'])
            res[i]['f'] = f_obj.strftime('%Y-%m-%dT%H:%M:%S')
            res[i]['t'] = t_obj.strftime('%Y-%m-%dT%H:%M:%S')

        res_out = []

        for row in res:
            if 't' not in row or not row['t']:
                continue
            t_to = dt_from_str_pendulum(row['t'], tz_name=tz_name)
            if not t_to:
                continue

            dt_now = get_dt_now_pendulum(tz_name)
            if t_to >= dt_now:
                res_out.append(row)
        return res_out

    def holidays_date(self):
        dates_in_datetime = self.holidays_date_in_datetime()
        dates = [d.strftime('%d/%m/%Y') for d in dates_in_datetime]
        return dates

    def holidays_date_range(self):
        dates_range_in_datetime = self.holidays_date_range_in_datetime()
        dates_range = ['{} - {}'.format(d_r.get('from').strftime('%d/%m/%Y'), d_r.get('to').strftime('%d/%m/%Y'))
                       for d_r in dates_range_in_datetime]
        return dates_range

    @staticmethod
    def parse_opening_hours(opening_hours):
        fh = opening_hours.get("fh")
        fm = opening_hours.get("fm")
        th = opening_hours.get("th")
        tm = opening_hours.get("tm")

        if fh and fm:
            open_from = time(int(fh), int(fm))
        else:
            open_from = None
        if th and tm:
            open_to = time(int(th), int(tm))
        else:
            open_to = None

        return {'open_from': open_from, 'open_to': open_to}

    def opening_hours_in_datetime(self):
        if self.opening_hours_defined():
            opening_hours_data = {}
            for day in range(1, 8):
                hours = self.opening_hours.get(str(day), [])
                opening_hours_data[day] = {
                    'day': day,
                    'week_day_name': WEEK_DAYS.get(str(day)),
                    'times': [self.__class__.parse_opening_hours(time) for time in hours]
                }
            return opening_hours_data
        else:
            return []

    def holidays_date_in_datetime(self):
        dates = []
        if self.closing_dates:
            for date_dict in self.closing_dates:
                f_date = date_dict['f'].split('T')[0]
                f_year, f_month, f_day = f_date.split('-')

                t_date = date_dict['t'].split('T')[0]

                if f_date == t_date:
                    dates.append(date(int(f_year), int(f_month), int(f_day)))
        return dates

    def holidays_date_range_in_datetime(self):
        dates_range = []
        if self.closing_dates:
            for date_dict in self.closing_dates:
                f_date = date_dict['f'].split('T')[0]
                f_year, f_month, f_day = f_date.split('-')

                t_date = date_dict['t'].split('T')[0]
                t_year, t_month, t_day = t_date.split('-')

                if f_date != t_date:
                    dates_range.append(
                        {
                            'from': date(int(f_year), int(f_month), int(f_day)),
                            'to': date(int(t_year), int(t_month), int(t_day))
                        }
                    )
        return dates_range

    def is_valid_hour(self, hour):
        """
        Check whether hour is valid
        """
        if hour < 0 or hour > 23:
            return False
        return True

    def validate_opening_hours(self):
        """
        Validate opening hours
        """
        for day_k, day_data in self.opening_hours.items():
            for hour_data in day_data:
                if 'fh' not in hour_data or 'th' not in hour_data:
                    continue
                fh = int(hour_data['fh'])
                th = int(hour_data['th'])
                if not self.is_valid_hour(fh) or not self.is_valid_hour(th):
                    return False
        return True

    def format_opening_hours(self):
        # if self.opening_hours and not self.validate_opening_hours():
        #     log.debug(f"Invalid opening hours for place with id={self.pk}")

        res = load_json_if_str(self.opening_hours, {})

        if not res:
            res = Place.get_default_opening_hours()

        res_out = {}
        for day_k, day_data in res.items():
            day_data_out = []
            for h_data in day_data:
                if 'fh' not in h_data or 'th' not in h_data or 'fm' not in h_data or 'tm' not in h_data:
                    continue

                h_data['fh'] = strip_leading_zero_ret_int_or_zero(h_data['fh'])
                h_data['th'] = strip_leading_zero_ret_int_or_zero(h_data['th'])
                h_data['fm'] = strip_leading_zero_ret_int_or_zero(h_data['fm'])
                h_data['tm'] = strip_leading_zero_ret_int_or_zero(h_data['tm'])
                day_data_out.append(h_data)
            res_out[int(day_k)] = day_data_out
        return res_out

    def check_place_open_and_opening_hours_by_tz_data(self, max_days=MAX_DAYS_OPEN_SEARCH):
        tz_name = self.tz_name
        dt_now_provided_tz = get_dt_now_pendulum(tz_name)

        # a simple way to get a SEPARATE COPY of the dt object
        first_dt = dt_now_provided_tz
        first_open_dt = None
        first_open_weekday = None

        first_day = first_dt.day
        first_month = first_dt.month
        first_year = first_dt.year
        first_open_hours_row = None
        open_found = False
        open_now = False
        open_slot_i = None

        opening_hours_out = self.format_opening_hours()
        closing_dates_out = self.format_closing_dates()

        for day_i in range(0, max_days):
            if day_i > 0:
                dt_now_provided_tz = dt_now_provided_tz.add(days=1)
            closed_date = False
            day_now = dt_now_provided_tz.day
            month_now = dt_now_provided_tz.month
            year_now = dt_now_provided_tz.year
            # isoweekday() = %u int(dt_now_provided_tz.strftime('%u'))
            weekday_now = dt_now_provided_tz.isoweekday()
            for row in closing_dates_out:
                t_to_to_use = dt_from_str_pendulum(row['t'])
                t_from_to_use = dt_from_str_pendulum(row['f'])
                # current time FITS the "closed" term - THE PLACE IS CLOSED
                if t_from_to_use <= dt_now_provided_tz <= t_to_to_use:
                    closed_date = True
                    break

            if closed_date:
                continue
            # info about the place opening status for today is not
            # provided - CLOSED FOR THIS DAY
            if weekday_now not in opening_hours_out or not opening_hours_out[weekday_now]:
                continue

            # 3: [
            #        {'fh': 8, 'fm': 0, 'th': 18, 'tm': 30},
            #        {'fh': 20, 'fm': 15, 'th': 0, 'tm': 30},
            #    ],
            for i, row in enumerate(opening_hours_out[weekday_now]):
                if 'fh' not in row or 'th' not in row or 'fm' not in row or 'tm' not in row:
                    continue
                hour_from = int(row['fh'])
                hour_to = int(row['th'])
                minute_from = int(row['fm'])
                minute_to = int(row['tm'])

                dt_from = pendulum_datetime(
                    year_now, month_now, day_now, hour_from,
                    minute_from, 0, tz_name
                )
                dt_to = pendulum_datetime(
                    year_now, month_now, day_now, hour_to,
                    minute_to, 0, tz_name
                )

                if (hour_from > hour_to) or (hour_from == hour_to and minute_from > minute_to):
                    dt_to = dt_to.add(days=1)

                opening_hours_out[weekday_now][i]['dt_from'] = dt_to_str_pendulum(dt_from)  # noqa
                opening_hours_out[weekday_now][i]['dt_to'] = dt_to_str_pendulum(dt_to)  # noqa

                # first day - just check whether current time fits into
                # the opening hours - if so, THE PLACE IS OPEN
                if day_now == first_day and month_now == first_month and year_now == first_year:
                    # current time fits the opening hours - THE PLACE IS OPEN
                    if dt_from <= dt_now_provided_tz <= dt_to:
                        open_found = True
                        open_now = True
                        test_slot_i = 0
                        for test_day in range(1, int(weekday_now) + 1):
                            for test_i, test_slot in enumerate(
                                opening_hours_out[test_day]
                            ):
                                if test_day == weekday_now and test_i == i:
                                    open_slot_i = test_slot_i
                                    break
                                test_slot_i += 1
                            if open_slot_i is not None:
                                break

                        first_open_dt = dt_now_provided_tz
                        first_open_weekday = weekday_now
                        # first_open_row_i = i
                        first_open_hours_row = row
                        break
                    elif dt_from > dt_now_provided_tz:
                        # the range starts after current time - will be open,
                        # but not now (it also means we didn't find the
                        # fitting interval, since they are sorted;
                        # had we found it, we'd not be here, since the above
                        # condition "current time fits the opening hours"
                        # would apply
                        open_found = True
                        open_now = False
                        first_open_dt = dt_now_provided_tz
                        first_open_weekday = weekday_now
                        # first_open_row_i = i
                        first_open_hours_row = row
                        break
                else:
                    # another day - just get the EARLIEST hour interval
                    # ... they will be sorted ascending anyway
                    first_open_dt = dt_now_provided_tz
                    first_open_weekday = weekday_now
                    # first_open_row_i = i
                    first_open_hours_row = row
                    open_found = True
                    open_now = False
                    break

                if open_now:
                    opening_hours_out[weekday_now][i]['open'] = True
                else:
                    opening_hours_out[weekday_now][i]['open'] = False
            if open_found:
                break

        if open_slot_i is not None:
            open_slot_i_plus_1 = open_slot_i + 1
        else:
            open_slot_i_plus_1 = 0

        is_open_now = True if open_found and open_now else False
        return {
            'is_open_now': is_open_now,
            # 'is_open_later': True if open_found and not open_now else False,
            # TODO - is_open_later is erroneously used for checking the venue
            # as open now on android.
            # RESTORE THE PREVIOUS VERSION ONCE THE APP IS FIXED OR REMOVE
            # IT ALTOGETHER - TO DISCUSS WITH APP TEAM.
            'is_open_later': is_open_now,
            'closest_open_date': first_open_dt.strftime('%Y-%m-%d') if first_open_dt else None,  # noqa
            'closest_open_hours': {
                first_open_weekday: [first_open_hours_row]
            } if first_open_weekday and first_open_hours_row else {},
            'slot_open_now': open_slot_i_plus_1,
            'first_dt': first_dt.strftime("%Y-%m-%dT%H:%M:%S%z")
        }

    def get_absolute_url(self):
        return reverse('edit_place', kwargs={'id': self.id})

    @property
    def absolute_url(self):
        return self.get_absolute_url()


class PlaceOpeningHoursWeek(models.Model):
    objects = models.Manager()
    active = ArchivingManager()

    # record data:
    # noqa id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_time = models.DateTimeField(default=datetime.now, null=False)
    modified_time = models.DateTimeField(default=datetime.now, null=True)
    is_archived = models.BooleanField(default=False, null=False)

    # main fields:
    place = models.ForeignKey('Place', null=False, on_delete=models.CASCADE)

    monday_from = models.TimeField(null=True)
    monday_to = models.TimeField(null=True)
    monday_active = models.BooleanField(null=False, default=False)

    tuesday_from = models.TimeField(null=True)
    tuesday_to = models.TimeField(null=True)
    tuesday_active = models.BooleanField(null=False, default=False)

    wednesday_from = models.TimeField(null=True)
    wednesday_to = models.TimeField(null=True)
    wednesday_active = models.BooleanField(null=False, default=False)

    thursday_from = models.TimeField(null=True)
    thursday_to = models.TimeField(null=True)
    thursday_active = models.BooleanField(null=False, default=False)

    friday_from = models.TimeField(null=True)
    friday_to = models.TimeField(null=True)
    friday_active = models.BooleanField(null=False, default=False)

    saturday_from = models.TimeField(null=True)
    saturday_to = models.TimeField(null=True)
    saturday_active = models.BooleanField(null=False, default=False)

    sunday_from = models.TimeField(null=True)
    sunday_to = models.TimeField(null=True)
    sunday_active = models.BooleanField(null=False, default=False)

    archive = archive_fn

    def duplicate(self, target_parent_item):
        dupl = PlaceOpeningHoursWeek(**{
            'place': target_parent_item,

            'monday_from': self.monday_from,
            'monday_to': self.monday_to,
            'monday_active': self.monday_active,

            'tuesday_from': self.tuesday_from,
            'tuesday_to': self.tuesday_to,
            'tuesday_active': self.tuesday_active,

            'wednesday_from': self.wednesday_from,
            'wednesday_to': self.wednesday_to,
            'wednesday_active': self.wednesday_active,

            'thursday_from': self.thursday_from,
            'thursday_to': self.thursday_to,
            'thursday_active': self.thursday_active,

            'friday_from': self.friday_from,
            'friday_to': self.friday_to,
            'friday_active': self.friday_active,

            'saturday_from': self.saturday_from,
            'saturday_to': self.saturday_to,
            'saturday_active': self.saturday_active,

            'sunday_from': self.sunday_from,
            'sunday_to': self.sunday_to,
            'sunday_active': self.sunday_active,
        })

        dupl.save()

        return dupl


class WineListFile(models.Model):
    class Meta:
        db_table = "winelist_file"

    SUB_PATH = 'winelists/'
    objects = models.Manager()
    active = ArchivingManager()

    # noqa id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey('UserProfile', null=True,
                               on_delete=models.SET(get_erased_user_uid()))
    created_time = models.DateTimeField(default=datetime.now, null=False)
    modified_time = models.DateTimeField(default=datetime.now, null=True)
    # noqa status = models.IntegerField(null=False)  # StatusE.xxxx (published, draft)
    is_archived = models.BooleanField(default=False, null=False)

    ordering = models.IntegerField(null=True)
    width = models.IntegerField(null=True)
    height = models.IntegerField(null=True)

    image_file = models.FileField(
        null=True, upload_to=update_filename, blank=False, max_length=1000
    )
    winelist = models.ForeignKey('WineList', on_delete=models.CASCADE)
    item_text_rows = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )

    def archive(self):
        archive_fn(self)

    def unarchive(self, modifier_user=None):
        self.is_archived = False
        self.save()
        self.refresh_from_db()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.image_file.name


class TotalStats(models.Model):
    objects = models.Manager()
    created_time = models.DateTimeField(default=datetime.now, null=False)
    modified_time = models.DateTimeField(default=datetime.now, null=True)

    vuforia_scans_total = models.IntegerField(null=False, default=0)
    vuforia_scans_android = models.IntegerField(null=False, default=0)
    vuforia_scans_ios = models.IntegerField(null=False, default=0)


class WineList(models.Model):
    objects = models.Manager()
    active = ArchivingManager()

    # record data:
    created_time = models.DateTimeField(default=datetime.now)
    modified_time = models.DateTimeField(default=datetime.now)
    status = models.IntegerField(null=False, choices=WineListStatusE.pairs)
    is_archived = models.BooleanField(default=False, null=False)
    total_score_data = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )
    place = models.ForeignKey('Place', null=True, on_delete=models.CASCADE)

    is_temp = models.BooleanField(default=False)
    temp_parent_id = models.TextField(null=True, blank=True)

    is_in_shared_pool = models.BooleanField(default=False)

    def archive(self, modifier_user=None):
        archive_fn(self)
        wfs = WineListFile.active.filter(winelist=self)
        if wfs:
            for wf in wfs:
                wf.archive()


class Wine(UniqueSlugModel, models.Model):
    """
        Stores a single wine entry

        Direct model relations:
            :model:`UserProfile`
            :model:`WineImage`
            :model:`VuforiaImage`
            :model:`Winemaker`
    """

    objects = models.Manager()
    active = ArchivingManager()

    # record data:
    # noqa id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_time = models.DateTimeField(default=datetime.now)
    modified_time = models.DateTimeField(default=datetime.now)
    status = models.IntegerField(null=False, choices=WineStatusE.pairs)
    is_archived = models.BooleanField(default=False, null=False)

    validated_at = models.DateTimeField(null=True)
    validated_by = models.ForeignKey(
        'UserProfile', null=True, related_name='wine_validated_by',
        on_delete=models.SET_NULL
    )

    # main data fields
    name = models.CharField(max_length=255)
    name_short = models.CharField(max_length=255, blank=True, null=True)
    domain = models.CharField(max_length=255, null=True, blank=True)
    designation = models.CharField(max_length=255, null=True, blank=True)
    grape_variety = models.CharField(max_length=255, null=True, blank=True)
    region = models.CharField(max_length=255, null=True, blank=True)
    color = models.IntegerField(null=True, choices=WineColorE.pairs)

    year = models.CharField(null=True, max_length=10)
    is_sparkling = models.BooleanField(default=False)

    similiar_wine_exists = models.BooleanField(default=False)
    similiar_wine_id = models.IntegerField(default=None, null=True)

    external_id = models.CharField(default=None, null=True, max_length=128)

    # relations:
    # author (many-to-one)
    author = models.ForeignKey('UserProfile',
                               on_delete=models.SET(get_erased_user_uid()))
    # winemaker = domain
    winemaker = models.ForeignKey('Winemaker', null=True,
                                  related_name='wines',
                                  on_delete=models.CASCADE)
    winemaker_name = models.CharField(
        max_length=128, null=True, blank=True
    )  # used for wines which don't have a winemaker in the DB

    # images - many-to-one, done on WineImage (many) side
    # main_image - image
    main_image = models.ForeignKey(
        'WineImage', related_name='main_image', blank=True, null=True,
        on_delete=models.CASCADE
    )
    ref_image = models.ForeignKey(
        'VuforiaImage', related_name='wine_ref_image', blank=True,
        null=True, on_delete=models.CASCADE
    )

    wine_post_number = models.IntegerField(default=0)
    likevote_number = models.IntegerField(default=0)  # ToDo: to be computed
    comment_number = models.IntegerField(default=0)  # ToDo: to be computed
    drank_it_too_number = models.IntegerField(default=0)  # ToDo: to be
    # computed
    total_star_review_number = models.IntegerField(default=0)

    @property
    def winemaker_identifier(self):
        return self.winemaker.id if self.winemaker else None

    @property
    def winemaker_name_property(self):
        return self.winemaker.name if self.winemaker else None

    def clone(self):
        new_wine = Wine(
            created_time=datetime.now(),
            modified_time=datetime.now(),
            status=self.status,
            is_archived=False,
            validated_by=None,
            validated_at=None,
            name=self.name,
            name_short=self.name_short,
            domain=self.domain,
            designation=self.designation,
            grape_variety=self.grape_variety,
            region=self.region,
            color=self.color,
            year=self.year,
            is_sparkling=self.is_sparkling,
            similiar_wine_exists=self.similiar_wine_exists,
            similiar_wine_id=self.similiar_wine_id,
            external_id=self.external_id,
            author=self.author,
            winemaker=self.winemaker,
            winemaker_name=self.winemaker_name,
            main_image=self.main_image,
            wine_post_number=1,
            likevote_number=0,
            comment_number=0,
            drank_it_too_number=0,
            total_star_review_number=0
        )
        new_wine.save()
        new_wine.refresh_from_db()
        return new_wine

    def clone_as_new_draft(self):
        new_wine = Wine(
            created_time=datetime.now(),
            modified_time=datetime.now(),
            status=WineStatusE.ON_HOLD,
            is_archived=False,
            validated_by=None,
            validated_at=None,
            name=self.name,
            name_short=self.name_short,
            domain=self.domain,
            designation=self.designation,
            grape_variety=self.grape_variety,
            region=self.region,
            color=self.color,
            year=self.year,
            is_sparkling=self.is_sparkling,
            similiar_wine_exists=self.similiar_wine_exists,
            similiar_wine_id=self.similiar_wine_id,
            external_id=self.external_id,
            author=self.author,
            winemaker=self.winemaker,
            winemaker_name=self.winemaker_name,
            main_image=self.main_image,
            wine_post_number=1,
            likevote_number=0,
            comment_number=0,
            drank_it_too_number=0,
            total_star_review_number=0
        )
        new_wine.save()
        new_wine.refresh_from_db()
        return new_wine

    def duplicate(self):
        target_wine = duplicate_fn(self)
        target_wine.name = self.name
        target_wine.created_time = datetime.now()
        target_wine.modified_time = datetime.now()
        target_wine.save()
        target_wine.refresh_from_db()

        if self.main_image:
            target_wine.main_image = self.main_image.duplicate(
                target_parent_item=target_wine
            )
            target_wine.save()
            target_wine.refresh_from_db()

        return target_wine

    def debug_save(self):
        super().save()

    def update_wine_post_number(self):
        self.wine_post_number = Post.active.filter(wine=self).count()
        self.save()

    def get_main_image_url(
        self, fallback_parent_post_image=False,
        fallback_child_post_image=False
    ):

        if self.main_image:
            return aws_url(self.main_image)

        if fallback_parent_post_image:
            pp = Post.active.filter(
                type=PostTypeE.WINE, wine=self, is_parent_post=True,
                main_image__isnull=False
            )

            if pp:
                return aws_url(pp.first().main_image)

        if fallback_child_post_image:
            child_posts = Post.active.filter(
                type=PostTypeE.WINE, wine=self, is_parent_post=False,
                main_image__isnull=False
            )

            if child_posts:
                return aws_url(child_posts.first().main_image)

        return aws_url(self.main_image)

    def get_square_image_url(self, fallback_parent_post_image=False, fallback_child_post_image=False):
        """
        Get wine square image url
        """

        if self.main_image:
            return aws_url(self.main_image, square=True)

        if fallback_parent_post_image:
            pp = Post.active.filter(type=PostTypeE.WINE, wine=self, is_parent_post=True, main_image__isnull=False)

            if pp:
                return aws_url(pp.first().main_image, square=True)

        if fallback_child_post_image:
            child_posts = Post.active.filter(
                type=PostTypeE.WINE, wine=self, is_parent_post=False, main_image__isnull=False
            )

            if child_posts:
                return aws_url(child_posts.first().main_image, square=True)

        return aws_url(self.main_image)

    def save(self, *args, **kwargs):
        self.modified_time = datetime.now()
        self.name = self.name.strip()
        self.domain = self.domain.strip() if self.domain else ""
        self.designation = self.designation.strip() if self.designation else ""  # noqa
        self.grape_variety = self.grape_variety.strip() if self.grape_variety else ""  # noqa
        self.region = self.region.strip() if self.region else ""
        # self.year = self.year.strip() if self.year else ""
        super(Wine, self).save(*args, **kwargs)
        # self.winemaker.update_wine_number()

    def archive(self, modifier_user=None):
        archive_fn(self)
        wineposts = Post.objects.filter(wine__id=self.id).filter(
            is_archived=False
        )
        for winepost in wineposts:
            winepost.archive()
        images = self.images.filter(is_archived=False)
        for image in images:
            image.archive()
        vuf_set_images_to_delete_for_wine(self.id, None)

    def unarchive(self, modifier_user=None):
        if not self.is_archived:
            return

        self.is_archived = False
        self.save()

        images = self.images.filter(is_archived=False)
        for image in images:
            image.unarchive()

        self.refresh_from_db()

    def __str__(self):
        return self.name


# post and winepost here
class Post(UniqueSlugModel, models.Model):
    """
        Stores a single post entry

        Direct model relations:
            :model:`Post` (self relation)
            :model:`UserProfile`
            :model:`Wine`
            :model:`Place`
            :model:`PostImage`
            :model:`VuforiaImage`

        Backref model relations:
            :model: `DrankItToo`, drank_it_toos
    """

    objects = models.Manager()
    active = ArchivingManager()
    app_wineposts_active = AppWinepostManager()

    # record data:
    # noqa id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent_post = models.ForeignKey('self', null=True,
                                    on_delete=models.CASCADE)
    last_modifier = models.ForeignKey(
        'UserProfile', null=True, related_name='post_last_modifier',
        on_delete=models.SET_NULL
    )
    expert = models.ForeignKey(
        'UserProfile', null=True, related_name='post_expert',
        on_delete=models.SET_NULL
    )
    author = models.ForeignKey('UserProfile', related_name='posts_authored',
                               on_delete=models.SET(get_erased_user_uid()))
    wine = models.ForeignKey('Wine', null=True, related_name='posts',
                             on_delete=models.CASCADE)
    # place (for wine posts)
    place = models.ForeignKey('Place', null=True, related_name='posts',
                              on_delete=models.CASCADE)
    venues = models.ManyToManyField(Place, related_name='post_venue_m2m')

    main_image = models.ForeignKey(
        'PostImage', related_name='main_image', blank=True, null=True,
        on_delete=models.CASCADE
    )
    ref_image = models.ForeignKey(
        'VuforiaImage', related_name='post_ref_image', blank=True,
        null=True, on_delete=models.CASCADE
    )
    vuf_match_post = models.ForeignKey(
        'Post', related_name='vuforia_matched_post', blank=True, null=True,
        on_delete=models.CASCADE
    )
    vuf_match_wine = models.ForeignKey(
        'Wine', related_name='vuforia_matched_wine', blank=True, null=True,
        on_delete=models.CASCADE
    )

    created_time = models.DateTimeField(default=datetime.now)
    modified_time = models.DateTimeField(default=datetime.now)
    published_time = models.DateTimeField(default=None, null=True)

    validated_at = models.DateTimeField(null=True)
    validated_by = models.ForeignKey(
        'UserProfile', null=True, related_name='post_validated_by',
        on_delete=models.CASCADE
    )

    # main data fields
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.IntegerField(null=False)
    in_doubt = models.BooleanField(default=False)
    type = models.IntegerField(null=False, choices=PostTypeE.pairs)
    is_parent_post = models.BooleanField(default=False)

    wine_year = models.CharField(max_length=10, null=True)
    wine_trade = models.BooleanField(default=False)
    free_so2 = models.TextField(null=True, blank=True)
    total_so2 = models.TextField(null=True, blank=True)
    grape_variety = models.CharField(max_length=255, null=True, blank=True)
    yearly_data = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )
    certified_by = models.TextField(blank=True, null=True)
    is_organic = models.BooleanField(default=False, null=False)
    is_biodynamic = models.BooleanField(default=False, null=False)

    user_mentions = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )
    team_comments = models.TextField(blank=True, null=True)
    is_archived = models.BooleanField(default=False)
    is_star_review = models.BooleanField(default=False)
    is_star_discovery = models.BooleanField(default=False)
    is_scanned = models.BooleanField(default=False)

    # it seems the posts can be geolocated too
    latitude = models.FloatField(default=0, null=True)
    longitude = models.FloatField(default=0, null=True)

    foursquare_place_name = models.CharField(max_length=255, null=True)
    foursquare_place_url = models.CharField(max_length=255, null=True)

    impression_number = models.IntegerField(default=0)
    tap_number = models.IntegerField(default=0)

    # images - many-to-one, done on PostImage (many) side
    # main_image - image
    comment_number = models.IntegerField(default=0)  # ToDo: computable field
    likevote_number = models.IntegerField(default=0)  # ToDo: computable field
    drank_it_too_number = models.IntegerField(default=0)  # ToDo: computable
    # field
    star_review_number = models.IntegerField(default=0)

    price = models.FloatField(null=True)
    currency = models.CharField(max_length=5, null=True)
    reports = GenericRelation('reports.Report', related_query_name='posts')

    def get_absolute_url(self):
        if self.type == PostTypeE.WINE:
            return reverse('edit_winepost', kwargs={'id': self.id})
        else:
            return reverse('edit_generalpost', kwargs={'id': self.id})

    @property
    def absolute_url(self):
        return self.get_absolute_url()

    @property
    def name(self):
        return self.title

    # wine.winemaker
    @property
    def wine_winemaker_author(self):
        if self.wine and self.wine.winemaker:
            return self.wine.winemaker.author
        else:
            return None

    @property
    def wine_winemaker_domain(self):
        if self.wine and self.wine.winemaker:
            return self.wine.winemaker.domain
        else:
            return None

    @property
    def wine_winemaker_get_is_natural(self):
        if self.wine and self.wine.winemaker:
            return self.wine.winemaker.get_is_natural()
        else:
            return None

    @property
    def wine_winemaker_identifier(self):
        if self.wine and self.wine.winemaker:
            return self.wine.winemaker.id
        else:
            return None

    @property
    def wine_winemaker_name(self):
        if self.wine and self.wine.winemaker:
            return self.wine.winemaker.name
        else:
            return None

    @property
    def wine_winemaker_region(self):
        if self.wine and self.wine.winemaker:
            return self.wine.winemaker.region
        else:
            return None

    # expert
    @property
    def expert_identifier(self):
        return self.expert.id if self.expert else None

    @property
    def expert_image(self):
        return self.expert.image if self.expert else None

    @property
    def expert_username(self):
        return self.expert.username if self.expert else None

    # wine.main_image
    @property
    def wine_main_image_property(self):
        return self.wine.main_image if self.wine else None

    @property
    def wine_main_image_identifier(self):
        return self.wine.main_image_id if self.wine else None

    # wine.ref_image
    @property
    def wine_ref_image_property(self):
        return self.wine.ref_image if self.wine else None

    @property
    def wine_ref_image_identifier(self):
        return self.wine.ref_image_id if self.wine else None

    @property
    def wine_ref_image_rating_reco(self):
        if self.wine and self.wine.ref_image:
            return self.wine.ref_image.rating_reco
        else:
            return None

    # vuf_match_post
    @property
    def vuf_match_post_status_property(self):
        return self.vuf_match_post.status if self.vuf_match_post else None

    @property
    def vuf_match_post_wine_name(self):
        if self.vuf_match_post and self.vuf_match_post.wine:
            return self.vuf_match_post.wine.name
        else:
            return None

    @property
    def vuf_match_post_is_parent_post(self):
        if self.vuf_match_post:
            return self.vuf_match_post.is_parent_post
        else:
            return None

    @property
    def vuf_match_post_wine_ref_image(self):
        if self.vuf_match_post and self.vuf_match_post.wine:
            return self.vuf_match_post.wine.ref_image
        else:
            return None

    @property
    def vuf_match_post_wine_ref_image_id(self):
        if self.vuf_match_post and self.vuf_match_post.wine:
            return self.vuf_match_post.wine.ref_image_id
        else:
            return None

    @property
    def vuf_match_post_wine_ref_image_rating_tracking(self):
        if self.vuf_match_post and \
                self.vuf_match_post.wine and \
                self.vuf_match_post.wine.ref_image:
            return self.vuf_match_post.wine.ref_image.rating_tracking
        else:
            return None

    @property
    def vuf_match_post_wine_winemaker_get_is_natural(self):
        if self.vuf_match_post and \
                self.vuf_match_post.wine and \
                self.vuf_match_post.wine.winemaker:
            return self.vuf_match_post.wine.winemaker.get_is_natural()
        else:
            return None

    @property
    def vuf_match_post_wine_year(self):
        if self.vuf_match_post:
            return self.vuf_match_post.wine_year
        else:
            return None

    # vuf_match_wine
    @property
    def vuf_match_wine_name_property(self):
        return self.vuf_match_wine.name if self.vuf_match_wine else None

    @property
    def vuf_match_wine_identifier(self):
        return self.vuf_match_wine.id if self.vuf_match_wine else None

    @property
    def vuf_match_wine_status_property(self):
        return self.vuf_match_wine.status if self.vuf_match_wine else None

    @property
    def vuf_match_wine_winemaker_get_is_natural(self):
        if self.vuf_match_wine and self.vuf_match_wine.winemaker:
            return self.vuf_match_wine.winemaker.get_is_natural()
        else:
            return None

    # wine
    @property
    def wine_color(self):
        return self.wine.color if self.wine else None

    @property
    def wine_comment_number(self):
        return self.wine.comment_number if self.wine else None

    @property
    def wine_designation(self):
        return self.wine.designation if self.wine else None

    @property
    def wine_domain(self):
        return self.wine.domain if self.wine else None

    @property
    def wine_drank_it_too_number(self):
        return self.wine.drank_it_too_number if self.wine else None

    @property
    def wine_grape_variety(self):
        return self.wine.grape_variety if self.wine else None

    @property
    def wine_identifier(self):
        return self.wine.id if self.wine else None

    @property
    def wine_is_sparkling(self):
        return self.wine.is_sparkling if self.wine else None

    @property
    def wine_likevote_number(self):
        return self.wine.likevote_number if self.wine else None

    @property
    def wine_name(self):
        return self.wine.name if self.wine else None

    @property
    def wine_name_short(self):
        return self.wine.name_short if self.wine else None

    @property
    def wine_region(self):
        return self.wine.region if self.wine else None

    @property
    def wine_similiar_wine_exists(self):
        return self.wine.similiar_wine_exists if self.wine else None

    @property
    def wine_similiar_wine_id(self):
        return self.wine.similiar_wine_id if self.wine else None

    @property
    def wine_status(self):
        return self.wine.status if self.wine else None

    @property
    def wine_total_star_review_number(self):
        return self.wine.total_star_review_number if self.wine else None

    @property
    def wine_wine_post_number(self):
        return self.wine.wine_post_number if self.wine else None

    @property
    def wine_winemaker(self):
        return self.wine.winemaker if self.wine else None

    # wine.author
    @property
    def wine_author_username(self):
        return self.wine.author.username if self.wine else None

    # place
    @property
    def place_identifier(self):
        return self.place.id if self.place else None

    @property
    def place_name_property(self):
        return self.place.name if self.place else None

    # place.free_glass
    @property
    def place_free_glass_property(self):
        return self.place.free_glass if self.place else None

    @property
    def place_free_glass_signup_date_property(self):
        return self.place.free_glass_signup_date if self.place else None

    def get_i_like_it(self, user):
        """
        Get post i like it
        """
        if not user or user.is_anonymous:
            return False

        return LikeVote.objects.filter(post=self, author=user).exists()

    def get_i_drank_it_too(self, user):
        """
        Get user I drank it too
        """
        if not user or user.is_anonymous:
            return False

        return DrankItToo.objects.filter(post=self, author=user).exists()

    def set_title_winepost(self):
        if self.type != PostTypeE.WINE or not self.wine:
            return
        if self.wine_year:
            self.title = "%s %s" % (self.wine.name, self.wine_year)
        else:
            self.title = self.wine.name

    def debug_save(self):
        super().save()

    def delete_from_timeline(self):
        timeline_items_to_delete = TimeLineItem.active.filter(post_item=self)
        for timeline_item_to_delete in timeline_items_to_delete:
            timeline_item_to_delete.archive()

    def delete_related_items(self):
        post_likes = self.like_votes.filter(is_archived=False)
        for postlike in post_likes:
            postlike.archive()

        post_comments = self.comments.filter(is_archived=False)
        for postcomment in post_comments:
            postcomment.archive()

        if self.type == PostTypeE.WINE:
            wine_drank_it_toos = self.drank_it_toos.filter(is_archived=False)
            for wine_drank_it_too in wine_drank_it_toos:
                wine_drank_it_too.archive()

    def get_is_natural(self):
        return True if self.status in [
            PostStatusE.PUBLISHED, PostStatusE.DRAFT
        ] else False

    def get_status_in_doubt(self):
        return PostStatusE.IN_DOUBT

    def set_venue_by_id(self, place_id):
        if not place_id:
            return
        venue = Place.active.get(id=place_id)
        self.set_venue(venue)

    def set_venue(self, venue):
        self.venue = venue
        if venue not in self.venues.all():
            self.venues.add(venue)
        self.debug_save()

    def get_in_doubt(self):
        return True if self.status == self.get_status_in_doubt() else False

    def move_to_general_post(self):
        if self.type != PostTypeE.WINE or not self.wine:
            return
        vuf_images = self.vuforia_images.filter(wine=self.wine, delete_from_vuforia=False)
        for vuf_image in vuf_images:
            vuf_image.delete_from_vuforia = True
            vuf_image.save()
            vuf_image.refresh_from_db()
        old_wine = self.wine
        self.type = PostTypeE.NOT_WINE
        self.is_parent_post = False
        self.is_star_review = False
        self.wine = None
        self.modified_time = datetime.now()
        self.save()
        self.refresh_from_db()

        other_posts_for_old_wine = Post.active.filter(wine=old_wine)

        if not other_posts_for_old_wine:
            vuf_images = old_wine.vuforia_images.filter(
                delete_from_vuforia=False
            )
            for vuf_image in vuf_images:
                vuf_image.delete_from_vuforia = True
                vuf_image.save()
                vuf_image.refresh_from_db()
            old_wine.archive()
            old_wine.refresh_from_db()
        return self

    def duplicate(self):
        target_post = duplicate_fn(self)
        target_post.title = self.title

        target_post.created_time = datetime.now()
        target_post.modified_time = datetime.now()
        target_post.save()
        target_post.refresh_from_db()

        if self.main_image:
            target_post.main_image = self.main_image.duplicate(target_parent_item=target_post)

        if self.is_winepost() and self.wine:
            target_wine = self.wine.duplicate()

            target_post.wine = target_wine
            target_post.save()
            target_post.refresh_from_db()

            if self.ref_image:
                ref_image = self.ref_image.duplicate(
                    target_parent_item=target_wine,
                    extra_data={'post': target_post},
                    for_vuforia=True
                )

                target_post.ref_image = ref_image
                target_post.save()
                target_post.refresh_from_db()

        return target_post

    update_user_mentions = update_user_mentions_fn

    def get_other_wines_for_winemaker(self):
        return Wine.active.filter(winemaker=self.wine.winemaker).exclude(id=self.wine_id)

    def get_other_posts_for_wine(self):
        other_posts_for_wine = Post.active.filter(type=PostTypeE.WINE, wine=self.wine).exclude(id=self.id)
        return other_posts_for_wine

    def get_archived_posts_for_wine(self):
        other_posts_for_wine = Post.objects.filter(
            type=PostTypeE.WINE, wine=self.wine, is_archived=True
        ).exclude(id=self.id)

        return other_posts_for_wine

    def save(self, modifier_user=None, *args, **kwargs):
        # self.modified_time = datetime.now()
        self.title = self.title.strip() if self.title else ""
        self.wine_year = self.wine_year if self.wine_year else ""

        if self.is_archived:
            self.status = PostStatusE.DELETED

        if modifier_user:
            self.last_modifier = modifier_user
            self.modified_time = datetime.now()
            if modifier_user.type == UserTypeE.ADMINISTRATOR:
                self.expert = modifier_user

        if self.is_winepost() and self.wine:
            # existed post object
            if self.id:
                old_from_db = Post.objects.get(id=self.id)
                old_status = old_from_db.status

                # delete vuforia image if existing post becomes DRAFT
                # to prevent grey frames "We are not sure about this wine"
                # during mobile scanning
                # DRAFTs shouldn't be scannable at all
                if self.status == PostStatusE.DRAFT:
                    if self.ref_image \
                            and self.ref_image.vuforia_deleted is False:
                        self.ref_image.delete_from_vuforia = True
                        self.ref_image.save()
                        # self.ref_image = None
                        # self.wine.ref_image = None

            # new object, id is not defined yet
            else:
                old_status = None

                # inherit freshly created parent/referrer winepost status from "Winemaker's status"
                if self.is_parent_winepost() and self.wine and self.wine.winemaker:
                    self.status = get_wine_status_for_winemaker_status(wm_status=self.wine.winemaker.status)

            super(Post, self).save(*args, **kwargs)

            self.wine.update_wine_post_number()

            # blocked on Bretin's request at 13. Dec 2017 (turn off
            # the winemaker modifications when wine is modified)
            # self.wine.winemaker.update_wine_post_number();

            self.author.update_wine_post_number()

            if self.status == PostStatusE.PUBLISHED and self.is_parent_post and old_status \
                    and old_status != PostStatusE.PUBLISHED:
                SenderNotifier().send_accepted_on_winepost(self)

            # blocked on Bretin's request at 12. Dec 2017
            # (turn off the winemaker modifications when wine is modified)
            # if self.is_star_review:
            #     self.author.update_star_review_number()
            #     self.wine.winemaker.update_star_review_number()
            #
            # if self.is_parent_post:
            #     self.wine.winemaker.update_is_parent_post_number()

        elif self.type == PostTypeE.NOT_WINE:
            super(Post, self).save(*args, **kwargs)
            self.author.update_general_post_number()
        elif self.type == PostTypeE.FOOD:
            super(Post, self).save(*args, **kwargs)

    def push_to_timeline(self, is_new=False, is_sticky=False, msg=None):
        author = self.author

        if msg:
            item_description = msg
        else:
            if is_new:
                item_description = "post created"
            else:
                item_description = "post updated"

        timeline_items_to_delete = TimeLineItem.active.filter(post_item=self)
        for timeline_item_to_delete in timeline_items_to_delete:
            timeline_item_to_delete.archive()

        timeline_item = TimeLineItem(
            author=author,
            post_item=self,
            item_description=item_description,
            item_type=TimeLineItemTypeE.POST,
            is_sticky=is_sticky
        )
        timeline_item.save()

    def get_post_main_image_url(self, fallback_wine_image=False):
        if self.main_image:
            return aws_url(self.main_image)
        elif fallback_wine_image and self.type == PostTypeE.WINE and self.wine and self.wine.main_image:
            return aws_url(self.wine.main_image)
        else:
            return None

    @property
    def main_image_url(self):
        return self.get_post_main_image_url(True)

    def get_post_square_image_url(self, fallback_wine_image=False):
        """
        Get post square image url
        """
        if self.main_image:
            return aws_url(self.main_image, square=True)
        elif fallback_wine_image and self.type == PostTypeE.WINE and self.wine and self.wine.main_image:
            return aws_url(self.wine.main_image, square=True)
        else:
            return None

    def get_currency(self):
        return self.currency if self.currency else 'EUR'

    def is_parent_winepost(self):
        """
        Check whether post is 'WINE' type and is a parent post
        """
        return self.is_winepost() and self.is_parent_post

    def is_winepost(self):
        """
        Check whether post is a 'WINE' type
        """
        return self.type == PostTypeE.WINE

    def archive(self, modifier_user=None):
        archive_fn(self)

        if self.type == PostTypeE.WINE and self.is_star_review:
            self.is_star_review = False

        self.save(modifier_user=modifier_user)
        self.refresh_from_db()
        self.author.update_star_review_number()
        # self.wine.winemaker.update_star_review_number()
        self.delete_from_timeline()

        if self.is_parent_winepost():
            for other_post in self.get_other_posts_for_wine():
                # 2019.06.06 on Bretin's request
                # other_post.archive(modifier_user=modifier_user)
                other_post.archive()
            self.wine.archive()
            self.wine.refresh_from_db()

        self.delete_related_items()

        if self.is_winepost():
            wine_drank_it_toos = self.drank_it_toos.filter(is_archived=False)
            for wine_drank_it_too in wine_drank_it_toos:
                wine_drank_it_too.archive()

        images = self.images.filter(is_archived=False)
        for image in images:
            image.archive()

    def unarchive(self, modifier_user=None):
        self.is_archived = False
        self.save(modifier_user=modifier_user)
        self.refresh_from_db()

        if self.is_winepost():
            if self.wine.winemaker.is_archived:
                self.wine.winemaker.unarchive()
                self.wine.winemaker.refresh_from_db()

            if self.wine.is_archived:
                self.wine.unarchive()
                self.wine.refresh_from_db()
            self.refresh_from_db()

        if self.is_parent_winepost():
            self.wine.refresh_from_db()
            for other_post in self.get_archived_posts_for_wine():
                # 2019.06.06 on Bretin's request
                # other_post.unarchive(modifier_user=modifier_user)
                other_post.unarchive()

        images = self.images.filter(is_archived=True)
        for image in images:
            image.unarchive()

        self.push_to_timeline(is_new=False)

    def set_in_doubt(self, modifier_user=None):
        if not self.is_winepost() or not self.wine or not self.wine.winemaker:
            return

        self.status = self.get_status_in_doubt()
        self.save(modifier_user=modifier_user)
        self.refresh_from_db()

        self.delete_related_items()

        if self.is_parent_winepost() and self.wine:
            self.wine.status = WineStatusE.IN_DOUBT
            self.wine.save()
            for other_post in self.get_other_posts_for_wine():
                # 2019.06.06 on Bretin's request
                # other_post.set_in_doubt(modifier_user=modifier_user)
                other_post.set_in_doubt()
            if not self.get_other_wines_for_winemaker():
                # 2019.06.06 on Bretin's request
                # self.wine.winemaker.set_in_doubt(modifier_user=modifier_user)
                self.wine.winemaker.set_in_doubt()

    def set_bio_organic(self, modifier_user=None):
        if not self.is_winepost() or not self.wine or not self.wine.winemaker:
            return
        self.status = PostStatusE.BIO_ORGANIC
        self.save(modifier_user=modifier_user)
        self.refresh_from_db()

        if self.is_parent_winepost() and self.wine:
            self.wine.status = WineStatusE.BIO_ORGANIC
            self.wine.save()
            for other_post in self.get_other_posts_for_wine():
                # 2019.06.06 on Bretin's request
                # other_post.set_bio_organic(modifier_user=modifier_user)
                other_post.set_bio_organic()
            if not self.get_other_wines_for_winemaker():
                self.wine.winemaker.set_bio_organic(
                    modifier_user=modifier_user, set_wineposts=False
                )

    def publish(
        self, is_new=False, is_sticky=False, msg=None, validated_by=None,
        modifier_user=None, update_published_time=False
    ):
        self.is_sticky = web.utils.views_common.is_privileged_account(
            self.author
        )
        self.status = PostStatusE.PUBLISHED
        if update_published_time:
            self.published_time = datetime.now()

        self.save()
        self.refresh_from_db()
        if not validated_by and modifier_user:
            validated_by = modifier_user
        elif validated_by and not modifier_user:
            modifier_user = validated_by

        if not self.is_star_review:
            select_star_review_for_winepost(self, self)
            self.refresh_from_db()

        just_validated = False
        # store the FIRST VALIDATOR ONLY
        if not self.validated_at and not self.validated_by and validated_by:
            just_validated = True
            self.validated_at = datetime.now()
            self.validated_by = validated_by

        self.save(modifier_user=modifier_user)
        self.refresh_from_db()

        if self.is_parent_winepost() and self.wine:
            self.wine.status = WineStatusE.VALIDATED
            if just_validated:
                if not self.is_star_review:
                    self.is_star_review = True
                if not self.is_star_discovery:
                    self.is_star_discovery = True
                self.save(modifier_user=modifier_user)
                self.refresh_from_db()

            if not self.wine.validated_at and not self.wine.validated_by and validated_by:
                self.wine.validated_at = datetime.now()
                self.wine.validated_by = validated_by

            self.wine.save()
            self.wine.refresh_from_db()

            if self.wine.winemaker.status != WinemakerStatusE.VALIDATED:
                self.wine.winemaker.status = WinemakerStatusE.VALIDATED
                if not self.wine.winemaker.validated_at and not self.wine.winemaker.validated_by and validated_by:
                    self.wine.winemaker.validated_at = datetime.now()
                    self.wine.winemaker.validated_by = validated_by
                    self.wine.winemaker.last_modifier = validated_by

                self.wine.winemaker.save()
                self.wine.winemaker.refresh_from_db()

            for other_post in self.get_other_posts_for_wine():
                # 2019.06.06 on Bretin's request
                # other_post.publish(validated_by=validated_by)
                other_post.publish()

    def unpublish(self, modifier_user=None):
        self.status = PostStatusE.DRAFT
        self.save(modifier_user=modifier_user)

        self.delete_related_items()

        if self.is_parent_winepost() and self.wine:
            self.wine.status = WineStatusE.ON_HOLD
            self.wine.save()
            for other_post in self.get_other_posts_for_wine():
                # 2019.06.06 on Bretin's request
                # other_post.unpublish(modifier_user=modifier_user)
                other_post.unpublish()

    def set_to_investigate(self, modifier_user=None):
        """
        Set post status to investigate.
        Recursive function to update to investigate status:
            - wine status
            - other posts statuses
        """
        self.status = PostStatusE.TO_INVESTIGATE
        self.save(modifier_user=modifier_user)
        self.refresh_from_db()

        self.delete_related_items()

        if self.is_parent_winepost() and self.wine:
            self.wine.status = WineStatusE.TO_INVESTIGATE
            self.wine.save()

            other_posts = self.get_other_posts_for_wine()
            for post in other_posts:
                # recursive call
                post.set_to_investigate()

    def refuse(self, modifier_user=None):
        status = PostStatusE.REFUSED
        self.status = status
        self.save(modifier_user=modifier_user)
        self.refresh_from_db()

        self.delete_related_items()

        if self.is_parent_winepost() and self.wine:
            self.wine.status = WineStatusE.REFUSED
            self.wine.save()
            for other_post in self.get_other_posts_for_wine():
                # 2019.06.06 on Bretin's request
                # other_post.refuse(modifier_user=modifier_user)
                other_post.refuse()
            # there is winemaker which is not "DRAFT" by status
            # check whether there are ther wines for the winemaker than
            # the wine being refused; if there are none,
            # refuse winemaker as well by turning its status
            # to WinemakerStatusE.REFUSED
            if not self.get_other_wines_for_winemaker():
                # 2019.06.06 on Bretin's request
                # noqa self.wine.winemaker.refuse(modifier_user=modifier_user, refuse_wineposts=False)
                self.wine.winemaker.refuse(refuse_wineposts=False)

    def get_main_image(self):
        return aws_url(self.main_image, thumb=True)

    def get_free_so2(self):
        if not self.is_parent_post:
            parent_post = Post.active.filter(
                wine=self.wine, is_parent_post=True
            ).first()

            if parent_post:
                return parent_post.get_free_so2()
            else:
                return {
                    'free_so2': '', 'total_so2': '', 'grape_variety': ''
                }

        year = self.wine_year
        is_parent_post = self.is_parent_post
        yearly_data = load_json_if_str(self.yearly_data, None)
        yd = None

        if yearly_data and year and year in yearly_data:
            yd = yearly_data[year]
        elif yearly_data and is_parent_post:
            years_sorted = sorted(yearly_data.keys(), reverse=True)
            for year in years_sorted:
                if yearly_data[year]['free_so2'] and yearly_data[year]['total_so2']:  # noqa
                    yd = yearly_data[year]
                    break

        if yd:
            return {
                'free_so2': yd['free_so2'],
                'total_so2': yd['total_so2'],
                'grape_variety': yd['grape_variety']
            }

        return {
            'free_so2': self.free_so2,
            'total_so2': self.total_so2,
            'grape_variety': self.grape_variety
        }

    def get_vuf_rating_tracking(self):
        if self.is_parent_post and self.wine.ref_image:
            return self.wine.ref_image.rating_tracking

        if not self.is_parent_post and self.ref_image:
            return self.ref_image.rating_tracking

    def __str__(self):
        return self.title

    def __repr__(self):
        return self.title


class Winemaker(UniqueSlugModel, models.Model):
    """
    Stores a single winemaker entry

    Direct model relations:
        :model:`UserProfile`
        :model:`WinemakerImage`
    """
    objects = models.Manager()
    active = ArchivingManager()
    app_winemakers_active = AppWinemakerManager()

    # record data:
    # noqa id = models.UUIDField(primary_key=True, default=uupostid.uuid4, editable=False)
    author = models.ForeignKey('UserProfile',
                               on_delete=models.SET(get_erased_user_uid()))
    # images - many-to-one, done on WinemakerImage (many) side
    # main_image - image
    main_image = models.ForeignKey(
        'WinemakerImage', related_name='main_image', blank=True, null=True,
        on_delete=models.CASCADE
    )

    created_time = models.DateTimeField(default=datetime.now, null=False)
    modified_time = models.DateTimeField(default=datetime.now, null=True)
    last_modifier = models.ForeignKey(
        'UserProfile', null=True, related_name='winemaker_last_modifier',
        on_delete=models.SET_NULL
    )
    validated_at = models.DateTimeField(null=True)
    validated_by = models.ForeignKey(
        'UserProfile', null=True, related_name='wm_validated_by',
        on_delete=models.SET_NULL
    )
    team_comments = models.TextField(blank=True, null=True)
    status = models.IntegerField(null=False)
    in_doubt = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False, null=False)

    # main data fields:
    name = models.CharField(max_length=128)
    name_short = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    user_mentions = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )

    domain = models.CharField(max_length=128, null=True)
    domain_short = models.CharField(max_length=255, blank=True, null=True)
    is_organic = models.BooleanField(default=False, null=False)
    is_biodynamic = models.BooleanField(default=False, null=False)
    certified_by = models.TextField(blank=True, null=True)
    wine_trade = models.BooleanField(default=False, null=False)
    plough_horse = models.BooleanField(default=False, null=False)
    domain_description = models.TextField(blank=True, null=True)

    # per translation
    # [{
    #   'lang': '<<lang>>',
    #   'text': '<<text contents>>',
    #   'author_id': '<<author_id>>',
    #   'author_username': '<<author_username>>',
    #   'modified_time': '<<modified_time>>'
    # }]
    domain_description_translations = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )

    # address/phone data:
    street_address = models.TextField(blank=True, null=True)
    full_street_address = models.TextField(blank=True, null=True)
    house_number = models.CharField(max_length=10, null=True)
    zip_code = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=128, null=True)
    country = models.CharField(max_length=128, null=True, blank=True)
    state = models.CharField(max_length=128, null=True, blank=True)
    country_iso_code = CountryField(
        null=True, blank=True, blank_label='(select country)'
    )
    region = models.CharField(max_length=128, null=True, blank=True)
    phone_number = models.CharField(max_length=50, null=True)
    mobile_phone_number = models.CharField(max_length=50, null=True)
    website_url = models.CharField(max_length=255, null=True)
    email = models.CharField(max_length=255, null=True)

    latitude = models.FloatField(default=0, null=True)
    longitude = models.FloatField(default=0, null=True)
    pin_latitude = models.FloatField(default=0, null=True)
    pin_longitude = models.FloatField(default=0, null=True)

    country_old = models.CharField(max_length=128, null=True, blank=True)
    country_iso_code_old = models.CharField(
        null=True, blank=True, max_length=3
    )
    city_old = models.CharField(null=True, blank=True, max_length=128)

    # social sites
    social_facebook_url = models.CharField(max_length=255)
    social_twitter_url = models.CharField(max_length=255)
    social_instagram_url = models.CharField(max_length=255)

    total_wine_number = models.IntegerField(default=0)
    total_wine_post_number = models.IntegerField(default=0)
    likevote_number = models.IntegerField(default=0)
    comment_number = models.IntegerField(default=0)
    drank_it_too_number = models.IntegerField(default=0)
    total_star_review_number = models.IntegerField(default=0)
    total_is_parent_post_number = models.IntegerField(default=0)

    external_id = models.CharField(default=None, null=True, max_length=128)

    # last_modifier properties
    @property
    def last_modifier_username(self):
        return self.last_modifier.username if self.last_modifier else None

    @property
    def last_modifier_identifier(self):
        return self.last_modifier_id if self.last_modifier else None

    @property
    def last_modifier_image(self):
        return self.last_modifier.image if self.last_modifier else None

    def debug_save(self):
        super().save()

    def refuse(self, refuse_wineposts=True, modifier_user=None):
        self.status = WinemakerStatusE.REFUSED
        if modifier_user:
            self.last_modifier = modifier_user
            self.modified_time = datetime.now()

        self.save()
        if refuse_wineposts:
            items = Post.active.filter(
                type=PostTypeE.WINE, wine__winemaker=self
            )
            if items:
                for item in items:
                    item.refuse(modifier_user=modifier_user)

    def set_bio_organic(self, set_wineposts=True, modifier_user=None):
        self.status = WinemakerStatusE.BIO_ORGANIC
        if modifier_user:
            self.last_modifier = modifier_user
            self.modified_time = datetime.now()
        self.save()
        self.refresh_from_db()
        if set_wineposts:
            items = Post.active.filter(
                type=PostTypeE.WINE, wine__winemaker=self
            )
            if items:
                for item in items:
                    item.set_bio_organic(modifier_user=modifier_user)

    def save(self, *args, **kwargs):
        self.modified_time = datetime.now()
        self.name = self.name.strip()
        self.domain = self.domain.strip() if self.domain else ""

        self.social_facebook_url = self.social_facebook_url.strip() if self.social_facebook_url else ""  # noqa
        self.social_twitter_url = self.social_twitter_url.strip() if self.social_twitter_url else ""  # noqa
        self.social_instagram_url = self.social_instagram_url.strip() if self.social_instagram_url else ""  # noqa
        self.website_url = self.website_url.strip() if self.website_url else ""

        super(Winemaker, self).save(*args, **kwargs)

    def save_only(self, *args, **kwargs):
        self.modified_time = datetime.now()
        super().save(*args, **kwargs)

    def publish(
        self, is_new=False, is_sticky=False, msg=None, modifier_user=None
    ):
        self.status = WinemakerStatusE.VALIDATED
        if modifier_user:
            self.last_modifier = modifier_user
            self.modified_time = datetime.now()
        self.save()

    def unpublish(
        self, is_new=False, is_sticky=False, msg=None, modifier_user=None
    ):
        self.status = WinemakerStatusE.DRAFT
        if modifier_user:
            self.last_modifier = modifier_user
            self.modified_time = datetime.now()
        self.save()

    def duplicate(self):
        target_parent_item = duplicate_fn(self)

        target_parent_item.name = '[DUPLICATE] %s' % self.name
        target_parent_item.save()

        duplicate_images_fn(self, target_parent_item=target_parent_item)

        return target_parent_item

    def get_status_in_doubt(self):
        return WinemakerStatusE.IN_DOUBT

    def get_in_doubt(self):
        return True if self.status == self.get_status_in_doubt() else False

    def get_is_natural(self):
        return True if self.status in wm_type_statuses[WinemakerTypeE.NATURAL] else False  # noqa

    def get_is_other(self):
        return True if self.status in wm_type_statuses[WinemakerTypeE.OTHER] else False  # noqa

    def set_in_doubt(self, modifier_user=None):
        self.status = self.get_status_in_doubt()
        if modifier_user:
            self.last_modifier = modifier_user
            self.modified_time = datetime.now()
        self.save()
        self.refresh_from_db()

    def set_to_investigate(self, modifier_user=None):
        """
        Set winemaker to 'TO_INVESTIGATE' status
        """
        self.status = WinemakerStatusE.TO_INVESTIGATE
        self.save()
        self.refresh_from_db()

    def to_choice(self):
        return self.pk, self.name

    def get_translations(self):
        dd_tr = self.domain_description_translations
        items_out = []
        if dd_tr and 'translations' in dd_tr and dd_tr['translations']:
            orig_lang = dd_tr['orig_lang'] if 'orig_lang' in dd_tr and dd_tr['orig_lang'] else None  # noqa
            for lang, item in dd_tr['translations'].items():
                items_out.append({
                    'lang': lang,
                    'text': item['text'],
                    "author_id": item['author_id'],
                    "author_username": item['author_username'],
                    "modified_time": item['modified_time'],
                    'is_default': True if orig_lang and orig_lang == lang else False,  # noqa
                })
        return items_out

    def update_wine_number(self):
        self.total_wine_number = Wine.active.filter(winemaker=self).count()
        self.save()

    def update_wine_post_number(self):
        self.total_wine_post_number = Post.active.filter(type=PostTypeE.WINE, wine__winemaker=self).count()
        self.save()

    def update_star_review_number(self):
        self.total_star_review_number = Post.active.filter(
            is_star_review=True, type=PostTypeE.WINE,
            wine__winemaker=self
        ).count()
        self.save()

    def update_is_parent_post_number(self):
        self.total_is_parent_post_number = Post.active.filter(
            is_parent_post=True, type=PostTypeE.WINE,
            wine__winemaker=self
        ).count()
        self.save()

    def archive(self, modifier_user=None):
        archive_fn(self)
        if modifier_user:
            self.last_modifier = modifier_user
            self.save()
            self.refresh_from_db()

        wines = Wine.objects.filter(
            winemaker__id=self.id
        ).filter(is_archived=False)

        for wine in wines:
            wine.archive()

        images = self.images.filter(is_archived=False)
        for image in images:
            image.archive()

    def unarchive(self, modifier_user=None):
        if not self.is_archived:
            return

        self.is_archived = False
        if modifier_user:
            self.last_modifier = modifier_user
            self.modified_time = datetime.now()
        self.save()

        images = self.images.filter(is_archived=False)
        for image in images:
            image.unarchive()

        self.refresh_from_db()

    def __str__(self):
        return self.name


class LikeVote(models.Model):
    objects = models.Manager()
    active = ArchivingManager()

    # record data:
    # noqa id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_time = models.DateTimeField(default=datetime.now, null=False)
    modified_time = models.DateTimeField(default=datetime.now, null=True)
    is_archived = models.BooleanField(default=False, null=False)

    # main data fields: --

    # relations:
    author = models.ForeignKey(
        'UserProfile', related_name='like_votes_authored',
        on_delete=models.CASCADE)
    post = models.ForeignKey('Post', null=True, related_name="like_votes",
                             on_delete=models.CASCADE)
    place = models.ForeignKey('Place', null=True, related_name="like_votes",
                              on_delete=models.CASCADE)
    # wine - for winepost-likevotes only
    wine = models.ForeignKey(
        'Wine', null=True, related_name="like_votes", on_delete=models.CASCADE
    )

    cal_event = models.ForeignKey(
        'CalEvent', null=True, related_name="like_votes",
        on_delete=models.CASCADE
    )
    news = models.ForeignKey(
        'news.News', null=True, related_name="like_votes",
        on_delete=models.CASCADE
    )
    featured_venue = models.ForeignKey(
        "news.FeaturedVenue", null=True, related_name="like_votes",
        on_delete=models.CASCADE
    )

    @property
    def place_main_image_property(self):
        return self.place.main_image if self.place else None

    get_parent_item = get_parent_item_fn
    get_parent_item_type = get_parent_item_type_fn

    def save_only(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.modified_time = datetime.now()

        if self.post and self.post.type == PostTypeE.WINE and self.post.wine:
            self.wine = self.post.wine

        super(LikeVote, self).save(*args, **kwargs)

        if self.post:
            if not self.is_archived:
                # we don't want to send notifications on un-liking
                SenderNotifier().send_like_on_winepost(self)

        elif self.place:
            if not self.is_archived:
                # we don't want to send notifications on un-liking
                SenderNotifier().send_like_on_place(self)
        elif self.cal_event:
            pass

    def get_wine_kind(self):
        if not self.post:
            return None

        is_archived = self.post.is_archived

        return PostStatusE.DELETED if is_archived else self.post.status

    archive = archive_fn


class Attendee(models.Model):
    objects = models.Manager()
    active = ArchivingManager()

    # record data:
    created_time = models.DateTimeField(default=datetime.now, null=False)
    modified_time = models.DateTimeField(default=datetime.now, null=True)
    is_archived = models.BooleanField(default=False, null=False)
    is_user_there = models.BooleanField(default=False, null=False)

    # main data fields: --

    # relations:
    # author
    author = models.ForeignKey('UserProfile', on_delete=models.CASCADE)
    # post
    cal_event = models.ForeignKey(
        'CalEvent', null=False, related_name="attendees",
        on_delete=models.CASCADE
    )

    def save(self, *args, **kwargs):
        self.modified_time = datetime.now()

        super().save(*args, **kwargs)

    def archive(self, modifier_user=None):
        self.is_user_there = False
        archive_fn(self)


class Comment(models.Model):
    objects = models.Manager()
    active = ArchivingManager()

    # record data:
    created_time = models.DateTimeField(default=datetime.now)
    modified_time = models.DateTimeField(default=datetime.now)
    status = models.IntegerField(
        null=False, default=StatusE.DRAFT, choices=StatusE.pairs
    )
    is_archived = models.BooleanField(default=False, null=False)

    # main data fields:
    description = models.TextField(blank=True, null=True)
    user_mentions = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )

    # relations:
    author = models.ForeignKey('UserProfile',
                               related_name="comments_authored",
                               on_delete=models.SET(get_erased_user_uid()))
    post = models.ForeignKey('Post', null=True, related_name="comments",
                             on_delete=models.CASCADE)
    place = models.ForeignKey('Place', null=True, related_name="comments",
                              on_delete=models.CASCADE)
    wine = models.ForeignKey('Wine', null=True, related_name="comments",
                             on_delete=models.CASCADE)
    news = models.ForeignKey("news.News", null=True, related_name="comments", on_delete=models.CASCADE)
    featured_venue = models.ForeignKey(
        "news.FeaturedVenue", null=True,
        related_name="comments", on_delete=models.CASCADE
    )
    cal_event = models.ForeignKey(
        'CalEvent', null=True, related_name="comments",
        on_delete=models.CASCADE
    )

    in_reply_to = models.ForeignKey(
        'UserProfile',
        related_name='comments_where_replied_to',
        null=True,
        on_delete=models.SET(get_erased_user_uid())
    )

    get_parent_item = get_parent_item_fn
    get_parent_item_type = get_parent_item_type_fn

    update_user_mentions = update_user_mentions_fn
    external_id = models.CharField(null=True, blank=True, max_length=255)
    external_description = models.TextField(blank=True, null=True)
    external_author_id = models.CharField(null=True, blank=True, max_length=255)
    external_author_email = models.CharField(null=True, blank=True, max_length=255)
    external_author_name = models.CharField(null=True, blank=True, max_length=255)
    reports = GenericRelation('reports.Report', related_query_name='comments')

    def archive(self, modifier_user=None):
        self.is_archived = True
        super(Comment, self).save()

    def save_only(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.modified_time = datetime.now()

        if self.post and self.post.type == PostTypeE.WINE and self.post.wine:
            self.wine = self.post.wine

        if not self.id:
            is_new = True
        else:
            is_new = False

        super(Comment, self).save(*args, **kwargs)

        if self.post:
            if is_new and not self.is_archived:
                SenderNotifier().send_comment_on_winepost(self)
        elif self.place:
            if is_new and not self.is_archived:
                SenderNotifier().send_comment_on_place(self)
        elif self.cal_event:
            pass


class CommentReadReceipt(models.Model):
    created_time = models.DateTimeField(default=datetime.now)
    modified_time = models.DateTimeField(default=datetime.now)
    comment = models.ForeignKey(
        'Comment', related_name="read_receipts", null=False,
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        'UserProfile', related_name="read_receipts", null=False,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('comment', 'user',)


class StatsClick(models.Model):
    objects = models.Manager()

    created_time = models.DateTimeField(default=datetime.now)
    modified_time = models.DateTimeField(default=datetime.now)
    author = models.ForeignKey('UserProfile', on_delete=models.CASCADE)
    place_clicks = models.IntegerField(null=False, default=0)
    wm_clicks = models.IntegerField(null=False, default=0)
    total_clicks = models.IntegerField(null=False, default=0)


class MonthlyStatsSubscriberPlace(models.Model):
    objects = models.Manager()
    created_time = models.DateTimeField(default=datetime.now)
    modified_time = models.DateTimeField(default=datetime.now)

    year = models.IntegerField(null=False)
    month = models.IntegerField(null=False)

    owner = models.ForeignKey(
        'UserProfile', related_name="stats_owner_place_owner", null=False,
        on_delete=models.CASCADE
    )
    place = models.ForeignKey(
        'Place', related_name="stats_owner_place_owner", null=False,
        on_delete=models.CASCADE
    )
    post = models.ForeignKey(
        'Post', related_name="stats_owner_place_owner", null=True,
        on_delete=models.CASCADE
    )

    daily_stats = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )
    this_week_stats = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )
    last_week_stats = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )

    # visits: slide 28 - Combined-Sig.pdf
    # (number of times venue screen was displayed on app)
    visits_total = models.IntegerField(null=False, default=0)

    # impressions: slide 28,29 - Combined-Sig.pdf
    # (number of impressions on app for the subscribing venue)
    imp_total = models.IntegerField(null=False, default=0)
    imp_home_venues_nearby = models.IntegerField(null=False, default=0)
    imp_home_food = models.IntegerField(null=False, default=0)
    imp_home_wines = models.IntegerField(null=False, default=0)
    imp_map_thumb = models.IntegerField(null=False, default=0)
    imp_venue_images_carousel = models.IntegerField(null=False, default=0)
    imp_venue_food = models.IntegerField(null=False, default=0)
    imp_venue_wines = models.IntegerField(null=False, default=0)

    # HOME: number of taps on venue screen slide 30 - Combined-Sig.pdf
    # (no. taps establishment got on app)
    tap_venue_total = models.IntegerField(null=False, default=0)
    tap_venue_website = models.IntegerField(null=False, default=0)
    tap_venue_direction = models.IntegerField(null=False, default=0)
    tap_venue_phone = models.IntegerField(null=False, default=0)
    tap_venue_opening = models.IntegerField(null=False, default=0)

    # HOME: from where users are coming to your venue's screen (taps)
    # slide 31 - Combined-Sig.pdf
    tap_from_total = models.IntegerField(null=False, default=0)
    tap_from_venues_nearby = models.IntegerField(null=False, default=0)
    tap_from_food = models.IntegerField(null=False, default=0)
    tap_from_wines = models.IntegerField(null=False, default=0)
    tap_from_map = models.IntegerField(null=False, default=0)

    class Meta:
        unique_together = [['place', 'year', 'month']]


class UserNotification(models.Model):
    objects = models.Manager()
    active = ArchivingManager()

    # record data:
    created_time = models.DateTimeField(default=datetime.now)
    modified_time = models.DateTimeField(default=datetime.now)
    status = models.IntegerField(
        null=False, default=StatusE.DRAFT, choices=StatusE.pairs
    )
    is_archived = models.BooleanField(default=False, null=False)

    # main data fields:
    type = models.IntegerField(choices=PushNotifyTypeE.pairs, null=False)
    contents = models.TextField(null=True)

    post = models.ForeignKey('Post', null=True, on_delete=models.CASCADE)
    wine_name = models.CharField(null=True, max_length=255)
    start_comment_post = models.IntegerField(null=True)

    place = models.ForeignKey('Place', null=True, on_delete=models.CASCADE)
    place_name = models.CharField(null=True, max_length=255)

    wm = models.ForeignKey('Winemaker', null=True, on_delete=models.CASCADE)
    wm_name = models.CharField(null=True, max_length=255)

    start_comment_place = models.IntegerField(null=True)

    # user here is an author of a subject of a notification.
    # it is possible to be the same as user_dest.
    user = models.ForeignKey(
        'UserProfile', related_name='user_notification_user',
        on_delete=models.CASCADE
    )
    # user_dest is an addressee for the notification.
    # it is possible to be the same with user.
    user_dest = models.ForeignKey(
        'UserProfile', related_name='user_notification_user_dest',
        on_delete=models.CASCADE
    )
    # notification subject author's name
    user_name = models.CharField(null=True, max_length=255)

    @property
    def place_name_property(self):
        return self.place.name if self.place else None

    @property
    def place_main_image(self):
        return self.place.main_image if self.place else None

    get_parent_item = get_parent_item_fn
    get_parent_item_type = get_parent_item_type_fn

    archive = archive_fn


class DrankItToo(models.Model):
    objects = models.Manager()
    active = ArchivingManager()

    # record data:
    created_time = models.DateTimeField(default=datetime.now)
    modified_time = models.DateTimeField(default=datetime.now)
    # noqa status = models.IntegerField(null=False)  # StatusE.xxxx (published, draft)
    is_archived = models.BooleanField(default=False, null=False)

    # relations:
    author = models.ForeignKey(
        'UserProfile', related_name='drank_it_toos_authored',
        on_delete=models.CASCADE
    )
    post = models.ForeignKey('Post', related_name='drank_it_toos',
                             on_delete=models.CASCADE)
    wine = models.ForeignKey('Wine', null=True,
                             related_name='drank_it_toos',
                             on_delete=models.CASCADE)

    def get_parent_item(self):
        return self.post

    def get_parent_item_type(self):
        return ParentItemTypeE.POST

    def save(self, *args, **kwargs):
        self.modified_time = datetime.now()
        self.wine = self.post.wine
        super(DrankItToo, self).save(*args, **kwargs)
        if not self.is_archived:
            SenderNotifier().send_drank_it_too_on_winepost(self)

    # deprecated method
    def get_wine_kind(self):
        is_archived = self.post.is_archived

        return PostStatusE.DELETED if is_archived else self.post.status

    archive = archive_fn


# --------------- message (email/sms) ----------------------------------------
class SysMessage(models.Model):
    message_type = models.IntegerField(
        null=False, choices=SysMessageTypeE.pairs
    )
    to_address = models.CharField(null=False, max_length=255)
    to_name = models.CharField(null=True, max_length=255)

    from_address = models.CharField(null=False, max_length=255)
    from_name = models.CharField(null=True, max_length=255)

    title = models.CharField(null=True, max_length=255)
    content = models.TextField(null=False)

    send_attempts_number = models.IntegerField(null=False, default=0)
    last_attempt_date = models.DateTimeField(null=True)

    created_time = models.DateTimeField(default=datetime.now, null=False)
    modified_time = models.DateTimeField(default=datetime.now, null=True)

    status = models.IntegerField(null=False, choices=SysMessageStatusE.pairs)

    def __str__(self):
        return 'To: "%s" <%s> Title: %s' % (
            self.to_name, self.to_address, self.title
        )

# ---------------- event models -----------------------------------------------


# calendar event
class CalEvent(models.Model):
    objects = models.Manager()
    active = ArchivingManager()

    ordering = models.IntegerField(null=False, default=1)
    # - for most events this will be admin-profile or some new profile,
    # true authors are outside Raisin CMS, they are
    # defined in the Raisin WordPress and will be stored here as
    # external_author_name (nickname) and external_author_id (ID)
    author = models.ForeignKey('UserProfile', null=True,
                               on_delete=models.SET(get_erased_user_uid()))
    last_modifier = models.ForeignKey(
        'UserProfile', null=True, related_name='cal_event_last_modifier',
        on_delete=models.SET_NULL
    )

    import_time = models.DateTimeField(default=datetime.now, null=True)
    # import_time_2 = models.DateTimeField(default=datetime.now, null=True)
    created_time = models.DateTimeField(default=datetime.now)
    modified_time = models.DateTimeField(default=datetime.now)
    is_archived = models.BooleanField(default=False)
    status = models.IntegerField(null=False)
    type = models.IntegerField(
        choices=CalEventTypeE.pairs, null=True, default=None
    )

    # main data fields
    lang = models.CharField(blank=True, null=True, max_length=2)
    external_id = models.CharField(blank=True, null=True, max_length=255)
    external_author_name = models.CharField(max_length=255, null=True)
    external_author_id = models.CharField(null=True, max_length=255)
    external_url = models.TextField(null=True)
    external_image_url = models.TextField(null=True)
    external_created_time = models.DateTimeField(
        default=datetime.now, null=True
    )
    external_modified_time = models.DateTimeField(
        default=datetime.now, null=True
    )
    external_cal_id = models.TextField(blank=True, null=True)
    external_cal_title = models.TextField(blank=True, null=True)
    external_cal_desc = models.TextField(blank=True, null=True)
    external_submitter_email = models.EmailField(blank=True, null=True)

    thumb_file = models.CharField(max_length=255, null=True)
    image_width = models.IntegerField(null=True)
    image_height = models.IntegerField(null=True)

    title = models.TextField(null=True)
    description = models.TextField(null=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    price = models.CharField(max_length=255, null=True)
    is_pro = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_raisin_participating = models.BooleanField(default=False)
    use_external_link = models.BooleanField(default=False)

    wine_faire_url = models.TextField(null=True, blank=True)
    tickets_url = models.TextField(null=True, blank=True)

    loc_name = models.TextField(max_length=255, null=True, blank=True)
    loc_external_id = models.TextField(max_length=255, null=True)
    loc_lat = models.FloatField(default=0, null=True)
    loc_lng = models.FloatField(default=0, null=True)

    loc_full_street_address = models.TextField(null=True, blank=True)
    loc_street_address = models.TextField(null=True, blank=True)
    loc_house_number = models.CharField(max_length=10, null=True, blank=True)
    loc_zip_code = models.CharField(max_length=255, null=True, blank=True)
    loc_city = models.CharField(max_length=128, null=True, blank=True)
    loc_country = models.CharField(max_length=128, null=True, blank=True)
    loc_state = models.CharField(max_length=128, null=True, blank=True)
    loc_country_iso_code = CountryField(
        null=True, blank=True, blank_label='(select country)'
    )

    poster_image_file = models.ImageField(
        null=True, upload_to=update_event_poster_filename, blank=True
    )
    gif_image_file = models.ImageField(
        null=True, upload_to=update_event_gif_filename, blank=True
    )
    image = models.ForeignKey(
        'EventImage', related_name='image', blank=True, null=True,
        on_delete=models.CASCADE
    )
    validated_at = models.DateTimeField(null=True)
    published_at = models.DateTimeField(null=True)
    validated_by = models.ForeignKey(
        'UserProfile', null=True, related_name='event_validated_by',
        on_delete=models.SET_NULL
    )

    comment_number = models.IntegerField(default=0)  # ToDo: computable field
    likevote_number = models.IntegerField(default=0)  # ToDo: computable field

    def debug_save(self):
        super().save()

    def strip_fields(self, field_names):
        for field in field_names:
            if field in self.__dict__ and self.__dict__[field]:
                self.__dict__[field] = self.__dict__[field].strip()

    def save(self, *args, **kwargs):
        self.strip_fields([
            'title', 'description', 'loc_name', 'loc_external_id',
            'loc_street_address', 'loc_full_street_address',
            'loc_house_number', 'external_url', 'external_image_url',
            'external_id', 'external_author_id', 'external_author_name'
        ])

        self.modified_time = datetime.now()
        super().save()

    def publish(
        self, is_new=False, is_sticky=False, msg=None,
        validated_by=None, modifier_user=None
    ):
        self.status = PostStatusE.PUBLISHED
        self.save()
        self.refresh_from_db()
        if not validated_by and modifier_user:
            validated_by = modifier_user
        elif validated_by and not modifier_user:
            modifier_user = validated_by

        if not self.validated_at and not self.validated_by and validated_by:
            self.validated_at = datetime.now()
            self.validated_by = validated_by

        self.save(modifier_user=modifier_user, published_at=datetime.now())
        self.refresh_from_db()

    def unpublish(self, modifier_user=None):
        self.status = PostStatusE.DRAFT
        self.delete_related_items()
        self.save(modifier_user=modifier_user)

    def refuse(self, modifier_user=None):
        status = PostStatusE.REFUSED
        self.delete_related_items()
        self.status = status
        self.save(modifier_user=modifier_user)
        self.refresh_from_db()

    def get_main_image(self):
        return self.external_image_url if self.external_image_url else None

    @property
    def main_image_url(self):
        return aws_url(self.image, thumb=True)

    def archive(self, modifier_user=None):
        archive_fn(self)

        self.delete_related_items()

        attendees = self.attendees.filter(is_archived=False)
        for attendee in attendees:
            attendee.archive()

    def delete_related_items(self):
        likes = self.like_votes.filter(is_archived=False)
        for like in likes:
            like.archive()

        comments = self.comments.filter(is_archived=False)
        for comment in comments:
            comment.archive()

    def unarchive(self, modifier_user=None):
        self.is_archived = False
        self.save()
        self.refresh_from_db()

    def __str__(self):
        return self.title

    def __repr__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('edit_event', kwargs={'id': self.id})

    @property
    def absolute_url(self):
        return self.get_absolute_url()


class GotFreeGlass(models.Model):
    class Meta:
        unique_together = ('author', 'place',)

    objects = models.Manager()
    active = ArchivingManager()

    # - for most events this will be admin-profile or some new profile,
    # true authors are outside Raisin CMS, they are
    # defined in the Raisin WordPress and will be stored here as
    # external_author_name (nickname) and external_author_id (ID)
    author = models.ForeignKey('UserProfile', on_delete=models.CASCADE)
    place = models.ForeignKey(
        'Place', null=True, related_name='got_free_glass_objects',
        on_delete=models.CASCADE
    )

    created_time = models.DateTimeField(default=datetime.now)
    modified_time = models.DateTimeField(default=datetime.now)
    is_archived = models.BooleanField(default=False)

    def debug_save(self):
        super().save()

    def save(self, *args, **kwargs):
        self.modified_time = datetime.now()
        super().save()

    def archive(self, modifier_user=None):
        archive_fn(self)

    def unarchive(self, modifier_user=None):
        self.is_archived = False
        self.save()
        self.refresh_from_db()

    def __str__(self):
        return "@%s - %s" % (self.author.username, self.place.name)

    def __repr__(self):
        return "@%s - %s" % (self.author.username, self.place.name)


class GetMyFreeGlass(models.Model):
    objects = models.Manager()
    active = ArchivingManager()

    # - for most events this will be admin-profile or some new profile,
    # true authors are outside Raisin CMS, they are defined in the Raisin
    # WordPress and will be stored here as external_author_name (nickname)
    # and external_author_id (ID)
    author = models.ForeignKey('UserProfile', on_delete=models.CASCADE)
    place = models.ForeignKey(
        'Place', null=True, related_name="get_free_glass_objects",
        on_delete=models.CASCADE
    )

    created_time = models.DateTimeField(default=datetime.now)
    modified_time = models.DateTimeField(default=datetime.now)
    is_archived = models.BooleanField(default=False)

    @property
    def place_name_property(self):
        return self.place.name if self.place else None

    def debug_save(self):
        super().save()

    def save(self, *args, **kwargs):
        self.modified_time = datetime.now()
        super().save()

    def archive(self, modifier_user=None):
        archive_fn(self)

    def unarchive(self, modifier_user=None):
        self.is_archived = False
        self.save()
        self.refresh_from_db()

    def __str__(self):
        return "@%s - %s" % (self.author.username, self.place.name)

    def __repr__(self):
        return "@%s - %s" % (self.author.username, self.place.name)


class DonationReceipt(models.Model):
    objects = models.Manager()
    active = ArchivingManager()

    # - for most events this will be admin-profile or some new profile,
    # true authors are outside Raisin CMS, they are defined in the Raisin
    # WordPress and will be stored here as external_author_name (nickname)
    # and external_author_id (ID)
    author = models.ForeignKey('UserProfile', on_delete=models.CASCADE)

    created_time = models.DateTimeField(default=datetime.now)
    modified_time = models.DateTimeField(default=datetime.now)
    is_archived = models.BooleanField(default=False)
    app_os = models.CharField(max_length=10, null=True)

    receipt_data = models.TextField(null=True)
    provider_response = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )

    is_sandbox = models.BooleanField(default=False)

    status = models.IntegerField(
        null=True, choices=DonationReceiptStatusE.pairs
    )

    def debug_save(self):
        super().save()

    def save(self, *args, **kwargs):
        self.modified_time = datetime.now()
        super().save()

    def archive(self, modifier_user=None):
        archive_fn(self)

    def unarchive(self, modifier_user=None):
        self.is_archived = False
        self.save()
        self.refresh_from_db()

    def __str__(self):
        return self.id

    def __repr__(self):
        return self.id


class Donation(models.Model):
    objects = models.Manager()
    active = ArchivingManager()

    # - for most events this will be admin-profile or some new profile,
    # true authors are outside Raisin CMS, they are defined in the Raisin
    # WordPress and will be stored here as external_author_name (nickname)
    # and external_author_id (ID)
    author = models.ForeignKey('UserProfile', related_name='donations',
                               on_delete=models.CASCADE)
    receipt = models.ForeignKey('DonationReceipt', on_delete=models.CASCADE)

    created_time = models.DateTimeField(default=datetime.now)
    modified_time = models.DateTimeField(default=datetime.now)
    is_archived = models.BooleanField(default=False)
    app_os = models.CharField(max_length=10, null=True)

    product_id = models.TextField(null=True)
    transaction_id = models.TextField(null=True)
    # receipt_data = models.TextField(null=True)

    is_sandbox = models.BooleanField(default=False)
    date_from = models.DateTimeField(null=True)
    date_to = models.DateTimeField(null=True)

    frequency = models.IntegerField(
        null=True, choices=DonationFrequencyE.pairs
    )
    status = models.IntegerField(null=True, choices=DonationStatusE.pairs)

    value = models.FloatField(null=True)
    qty = models.IntegerField(null=True)
    currency = models.CharField(max_length=3, null=True)
    resp_item_json = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )
    extra_json = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )

    def debug_save(self):
        super().save()

    def save(self, *args, **kwargs):
        self.modified_time = datetime.now()
        super().save()

    def archive(self, modifier_user=None):
        archive_fn(self)

    def unarchive(self, modifier_user=None):
        self.is_archived = False
        self.save()
        self.refresh_from_db()

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return str(self.id)


class FreeGlassEvent(models.Model):
    objects = models.Manager()
    active = ArchivingManager()

    # - for most events this will be admin-profile or some new profile,
    # true authors are outside Raisin CMS, they are defined in the Raisin
    # WordPress and will be stored here as external_author_name (nickname)
    # and external_author_id (ID)
    author = models.ForeignKey('UserProfile', on_delete=models.CASCADE)
    created_time = models.DateTimeField(default=datetime.now)
    modified_time = models.DateTimeField(default=datetime.now)
    is_archived = models.BooleanField(default=False)

    name = models.CharField(max_length=255, null=True)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    map_fullscreen_end_date = models.DateTimeField(null=True)
    announcement_date = models.DateTimeField(null=True)

    def debug_save(self):
        super().save()

    def save(self, *args, **kwargs):
        self.modified_time = datetime.now()
        super().save()

    def archive(self, modifier_user=None):
        archive_fn(self)

    def unarchive(self, modifier_user=None):
        self.is_archived = False
        self.save()
        self.refresh_from_db()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class TimeLineItem(models.Model):
    active = ArchivingManager()

    author = models.ForeignKey(
        "UserProfile", related_name="timeline_item_author", null=False,
        on_delete=models.SET(get_erased_user_uid())
    )
    created_time = models.DateTimeField(default=datetime.now, null=False)
    modified_time = models.DateTimeField(default=datetime.now, null=True)
    is_archived = models.BooleanField(default=False, null=False)
    is_sticky = models.BooleanField(default=False)

    user_item = models.ForeignKey("UserProfile", null=True,
                                  on_delete=models.SET_NULL)
    post_item = models.ForeignKey("Post", null=True, on_delete=models.CASCADE)
    place_item = models.ForeignKey("Place", null=True,
                                   on_delete=models.CASCADE)

    item_description = models.TextField(null=True, blank=True)
    cached_item = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )
    item_type = models.IntegerField(
        choices=TimeLineItemTypeE.pairs, null=False, default=None
    )

    archive = archive_fn

    def get_item(self):
        if self.item_type == TimeLineItemTypeE.POST:
            return self.post_item
        if self.item_type == TimeLineItemTypeE.PLACE:
            return self.place_item
        if self.item_type == TimeLineItemTypeE.USER:
            return self.user_item

    def get_cached_item(self):
        if not self.cached_item:
            return None

        if self.item_type == TimeLineItemTypeE.POST:
            return Post.active.get(id=self.cached_item['id'])
        # elif self.item_type == TimeLineItemTypeE.PLACE:
        #     return Place.active.get(id=self.cached_item['id'])
        # elif self.item_type == TimeLineItemTypeE.USER:
        #     return UserProfile.active.get(id=self.cached_item['id'])
        else:
            return None

    def get_cached_item_type_as_parent_item_type(self):
        if self.item_type == TimeLineItemTypeE.POST:
            return ParentItemTypeE.POST
        # elif self.item_type == TimeLineItemTypeE.PLACE:
        #     return ParentItemTypeE.PLACE
        # elif self.item_type == TimeLineItemTypeE.USER:
        #     return ParentItemTypeE.USER
        else:
            return None


class Setting(models.Model):
    # there is NO "id" column here, "key" plays the role of the
    # primary key and it contains an arbitrary value.
    key = models.IntegerField(
        null=False, blank=False, unique=True, primary_key=True
    )
    int_value = models.IntegerField(null=True)
    text_value = models.TextField(null=True)
    float_value = models.FloatField(null=True)
    type = models.IntegerField(null=False)


class ApiUserStorage(models.Model):
    user = models.ForeignKey(
        "UserProfile", related_name="api_storage_user", null=False,
        on_delete=models.CASCADE
    )
    token = models.TextField(null=False, unique=True)
    created_time = models.DateTimeField(default=datetime.now, null=False)
    modified_time = models.DateTimeField(default=datetime.now, null=True)
    stored_data = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )


class CmsAdminComment(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               db_index=True,
                               on_delete=models.SET(get_erased_user_uid()))
    content = models.TextField()

    class Meta:
        ordering = ('-created',)
        index_together = [
            ['content_type', 'object_id']
        ]


class Like(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               db_index=True,
                               on_delete=models.CASCADE)

    class Meta:
        ordering = ('-created',)
        index_together = [
            ['content_type', 'object_id']
        ]


class FormitableRequest(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    request_data = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )
    place = models.ForeignKey(Place, null=True, blank=True,
                              on_delete=models.SET_NULL)

    class Meta:
        ordering = ('created_date', )


def validate_word_caseinsensitive(value):
    if NWLAExcludedWord.objects.filter(word__iexact=value).exists():
        raise ValidationError('This WORD already exists.')
    return value


class NWLAExcludedWord(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               null=True,
                               on_delete=models.SET_NULL)
    created_date = models.DateTimeField(auto_now_add=True)
    word = models.CharField(unique=True,
                            max_length=255,
                            null=False,
                            blank=False,
                            validators=[validate_word_caseinsensitive])

    class Meta:
        ordering = ('word', )
