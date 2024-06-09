# from django.contrib.postgres.aggregates.general import ArrayAgg
from django.db.models import (Case, When, Sum, F, CharField, Count, Q,
                              IntegerField, BooleanField)
from django.urls import reverse
from django.views.generic import ListView, UpdateView, FormView

from cities.models import (Country, Continent, City, UrbanArea, Region, District)
from web.constants import LANGUAGES
from web.helpers.places import PlaceHelper
from web.models import Place
from .forms import (CountrySearchFrom, CitySearchForm, VenueSearchFrom, AuthorForm, RegionSearchForm,
                    DistrictSearchFrom, DistrictCreateForm)
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import permissions
from django.views.generic.list import MultipleObjectMixin
from django.http import Http404
from django.utils.translation import gettext as _
from cities.tasks import add_districts_to_venues, delete_districts_from_venues
from raisin.settings import RAISIN_NEW_WEBSITE


class ContinentListView(LoginRequiredMixin, ListView):
    model = Continent
    template_name = 'cities/continent_list.html'
    queryset = Continent.objects.all()
    ordering = ['-venues_count']
    permission_classes = [permissions.IsAuthenticated]

    def get_ordering(self):
        self.ordering = self.request.GET.getlist('order_by', self.ordering)
        return self.ordering

    def get_queryset(self):
        qs = self.queryset
        qs = qs.annotate(
            venues_count=Count('countries__cities__places', filter=Q(countries__cities__places__is_archived=False),
                               distinct=True),
            country_count=Count(
                'countries',
                distinct=True,
                filter=Q(countries__cities__places__isnull=False)
            ),
            cities_count=Count(
                'countries__cities',
                distinct=True,
                filter=Q(countries__cities__places__isnull=False)
            )
        )
        qs = qs.filter(venues_count__gt=0)
        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            qs = qs.order_by(*ordering)
        return qs

    def get_context_data(self, *, object_list=None, **kwargs):
        ctx = super().get_context_data(object_list=object_list, **kwargs)
        qs = self.get_queryset()
        qs_aggregation = qs.aggregate(
            countries_sum=Sum('country_count'),
            cities_sum=Sum('cities_count')
        )
        ctx['countries_count'] = qs_aggregation.get('countries_sum')
        ctx['cities_count'] = qs_aggregation.get('cities_sum')
        ctx['order_by'] = self.ordering[0] if self.ordering else ''
        bc_path = [
            ('/', 'Home'),
            (reverse('continent_list'), "Areas"),
        ]
        ctx['bc_path'] = bc_path
        return ctx


