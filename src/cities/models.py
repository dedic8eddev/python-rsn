from django.conf import settings

from web.utils.upload_tools import aws_url

from django.utils.encoding import force_str

from django.contrib.gis.db.models import PointField, PolygonField, \
    MultiPolygonField
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.template.defaultfilters import slugify as slugify_django

from model_utils import Choices
import swapper

from .conf import (ALTERNATIVE_NAME_TYPES, SLUGIFY_FUNCTION, DJANGO_VERSION)
from .managers import AlternativeNameManager
from .util import unicode_func
from django.urls import reverse

__all__ = [
    'Point', 'Continent', 'Country', 'Region', 'Subregion', 'City', 'District',
    'PostalCode', 'AlternativeName',
]


if DJANGO_VERSION < 2:
    from django.contrib.gis.db.models import GeoManager
else:
    from django.db.models import Manager as GeoManager

slugify_func = SLUGIFY_FUNCTION

ZOOM_SCALE = ((i, i) for i in range(1, 17))

ADMIN_LEVEL_OSM = (
    # ('1', 1),
    # ('2', 2),
    # ('3', 3),
    # ('4', 4),
    # ('5', 5),
    # ('6', 6),
    ('7', 7),
    ('8', 8),
    ('9', 9),
    ('10', 10),
    ('11', 11),
    ('12', 12),
    ('13', 13),
    ('14', 14),
    ('15', 15),
)


def SET_NULL_OR_CASCADE(collector, field, sub_objs, using):
    if field.null is True:
        models.SET_NULL(collector, field, sub_objs, using)
    else:
        models.CASCADE(collector, field, sub_objs, using)


class SlugModel(models.Model):
    slug = models.CharField(blank=True, max_length=255, null=True)
    slug_en = models.CharField(blank=True, max_length=255, null=True)
    slug_fr = models.CharField(blank=True, max_length=255, null=True)
    slug_it = models.CharField(blank=True, max_length=255, null=True)
    slug_ja = models.CharField(blank=True, max_length=255, null=True)
    slug_es = models.CharField(blank=True, max_length=255, null=True)

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(fields=['id', 'slug'],
                                    condition=models.Q(slug__isnull=False),
                                    name='slug_uniq_%(class)s'),
            models.UniqueConstraint(fields=['id', 'slug_en'],
                                    condition=models.Q(slug_en__isnull=False),
                                    name='slug_en_uniq_%(class)s'),
            models.UniqueConstraint(fields=['id', 'slug_ja'],
                                    condition=models.Q(slug_ja__isnull=False),
                                    name='slug_js_uniq_%(class)s'),
            models.UniqueConstraint(fields=['id', 'slug_fr'],
                                    condition=models.Q(slug_fr__isnull=False),
                                    name='slug_fr_uniq_%(class)s'),
            models.UniqueConstraint(fields=['id', 'slug_it'],
                                    condition=models.Q(slug_it__isnull=False),
                                    name='slug_it_uniq_%(class)s'),
            models.UniqueConstraint(fields=['id', 'slug_es'],
                                    condition=models.Q(slug_es__isnull=False),
                                    name='slug_es_uniq_%(class)s')
        ]

    def slugify(self):
        if hasattr(self, 'name'):
            if hasattr(self, 'region'):
                slug = slugify_django(self.name)
                qs = self.__class__.objects.filter(region=self.region, slug=slug)
                if self.id:
                    qs = qs.exclude(id=self.id)
                if qs.exists():
                    number = qs.count()
                    return f'{slug}-{number}'
            return slugify_django(self.name)
        raise NotImplementedError("Subclasses of Place must implement slugify()")

    def save(self, *args, **kwargs):
        self.slug = slugify_func(self, self.slugify())
        if hasattr(self, 'name') and hasattr(self, 'name_en'):
            self.slug_en = slugify_func(self, slugify_django(self.name_en or self.name))
        if hasattr(self, 'name') and hasattr(self, 'name_jp'):
            self.slug_ja = slugify_func(self, slugify_django(self.name_en or self.name))
        if hasattr(self, 'name') and hasattr(self, 'name_es'):
            self.slug_es = slugify_func(self, slugify_django(self.name_es or self.name))
        if hasattr(self, 'name') and hasattr(self, 'name_it'):
            self.slug_it = slugify_func(self, slugify_django(self.name_it or self.name))
        if hasattr(self, 'name') and hasattr(self, 'name_fr'):
            self.slug_fr = slugify_func(self, slugify_django(self.name_fr or self.name))
        super(SlugModel, self).save(*args, **kwargs)


