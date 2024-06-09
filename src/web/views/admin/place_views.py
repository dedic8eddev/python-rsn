import datetime as dt
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, generics
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from my_chargebee.serializers import SubscriptionSerializer
from web.constants import PlaceStatusE, SpecialStatusE, StatusE, UserStatusE, \
    PlaceSourceInfoE
from web.forms.admin_forms import AdminPlaceForm, CommentViewForm
from web.models import Comment, Place, PlaceImage
from web.serializers.places import RightPanelPlaceSerializer, \
    RightPanelPlaceSubscriptionSerializer, RightPanelCheckSubcriptionSerializer
from web.serializers.users import RightPanelUserUpdateSerializer, \
    RightPanelUserReadSerializer
from web.utils.geoloc import set_address_data_from_cd
from web.utils.mentions import strip_description_update_user_mentions_indexes
from web.utils.ocr_tools import (duplicate_wls_for_place,
                                 move_uploaded_temp_winelists,
                                 update_place_score)
from web.utils.temp_images import (create_temp_directory_if_not_exists,
                                   move_uploaded_temp_files)
from web.views.admin.common import get_c
from cities.models import (Country, City, Region)
from django.contrib.gis.geos import Point
from raisin.settings import RAISIN_NEW_WEBSITE


# /places
@login_required
def places(request):
    c = get_c(request=request, active='list_places', path='/', add_new_url='add_place')
    c["google_api_key"] = settings.GOOGLE_API_KEY
    return render(request, "lists/places.html", c)


# /subscribers
@login_required
def places_subscribers(request):
    c = get_c(request=request, active='list_places_subscribers', path='/', add_new_url='add_place')
    return render(request, "lists/places-subscribers.html", c)


# /place/add
@login_required
@csrf_protect
def add_place(request):
    c = get_c(request=request, active='list_places', path='/add')

    place = Place(
        author=c['current_user'],
        status=PlaceStatusE.DRAFT
    )

    if request.method == 'POST':
        request_data = request.POST.copy()
        # if request_data.get('district') == 'new':
        #     request_data['district'] = None
        form = AdminPlaceForm(request_data, instance=place)
        if form.is_valid():
            cd = form.cleaned_data

            place.expert = c['current_user']
            place.is_expert_modified = True
            place.src_info = PlaceSourceInfoE.REGISTERED_ON_CMS

            # this is a new place, so if its status is PUBLISHED or SUBSCRIBER,
            # we can set validated_xxxx without any hesitation
            if cd['status'] in [PlaceStatusE.SUBSCRIBER,
                                PlaceStatusE.PUBLISHED]:
                place.validated_by = request.user
                place.validated_at = dt.datetime.now()
            set_address_data_from_cd(cd, place)

            if not form.cleaned_data.get('new_city') and form.cleaned_data.get('city') and \
                    form.cleaned_data.get('country'):
                try:
                    country = Country.objects.get(name=form.cleaned_data.get('country'))
                    if form.cleaned_data.get('state'):
                        try:
                            region = Region.objects.get(name=form.cleaned_data.get('state'), country=country)
                        except Region.DoesNotExist:
                            region = Region(
                                name=form.cleaned_data.get('state'),
                                name_std=form.cleaned_data.get('state'),
                                country=country
                            )
                            region.save()
                    else:
                        region = None
                    location = Point(form.cleaned_data.get('longitude', 0), form.cleaned_data.get('latitude', 0),
                                     srid=4326)
                    city = City(
                        name=form.cleaned_data.get('city'),
                        name_std=form.cleaned_data.get('city'),
                        location=location,
                        region=region,
                        country=country
                    )
                    city.save()
                    place.new_city = city
                    form.cleaned_data['new_city'] = city
                except Country.DoesNotExist:
                    pass

            # if form.cleaned_data.get('new_city'):
            #     if not form.cleaned_data.get('district') and form.cleaned_data.get('new_district_name'):
            #         location = Point(form.cleaned_data.get('longitude', 0), form.cleaned_data.get('latitude', 0),
            #                          srid=4326)
            #         district = District(
            #             city=form.cleaned_data.get('new_city'),
            #             location=location,
            #             name=form.cleaned_data.get('new_district_name'),
            #             name_std=form.cleaned_data.get('new_district_name'),
            #             population=0
            #         )
            #         district.save()
            #         place.district = district
            # if str(cd['latitude']) and str(cd['longitude']) and \
            #         (not cd['country_iso_code'] or cd['country_iso_code'] != 'JP'):
            #     address_data_latlng = get_address_data_for_latlng(cd['latitude'], cd['longitude'])
            #     if address_data_latlng['country']:
            #         place.country = address_data_latlng['country']
            #     if address_data_latlng['iso']:
            #         place.country_iso_code = address_data_latlng['iso']
            #     if address_data_latlng['city'] and address_data_latlng['quality'] < 3:
            #         place.city = address_data_latlng['city']
            #     if address_data_latlng['state'] and address_data_latlng['quality'] < 3:
            #         place.state = address_data_latlng['state']
            # elif cd['country_iso_code'] and cd['country_iso_code'] == 'JP':
            #     place.country_iso_code = cd['country_iso_code']

            if place.free_glass:
                place.free_glass_signup_date = dt.datetime.now()

            place.save(update_timezone=True)
            place.refresh_from_db()

            move_uploaded_temp_files(dir_name=cd['images_temp_dir'], category_dir_name='places',
                                     user=c['current_user'], ImageClass=PlaceImage, parent_item=place,
                                     parent_item_field_name='place', temp_image_ordering=cd['image_ordering'])

            move_uploaded_temp_winelists(temp_parent_id=cd['images_temp_dir'], dst_parent_id=place.id)

            place = Place.active.get(id=place.id)
            images = PlaceImage.active.filter(place=place).order_by('ordering')
            if images:
                place.main_image = images[0]
                place.save()
                place.refresh_from_db()

            place.refresh_from_db()

            form = AdminPlaceForm(instance=place)
            return redirect('edit_place', place.id)
    else:
        form = AdminPlaceForm(instance=place)
        dir_name = str(uuid.uuid4())
        form.fields["images_temp_dir"].initial = dir_name
        create_temp_directory_if_not_exists(dir_name, 'places')

    c["form"] = form
    c["google_api_key"] = settings.GOOGLE_API_KEY
    c["place"] = place
    c["action_url"] = reverse('add_place')
    c["is_new"] = True
    c["is_subscriber"] = place.is_subscriber()

    c["pdg_title"] = "[New place]"

    opts_in = PlaceStatusE.names

    c["pdg_options"] = [
        {'value': PlaceStatusE.DRAFT,
         'name': opts_in[PlaceStatusE.DRAFT],
         'class': 'onhold',
         'selclass': 'onhold'},
        {'value': PlaceStatusE.PUBLISHED,
         'name': opts_in[PlaceStatusE.PUBLISHED],
         'class': 'btincluded',
         'selclass': 'included'},
    ]
    return render(request, "edit/place.html", c)


