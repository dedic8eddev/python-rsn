from django.db import models
from web.models.images import AbstractImage
from datetime import datetime
from .constants import NewsStatus
from web.utils.upload_tools import aws_url
from web.utils.default_data import get_erased_user_uid
from django.db.models import JSONField
from web.utils import json_handling
from web.utils.filenames import get_news_image_filename
from web.models.models import UniqueSlugModel
from web.models.images import get_max_id
from django.utils import timezone


class MultiLanguageTitleModel(models.Model):
    name = models.CharField(max_length=200, verbose_name="name", blank=True)
    slug_en = models.SlugField(blank=True, max_length=255, null=True, unique=True)
    slug_fr = models.SlugField(blank=True, max_length=255, null=True, unique=True)
    slug_ja = models.SlugField(blank=True, max_length=255, null=True, unique=True)
    slug_it = models.SlugField(blank=True, max_length=255, null=True, unique=True)
    slug_es = models.SlugField(blank=True, max_length=255, null=True, unique=True)
    title_en = models.CharField(max_length=200, verbose_name="title EN", blank=True)
    title_fr = models.CharField(max_length=200, verbose_name="title FR", blank=True)
    title_ja = models.CharField(max_length=200, verbose_name="title JA", blank=True)
    title_it = models.CharField(max_length=200, verbose_name="title IT", blank=True)
    title_es = models.CharField(max_length=200, verbose_name="title ES", blank=True)
    meta_description_en = models.TextField(blank=True)
    meta_description_fr = models.TextField(blank=True)
    meta_description_ja = models.TextField(blank=True)
    meta_description_it = models.TextField(blank=True)
    meta_description_es = models.TextField(blank=True)
    content_en = models.TextField(blank=True)
    content_fr = models.TextField(blank=True)
    content_ja = models.TextField(blank=True)
    content_it = models.TextField(blank=True)
    content_es = models.TextField(blank=True)
    status_en = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)
    status_fr = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)
    status_ja = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)
    status_it = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)
    status_es = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)

    class Meta:
        abstract = True


class NewsImage(AbstractImage):
    SUB_PATH = 'news/'
    TARGET_PARENT_ITEM_FIELD_NAME = 'news'
    event = models.ForeignKey('News', related_name='images', on_delete=models.CASCADE)

    class Meta:
        db_table = "news_image"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._meta.get_field("image_file").upload_to = get_news_image_filename

    @property
    def max_id(self):
        return get_max_id(NewsImage)

    @property
    def slug(self):
        return self.event.slug


class FeaturedVenueImage(AbstractImage):
    SUB_PATH = 'featured-venue/'
    TARGET_PARENT_ITEM_FIELD_NAME = 'featured_venue'
    featured_venue = models.ForeignKey('FeaturedVenue', related_name='images', on_delete=models.CASCADE)

    class Meta:
        db_table = "featured_venue_image"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._meta.get_field("image_file").upload_to = get_news_image_filename

    @property
    def max_id(self):
        return get_max_id(FeaturedVenueImage)

    @property
    def slug(self):
        return self.featured_venue.slug


class LPBImage(AbstractImage):
    SUB_PATH = 'events/'
    TARGET_PARENT_ITEM_FIELD_NAME = 'lpb'

    event = models.ForeignKey('LPB', related_name='images', on_delete=models.CASCADE)

    class Meta:
        db_table = "lpb_image"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._meta.get_field("image_file").upload_to = get_news_image_filename

    @property
    def max_id(self):
        return get_max_id(LPBImage)

    @property
    def slug(self):
        return self.event.slug


class QuoteImage(AbstractImage):
    SUB_PATH = 'quote/'
    TARGET_PARENT_ITEM_FIELD_NAME = 'quote'
    quote = models.ForeignKey('Quote', related_name='images', on_delete=models.CASCADE)

    class Meta:
        db_table = "quote_image"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._meta.get_field("image_file").upload_to = get_news_image_filename

    @property
    def max_id(self):
        return get_max_id(QuoteImage)

    @property
    def slug(self):
        return self.quote.slug


