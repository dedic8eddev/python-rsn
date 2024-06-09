import datetime as dt
import logging

from web.constants import PostTypeE
from web.models import Post, Wine

log = logging.getLogger(__name__)


def remove_vuforia_image_for_wine(wine_id):
    wine = Wine.objects.get(id=wine_id)
    if not wine.ref_image:
        return

    vuf_image = wine.ref_image
    posts = Post.objects.filter(ref_image=vuf_image)
    if posts:
        for post in posts:
            post.ref_image = None
            post.debug_save()
            post.refresh_from_db()

    wines = Wine.objects.filter(ref_image=vuf_image)
    if wines:
        for wine in wines:
            wine.ref_image = None
            wine.debug_save()
            wine.refresh_from_db()


def set_other_posts_as_non_parents(wine, post):
    other_posts = Post.active.filter(wine=wine).exclude(id=post.id)
    for other_post in other_posts:
        other_post.is_parent_post = False
        other_post.save()
        other_post.refresh_from_db()


def set_yearly_data_from_parent_post(winepost, parent_post):
    # vintage (year) was defined in winepost - use it
    if winepost.wine_year:
        year = winepost.wine_year
    # vintage (year) was not defined in wine post,
    # but it was defined in new parent post - use the one from the new pp
    elif parent_post.wine_year:
        year = parent_post.wine_year
        winepost.wine_year = parent_post.wine_year
    # year was not defined either in winepost or
    # in new parent post - set the yearly data from parent post and FINISH
    else:
        winepost.grape_variety = parent_post.grape_variety
        winepost.free_so2 = parent_post.free_so2
        winepost.total_so2 = parent_post.total_so2
        return

    # year was set - do things for it

    w_year = None
    # yearly data was defined in parent post and
    # year (int) is in parent post - use it
    if parent_post.yearly_data and int(year) in parent_post.yearly_data:
        w_year = int(year)
    # yearly data was defined in parent post and
    # year (str) is in parent post - use it
    elif parent_post.yearly_data and str(year) in parent_post.yearly_data:
        w_year = str(year)
    else:  # noqa yearly data was not defined or year is not in it - add the new vintage to the yearly data
        w_year = str(year)
        log.debug(
            "set_yearly_data_from_parent_post - parent post ID %s winepost ID %s " % (  # noqa
                winepost.id if winepost else '--',
                parent_post.id if parent_post else ''
            )
        )
        if not parent_post.yearly_data:
            parent_post.yearly_data = {}

        parent_post.yearly_data[year] = {
            'grape_variety': winepost.grape_variety,
            'free_so2': winepost.free_so2,
            'total_so2': winepost.total_so2,
        }
        parent_post.debug_save()
        parent_post.refresh_from_db()

    w_yd = parent_post.yearly_data[w_year]
    winepost.grape_variety = w_yd['grape_variety']
    winepost.free_so2 = w_yd['free_so2']
    winepost.total_so2 = w_yd['total_so2']


def define_as_children_obj(winepost, new_parent_post_id, user):
    old_wine = winepost.wine
    old_winemaker = old_wine.winemaker
    # the new parent post for the winepost to be moved
    new_parent_post = Post.objects.get(
        id=new_parent_post_id, type=PostTypeE.WINE
    )

    # if the winepost-to-be-moved has is_parent_post=true
    # (eg. it was DRAFT when is_parent_post was set and not
    # visible, ie. the first DRAFT post of a new wine or a
    # visible PUBLISHED PARENT POST), we set the flag
    # is_parent_post to FALSE, SAVE and REFRESH the post
    if winepost.is_parent_post:
        winepost.is_parent_post = False
        winepost.save()
        winepost.refresh_from_db()
        # we are moving other posts from the old_wine - they are being moved
        # along with their parent post to a new wine
        other_posts = Post.active.filter(
            wine=old_wine, type=PostTypeE.WINE
        ).exclude(id=winepost.id)
        for other_post in other_posts:
            other_post.wine = new_parent_post.wine
            other_post.is_parent_post = False
            set_yearly_data_from_parent_post(other_post, new_parent_post)
            other_post.save()
            other_post.refresh_from_db()

    # doing the same as above for
    # OLD WINEMAKER - if there are no non-archived posts, then archive the
    # winemaker as well.
    posts_for_old_winemaker = Post.active.filter(wine__winemaker=old_winemaker)
    if not posts_for_old_winemaker:
        old_winemaker.archive()
        old_winemaker.refresh_from_db()

    # finally, we set the new wine for winepost-to-be-moved, thus moving it
    winepost.wine = new_parent_post.wine
    winepost.status = new_parent_post.status
    winepost.set_title_winepost()

    set_yearly_data_from_parent_post(winepost, new_parent_post)
    winepost.expert = user
    winepost.last_modifier = user
    winepost.modified_time = dt.datetime.now()
    winepost.save()
    winepost.refresh_from_db()
    winepost.wine.refresh_from_db()

    # checking whether some other posts for the old wine exist.
    # If not, the old_wine will be archived, in order to prevent the
    # "orphaned" wines being listed: set them as ARCHIVED (is_archived = true)
    # if there are no more ACTIVE (is_archived=false) posts for it
    # (if all posts for it are archived, it should be archived, too)
    posts_for_old_wine = Post.active.filter(
        wine=old_wine
    ).exclude(id=winepost.id)

    if not posts_for_old_wine:
        log.info(
            "NO MORE POSTS FOR OLD WINE %s (ID: %s) - ARCHIVING THE WINE" % (
                old_wine.id, old_wine.name
            )
        )
        remove_vuforia_image_for_wine(old_wine.id)
        old_wine.archive()
        old_wine.refresh_from_db()
    winepost.ref_image = new_parent_post.ref_image if not winepost.ref_image else winepost.ref_image
    winepost.save()
    return new_parent_post_id