# /place/edit/{id}
@login_required
@csrf_protect
def edit_place(request, id):
    c = get_c(request=request, active='list_places', path='/')
    place = Place.active.get(id=id)
    old_status = place.status
    old_free_glass = place.free_glass

    if request.method == 'POST':
        place.clear_cached()
        form = AdminPlaceForm(request.POST, instance=place)

        if form.is_valid():
            cd = form.cleaned_data

            cd['user_mentions'] = place.user_mentions
            cd = strip_description_update_user_mentions_indexes(cd, mentions_field='user_mentions')

            if cd['status'] in [
                PlaceStatusE.SUBSCRIBER, PlaceStatusE.PUBLISHED
            ] and old_status not in [
                PlaceStatusE.SUBSCRIBER, PlaceStatusE.PUBLISHED
            ] and not place.validated_at and not place.validated_by:
                place.validated_by = request.user
                place.validated_at = dt.datetime.now()
            elif (cd['status'] != PlaceStatusE.PUBLISHED or
                  cd['status'] != PlaceStatusE.SUBSCRIBER) and \
                    (old_status == PlaceStatusE.PUBLISHED or
                     old_status == PlaceStatusE.SUBSCRIBER):
                # disabled on request by JHB 06.06.2022
                # place.delete_related_items()
                pass

            if cd['status'] == SpecialStatusE.DELETE:
                place.archive()
                return redirect('list_places')
            elif cd['status'] == SpecialStatusE.DUPLICATE:
                new_place = place.duplicate()
                duplicate_wls_for_place(src_place=place, dst_place=new_place)
                return redirect("edit_place", **{'id': new_place.id})
            else:
                place.last_modifier = c['current_user']
                place.expert = c['current_user']
                place.is_expert_modified = True
                last_modified_time = dt.datetime.now()
                place.modified_time = last_modified_time
                set_address_data_from_cd(cd, place)

                if cd['status'] in [PlaceStatusE.SUBSCRIBER,
                                    PlaceStatusE.PUBLISHED]:
                    c['is_published'] = True

                place.status = cd['status']

                if place.free_glass and not old_free_glass:
                    place.free_glass_signup_date = last_modified_time

                place.save(update_timezone=True)

                images = PlaceImage.active.filter(place=place, image_area__isnull=True).order_by('ordering')
                if images:
                    place.main_image = images[0]
                    place.save()
                    place.refresh_from_db()

                place.refresh_from_db()
                form = AdminPlaceForm(instance=place)
            update_place_score(place.id)

            # ensure to save changes and Place 'post_save' signal calls to clear cached place
            place.save(update_timezone=True)
        else:
            pass
    else:
        form = AdminPlaceForm(instance=place)

    if place.last_modifier:
        c["saved_by"] = place.last_modifier
        c["saved_at"] = place.modified_time
    else:
        c["saved_by"] = place.author
        c["saved_at"] = place.created_time

    images = PlaceImage.active.filter(
        place=place, image_area__isnull=True
    ).order_by('ordering')

    c["google_api_key"] = settings.GOOGLE_API_KEY
    subscriptions = place.owner.customer.subscription_set \
        if place.owner and place.owner.customer else None
    serialized_subscriptions = SubscriptionSerializer(subscriptions, many=True)
    c['subscription'] = serialized_subscriptions.data

    c["is_new"] = False
    c["images"] = images
    c["form"] = form
    c["place"] = place
    c["action_url"] = reverse('edit_place', args=[id])
    c["pdg_title"] = place.name
    c["pdg_author"] = place.author
    c["pdg_created_at"] = place.created_time
    c["pdg_validated_at"] = place.validated_at
    c["pdg_validated_by"] = place.validated_by
    c["owner"] = place.owner
    c["is_subscriber"] = place.is_subscriber()

    opts_in = PlaceStatusE.names
    c["pdg_options"] = [
        {'value': PlaceStatusE.DRAFT, 'name': opts_in[PlaceStatusE.DRAFT], 'class': 'onhold', 'selclass': 'onhold'},  # noqa
        {'value': PlaceStatusE.PUBLISHED, 'name': opts_in[PlaceStatusE.PUBLISHED], 'class': 'btincluded', 'selclass': 'included'},  # noqa
        {'value': place.get_status_in_doubt(), 'name': _("In doubt"), 'class': 'btindoubt', 'selclass': 'indoubt'},  # noqa
        {'value': PlaceStatusE.CLOSED, 'name': _("Closed"), 'class': 'btdelete', 'selclass': 'delete'},  # noqa
        {'value': SpecialStatusE.DELETE, 'name': _("Delete"), 'class': 'btrefused', 'selclass': 'refused'},  # noqa
        {'value': SpecialStatusE.DUPLICATE, 'name': _("Duplicate"), 'class': 'btduplicate', 'selclass': 'duplicate'},  # noqa
        {'value': PlaceStatusE.SUBSCRIBER, 'name': _("Subscriber"), 'class': 'btsubscriber', 'selclass': 'subscriber'},  # noqa
        {'value': PlaceStatusE.ELIGIBLE, 'name': _("Eligible"), 'class': 'bteligible', 'selclass': 'eligible'},  # noqa
        {'value': PlaceStatusE.NOT_ELIGIBLE, 'name': _("Not eligible"), 'class': 'btnoteligible', 'selclass': 'noteligible'},  # noqa
        {'value': PlaceStatusE.IN_REVIEW, 'name': _("In review"), 'class': 'btinreview', 'selclass': 'inreview'},  # noqa
        {'value': PlaceStatusE.TO_PUBLISH, 'name': _("To publish"), 'class': 'bttopublish', 'selclass': 'topublish'}  # noqa
    ]
    c['new_raisin_url'] = f"{RAISIN_NEW_WEBSITE}/en/venue/{place.slug}/"
    c['venue_is_visible'] = place.status == PlaceStatusE.SUBSCRIBER or place.status == PlaceStatusE.PUBLISHED
    return render(request, "edit/place.html", c)