class TestimonialImage(AbstractImage):
    SUB_PATH = 'testimonial/'
    TARGET_PARENT_ITEM_FIELD_NAME = 'testimonial'
    testimonial = models.ForeignKey('Testimonial', related_name='images', on_delete=models.CASCADE)

    class Meta:
        db_table = "testimonial_image"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._meta.get_field("image_file").upload_to = get_news_image_filename

    @property
    def max_id(self):
        return get_max_id(TestimonialImage)

    @property
    def slug(self):
        return self.testimonial.slug


class CheffeImage(AbstractImage):
    SUB_PATH = 'cheffe/'
    TARGET_PARENT_ITEM_FIELD_NAME = 'cheffe'
    cheffe = models.ForeignKey('Cheffe', related_name='images', on_delete=models.CASCADE)

    class Meta:
        db_table = "cheffe_image"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._meta.get_field("image_file").upload_to = get_news_image_filename

    @property
    def max_id(self):
        return get_max_id(CheffeImage)

    @property
    def slug(self):
        return self.cheffe.slug


class WebsitePageImage(AbstractImage):
    SUB_PATH = 'website-page/'
    TARGET_PARENT_ITEM_FIELD_NAME = 'website_page'
    website_page = models.ForeignKey('WebsitePage', related_name='images', on_delete=models.CASCADE)

    class Meta:
        db_table = "website_page_image"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._meta.get_field("image_file").upload_to = get_news_image_filename

    @property
    def max_id(self):
        return get_max_id(WebsitePageImage)

    @property
    def slug(self):
        return self.website_page.slug


class NewsQuerySet(models.QuerySet):
    def all_with_deleted(self):
        qs = super(NewsQuerySet, self).all()
        qs.__class__ = NewsQuerySet
        return qs

    def delete_from_db(self):
        super(NewsQuerySet, self).delete()


class NewsManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        qs.__class__ = NewsQuerySet
        return qs

    def all_with_deleted(self):
        qs = super().get_queryset()
        qs.__class__ = NewsQuerySet
        return qs

    def all(self):
        qs = self.get_queryset().filter(deleted=False)
        qs.__class__ = NewsQuerySet
        return qs

    def filter(self, *args, **kwargs):
        qs = self.get_queryset().filter(deleted=False).filter(*args, **kwargs)
        return qs


