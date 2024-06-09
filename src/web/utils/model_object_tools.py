import time
from web.constants import ParentItemTypeE


def archive_fn(self):
    self.is_archived = True
    self.save()


def archive_images_fn(parent_item, parent_item_field, ImageClass):
    if (
        ImageClass.__name__ == 'PlaceImage' and
        parent_item.__class__.__name__ == 'Place'
    ):
        images = ImageClass.active.filter(**{
            parent_item_field: parent_item,
            'image_area__isnull': True,
        })
    else:
        images = ImageClass.active.filter(**{parent_item_field: parent_item})
    if images:
        for image in images:
            image.archive()


def duplicate_fn(self, save=True):
    dup = self.__class__.active.get(id=self.pk)
    dup.pk = None
    if save:
        dup.save()
        dup.refresh_from_db()
    return dup


def duplicate_images_fn(self, target_parent_item, item_id_field='images'):
    new_images = []
    images = getattr(self, item_id_field).filter(is_archived=False).order_by('ordering')

    if not images:
        return []

    for image in images:
        new_image = image.duplicate(target_parent_item=target_parent_item)

        if new_image:
            new_images.append(new_image)

    target_parent_item.main_image = new_images[0] if new_images else None
    target_parent_item.save()

    return new_images


def get_parent_item_fn(self):
    if self.post:
        return self.post
    elif self.place:
        return self.place
    elif self.news:
        return self.news
    elif self.cal_event:
        return self.cal_event
    elif self.featured_venue:
        return self.featured_venue
    else:
        return None


def get_parent_item_type_fn(self):
    if self.post:
        return ParentItemTypeE.POST
    elif self.place:
        return ParentItemTypeE.PLACE
    elif self.cal_event:
        return ParentItemTypeE.CAL_EVENT
    else:
        return None


def author_has_badge_data(p_once_expiry_date_ms, p_monthly_expiry_date_ms):
    date_now_ms = int(round(time.time() * 1000))
    has_badge = False
    badge_expiry_date_ms = None
    dates_used = []

    if p_once_expiry_date_ms and p_once_expiry_date_ms + 86400000 > date_now_ms:  # noqa
        dates_used.append(p_once_expiry_date_ms + 86400000)

    if p_monthly_expiry_date_ms and p_monthly_expiry_date_ms + 86400000 > date_now_ms:  # noqa
        dates_used.append(p_monthly_expiry_date_ms + 86400000)

    if dates_used:
        has_badge = True
        dates_used.sort(reverse=True)
        badge_expiry_date_ms = dates_used[0]
    return has_badge, badge_expiry_date_ms
