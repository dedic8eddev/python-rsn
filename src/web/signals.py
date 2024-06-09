from django.core.cache import cache
from django.db.models.signals import post_delete, pre_save, post_save,\
    pre_delete
from django.db.models import Q
from django.dispatch import receiver
from web.constants import ParentItemTypeE, PostTypeE, PLACE_GEO_CACHE_KEY, \
    UserTypeE
from web.models import (Comment, DrankItToo, LikeVote, Place, PlaceImage,
                        PostImage, FormitableRequest, UserProfile, Winemaker, Wine, Post)
import logging
from cities.osm import get_osm_address
from cities.models import District
from web.utils.slugs import unique_slug_generator
from news.models import Quote, FeaturedVenue, WebsitePage, News, LPB, Testimonial, Cheffe


log = logging.getLogger(__name__)


def clear_place_cache(id):
    """
    Clear cached place if any

    :param id: The place id.
    """
    place_cache_key = PLACE_GEO_CACHE_KEY.format(str(id))
    cached_value = cache.get(place_cache_key)
    if cached_value:
        cache.delete(place_cache_key)
        log.info(f"Cache deleted '{place_cache_key}' for the place with id={str(id)}.")


def update_dit_number(instance):
    parent_item = instance.get_parent_item()
    parent_item.drank_it_too_number = parent_item.drank_it_toos.filter(
        is_archived=False
    ).count()
    parent_item.save(update_fields=["drank_it_too_number"])

    if (
        instance.get_parent_item_type() == ParentItemTypeE.POST and
        parent_item.type == PostTypeE.WINE
    ):
        wine = parent_item.wine
        if wine:
            wine.drank_it_too_number = DrankItToo.active.filter(
                post__wine=wine
            ).count()
            wine.save(update_fields=["drank_it_too_number"])

            winemaker = wine.winemaker
            if winemaker:
                winemaker.drank_it_too_number = DrankItToo.active.filter(
                    post__wine__winemaker=winemaker
                ).count()
                winemaker.save(update_fields=["drank_it_too_number"])

    user = instance.author
    user.drank_it_too_number = user.drank_it_toos_authored.filter(
        is_archived=False
    ).count()
    user.save(update_fields=["drank_it_too_number"])


def update_likevote_number(instance):
    parent_item = instance.get_parent_item()
    parent_item.likevote_number = parent_item.like_votes.filter(
        is_archived=False
    ).count()
    parent_item.save(update_fields=["likevote_number"])

    if (
        instance.get_parent_item_type() == ParentItemTypeE.POST and
        parent_item.type == PostTypeE.WINE
    ):
        wine = parent_item.wine
        if wine:
            wine.likevote_number = LikeVote.active.filter(
                post__wine=wine
            ).count()
            wine.save(update_fields=["likevote_number"])

            winemaker = wine.winemaker
            if winemaker:
                winemaker.likevote_number = LikeVote.active.filter(
                    post__wine__winemaker=winemaker
                ).count()
                winemaker.save(update_fields=["likevote_number"])

    user = instance.author
    user.likevote_number = user.like_votes_authored.filter(
        is_archived=False
    ).count()
    user.save(update_fields=["likevote_number"])


def update_comment_number(instance):
    parent_item = instance.get_parent_item()
    parent_item.comment_number = parent_item.comments.filter(
        is_archived=False
    ).count()
    parent_item.save(update_fields=["comment_number"])
    if (
        instance.get_parent_item_type() == ParentItemTypeE.POST and
        parent_item.type == PostTypeE.WINE
    ):
        wine = parent_item.wine
        if wine:
            wine.comment_number = Comment.active.filter(
                post__wine=wine
            ).count()
            wine.save(update_fields=["comment_number"])

            winemaker = wine.winemaker
            if winemaker:
                winemaker.comment_number = Comment.active.filter(
                    post__wine__winemaker=winemaker
                ).count()
                winemaker.save(update_fields=["comment_number"])
    user = instance.author
    user.comment_number = user.comments_authored.filter(
        is_archived=False
    ).count()
    user.save(update_fields=["comment_number"])


@receiver(post_save, sender=Comment)
def create_update_comment(sender, instance, **kwargs):
    update_comment_number(instance)
    if instance.get_parent_item_type == ParentItemTypeE.PLACE:
        clear_place_cache(instance.get_parent_item().id)


@receiver(post_delete, sender=Comment)
def delete_comment(sender, instance, **kwargs):
    update_comment_number(instance)
    if instance.get_parent_item_type == ParentItemTypeE.PLACE:
        clear_place_cache(instance.get_parent_item().id)


@receiver(post_save, sender=LikeVote)
def create_update_likevote(sender, instance, **kwargs):
    update_likevote_number(instance)
    if instance.get_parent_item_type == ParentItemTypeE.PLACE:
        clear_place_cache(instance.get_parent_item().id)


@receiver(post_delete, sender=LikeVote)
def delete_likevote(sender, instance, **kwargs):
    update_likevote_number(instance)
    if instance.get_parent_item_type == ParentItemTypeE.PLACE:
        clear_place_cache(instance.get_parent_item().id)