class PlaceUpdateViewMixin(LoginRequiredMixin, MultipleObjectMixin, UpdateView):
    author_form = AuthorForm
    fields_ = ['image']
    permission_classes = [permissions.IsAuthenticated]
    paginate_by = 10
    ordering_list = ['-venues_count']

    def dispatch(self, request, *args, **kwargs):
        self.paginate_by = request.GET.get('page_size', self.paginate_by)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()
        self.object = self.get_object(queryset=qs)
        self.object_list = self.get_queryset_object_list()
        obj_qs = self.object_list.first()
        ordering_list = [ord_attr for ord_attr in self.ordering_list
                         if hasattr(obj_qs, ord_attr) or hasattr(obj_qs, ord_attr[1:])]
        self.object_list = self.object_list.order_by(*ordering_list)
        allow_empty = self.get_allow_empty()

        if not allow_empty:
            # When pagination is enabled and object_list is a queryset,
            # it's better to do a cheap query than to load the unpaginated
            # queryset in memory.
            if self.get_paginate_by(self.object_list) is not None and hasattr(self.object_list, 'exists'):
                is_empty = not self.object_list.exists()
            else:
                is_empty = not self.object_list
            if is_empty:
                raise Http404(_("Empty list and '%(class_name)s.allow_empty' is False.") % {
                    'class_name': self.__class__.__name__,
                })
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_ordering(self):
        self.ordering_list = self.request.GET.getlist('order_by', self.ordering_list)
        return None

    def get_queryset_object_list(self):
        return self.queryset

    def setup(self, *args, **kwargs):
        super(PlaceUpdateViewMixin, self).setup(*args, **kwargs)
        fields = ['title', 'meta_description', 'description', 'published']
        self.fields = self.fields_ + ['{}_{}'.format(field, kwargs.get('language')) for field in fields]

    def get_context_data(self, **kwargs):
        ctx = super(PlaceUpdateViewMixin, self).get_context_data(**kwargs)
        ctx['language_code'] = self.kwargs.get('language')
        ctx['language'] = LANGUAGES.get(self.kwargs.get('language'))
        if hasattr(self.object, 'title_{}'.format(self.kwargs.get('language'))):
            ctx['title'] = getattr(self.object, 'title_{}'.format(self.kwargs.get('language')))
        if hasattr(self.object, 'meta_description_{}'.format(self.kwargs.get('language'))):
            ctx['meta_description'] = getattr(self.object, 'meta_description_{}'.format(self.kwargs.get('language')))
        if hasattr(self.object, 'description_{}'.format(self.kwargs.get('language'))):
            ctx['description'] = getattr(self.object, 'description_{}'.format(self.kwargs.get('language')))
        if hasattr(self.object, 'published_{}'.format(self.kwargs.get('language'))):
            ctx['published'] = getattr(self.object, 'published_{}'.format(self.kwargs.get('language')))
        bc_path = [
            ('/', 'Home'),
            (reverse('continent_list'), "Areas"),
        ]
        ctx['bc_path'] = bc_path
        ctx['page_size'] = self.paginate_by
        ctx['order_by'] = self.ordering_list[0] if self.ordering_list else ''
        return ctx

    def form_valid(self, form):
        author = self.object.author
        author_data = {
            'name': self.request.POST.get('author__name'),
            'description': self.request.POST.get('author__description'),
            'url': self.request.POST.get('author__url'),
        }
        author_file_data = {'image': self.request.FILES.get('author__image')}
        author_form = self.author_form(instance=author, data=author_data, files=author_file_data)
        if author_form.is_valid():
            author = author_form.save()
            self.object.author = author
            self.object.save()

        self.object.last_editor = self.request.user
        self.object.save()
        return super(PlaceUpdateViewMixin, self).form_valid(form)


class ContinentUpdateView(PlaceUpdateViewMixin):
    model = Continent
    template_name = 'cities/continent_update.html'
    permission_classes = [permissions.IsAuthenticated]

    def get_success_url(self):
        return reverse('continent_update', kwargs={'slug': self.object.slug, 'language': self.kwargs.get('language')})

    def get_queryset_object_list(self):
        qs = Country.objects.all()
        qs = qs.filter(continent__slug=self.object.slug)
        qs = qs.annotate(venues_count=Count('cities__places', filter=Q(cities__places__is_archived=False),
                                            distinct=True))
        qs = qs.filter(venues_count__gt=0)
        qs = qs.annotate(
            cities_count=Count(
                'cities',
                distinct=True,
                filter=Q(cities__urban_area__isnull=True) & Q(cities__places__isnull=False)
            ),
            urban_area_count=Count(
                'cities__urban_area',
                distinct=True,
                filter=Q(cities__places__isnull=False)
            )
        ).annotate(cities_and_ua=F('cities_count') + F('urban_area_count'))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs_aggr = self.object_list.aggregate(cities_sum=Sum('cities_and_ua'))
        ctx['cities_sum'] = qs_aggr.get('cities_sum')
        ctx['continent'] = self.object
        return ctx