class PlaceQuerySet(models.QuerySet):
    def all_with_deleted(self):
        qs = super(PlaceQuerySet, self).all()
        qs.__class__ = PlaceQuerySet
        return qs

    def delete_from_db(self):
        super(PlaceQuerySet, self).delete()


class PlaceManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset().filter(deleted=False)
        qs.__class__ = PlaceQuerySet
        return qs

    def all_with_deleted(self):
        qs = super().get_queryset()
        qs.__class__ = PlaceQuerySet
        return qs

    def all(self):
        qs = self.get_queryset()
        qs.__class__ = PlaceQuerySet
        return qs

    def filter(self, *args, **kwargs):
        qs = self.get_queryset().filter(*args, **kwargs)
        return qs

    def filter_with_deleted(self, *args, **kwargs):
        qs = super().get_queryset().filter(*args, **kwargs)
        return qs


class Place(SlugModel):
    name = models.CharField(max_length=200, db_index=True, verbose_name="ascii name", blank=True)
    name_en = models.CharField(max_length=200, db_index=True, blank=True)
    name_fr = models.CharField(max_length=200, db_index=True, blank=True)
    name_ja = models.CharField(max_length=200, db_index=True, blank=True)
    name_it = models.CharField(max_length=200, db_index=True, blank=True)
    name_es = models.CharField(max_length=200, db_index=True, blank=True)
    title_en = models.CharField(max_length=200, verbose_name="nmae EN", blank=True)
    title_fr = models.CharField(max_length=200, verbose_name="nmae FR", blank=True)
    title_ja = models.CharField(max_length=200, verbose_name="nmae JA", blank=True)
    title_it = models.CharField(max_length=200, verbose_name="nmae IT", blank=True)
    title_es = models.CharField(max_length=200, verbose_name="nmae ES", blank=True)
    meta_description_en = models.TextField(blank=True)
    meta_description_fr = models.TextField(blank=True)
    meta_description_ja = models.TextField(blank=True)
    meta_description_it = models.TextField(blank=True)
    meta_description_es = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    description_fr = models.TextField(blank=True)
    description_ja = models.TextField(blank=True)
    description_it = models.TextField(blank=True)
    description_es = models.TextField(blank=True)
    published_en = models.BooleanField(default=False)
    published_fr = models.BooleanField(default=False)
    published_ja = models.BooleanField(default=False)
    published_it = models.BooleanField(default=False)
    published_es = models.BooleanField(default=False)
    image = models.ImageField(null=True, blank=True, upload_to='cities/')
    alt_names = models.ManyToManyField('AlternativeName', blank=True)
    author = models.ForeignKey('Author', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_editor = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True, on_delete=models.SET_NULL, null=True,
                                    blank=True)
    deleted = models.BooleanField(default=False)
    osm_id = models.CharField(max_length=64, blank=True)
    osm_place_id = models.IntegerField(null=True, blank=True)
    osm_name = models.CharField(max_length=255, blank=True)
    location = PointField(null=True, blank=True)
    zoom_scale = models.IntegerField(default=1, choices=ZOOM_SCALE)

    objects = PlaceManager()

    class Meta(SlugModel.Meta):
        abstract = True
        constraints = [
            models.UniqueConstraint(fields=['id', 'slug'],
                                    condition=models.Q(deleted=False, slug__isnull=False),
                                    name='slug_uniq_%(class)s'),
            models.UniqueConstraint(fields=['id', 'slug_en'],
                                    condition=models.Q(deleted=False, slug_en__isnull=False),
                                    name='slug_en_uniq_%(class)s'),
            models.UniqueConstraint(fields=['id', 'slug_ja'],
                                    condition=models.Q(deleted=False, slug_ja__isnull=False),
                                    name='slug_js_uniq_%(class)s'),
            models.UniqueConstraint(fields=['id', 'slug_fr'],
                                    condition=models.Q(deleted=False, slug_fr__isnull=False),
                                    name='slug_fr_uniq_%(class)s'),
            models.UniqueConstraint(fields=['id', 'slug_it'],
                                    condition=models.Q(deleted=False, slug_it__isnull=False),
                                    name='slug_it_uniq_%(class)s'),
            models.UniqueConstraint(fields=['id', 'slug_es'],
                                    condition=models.Q(deleted=False, slug_es__isnull=False),
                                    name='slug_es_uniq_%(class)s')
        ]

    @property
    def hierarchy(self):
        """Get hierarchy, root first"""
        lst = self.parent.hierarchy if self.parent else []
        lst.append(self)
        return lst

    def get_absolute_url(self):
        return "/".join([place.slug for place in self.hierarchy])

    def __str__(self):
        return force_str(self.name)

    def get_name(self):
        return self.name_en or self.name

    def get_image_url(self):
        return aws_url(self.image)

    def save(self, *args, **kwargs):
        self.name = self.get_name()
        if not self.name_en:
            self.name_en = self.get_name_en()
        if not self.name_ja:
            self.name_ja = self.get_name_ja()
        if not self.name_fr:
            self.name_fr = self.get_name_fr()
        if not self.name_es:
            self.name_es = self.get_name_es()
        if not self.name_it:
            self.name_it = self.get_name_it()
        if hasattr(self, 'clean'):
            self.clean()
        super(Place, self).save(*args, **kwargs)

    def delete(self, **kwargs):
        self.deleted = True
        super().save(**kwargs)

    @property
    def model_name(self):
        return self._meta.model_name

    @property
    def name_jp(self):
        return self.name_ja

    def get_name_en(self):
        alt_names = self.alt_names.filter(language_code='en')
        if alt_names.exists():
            return alt_names.first().name
        return self.name

    def get_name_ja(self):
        alt_names = self.alt_names.filter(language_code='ja')
        if alt_names.exists():
            return alt_names.first().name
        return self.name

    def get_name_fr(self):
        alt_names = self.alt_names.filter(language_code='fr')
        if alt_names.exists():
            return alt_names.first().name
        return self.name

    def get_name_it(self):
        alt_names = self.alt_names.filter(language_code='it')
        if alt_names.exists():
            return alt_names.first().name
        return self.name

    def get_name_es(self):
        alt_names = self.alt_names.filter(language_code='es')
        if alt_names.exists():
            return alt_names.first().name
        return self.name


