import logging
from datetime import datetime

from django.core.files.base import ContentFile
from django.db import models
from datetime import date
from web.models.models import ArchivingManager
from web.utils.filenames import (get_extension, get_vuforia_image_filename,
                                 update_filename)
from web.utils.model_object_tools import archive_fn
from web.utils.default_data import get_erased_user_uid
from web.utils.filenames import get_news_image_filename, get_event_image_filename
from django.template.defaultfilters import slugify
from web.constants import PostTypeE
from web.utils.filenames import get_max_id
from web.utils.slugs import detect_language_and_translate

log = logging.getLogger(__name__)


class AbstractImage(models.Model):
    objects = models.Manager()
    active = ArchivingManager()

    author = models.ForeignKey('UserProfile', null=True,
                               on_delete=models.SET(get_erased_user_uid()))
    created_time = models.DateTimeField(default=datetime.now, null=False)
    modified_time = models.DateTimeField(default=datetime.now, null=True)
    is_archived = models.BooleanField(default=False, null=False)

    ordering = models.IntegerField(null=True)

    width = models.IntegerField(null=True)
    height = models.IntegerField(null=True)

    image_file = models.ImageField(
        null=True, upload_to=update_filename, blank=False
    )
    real_name = models.CharField(max_length=255, null=True, blank=True)

    def archive(self):
        archive_fn(self)

    def unarchive(self, modifier_user=None):
        self.is_archived = False
        self.save()
        self.refresh_from_db()

    def duplicate(self, target_parent_item, extra_data={}, for_vuforia=False):
        target_parent_item_field_name = self.TARGET_PARENT_ITEM_FIELD_NAME
        image_class = self.__class__ if not for_vuforia else VuforiaImage

        img_data = {
            'author': self.author,
            'width': self.width,
            'height': self.height,
            'ordering': self.ordering,
            target_parent_item_field_name: target_parent_item
        }

        if extra_data:
            img_data.update(extra_data)

        dupl = image_class(**img_data)

        if image_class.__name__ == 'PlaceImage':
            # prefix image with new parent id
            current_parent = getattr(self, target_parent_item_field_name)
            new_file = ContentFile(self.image_file.read())
            new_file.name = self.image_file.name.replace(
                '{}---'.format(current_parent.id),
                '{}---'.format(target_parent_item.id)
            )
            new_file.content_type = 'image/{}'.format(
                get_extension(self.image_file.name)
            )
            dupl.image_file = new_file
        elif image_class.__name__ == 'VuforiaImage':
            ext = get_extension(self.image_file.name)
            new_file = ContentFile(self.image_file.read())
            new_file.name = get_vuforia_image_filename(
                target_parent_item.id,
                extra_data['post'].id,
                ext
            )
            new_file.content_type = 'image/{}'.format(ext)
            dupl.image_file = new_file
        else:
            dupl.image_file = self.image_file

        dupl.save()

        return dupl

    def __str__(self):
        return self.image_file.name


class WineImage(AbstractImage):
    SUB_PATH = 'wines/'
    TARGET_PARENT_ITEM_FIELD_NAME = 'wine'

    wine = models.ForeignKey('Wine', related_name='images',
                             on_delete=models.CASCADE)

    class Meta:
        db_table = "wine_image"

    @property
    def max_id(self):
        return get_max_id(WineImage)

    @property
    def slug(self):
        return slugify(self.wine.slug)


class VuforiaImage(AbstractImage):
    SUB_PATH = 'vuforia/'
    TARGET_PARENT_ITEM_FIELD_NAME = 'wine'
    wine = models.ForeignKey('Wine', related_name='vuforia_images',
                             on_delete=models.CASCADE)
    post = models.ForeignKey('Post', null=True,
                             related_name='vuforia_images',
                             on_delete=models.CASCADE)
    target_id = models.TextField(null=True, blank=True)
    rating_tracking = models.FloatField(null=True, blank=True)
    rating_reco = models.TextField(null=True, blank=True)
    is_dirty = models.BooleanField(default=False)
    update_rating = models.BooleanField(default=False)
    error = models.BooleanField(default=False)
    vuforia_deleted = models.BooleanField(default=False)
    delete_from_vuforia = models.BooleanField(default=False)
    for_child_post = models.BooleanField(default=False)

    class Meta:
        db_table = "vuforia_image"

    def get_name(self):
        return str(self.image_file).replace(
            'vuforia/', ''
        ) if self.image_file else None

    @property
    def max_id(self):
        return get_max_id(VuforiaImage)

    @property
    def slug(self):
        return "wine"