class CountryListView(ListView):
    model = Country
    template_name = 'cities/country_list.html'
    paginate_by = 10
    queryset = Country.objects.all().select_related('continent')
    form_class = CountrySearchFrom
    ordering = ['-venues_count']
    permission_classes = [permissions.IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        self.paginate_by = request.GET.get('page_size', self.paginate_by)
        return super().dispatch(request, *args, **kwargs)

    def get_ordering(self):
        self.ordering = self.request.GET.getlist('order_by', self.ordering)
        return self.ordering

    def get_queryset(self):
        qs = self.queryset
        qs = qs.filter(continent__slug=self.kwargs.get('continent_slug'))
        qs = qs.annotate(venues_count=Count('cities__places', filter=Q(cities__places__is_archived=False),
                                            distinct=True))
        qs = qs.filter(venues_count__gt=0)
        qs = qs.annotate(
            cities_count=Count(
                'cities',
                distinct=True,
                filter=Q(cities__urban_area__isnull=True) & Q(cities__places__isnull=False)
            ),
            urban_area_count=Count(
                'cities__urban_area',
                distinct=True,
                filter=Q(cities__places__isnull=False)
            )
        ).annotate(cities_and_ua=F('cities_count') + F('urban_area_count'))
        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            qs = qs.order_by(*ordering)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        qs_aggr = qs.aggregate(cities_sum=Sum('cities_and_ua'))
        ctx['continent'] = Continent.objects.get(slug=self.kwargs.get('continent_slug'))
        ctx['cities_sum'] = qs_aggr.get('cities_sum')
        ctx['search_form'] = self.form_class()
        ctx['page_size'] = self.paginate_by
        ctx['search_name'] = self.request.GET.get('name')
        ctx['order_by'] = self.ordering[0] if self.ordering else ''
        bc_path = [
            ('/', 'Home'),
            (reverse('continent_list'), "Areas"),
        ]
        ctx['bc_path'] = bc_path
        return ctx


class CountryUpdateView(PlaceUpdateViewMixin):
    model = Country
    template_name = 'cities/country_update.html'
    permission_classes = [permissions.IsAuthenticated]
    paginate_by = 10

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['continent_slug'] = self.kwargs.get('continent_slug')
        ctx['country'] = self.object
        qs = self.get_queryset_object_list()
        qs_aggr = qs.aggregate(cities_sum=Sum('cities_and_ua'))
        ctx['cities_sum'] = qs_aggr.get('cities_sum')
        ctx['new_raisin_url'] = f"{RAISIN_NEW_WEBSITE}/en/countries/{self.object.slug_en}/"
        return ctx

    def get_success_url(self):
        return reverse('country_update', kwargs={'continent_slug': self.kwargs.get('continent_slug'),
                                                 'slug': self.object.slug,
                                                 'language': self.kwargs.get('language')})

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(continent__slug=self.kwargs.get('continent_slug'))
        return qs

    def get_queryset_object_list(self):
        qs = Region.objects.all().select_related('country')
        qs = qs.filter(country__slug=self.object.slug)
        qs = qs.annotate(venues_count=Count('cities__places', filter=Q(cities__places__is_archived=False),
                                            distinct=True))
        qs = qs.filter(venues_count__gt=0)
        qs = qs.annotate(
            cities_count=Count(
                'cities',
                distinct=True,
                filter=Q(cities__urban_area__isnull=True) & Q(cities__places__isnull=False)
            ),
            urban_area_count=Count(
                'cities__urban_area',
                distinct=True,
                filter=Q(cities__places__isnull=False)
            )
        ).annotate(cities_and_ua=F('cities_count') + F('urban_area_count'))
        return qs


class RegionListView(ListView):
    model = Region
    template_name = 'cities/region_list.html'
    paginate_by = 10
    queryset = Region.objects.all()
    form_class = RegionSearchForm
    ordering = ['-venues_count']
    permission_classes = [permissions.IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        self.paginate_by = request.GET.get('page_size', self.paginate_by)
        return super().dispatch(request, *args, **kwargs)

    def get_ordering(self):
        self.ordering = self.request.GET.getlist('order_by', self.ordering)
        return self.ordering

    def get_queryset(self):
        qs = self.queryset
        qs = qs.filter(country__slug=self.kwargs.get('country_slug'))
        qs = qs.annotate(venues_count=Count('cities__places', filter=Q(cities__places__is_archived=False),
                                            distinct=True))
        qs = qs.filter(venues_count__gt=0)
        qs = qs.annotate(
            cities_count=Count(
                'cities',
                distinct=True,
                filter=Q(cities__urban_area__isnull=True) & Q(cities__places__isnull=False)
            ),
            urban_area_count=Count(
                'cities__urban_area',
                distinct=True,
                filter=Q(cities__places__isnull=False)
            )
        ).annotate(cities_and_ua=F('cities_count') + F('urban_area_count'))
        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            qs = qs.order_by(*ordering)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        qs_aggr = qs.aggregate(cities_sum=Sum('cities_and_ua'))
        ctx['country'] = Country.objects.get(slug=self.kwargs.get('country_slug'))
        ctx['cities_sum'] = qs_aggr.get('cities_sum')
        ctx['search_form'] = self.form_class()
        ctx['continent_slug'] = self.kwargs.get('continent_slug')
        ctx['country_slug'] = self.kwargs.get('country_slug')
        ctx['page_size'] = self.paginate_by
        ctx['search_name'] = self.request.GET.get('name')
        ctx['order_by'] = self.ordering[0] if self.ordering else ''
        bc_path = [
            ('/', 'Home'),
            (reverse('continent_list'), "Areas"),
        ]
        ctx['bc_path'] = bc_path
        return ctx


class RegionUpdateView(PlaceUpdateViewMixin):
    model = Region
    template_name = 'cities/region_update.html'
    permission_classes = [permissions.IsAuthenticated]
    paginate_by = 10

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['region'] = self.object
        url = f"{self.object.country.slug_en}/{self.object.slug_en}/"
        ctx['new_raisin_url'] = f"{RAISIN_NEW_WEBSITE}/en/countries/{url}"
        return ctx

    def get_success_url(self):
        return reverse('region_update', kwargs={'continent_slug': self.kwargs.get('continent_slug'),
                                                'country_slug': self.object.country.slug,
                                                'slug': self.object.slug,
                                                'language': self.kwargs.get('language')})

    def get_queryset(self):
        qs = super(RegionUpdateView, self).get_queryset()
        qs = qs.filter(country__slug=self.kwargs.get('country_slug'),
                       country__continent__slug=self.kwargs.get('continent_slug'))
        return qs

    def get_queryset_object_list(self):
        qs = City.objects.all()
        qs = qs.filter(country__slug=self.kwargs.get('country_slug'))
        qs = qs.filter(region__slug=self.kwargs.get('slug'))
        qs_ua = qs.filter(urban_area__isnull=False)
        qs_ua = qs_ua.order_by('urban_area').distinct('urban_area')
        qs_ua_ids = qs_ua.values_list('id', flat=True)
        qs_cities = qs.select_related('urban_area').filter(
            Q(urban_area__isnull=True) |
            Q(id__in=qs_ua_ids)
        )
        qs_cities = qs_cities.annotate(
            display_name=Case(
                When(urban_area__isnull=False, then='urban_area__name'),
                When(urban_area__isnull=True, then='name'),
                output_field=CharField()
            )
        )
        qs_cities = qs_cities.annotate(
            venues_count=Case(
                When(urban_area__isnull=True, then=Count('places', filter=Q(places__is_archived=False), distinct=True)),
                When(urban_area__isnull=False, then=Count('urban_area__cities__places', distinct=True)),
                output_field=IntegerField()
            ),
        ).filter(venues_count__gt=0)
        qs_cities = qs_cities.annotate(
            cities_count=Count(
                'urban_area__cities',
                distinct=True,
                filter=Q(urban_area__cities__places__isnull=False)
            )
        )
        qs_cities = qs_cities.annotate(district_count=Count(
            'districts',
            filter=Q(districts__places__isnull=False, districts__deleted=False),
            distinct=True)
        )
        return qs_cities


class UrbanAreaAndCitiesListView(ListView):
    model = City
    queryset = City.objects.all()
    paginate_by = 10
    template_name = 'cities/ua_city_list.html'
    form_class = CitySearchForm
    ordering = ['-venues_count']
    permission_classes = [permissions.IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        self.paginate_by = request.GET.get('page_size', self.paginate_by)
        return super().dispatch(request, *args, **kwargs)

    def get_ordering(self):
        self.ordering = self.request.GET.getlist('order_by', self.ordering)
        return self.ordering

    def get_queryset(self):
        qs = self.queryset
        qs = qs.filter(country__slug=self.kwargs.get('country_slug'))
        qs = qs.filter(region__slug=self.kwargs.get('slug'))
        qs_ua = qs.filter(urban_area__isnull=False)
        qs_ua = qs_ua.order_by('urban_area').distinct('urban_area')
        qs_ua_ids = qs_ua.values_list('id', flat=True)
        qs_cities = qs.select_related('urban_area').filter(
            Q(urban_area__isnull=True) |
            Q(id__in=qs_ua_ids)
        )
        qs_cities = qs_cities.annotate(
            display_name=Case(
                When(urban_area__isnull=False, then='urban_area__name'),
                When(urban_area__isnull=True, then='name'),
                output_field=CharField()
            )
        )
        qs_cities = qs_cities.annotate(
            venues_count=Case(
                When(urban_area__isnull=True, then=Count('places', filter=Q(places__is_archived=False), distinct=True)),
                When(urban_area__isnull=False, then=Count('urban_area__cities__places', distinct=True)),
                output_field=IntegerField()
            ),
        ).filter(venues_count__gt=0)
        qs_cities = qs_cities.annotate(
            cities_count=Count(
                'urban_area__cities',
                distinct=True,
                filter=Q(urban_area__cities__places__isnull=False)
            )
        )
        qs_cities = qs_cities.annotate(
            district_count=Count('districts', filter=Q(districts__places__isnull=False, districts__deleted=False),
                                 distinct=True))
        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            qs_cities = qs_cities.order_by(*ordering)
        return qs_cities

    def get_context_data(self, *, object_list=None, **kwargs):
        ctx = super(UrbanAreaAndCitiesListView, self).get_context_data(
            object_list=object_list,
            **kwargs
        )
        ctx['region'] = Region.objects.get(slug=self.kwargs.get('slug'), country__slug=self.kwargs.get('country_slug'))
        ctx['country_slug'] = self.kwargs.get('country_slug')
        ctx['continent_slug'] = self.kwargs.get('continent_slug')
        ctx['page_size'] = self.paginate_by
        ctx['search_name'] = self.request.GET.get('name')
        ctx['order_by'] = self.ordering[0] if self.ordering else ''
        bc_path = [
            ('/', 'Home'),
            (reverse('continent_list'), "Areas"),
        ]
        ctx['bc_path'] = bc_path
        return ctx


class CityUpdateView(PlaceUpdateViewMixin):
    model = City
    template_name = 'cities/city_update.html'
    permission_classes = [permissions.IsAuthenticated]
    ordering_list = ['-venues_count', 'name']

    def get_context_data(self, **kwargs):
        print('-0-')
        ctx = super().get_context_data(**kwargs)
        qs = self.object.districts.all()
        qs = qs.annotate(venues_count=Count('places', filter=Q(places__is_archived=False), distinct=True))
        qs = qs.filter(venues_count__gt=0)
        qs_obj = qs.first()
        ordering_list = [ordering_attr for ordering_attr in self.ordering_list
                         if hasattr(qs_obj, ordering_attr) or hasattr(qs_obj, ordering_attr[1:])]
        qs = qs.order_by(*ordering_list)

        page_district_size = self.get_paginate_by(qs)
        # if 'page_number' in self.request.GET:
        self.page_kwarg = 'page_number'

        if page_district_size:
            paginator, page, qs, is_paginated = self.paginate_queryset(qs, page_district_size)
            ctx['paginator_district'] = paginator
            ctx['page_district_obj'] = page
            ctx['is_paginated_district'] = is_paginated
            ctx['districts'] = qs

        else:
            ctx['paginator_district'] = None
            ctx['page_district_obj'] = None
            ctx['is_paginated_district'] = False
            ctx['districts'] = qs
        ctx['continent_slug'] = self.object.country.continent.slug
        ctx['city'] = self.object
        ctx['country'] = self.object.country
        url = f"{self.object.country.slug_en}/{self.object.region.slug_en}/{self.object.slug_en}/"
        ctx['new_raisin_url'] = f"{RAISIN_NEW_WEBSITE}/en/countries/{url}"
        return ctx

    def get_success_url(self):
        return reverse('city_update', kwargs={'continent_slug': self.kwargs.get('continent_slug'),
                                              'slug': self.object.slug,
                                              'region_slug': self.object.region.slug,
                                              'country_slug': self.object.country.slug,
                                              'language': self.kwargs.get('language')})

    def get_queryset(self):
        qs = super(CityUpdateView, self).get_queryset()
        qs = qs.filter(country__slug=self.kwargs.get('country_slug'),
                       region__slug=self.kwargs.get('region_slug'),
                       country__continent__slug=self.kwargs.get('continent_slug'))
        return qs

    def get_queryset_object_list(self):
        qs = Place.active.all()
        qs = qs.annotate(
            place_subscribed=Case(
                When(Q(subscription__status__in=PlaceHelper.place_subscribing_statuses), then=True),
                default=False,
                output_field=BooleanField()
            ),
            place_street_address=Case(
                When(Q(full_street_address__isnull=False), then='full_street_address'),
                default='street_address'
            ),
        )
        qs = qs.filter(new_city__slug=self.kwargs.get('slug'), new_city__region__slug=self.kwargs.get('region_slug'))
        qs = qs.select_related('new_city', 'new_city__urban_area',
                               'new_city__country', 'district')
        return qs

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.fields.append('admin_level')

    def form_valid(self, form):
        object = self.get_object()
        if not object.admin_level and form.cleaned_data.get('admin_level'):
            object.admin_level = form.cleaned_data.get('admin_level')
            object.save()
            add_districts_to_venues.delay(object.id)
        elif object.admin_level and not form.cleaned_data.get('admin_level'):
            object.admin_level = form.cleaned_data.get('admin_level')
            object.save()
            delete_districts_from_venues(object.id)
        elif object.admin_level and form.cleaned_data.get('admin_level') and \
                int(object.admin_level) != int(form.cleaned_data.get('admin_level')):
            object.admin_level = form.cleaned_data.get('admin_level')
            object.save()
            delete_districts_from_venues(object.id)
            add_districts_to_venues.delay(object.id)
        return super().form_valid(form)


class UrbanAreaUpdateView(PlaceUpdateViewMixin):
    model = UrbanArea
    template_name = 'cities/ua_update.html'
    permission_classes = [permissions.IsAuthenticated]
    paginate_by = 10
    ordering = ['-venues_count']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['continent_code'] = self.kwargs.get('code')
        ctx['country'] = Country.objects.get(slug=self.kwargs.get('country_slug'))
        ctx['region'] = Region.objects.get(slug=self.kwargs.get('region_slug'))
        ctx['country'] = Country.objects.get(slug=self.kwargs.get('country_slug'))
        ctx['country_slug'] = self.kwargs.get('country_slug')
        ctx['urban_area_name'] = self.object.name
        return ctx

    def get_success_url(self):
        return reverse('ua_update', kwargs={'continent_slug': self.kwargs.get('continent_slug'),
                                            'pk': self.object.id,
                                            'region_slug': self.kwargs.get('region_slug'),
                                            'country_slug': self.kwargs.get('country_slug'),
                                            'language': self.kwargs.get('language')})

    def get_queryset_object_list(self):
        qs = City.objects.all()
        qs = qs.select_related('urban_area')
        qs = qs.filter(
            urban_area=self.object,
            country__slug=self.kwargs.get('country_slug')
        )
        qs = qs.annotate(venues_count=Count('places', filter=Q(places__is_archived=False), distinct=True))
        qs = qs.annotate(
            district_count=Count('districts', filter=Q(districts__places__isnull=False, districts__deleted=False),
                                 distinct=True))
        qs = qs.filter(venues_count__gt=0)
        qs = qs.prefetch_related('districts')
        return qs


class CitiesByUAListView(ListView):
    model = City
    queryset = City.objects.all()
    paginate_by = 10
    template_name = 'cities/city_by_ua_list.html'
    form_class = CitySearchForm
    ordering = ['-venues_count']
    permission_classes = [permissions.IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        self.paginate_by = request.GET.get('page_size', self.paginate_by)
        return super().dispatch(request, *args, **kwargs)

    def get_ordering(self):
        self.ordering = self.request.GET.getlist('order_by', self.ordering)
        return self.ordering

    def get_queryset(self):
        # form = self.form_class(self.request.GET)
        qs = self.queryset
        qs = qs.select_related('urban_area')
        qs = qs.filter(
            urban_area__name=self.kwargs.get('name'),
            country__slug=self.kwargs.get('country_slug')
        )
        # if form.is_valid():
        #     qs = qs.filter(
        #         name__icontains=form.cleaned_data['name']
        #     )
        qs = qs.annotate(venues_count=Count('places', filter=Q(places__is_archived=False), distinct=True))
        qs = qs.annotate(district_count=Count('districts', filter=Q(districts__deleted=False, places__isnull=False),
                                              distinct=True))
        qs = qs.filter(venues_count__gt=0)
        qs = qs.prefetch_related('districts')
        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            qs = qs.order_by(*ordering)
        return qs

    def get_context_data(self, *, object_list=None, **kwargs):
        ctx = super(CitiesByUAListView, self).get_context_data(
            object_list=object_list,
            **kwargs
        )
        ctx['region'] = Region.objects.get(slug=self.kwargs.get('region_slug'))
        ctx['country'] = Country.objects.get(slug=self.kwargs.get('country_slug'))
        ctx['country_slug'] = self.kwargs.get('country_slug')
        ctx['continent_slug'] = self.kwargs.get('continent_slug')
        ctx['urban_area_name'] = self.kwargs.get('name')
        # ctx['urban_area'] = UrbanArea.objects.filter(name=self.kwargs.get('name'))
        ctx['page_size'] = self.paginate_by
        ctx['search_name'] = self.request.GET.get('name')
        ctx['order_by'] = self.ordering[0] if self.ordering else ''
        bc_path = [
            ('/', 'Home'),
            (reverse('continent_list'), "Areas"),
        ]
        ctx['bc_path'] = bc_path
        return ctx


class VenuesByCityListView(ListView):
    model = Place
    queryset = Place.active.all()
    template_name = 'cities/venues_list.html'
    paginate_by = 50
    ordering = ['name']
    form_class = VenueSearchFrom
    permission_classes = [permissions.IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        self.paginate_by = request.GET.get('page_size', self.paginate_by)
        return super().dispatch(request, *args, **kwargs)

    def get_ordering(self):
        self.ordering = self.request.GET.getlist('order_by', self.ordering)
        return self.ordering

    def get_queryset(self):
        qs = self.queryset
        qs = qs.annotate(
            place_subscribed=Case(
                When(Q(subscription__status__in=PlaceHelper.place_subscribing_statuses), then=True),
                default=False,
                output_field=BooleanField()
            ),
            place_street_address=Case(
                When(Q(full_street_address__isnull=False), then='full_street_address'),
                default='street_address'
            ),
        )
        qs = qs.filter(new_city__slug=self.kwargs.get('slug'), new_city__region__slug=self.kwargs.get('region_slug'))
        qs = qs.select_related('new_city', 'new_city__urban_area',
                               'new_city__country')
        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            qs = qs.order_by(*ordering)
        return qs

    def get_context_data(self, *, object_list=None, **kwargs):
        ctx = super(VenuesByCityListView, self).get_context_data(
            object_list=object_list,
            **kwargs
        )
        ctx['city'] = City.objects.get(slug=self.kwargs.get('slug'),
                                       country__slug=self.kwargs.get('country_slug'),
                                       region__slug=self.kwargs.get('region_slug'))
        ctx['country'] = Country.objects.get(slug=self.kwargs.get('country_slug'))
        ctx['continent_slug'] = self.kwargs.get('continent_slug')
        ctx['page_size'] = str(self.paginate_by)
        ctx['search_name'] = self.request.GET.get('name')
        ctx['order_by'] = self.ordering[0] if self.ordering else ''
        bc_path = [
            ('/', 'Home'),
            (reverse('continent_list'), "Areas"),
        ]
        ctx['bc_path'] = bc_path
        return ctx


class DistrictListView(ListView):
    model = District
    queryset = District.objects.all()
    template_name = 'cities/district_list.html'
    paginate_by = 10
    ordering = ['-venues_count']
    form_class = DistrictSearchFrom
    permission_classes = [permissions.IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        self.paginate_by = request.GET.get('page_size', self.paginate_by)
        return super().dispatch(request, *args, **kwargs)

    def get_ordering(self):
        self.ordering = self.request.GET.getlist('order_by', self.ordering)
        return self.ordering

    def get_queryset(self):
        qs = self.queryset
        qs = qs.filter(city__slug=self.kwargs.get('city_slug'), city__region__slug=self.kwargs.get('region_slug'))
        qs = qs.annotate(venues_count=Count('places', filter=Q(places__is_archived=False), distinct=True))
        qs = qs.filter(venues_count__gt=0)
        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            qs = qs.order_by(*ordering)
        return qs

    def get_context_data(self, *, object_list=None, **kwargs):
        ctx = super(DistrictListView, self).get_context_data(
            object_list=object_list,
            **kwargs
        )
        ctx['city'] = City.objects.get(slug=self.kwargs.get('city_slug'),
                                       country__slug=self.kwargs.get('country_slug'),
                                       region__slug=self.kwargs.get('region_slug'))
        ctx['country'] = Country.objects.get(slug=self.kwargs.get('country_slug'))
        ctx['continent_slug'] = self.kwargs.get('continent_slug')
        ctx['page_size'] = str(self.paginate_by)
        ctx['search_name'] = self.request.GET.get('name')
        ctx['order_by'] = self.ordering[0] if self.ordering else ''
        bc_path = [
            ('/', 'Home'),
            (reverse('continent_list'), "Areas"),
        ]
        ctx['bc_path'] = bc_path
        return ctx


class DistrictUpdateView(PlaceUpdateViewMixin):
    model = District
    template_name = 'cities/district_update.html'
    permission_classes = [permissions.IsAuthenticated]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['continent_slug'] = self.object.city.country.continent.slug
        ctx['city'] = self.object.city
        ctx['country'] = self.object.city.country
        return ctx

    def get_success_url(self):
        return reverse('district_update', kwargs={'continent_slug': self.kwargs.get('continent_slug'),
                                                  'slug': self.object.slug,
                                                  'region_slug': self.object.city.region.slug,
                                                  'country_slug': self.object.city.country.slug,
                                                  'city_slug': self.object.city.slug,
                                                  'language': self.kwargs.get('language')})

    def get_queryset_object_list(self):
        qs = Place.active.all()
        qs = qs.annotate(
            place_subscribed=Case(
                When(Q(subscription__status__in=PlaceHelper.place_subscribing_statuses), then=True),
                default=False,
                output_field=BooleanField()
            ),
            place_street_address=Case(
                When(Q(full_street_address__isnull=False), then='full_street_address'),
                default='street_address'
            ),
        )
        qs = qs.filter(district=self.object)
        qs = qs.select_related('new_city', 'new_city__urban_area',
                               'new_city__country')
        return qs


class DistrictCreateView(FormView):
    form_class = DistrictCreateForm

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        city = City.objects.get(slug=self.kwargs.get('city_slug'))
        return reverse('city_update', kwargs={'continent_slug': city.country.continent.slug,
                                              'slug': city.slug,
                                              'region_slug': city.region.slug,
                                              'country_slug': city.country.slug,
                                              'language': self.kwargs.get('language')})