class News(UniqueSlugModel, MultiLanguageTitleModel, models.Model):
    author = models.ForeignKey(
        'web.UserProfile', on_delete=models.SET(get_erased_user_uid()),
        related_name="news_author", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    comment_number = models.IntegerField(default=0)
    likevote_number = models.IntegerField(default=0)
    image = models.ForeignKey('NewsImage', related_name='image', blank=True, null=True, on_delete=models.CASCADE)
    last_editor = models.ForeignKey(
        "web.UserProfile", db_index=True, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="news_last_editor"
    )
    is_archived = models.BooleanField(default=False)
    external_id = models.CharField(blank=True, null=True, max_length=255)
    external_author_name = models.CharField(max_length=255, null=True)
    external_author_id = models.CharField(null=True, max_length=255)
    external_url = models.TextField(null=True)
    external_image_url = models.TextField(null=True)
    external_created_time = models.DateTimeField(default=datetime.now, null=True)
    external_post_title = models.TextField(blank=True, null=True)
    external_post_content = models.TextField(blank=True, null=True)
    external_language = models.CharField(max_length=255, null=True, blank=True)
    objects = NewsManager()

    def __str__(self):
        return f"{ self.name }"

    def get_name(self):
        return self.name or self.title_en or self.title_fr or self.title_ja or self.title_it or self.title_es

    def change_status(self, modifier_user, status):
        if status == NewsStatus.DELETED:
            self.deleted = True
        else:
            self.status_en = status
            self.status_fr = status
            self.status_es = status
            self.status_it = status
            self.status_ja = status
        self.last_editor = modifier_user
        self.updated_at = datetime.now()
        self.save()
        return True

    def get_image_url(self):
        return aws_url(self.image)

    def save(self, *args, **kwargs):
        self.name = self.get_name()
        if hasattr(self, 'clean'):
            self.clean()
        super(News, self).save(*args, **kwargs)

    def delete(self, **kwargs):
        self.deleted = True
        super().save(**kwargs)

    @property
    def model_name(self):
        return self._meta.model_name


class FeaturedVenue(UniqueSlugModel, MultiLanguageTitleModel, models.Model):
    connected_venue = models.ForeignKey("web.Place", on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200, verbose_name="name", blank=True)
    author = models.ForeignKey(
        'web.UserProfile', on_delete=models.SET(get_erased_user_uid()),
        related_name="featured_venue_author", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    comment_number = models.IntegerField(default=0)
    likevote_number = models.IntegerField(default=0)
    is_archived = models.BooleanField(default=False)
    image = models.ForeignKey(
        'FeaturedVenueImage', related_name='image', blank=True, null=True,
        on_delete=models.CASCADE
    )
    last_editor = models.ForeignKey(
        "web.UserProfile", db_index=True, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="featured_venue_last_editor"
    )
    objects = NewsManager()

    def __str__(self):
        return f"{ self.name }"

    def get_name(self):
        return self.name or self.title_en or self.title_fr or self.title_ja or self.title_it or self.title_es

    def change_status(self, modifier_user, status):
        if status == NewsStatus.DELETED:
            self.deleted = True
        else:
            self.status_en = status
            self.status_fr = status
            self.status_es = status
            self.status_it = status
            self.status_ja = status
        self.last_editor = modifier_user
        self.updated_at = datetime.now()
        self.save()
        return True

    def get_image_url(self):
        return aws_url(self.image)

    def save(self, *args, **kwargs):
        self.name = self.get_name()
        if hasattr(self, 'clean'):
            self.clean()
        super(FeaturedVenue, self).save(*args, **kwargs)

    def delete(self, **kwargs):
        self.deleted = True
        super().save(**kwargs)

    @property
    def model_name(self):
        return self._meta.model_name


class WebsitePage(UniqueSlugModel, MultiLanguageTitleModel, models.Model):
    p_code = models.CharField(max_length=200, null=True, blank=True)
    author = models.ForeignKey(
        'web.UserProfile', on_delete=models.SET(get_erased_user_uid()),
        related_name="website_page_author", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    image = models.ForeignKey(
        'WebsitePageImage', related_name='image', blank=True, null=True,
        on_delete=models.CASCADE
    )
    last_editor = models.ForeignKey(
        "web.UserProfile", db_index=True, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="website_page_last_editor"
    )
    objects = NewsManager()

    def __str__(self):
        return f"{ self.name }"

    def get_name(self):
        return self.name or self.title_en or self.title_fr or self.title_ja or self.title_it or self.title_es

    def change_status(self, modifier_user, status):
        if status == NewsStatus.DELETED:
            self.deleted = True
        else:
            self.status_en = status
            self.status_fr = status
            self.status_es = status
            self.status_it = status
            self.status_ja = status
        self.last_editor = modifier_user
        self.updated_at = datetime.now()
        self.save()
        return True

    def get_image_url(self):
        return aws_url(self.image)

    def delete(self, **kwargs):
        self.deleted = True
        super().save(**kwargs)

    @property
    def model_name(self):
        return self._meta.model_name


class LPBQuerySet(models.QuerySet):
    def all_with_deleted(self):
        qs = super(LPBQuerySet, self).all()
        qs.__class__ = LPBQuerySet
        return qs

    def delete_from_db(self):
        super(LPBQuerySet, self).delete()


class LPBManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset().filter(deleted=False)
        qs.__class__ = LPBQuerySet
        return qs

    def all_with_deleted(self):
        qs = super().get_queryset()
        qs.__class__ = LPBQuerySet
        return qs

    def all(self):
        qs = self.get_queryset()
        qs.__class__ = LPBQuerySet
        return qs

    def filter(self, *args, **kwargs):
        qs = self.get_queryset().filter(*args, **kwargs)
        return qs


class LPB(UniqueSlugModel, MultiLanguageTitleModel, models.Model):
    author = models.ForeignKey(
        'web.UserProfile', on_delete=models.SET(get_erased_user_uid()),
        related_name="lpb_author", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    image = models.ForeignKey('LPBImage', related_name='image', blank=True, null=True, on_delete=models.CASCADE)
    last_editor = models.ForeignKey(
        "web.UserProfile", db_index=True, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="lpb_last_editor"
    )
    is_archived = models.BooleanField(default=False)
    objects = LPBManager()

    def __str__(self):
        return f"{ self.name }"

    def get_name(self):
        return self.name or self.title_en or self.title_fr or self.title_ja or self.title_it or self.title_es

    def get_image_url(self):
        return aws_url(self.image)

    def save(self, *args, **kwargs):
        self.name = self.get_name()
        if hasattr(self, 'clean'):
            self.clean()
        super(LPB, self).save(*args, **kwargs)

    def change_status(self, modifier_user, status):
        if status == NewsStatus.DELETED:
            self.deleted = True
        else:
            self.status_en = status
            self.status_fr = status
            self.status_es = status
            self.status_it = status
            self.status_ja = status
        self.last_editor = modifier_user
        self.updated_at = datetime.now()
        self.save()
        return True

    def delete(self, **kwargs):
        self.deleted = True
        super().save(**kwargs)

    @property
    def model_name(self):
        return self._meta.model_name


class Quote(UniqueSlugModel, models.Model):
    connected_venue = models.ForeignKey("web.Place", on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name="venue_quote")
    default_quote = models.TextField(verbose_name="default quote", blank=True)
    quote_en = models.TextField(blank=True)
    quote_fr = models.TextField(blank=True)
    quote_ja = models.TextField(blank=True)
    quote_it = models.TextField(blank=True)
    quote_es = models.TextField(blank=True)
    status_en = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)
    status_fr = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)
    status_ja = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)
    status_it = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)
    status_es = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)
    author = models.ForeignKey(
        'web.UserProfile', on_delete=models.SET(get_erased_user_uid()),
        related_name="quote_author", null=True, blank=True
    )
    quote_translations = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    image = models.ForeignKey(
        'QuoteImage', related_name='image', blank=True, null=True,
        on_delete=models.CASCADE
    )
    last_editor = models.ForeignKey(
        "web.UserProfile", db_index=True, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="quote_last_editor"
    )
    objects = NewsManager()

    def __str__(self):
        return f"{ self.default_quote }"

    def get_name(self):
        return self.default_quote

    @property
    def name(self):
        if self.connected_venue:
            return self.connected_venue.name.lower() + "-quote"
        else:
            return self.default_quote[:35]

    def change_status(self, modifier_user, status):
        if status == NewsStatus.DELETED:
            self.deleted = True
        else:
            self.status_en = status
            self.status_fr = status
            self.status_es = status
            self.status_it = status
            self.status_ja = status
        self.last_editor = modifier_user
        self.updated_at = datetime.now()
        self.save()
        return True

    def get_image_url(self):
        return aws_url(self.image)

    def save(self, *args, **kwargs):
        self.default_quote = self.get_name()
        if hasattr(self, 'clean'):
            self.clean()
        super(Quote, self).save(*args, **kwargs)

    def delete(self, **kwargs):
        self.deleted = True
        super().save(**kwargs)

    @property
    def model_name(self):
        return self._meta.model_name