class WinemakerImage(AbstractImage):
    SUB_PATH = 'winemakers/'
    TARGET_PARENT_ITEM_FIELD_NAME = 'winemaker'

    winemaker = models.ForeignKey('Winemaker', related_name='images',
                                  on_delete=models.CASCADE)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._meta.get_field("image_file").upload_to = get_news_image_filename

    class Meta:
        db_table = "winemaker_image"

    @property
    def max_id(self):
        return get_max_id(WinemakerImage)

    @property
    def slug(self):
        return slugify(self.winemaker.slug)


class WinemakerFile(AbstractImage):
    SUB_PATH = 'wmfiles/'
    TARGET_PARENT_ITEM_FIELD_NAME = 'winemaker'

    winemaker = models.ForeignKey('Winemaker', related_name='files',
                                  on_delete=models.CASCADE)

    class Meta:
        db_table = "winemaker_file"

    @property
    def max_id(self):
        return get_max_id(WinemakerFile)

    @property
    def slug(self):
        return slugify(self.winemaker.slug)


class PostImage(AbstractImage):
    SUB_PATH = 'posts/'
    TARGET_PARENT_ITEM_FIELD_NAME = 'post'

    post = models.ForeignKey('Post', related_name='images',
                             on_delete=models.CASCADE)

    class Meta:
        db_table = "post_image"

    def debug_save(self):
        super().save()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._meta.get_field("image_file").upload_to = get_news_image_filename

    @property
    def max_id(self):
        return get_max_id(PostImage)

    @property
    def slug(self):
        if self.post.type == PostTypeE.WINE:
            w = self.post.wine
            string = f"{w.slug} "
            if w.domain:
                string += f"{detect_language_and_translate(w.domain)} "
            if w.winemaker:
                string += f"{w.winemaker.slug} "
            elif w.winemaker_name:
                string += f"{detect_language_and_translate(w.winemaker_name)} "
            if self.post.wine_year:
                string += f"{self.post.wine_year} "
            return slugify(string)
        else:
            return slugify(self.post.slug)


class EventImage(AbstractImage):
    SUB_PATH = 'events/'
    TARGET_PARENT_ITEM_FIELD_NAME = 'event'

    event = models.ForeignKey('CalEvent', related_name='images',
                              on_delete=models.CASCADE)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._meta.get_field("image_file").upload_to = get_event_image_filename

    class Meta:
        db_table = "event_image"

    @property
    def max_id(self):
        return get_max_id(EventImage)

    @property
    def slug(self):
        return f"{slugify(self.event.title)}-{self.event.id}-{str(date.today())}"


class PostFile(AbstractImage):
    SUB_PATH = 'postfiles/'
    TARGET_PARENT_ITEM_FIELD_NAME = 'post'

    post = models.ForeignKey('Post', related_name='files',
                             on_delete=models.CASCADE)

    class Meta:
        db_table = "post_file"

    @property
    def max_id(self):
        return get_max_id(PostFile)

    @property
    def slug(self):
        return slugify(self.post.slug)


class PlaceImage(AbstractImage):
    SUB_PATH = 'places/'
    TARGET_PARENT_ITEM_FIELD_NAME = 'place'

    place = models.ForeignKey('Place', related_name='place_images',
                              on_delete=models.CASCADE)

    image_area = models.IntegerField(null=True)
    area_ordering = models.IntegerField(null=True)

    class Meta:
        db_table = "place_image"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._meta.get_field("image_file").upload_to = get_news_image_filename

    @property
    def max_id(self):
        return get_max_id(PlaceImage)

    @property
    def slug(self):
        string = ""
        if self.place.is_bar:
            string += "bar "
        if self.place.is_restaurant:
            string += "restaurant "
        if self.place.is_wine_shop:
            string += "wineshop "
        string = slugify(string)
        return f"{string}-{self.place.slug}"


class UserImage(AbstractImage):
    SUB_PATH = 'users/'
    TARGET_PARENT_ITEM_FIELD_NAME = 'user'

    user = models.ForeignKey('UserProfile', related_name='images',
                             on_delete=models.CASCADE)

    class Meta:
        db_table = "user_image"

    @property
    def max_id(self):
        return get_max_id(UserImage)

    @property
    def slug(self):
        return slugify(self.user.username)