@receiver(post_save, sender=DrankItToo)
def create_update_dit(sender, instance, **kwargs):
    update_dit_number(instance)


@receiver(post_delete, sender=DrankItToo)
def delete_dit(sender, instance, **kwargs):
    update_dit_number(instance)


@receiver(post_save, sender=Place)
def save_post(sender, instance, **kwargs):
    clear_place_cache(instance.id)


@receiver(pre_delete, sender=Place)
def delete_post(sender, instance, **kwargs):
    clear_place_cache(instance.id)


@receiver(post_save, sender=PlaceImage)
def save_place_image(sender, instance, **kwargs):
    clear_place_cache(instance.place_id)


@receiver(post_delete, sender=PlaceImage)
def delete_place_imagee(sender, instance, **kwargs):
    clear_place_cache(instance.place_id)


@receiver(post_save, sender=PostImage)
def save_post_image(sender, instance, **kwargs):
    if instance.post and instance.post.place_id:
        clear_place_cache(instance.post.place_id)


@receiver(post_delete, sender=PostImage)
def delete_post_image(sender, instance, **kwargs):
    if instance.post and instance.post.place_id:
        clear_place_cache(instance.post.place_id)


@receiver(pre_save, sender=UserProfile)
def save_user(sender, instance, **kwargs):
    obj = None
    try:
        obj = sender.objects.get(id=instance.id)
    except UserProfile.DoesNotExist:
        pass
    if obj:
        if (
                obj.type == UserTypeE.OWNER and
                instance.type != UserTypeE.OWNER
        ):
            try:
                place = Place.active.get(owner=instance)
                place.owner = None
                place.subscription = None
                place.save()
            except Place.DoesNotExist:  # the case when the place
                # has already been deleted
                pass

            instance.customer = None


@receiver(post_save, sender=FormitableRequest)
def check_formitable_request(sender, instance, created, **kwargs):
    if created:
        formitable_data = instance.request_data
        if 'restaurant' in formitable_data:
            event = formitable_data.get('event', None)
            restaurant = formitable_data.get('restaurant', {})
            uid = restaurant.get('uid', '')
            if not uid:
                return
            if event == 'app.uninstalled':
                users = UserProfile.objects.filter(formitable_url__contains=uid)
                for user in users:
                    user.formitable_uid = uid
                    user.formitable_url = ''
                    user.save()
            elif event == 'app.installed':
                users = UserProfile.objects.filter(
                    Q(formitable_url__contains=uid) | Q(formitable_uid=uid)
                )
                user = None
                if not users.exists():
                    email = restaurant.get('email', '')
                    if email:
                        places = Place.objects.filter(email=email)
                        if places.exists():
                            place = places.first()
                            user = place.owner
                else:
                    user = users.first()
                if user:
                    user.formitable_uid = uid
                    user.formitable_url = 'https://widget.formitable.com/page/{}'.format(uid)
                    user.save()


@receiver(pre_save, sender=Place)
def link_district(sender, instance, **kwargs):
    if instance.new_city and instance.new_city.admin_level and instance.full_street_address and not instance.district:
        full_address = '{address}+{city}+{country}'.format(
            address=instance.full_street_address,
            city=instance.new_city.name,
            country=instance.new_city.country.name
        )
        address = get_osm_address(instance.new_city.admin_level, full_address)
        if address:
            location = instance.point
            name = address.get('localname')
            osm_id = address.get('osm_id')
            osm_place_id = address.get('place_id')
            district = District.objects.filter_with_deleted(osm_id=osm_id, osm_place_id=osm_place_id)
            if not district.exists():
                district = District(
                    city=instance.new_city,
                    location=location,
                    name=name,
                    name_std=name,
                    population=0,
                    osm_id=osm_id,
                    osm_place_id=osm_place_id,
                    deleted=False
                )
                district.save()
            else:
                district = district.first()
                if district.deleted:
                    district.deleted = False
                    district.save()
            instance.district = district
            # instance.save()


@receiver(pre_save, sender=Place)
@receiver(pre_save, sender=Quote)
@receiver(pre_save, sender=Cheffe)
@receiver(pre_save, sender=Testimonial)
@receiver(pre_save, sender=Winemaker)
@receiver(pre_save, sender=Wine)
@receiver(pre_save, sender=Post)
def generate_quote_slug_before_save(sender, instance, **kwargs):
    instance.slug = unique_slug_generator(instance=instance)


@receiver(pre_save, sender=FeaturedVenue)
@receiver(pre_save, sender=WebsitePage)
@receiver(pre_save, sender=News)
@receiver(pre_save, sender=LPB)
def generate_slugs_before_save(sender, instance, **kwargs):
    instance.slug = unique_slug_generator(instance=instance)
    for i in ["en", "fr", "es", "ja", "it"]:
        setattr(instance, f"slug_{i}", unique_slug_generator(instance=instance, lang=i))