class BaseContinent(Place):
    code = models.CharField(max_length=2, unique=True, db_index=True, null=True, blank=True)
    zoom_scale = models.IntegerField(default=2, choices=ZOOM_SCALE)

    def __str__(self):
        return force_str(self.name)

    class Meta(Place.Meta):
        abstract = True


class Continent(BaseContinent):

    class Meta(BaseContinent.Meta):
        swappable = swapper.swappable_setting('cities', 'Continent')


class BaseCountry(Place):
    code = models.CharField(max_length=2, db_index=True, unique=True, null=True, blank=True)
    code3 = models.CharField(max_length=3, db_index=True, unique=True)
    population = models.IntegerField(null=True)
    area = models.IntegerField(null=True)
    currency = models.CharField(max_length=3, null=True)
    currency_name = models.CharField(max_length=50, blank=True, null=True)
    currency_symbol = models.CharField(max_length=31, blank=True, null=True)
    language_codes = models.CharField(max_length=250, null=True)
    phone = models.CharField(max_length=20)
    continent = models.ForeignKey(swapper.get_model_name('cities', 'Continent'),
                                  null=True,
                                  related_name='countries',
                                  on_delete=SET_NULL_OR_CASCADE)
    tld = models.CharField(max_length=5, verbose_name='TLD')
    postal_code_format = models.CharField(max_length=127)
    postal_code_regex = models.CharField(max_length=255)
    capital = models.CharField(max_length=100)
    neighbours = models.ManyToManyField("self")
    zoom_scale = models.IntegerField(default=5, choices=ZOOM_SCALE)

    class Meta(Place.Meta):
        abstract = True
        ordering = ['name']
        verbose_name_plural = "countries"

    @property
    def parent(self):
        return None

    def __str__(self):
        return force_str(self.name)

    def clean(self):
        self.tld = self.tld.lower()