class FeaturedQuote(models.Model):
    quote = models.ForeignKey("news.Quote", on_delete=models.SET_NULL, null=True, blank=True,
                              related_name="quote_fetured")
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=1)


class Testimonial(UniqueSlugModel, models.Model):
    default_title = models.CharField(blank=True, null=True, max_length=255)
    title_en = models.CharField(blank=True, null=True, max_length=255)
    title_fr = models.CharField(blank=True, null=True, max_length=255)
    title_ja = models.CharField(blank=True, null=True, max_length=255)
    title_it = models.CharField(blank=True, null=True, max_length=255)
    title_es = models.CharField(blank=True, null=True, max_length=255)
    default_username = models.CharField(blank=True, null=True, max_length=255)
    username_en = models.CharField(blank=True, null=True, max_length=255)
    username_fr = models.CharField(blank=True, null=True, max_length=255)
    username_ja = models.CharField(blank=True, null=True, max_length=255)
    username_it = models.CharField(blank=True, null=True, max_length=255)
    username_es = models.CharField(blank=True, null=True, max_length=255)
    default_testimonial = models.TextField(verbose_name="default testimonial", blank=True)
    testimonial_en = models.TextField(blank=True)
    testimonial_fr = models.TextField(blank=True)
    testimonial_ja = models.TextField(blank=True)
    testimonial_it = models.TextField(blank=True)
    testimonial_es = models.TextField(blank=True)
    status_en = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)
    status_fr = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)
    status_ja = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)
    status_it = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)
    status_es = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)
    date = models.DateField(default=timezone.now)
    author = models.ForeignKey(
        'web.UserProfile', on_delete=models.SET(get_erased_user_uid()),
        related_name="testimonial_author", null=True, blank=True
    )
    testimonial_translations = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    image = models.ForeignKey(
        'TestimonialImage', related_name='image', blank=True, null=True,
        on_delete=models.CASCADE
    )
    last_editor = models.ForeignKey(
        "web.UserProfile", db_index=True, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="testimonial_last_editor"
    )
    objects = NewsManager()

    def __str__(self):
        return f"{ self.default_testimonial }"

    def get_name(self):
        return self.default_testimonial

    @property
    def name(self):
        if self.default_username:
            return self.default_username.lower()
        else:
            return self.default_title

    def change_status(self, modifier_user, status):
        if status == NewsStatus.DELETED:
            self.deleted = True
        else:
            self.status_en = status
            self.status_fr = status
            self.status_es = status
            self.status_it = status
            self.status_ja = status
        self.last_editor = modifier_user
        self.updated_at = datetime.now()
        self.save()
        return True

    def get_image_url(self):
        return aws_url(self.image)

    def save(self, *args, **kwargs):
        self.default_testimonial = self.get_name()
        if hasattr(self, 'clean'):
            self.clean()
        super(Testimonial, self).save(*args, **kwargs)

    def delete(self, **kwargs):
        self.deleted = True
        super().save(**kwargs)

    @property
    def model_name(self):
        return self._meta.model_name


