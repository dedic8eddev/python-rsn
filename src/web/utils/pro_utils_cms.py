from web.constants import PlaceStatusE
from web.models import Place, Post


"""
PRO-related functions used in the CMS
"""


def update_owner_venue(user, place):
    if not place:
        _update_old_places_for_owner(user, place)
        return
    # we update place owner only if different than the selected user
    if not place.owner or place.owner != user:
        # updating "old" places only when there was a change
        _update_old_places_for_owner(user, place)
        place.owner = user
        place.status = PlaceStatusE.SUBSCRIBER \
            if place.status != PlaceStatusE.PUBLISHED else PlaceStatusE.PUBLISHED # noqa
        place.save()
        place.refresh_from_db()


# ToDo: should be reviewed since PlaceStatusE.SUBSCRIBER taken place
def _update_old_places_for_owner(owner, place):
    places_this_owner = Place.objects.filter(owner=owner)
    # we don't have to update this if the owner didn't change
    if not places_this_owner or (place and place.owner == owner):
        return

    places_this_owner.update(status=PlaceStatusE.PUBLISHED)

    for old_place_owner in places_this_owner:
        foods_and_wines = Post.objects.filter(
            venues__id=old_place_owner.id, author=owner
        )
        # moving foods and wines for all old venues for the user to new venue
        for post_x in foods_and_wines:
            post_x.venues__id = place.id if place else None
            post_x.save()
            post_x.refresh_from_db()

        old_place_owner.owner = None
        old_place_owner.save_keep_modified_dt()
        old_place_owner.refresh_from_db()

        # image_logo = old_place_owner.main_image
        # images = [image_logo] if image_logo else []
        # images_in = PlaceImage.active.filter(
        #     **{
        #         'place': old_place_owner,
        #         'image_area__gte': PlaceImageAreaE.FRONT,
        #         'image_area__lte': PlaceImageAreaE.TEAM,
        #     }).order_by('image_area', 'ordering')
        # for image in images_in:
        #     images.append(image)
        # for i, image in enumerate(images):
        #     old_ordering = image.ordering
        #     image.area_ordering = old_ordering
        #     image.ordering = i
        #     image.save()
        #     image.refresh_from_db()