class Country(BaseCountry):
    class Meta(BaseCountry.Meta):
        swappable = swapper.swappable_setting('cities', 'Country')

    def get_absolute_url(self):
        return reverse(
            'country_update',
            kwargs={
                'continent_slug': self.continent.slug,
                'slug': self.slug,
                'language': 'en'
            }
        )


class Region(Place):
    name_std = models.CharField(max_length=200, db_index=True, verbose_name="standard name")
    code = models.CharField(max_length=200, db_index=True)
    country = models.ForeignKey(swapper.get_model_name('cities', 'Country'),
                                related_name='regions',
                                on_delete=SET_NULL_OR_CASCADE)
    zoom_scale = models.IntegerField(default=6, choices=ZOOM_SCALE)

    class Meta(Place.Meta):
        unique_together = (('country', 'name'),)

    @property
    def parent(self):
        return self.country

    def full_code(self):
        return unicode_func(".".join([self.parent.code, self.code]))

    def get_absolute_url(self):
        return reverse(
            'region_update',
            kwargs={
                'continent_slug': self.country.continent.slug,
                'country_slug': self.country.slug,
                'slug': self.slug,
                'language': 'en'
            }
        )


class Subregion(Place):
    slug_contains_id = True

    name_std = models.CharField(max_length=200, db_index=True, verbose_name="standard name")
    code = models.CharField(max_length=200, db_index=True)
    region = models.ForeignKey(Region,
                               related_name='subregions',
                               on_delete=SET_NULL_OR_CASCADE)
    zoom_scale = models.IntegerField(default=8, choices=ZOOM_SCALE)

    class Meta(Place.Meta):
        unique_together = (('region', 'id', 'name'),)

    @property
    def parent(self):
        return self.region

    def full_code(self):
        return ".".join([self.parent.parent.code, self.parent.code, self.code])


class BaseCity(Place):
    slug_contains_id = True

    name_std = models.CharField(max_length=200, db_index=True, verbose_name="standard name")
    country = models.ForeignKey(swapper.get_model_name('cities', 'Country'),
                                related_name='cities',
                                on_delete=SET_NULL_OR_CASCADE,
                                null=True,
                                blank=True)
    region = models.ForeignKey(Region,
                               null=True,
                               blank=True,
                               related_name='cities',
                               on_delete=SET_NULL_OR_CASCADE)
    subregion = models.ForeignKey(Subregion,
                                  null=True,
                                  blank=True,
                                  related_name='cities',
                                  on_delete=SET_NULL_OR_CASCADE)
    location = PointField(null=True)
    population = models.IntegerField(null=True)
    elevation = models.IntegerField(null=True)
    kind = models.CharField(max_length=10)  # http://www.geonames.org/export/codes.html
    timezone = models.CharField(max_length=40)
    zoom_scale = models.IntegerField(default=12, choices=ZOOM_SCALE)

    class Meta(Place.Meta):
        abstract = True
        unique_together = (('country', 'region', 'subregion', 'id', 'name'),)
        verbose_name_plural = "cities"

    @property
    def parent(self):
        return self.region


class City(BaseCity):
    urban_area = models.ForeignKey('UrbanArea',
                                   null=True,
                                   blank=True,
                                   related_name='cities',
                                   on_delete=models.SET_NULL)
    admin_level = models.CharField(max_length=2, blank=True, choices=ADMIN_LEVEL_OSM)

    class Meta(BaseCity.Meta):
        swappable = swapper.swappable_setting('cities', 'City')

    def get_absolute_url(self):
        return reverse(
            'city_update',
            kwargs={
                'continent_slug': self.country.continent.slug,
                'slug': self.slug,
                'region_slug': self.region.slug,
                'country_slug': self.country.slug,
                'language': 'en'
            }
        )


class District(Place):
    slug_contains_id = True

    name_std = models.CharField(max_length=200, db_index=True, verbose_name="standard name")
    code = models.CharField(blank=True, db_index=True, max_length=200, null=True)
    location = PointField()
    population = models.IntegerField()
    city = models.ForeignKey(swapper.get_model_name('cities', 'City'),
                             related_name='districts',
                             on_delete=SET_NULL_OR_CASCADE)
    zoom_scale = models.IntegerField(default=14, choices=ZOOM_SCALE)

    class Meta(Place.Meta):
        ordering = ['name']
        unique_together = (('city', 'name'),)

    def delete(self, **kwargs):
        super().delete(**kwargs)
        places = self.places.all()
        if places.exists():
            places.update(district=None)

    @property
    def parent(self):
        return self.city

    def get_absolute_url(self):
        return reverse(
            'district_update',
            kwargs={
                'continent_slug': self.city.country.continent.slug,
                'country_slug': self.city.country.slug,
                'region_slug': self.city.region.slug,
                'city_slug': self.city.slug,
                'slug': self.slug,
                'language': 'en'
            }
        )