class FeaturedTestimonial(models.Model):
    testimonial = models.ForeignKey("news.Testimonial", on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="testimonial_fetured")
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=1)


class Cheffe(UniqueSlugModel, models.Model):
    connected_venue = models.ForeignKey("web.Place", on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name="venue_cheffe")
    default_fullname = models.CharField(blank=True, null=True, max_length=255)
    fullname_en = models.CharField(blank=True, null=True, max_length=255)
    fullname_fr = models.CharField(blank=True, null=True, max_length=255)
    fullname_ja = models.CharField(blank=True, null=True, max_length=255)
    fullname_it = models.CharField(blank=True, null=True, max_length=255)
    fullname_es = models.CharField(blank=True, null=True, max_length=255)
    default_cheffe = models.TextField(verbose_name="default cheffe", blank=True)
    cheffe_en = models.TextField(blank=True)
    cheffe_fr = models.TextField(blank=True)
    cheffe_ja = models.TextField(blank=True)
    cheffe_it = models.TextField(blank=True)
    cheffe_es = models.TextField(blank=True)
    status_en = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)
    status_fr = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)
    status_ja = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)
    status_it = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)
    status_es = models.CharField(max_length=200, verbose_name="title ES", blank=True, default=NewsStatus.DRAFT)
    author = models.ForeignKey(
        'web.UserProfile', on_delete=models.SET(get_erased_user_uid()),
        related_name="cheffe_author", null=True, blank=True
    )
    cheffe_translations = JSONField(
        encoder=json_handling.JsonEncoder,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    image = models.ForeignKey(
        'CheffeImage', related_name='image', blank=True, null=True,
        on_delete=models.CASCADE
    )
    last_editor = models.ForeignKey(
        "web.UserProfile", db_index=True, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="cheffe_last_editor"
    )
    objects = NewsManager()

    def __str__(self):
        return f"{ self.default_cheffe }"

    def get_name(self):
        return self.default_cheffe

    @property
    def name(self):
        if self.default_fullname:
            return self.default_fullname
        else:
            return self.default_cheffe[:35]

    def change_status(self, modifier_user, status):
        if status == NewsStatus.DELETED:
            self.deleted = True
        else:
            self.status_en = status
            self.status_fr = status
            self.status_es = status
            self.status_it = status
            self.status_ja = status
        self.last_editor = modifier_user
        self.updated_at = datetime.now()
        self.save()
        return True

    def get_image_url(self):
        return aws_url(self.image)

    def save(self, *args, **kwargs):
        self.default_cheffe = self.get_name()
        if hasattr(self, 'clean'):
            self.clean()
        super(Cheffe, self).save(*args, **kwargs)

    def delete(self, **kwargs):
        self.deleted = True
        super().save(**kwargs)

    @property
    def model_name(self):
        return self._meta.model_name


class FeaturedCheffe(models.Model):
    cheffe = models.ForeignKey("news.Cheffe", on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="cheffe_fetured")
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=1)