# right-panel/place/edit/{id}
class PlaceDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                  generics.GenericAPIView):
    serializer_class = RightPanelPlaceSerializer
    queryset = Place.objects.all()

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.update(request, partial=True, *args, **kwargs)


# right-panel/place/subscription/{id}
class PlaceSubscriptionDetail(mixins.RetrieveModelMixin,
                              generics.GenericAPIView):
    serializer_class = RightPanelPlaceSubscriptionSerializer
    queryset = Place.active.all()

    # get a place_id but return a Subscription object
    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)
        try:
            subscription = obj.subscription
        except (TypeError, ValueError, ValidationError):
            raise Http404
        # May raise a permission denied
        self.check_object_permissions(self.request, subscription)

        return subscription

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


# right-panel/place/owner/edit/{id}
class PlaceOwnerDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                       generics.GenericAPIView):
    serializer_class = RightPanelUserReadSerializer
    queryset = Place.active.all()

    def perform_update(self, serializer):
        return serializer.save()

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return RightPanelUserUpdateSerializer
        return self.serializer_class

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.owner:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        return JsonResponse(
            {"exception": _("There is no Owner for this venue.")},
            status=404, safe=False
        )

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=self.get_object(),
                                         data=request.data,
                                         partial=True)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_update(serializer)
        instance_serializer = self.serializer_class(
            instance,
            context=self.get_serializer_context()
        )
        return Response(instance_serializer.data)