class AlternativeName(SlugModel):
    slug_contains_id = True

    KIND = Choices(*ALTERNATIVE_NAME_TYPES)

    name = models.CharField(max_length=255)
    kind = models.CharField(max_length=4, choices=KIND, default=KIND.name)
    language_code = models.CharField(max_length=100)
    is_preferred = models.BooleanField(default=False)
    is_short = models.BooleanField(default=False)
    is_colloquial = models.BooleanField(default=False)
    is_historic = models.BooleanField(default=False)

    objects = AlternativeNameManager()

    class Meta(SlugModel.Meta):
        ordering = ['-is_preferred']

    def __str__(self):
        return "%s (%s)" % (force_str(self.name), force_str(self.language_code))


class PostalCode(Place):
    slug_contains_id = True

    code = models.CharField(max_length=20)
    location = PointField()

    country = models.ForeignKey(swapper.get_model_name('cities', 'Country'),
                                related_name='postal_codes',
                                on_delete=SET_NULL_OR_CASCADE)

    # Region names for each admin level, region may not exist in DB
    region_name = models.CharField(max_length=100, db_index=True)
    subregion_name = models.CharField(max_length=100, db_index=True)
    district_name = models.CharField(max_length=100, db_index=True)

    region = models.ForeignKey(Region,
                               blank=True,
                               null=True,
                               related_name='postal_codes',
                               on_delete=SET_NULL_OR_CASCADE)
    subregion = models.ForeignKey(Subregion,
                                  blank=True,
                                  null=True,
                                  related_name='postal_codes',
                                  on_delete=SET_NULL_OR_CASCADE)
    city = models.ForeignKey(swapper.get_model_name('cities', 'City'),
                             blank=True,
                             null=True,
                             related_name='postal_codes',
                             on_delete=SET_NULL_OR_CASCADE)
    district = models.ForeignKey(District,
                                 blank=True,
                                 null=True,
                                 related_name='postal_codes',
                                 on_delete=SET_NULL_OR_CASCADE)

    objects = GeoManager()

    class Meta(Place.Meta):
        unique_together = (
            ('country', 'region', 'subregion', 'city', 'district', 'name', 'id', 'code'),
            ('country', 'region_name', 'subregion_name', 'district_name', 'name', 'id', 'code'),
        )

    @property
    def parent(self):
        return self.country

    @property
    def name_full(self):
        """Get full name including hierarchy"""
        return force_str(', '.join(reversed(self.names)))

    @property
    def names(self):
        """Get a hierarchy of non-null names, root first"""
        return [e for e in [
            force_str(self.country),
            force_str(self.region_name),
            force_str(self.subregion_name),
            force_str(self.district_name),
            force_str(self.name),
        ] if e]

    def __str__(self):
        return force_str(self.code)


class UrbanArea(Place):
    country_code = models.CharField(max_length=3)
    category = models.CharField(max_length=1)
    code = models.CharField(max_length=10)
    geometry_polygon = PolygonField()
    geometry_multipolygon = MultiPolygonField()
    name = models.CharField(max_length=255)
    alt_names = models.ManyToManyField('cities.AlternativeName')
    region = models.ForeignKey('cities.Region',
                               null=True,
                               blank=True,
                               on_delete=models.SET_NULL)

    def get_absolute_url(self):
        return reverse(
            'ua_update',
            kwargs={
                'continent_slug': self.region.country.continent.slug,
                'country_slug': self.region.country.slug,
                'region_slug': self.region.slug,
                'pk': self.pk,
                'language': 'en'
            }
        )


class Author(models.Model):
    name = models.CharField(max_length=200, blank=True)
    url = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='cities/authors/', null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name', )

    def get_image_url(self):
        return aws_url(self.image)