# right-panel/check-subscription
class CheckSubscription(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RightPanelCheckSubcriptionSerializer
    queryset = Place.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['subscription']


# /est-com
@login_required
def est_comments(request):
    bc_path = [
        ('/', 'Home'),
        (reverse('list_places'), 'places'),
        (reverse('list_est_comments'), 'comments'),
    ]

    c = get_c(request=request, active='list_places', sub_active='list_est_comments',
              path="places/est-com",
              bc_path_alt=bc_path,
              add_new_url=None)

    c['total_records_places'] = Place.active.all().count()

    return render(request, "lists/est-comments.html", c)


# /est-com/view/{id}
def view_comment(request, id):
    comment = Comment.active.get(id=id)

    count_all_places = Place.active.all().count()

    bc_path = [
        ('/', 'LAST PUBLISHED PLACES: %d' % count_all_places),
        (reverse('list_est_comments'), 'Comments'),
        (reverse('view_comment', args=[id]), 'Comment - Posted by: %s' % comment.author)
    ]

    c = get_c(request=request,
              active='list_places',
              path=None,
              bc_path_alt=bc_path,
              sub_active='list_est_comments')

    bc_desc = '<a href="%s">LAST PUBLISHED PLACES: %d</a> - <a class="caption-est-comments" href="%s">Comments</a> - ' \
              'Comment - Posted by %s</a>' % (reverse('list_places'),
                                              count_all_places,
                                              reverse('list_est_comments'),
                                              comment.author)

    data_in = {
        'description': comment.description,
        'status': SpecialStatusE.UNBAN_USER if comment.author.status == UserStatusE.BANNED else comment.status
    }

    if request.method == 'POST':
        form = CommentViewForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            if cd['status'] == SpecialStatusE.DELETE:
                comment.archive()
                return redirect('list_est_comments')
            elif cd['status'] == SpecialStatusE.BAN_USER and comment.author.status != UserStatusE.BANNED \
                    and comment.author != request.user:
                comment.author.status = UserStatusE.BANNED
                comment.author.save()

                comment.author.refresh_from_db()
                comment.refresh_from_db()
            elif cd['status'] == SpecialStatusE.UNBAN_USER and comment.author.status == UserStatusE.BANNED:
                comment.author.status = UserStatusE.ACTIVE
                comment.author.save()

                comment.author.refresh_from_db()
                comment.refresh_from_db()

            data_in = {
                'description': comment.description,
                'status': SpecialStatusE.UNBAN_USER if comment.author.status == UserStatusE.BANNED else comment.status
            }

            form = CommentViewForm(data=data_in)
    else:
        form = CommentViewForm(data=data_in)

    c['form'] = form
    c['comment'] = comment
    c["saved_by"] = comment.author
    c["saved_at"] = comment.modified_time
    c["action_url"] = reverse('view_comment', args=[id])
    c["pdg_title"] = bc_desc

    if comment.author != request.user:
        if comment.author.status == UserStatusE.BANNED:
            ban_or_unban = {
                'value': SpecialStatusE.UNBAN_USER, 'name': _("Un-Ban Author"), 'class': 'onhold', 'selclass': 'onhold'
            }
        else:
            ban_or_unban = {
                'value': SpecialStatusE.BAN_USER, 'name': _("Ban Author"), 'class': 'onhold', 'selclass': 'onhold'
            }

        c["pdg_options"] = [
            {'value': StatusE.PUBLISHED, 'name': _("Published"), 'class': 'btincluded', 'selclass': 'included'},
            {'value': SpecialStatusE.DELETE, 'name': _("Delete"), 'class': 'btrefused', 'selclass': 'refused'},
            ban_or_unban,
        ]
    else:
        c["pdg_options"] = [
            {'value': StatusE.PUBLISHED, 'name': _("Published"), 'class': 'btincluded', 'selclass': 'included'},
            {'value': SpecialStatusE.DELETE, 'name': _("Delete"), 'class': 'btrefused', 'selclass': 'refused'},
        ]

    return render(request, "edit/view_comment.html", c)
