from email.policy import default
import json

from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django.core.exceptions import ValidationError
from django.forms import Textarea, TextInput
from django.utils.translation import ugettext_lazy as _

from my_chargebee.models import Customer, Subscription
from web.constants import (CalEventTypeE, PlaceStatusE, PostTypeE, UserTypeE,
                           WineColorE, WinemakerStatusE,
                           get_original_language_choices,
                           get_pro_language_choices,
                           get_selected_language_choices)
from web.forms.common import strip_cleaned_data
from web.models import (CalEvent, Comment, Place, Post, UserProfile, Wine,
                        Winemaker)
from web.utils.form_tools import (FieldItemCollectionManager,
                                  WinemakerWineItemField, validate_password,
                                  wine_item_ordered_field_mapping)
from web.utils.model_tools import beautify_place_name


def winemakers_to_choices_with_draft_and_opt_none(objects, opt_none_label=""):
    objects_out = []
    objects_out.append((None, opt_none_label))

    objects = objects.only('status', 'name', 'domain', 'pk')
    objs = objects.values('status', 'name', 'domain', 'pk')

    for item in objs:
        if item['status'] == WinemakerStatusE.VALIDATED:
            name_str = "%s [%s]" % (item['name'], item['domain']) if item['domain'] else "%s [no domain]" % item['name']
        else:
            name_str = "%s: %s [DRAFT]" % (item['name'], item['domain']) if item['domain'] else "%s [DRAFT]" % item['name']

        objects_out.append((item['pk'], name_str))

    return objects_out


class AjaxFileDeleteForm(forms.Form):
    id = forms.IntegerField(required=True)


class AjaxFileIdForm(forms.Form):
    id = forms.IntegerField(required=True)


class AjaxTempFileDeleteForm(forms.Form):
    filename = forms.CharField(required=True)
    temp_image_ordering = forms.CharField(required=False)


class AjaxTempFileRefreshForm(forms.Form):
    temp_image_ordering = forms.CharField(required=False)


class AjaxFileUploadForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=True)
    parent_id = forms.CharField(required=False)


class AjaxDataFileUploadForm(forms.Form):
    parent_id = forms.CharField(required=True)
    # image_id = forms.CharField(required=False)
    name = forms.CharField(required=True)
    editor_name = forms.CharField(required=True)
    data = forms.CharField(required=False)


class AjaxWinelistFileUploadForm(forms.Form):
    winelist_file_id = forms.IntegerField(required=True)
    parent_id = forms.CharField(required=False)
    is_temp = forms.BooleanField(required=False)
    is_in_shared_pool = forms.BooleanField(required=False)


class AjaxTempFileUploadForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=True)
    dir_name = forms.CharField(required=True)


# for AJAX lists
class AjaxListForm(forms.Form):
    order = forms.CharField(required=False)
    limit = forms.IntegerField(required=False)
    page = forms.IntegerField(required=False)
    start = forms.IntegerField(required=False)
    length = forms.IntegerField(required=False)


class ImageOrderingForm(forms.Form):
    parent_item_id = forms.IntegerField(required=True)
    ids = forms.CharField()


class PlaceImageOrderingForm(ImageOrderingForm):
    pass


class WinemakerImageOrderingForm(ImageOrderingForm):
    pass


class AdminUserProfileForm(forms.ModelForm):
    password_plain = forms.CharField(
        widget=forms.PasswordInput(
            attrs=dict(required=False, render_value=False)
        ),
        label=_("Password"), required=False, min_length=6, max_length=30
    )

    website_url = forms.URLField()

    lang = forms.ChoiceField(
        required=True, widget=forms.Select,
        label=_("Current language"),
        choices=get_pro_language_choices()
    )

    image_avatar = forms.ImageField(required=False)

    place = forms.ModelChoiceField(
        required=False,
        label="Establishment",
        queryset=Place.active.filter(
            status__in=[
                PlaceStatusE.SUBSCRIBER,
                PlaceStatusE.PUBLISHED]
        ).order_by('name')
    )

    customer = forms.CharField(
        label=_("Chargebee Customer ID"), required=False, min_length=5,
        max_length=50,
    )

    subscription = forms.ModelChoiceField(
        required=False,
        label="Chargebee Subscription ID",
        queryset=Subscription.objects.all()
    )

    secondary_emails = SimpleArrayField(
        forms.EmailField(required=True),
        required=False,
        label=_("Additional emails")
    )

    formitable_url = forms.URLField()

    field_order = ['customer', 'place', 'subscription']

    def clean_password_plain(self):
        if not self.cleaned_data['password_plain']:
            self.cleaned_data.pop('password_plain')

            return ''

        return validate_password(self.cleaned_data, 'password_plain')

    class Meta:
        model = UserProfile
        fields = [
            'username', 'email', 'type', 'status', 'full_name',
            'description', 'lang', 'website_url', 'customer', 'subscription',
            'secondary_emails', 'formitable_url',
        ]

        labels = {
            "full_name": _("Name"),
            "username": _("Username"),
            "email": _("Email"),
            "website_url": _("URL Website"),
            "password_plain": _("Password"),
            "type": _("Status:"),
            "status": "",
            "customer": _("Chargebee Customer ID"),
            "subscription": _("Chargebee Subscription ID"),
            "formitable_url": _("Formitable UID (url)"),
        }

        widgets = {
            "description": Textarea(attrs={"placeholder": _("Type in your message")}),
            "status": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        place = kwargs.pop('place') if 'place' in kwargs else None
        allNonRequired = kwargs.pop('allNonRequired', False)

        # 'notify_likes', 'notify_drank_it_toos', 'notify_comments', 'notify_wine_reviewed'
        not_required_fields = ['website_url', 'customer', 'subscription', 'formitable_url']
        super(AdminUserProfileForm, self).__init__(*args, **kwargs)
        self.fields['type'].choices = UserTypeE.pairs
        self.fields['email'].required = True

        if place:
            self.fields['place'].initial = place

        if place and place.subscription:
            self.fields['subscription'].initial = place.subscription

        if allNonRequired:
            not_required_fields = self.fields
        for nr_field in not_required_fields:
            self.fields[nr_field].required = False

    def clean_email(self):
        value = self.cleaned_data['email']
        if not value:
            return None
        if self.instance:
            users_count = UserProfile.objects.filter(email=value).exclude(id=self.instance.id).count()
        else:
            users_count = UserProfile.objects.filter(email=value).count()
        if users_count > 0:
            msg = 'Email already exists.'
            raise ValidationError(msg)
        else:
            return value

    def clean_username(self):
        value = self.cleaned_data['username']
        if not value:
            return None
        if self.instance:
            users_count = UserProfile.objects.filter(username=value).exclude(id=self.instance.id).count()
        else:
            users_count = UserProfile.objects.filter(username=value).count()
        if users_count > 0:
            msg = _('A user with that username already exists.')
            raise ValidationError(msg)
        else:
            return value

    def clean_customer(self):
        value = self.cleaned_data['customer']
        place = self.instance.place_owner.first()

        if not value or value == '':
            if place and place.subscription:
                place.subscription = None
                place.save()

            return None

        try:
            customer = Customer.objects.get(id=value)
        except Customer.DoesNotExist:
            msg = _('This Chargebee Customer ID is invalid.')
            raise ValidationError(msg)

        if self.instance:
            customer_users_count = UserProfile.objects.filter(
                customer=value
            ).exclude(id=self.instance.id).count()

            for establishment in self.instance.place_owner.all():
                if establishment.subscription \
                        and establishment.subscription.customer != customer:
                    establishment.subscription = None

        else:
            customer_users_count = UserProfile.objects.filter(
                customer=value
            ).count()

        # commented until one user - more establishemnts is implemented
        # if customer_users_count > 0:
        #     msg = _('Customer ID is already assigned to another user.')
        #     raise ValidationError(msg)

        return customer

    def clean_subscription(self):
        subscription = self.cleaned_data['subscription']
        customer = self.cleaned_data.get('customer')
        place = self.instance.place_owner.first()
        target_place = self.cleaned_data.get('place')
        excluded_places = [place, target_place]
        excl_places_id = []
        for p in excluded_places:
            if p:
                excl_places_id.append(p.id)

        if not subscription or not customer:
            return

        if subscription.customer != customer:
            msg = _('The Customer ID assigned to this Subscription is '
                    'other than the Customer ID assigned to the user.')
            raise ValidationError(msg)

        if (place or target_place) and subscription:
            subscription_places_count = Place.active.filter(
                subscription=subscription
            ).exclude(id__in=excl_places_id).count()
        else:
            subscription_places_count = Place.active.filter(
                subscription=subscription
            ).count()

        if subscription_places_count > 0:
            msg = _('Subscription ID is already assigned to another place.') # noqa
            raise ValidationError(msg)

        return subscription

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data['type']
        place = cleaned_data.get('place', None)

        if user_type != UserTypeE.OWNER:
            return cleaned_data

        if cleaned_data.get('lang') == 'JA':
            self.add_error(
                'place',
                _("PRO is not supported for Japanese language.")
            )

        if not place:
            self.add_error(
                'place',
                _("You must connect this owner to an establishment")
            )

        old_place = self.instance.place_owner.all().first() \
            if self.instance and self.instance.place_owner.all().first() \
            else None

        if old_place and old_place != place and old_place.subscription:
            old_place.subscription = None
            old_place.save()

        return cleaned_data


class AdminPlaceForm(forms.ModelForm):
    images_temp_dir = forms.CharField(required=False, widget=forms.HiddenInput)
    image_ordering = forms.CharField(required=False, widget=forms.HiddenInput)
    secondary_emails = SimpleArrayField(
        forms.EmailField(required=True),
        required=False,
        label=_("Additional emails")
    )
    new_city_name = forms.CharField(required=False, widget=forms.HiddenInput)
    new_district_name = forms.CharField(required=False, widget=forms.HiddenInput(attrs={'placeholder': 'Type a new District name'}))

    def get_is_30_p_natural_already(self, obj):
        return not obj.is_30_p_natural_already

    class Meta:
        model = Place
        fields = ['name', 'type', 'description',
                  'full_street_address', 'street_address', 'house_number', 'zip_code',
                  'city', 'country', 'country_iso_code', 'state',
                  'phone_number', 'website_url', 'email',
                  'latitude', 'longitude',
                  'pin_latitude', 'pin_longitude',
                  'social_facebook_url', 'social_twitter_url', 'social_instagram_url',
                  'sticker_sent', 'team_comments',
                  'is_bar', 'is_restaurant', 'is_wine_shop', 'status', 'free_glass',
                  'is_30_p_natural_already', 'secondary_emails', 'new_city', 'district']

        labels = {
            "name": _("Name:"),
            "phone_number": _("Phone"),
            "type": _("Select a type"),
            "website_url": _("URL Website:"),
            "social_facebook_url": _("Facebook:"),
            "social_twitter_url": _("Twitter:"),
            "social_instagram_url": _("Instagram:"),
            "email": _("Email:"),
            "sticker_sent": _("Sticker sent:"),
            "description": _("Description:"),
            "is_bar": _("Bar"),
            "is_restaurant": _("Restaurant"),
            "is_wine_shop": _("Wine shop"),
            "team_comments": _("Comments by team"),
            "free ": _("Comments by team"),
            'is_30_p_natural_already': _("Not yet 30%"),
        }

        widgets = {
            'team_comments': Textarea(attrs={"placeholder": _("Comments by team")}),
            'full_street_address': forms.HiddenInput(),
            'street_address': forms.HiddenInput(),
            'house_number': forms.HiddenInput(),
            'zip_code': forms.HiddenInput(),
            'city': forms.HiddenInput(),
            'country': forms.HiddenInput(),
            'country_iso_code': forms.HiddenInput(),
            'state': forms.HiddenInput(),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'pin_latitude': forms.HiddenInput(),
            'pin_longitude': forms.HiddenInput(),
            'status': forms.HiddenInput(),
            'is_bar': forms.CheckboxInput(),
            'is_restaurant': forms.CheckboxInput(),
            'is_wine_shop': forms.CheckboxInput(),
            'is_30_p_natural_already': forms.CheckboxInput(),
            'new_city': forms.HiddenInput(),
            'district': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super(AdminPlaceForm, self).__init__(*args, **kwargs)
        self.fields['district'].choices = [('', '--No District--')]
        # if 'instance' in kwargs and kwargs['instance']:
        if kwargs.get('instance'):
            instance = kwargs.get('instance')
            instance.name = beautify_place_name(instance.name)
            if instance.new_city:
                districts = instance.new_city.districts.all()
                for district in districts:
                    self.fields['district'].choices.append((district.id, district.name))

        allNonRequired = kwargs.pop('allNonRequired', False)

        not_required_fields = [
            'full_street_address', 'street_address', 'house_number', 'zip_code',
            'city', 'country', 'country_iso_code',
            'phone_number', 'website_url', 'email',
            'latitude', 'longitude',
            'pin_latitude', 'pin_longitude',
            'social_facebook_url', 'social_twitter_url', 'social_instagram_url',
            'is_bar', 'is_restaurant', 'is_wine_shop', 'type', 'status',
            'is_30_p_natural_already',
        ]
        # super(AdminPlaceForm, self).__init__(*args, **kwargs)

        if allNonRequired:
            not_required_fields = self.fields
        for nr_field in not_required_fields:
            self.fields[nr_field].required = False
            self.fields['description'].strip = False

    def clean_uploaded_file_names(self):
        uploaded_file_names = self.cleaned_data['uploaded_file_names']

        if not uploaded_file_names:
            return None

        try:
            uploaded_file_names_array = json.loads(uploaded_file_names)
        except ValueError:
            raise forms.ValidationError(_("invalid uploaded file names"))

        if not uploaded_file_names_array:
            raise forms.ValidationError(_("invalid uploaded file names"))

        return uploaded_file_names_array

    def clean(self):
        cleaned_data = strip_cleaned_data(self.cleaned_data, ['name', 'city', 'street_address',
                                                              'full_street_address'])

        return cleaned_data


class WineItemHandlingForm(forms.Form):
    auto_id = 'wines'

    def __init__(self, *args, **kwargs):
        if 'initial_row_number' in kwargs:
            initial_row_number = kwargs['initial_row_number']
            del kwargs['initial_row_number']
        else:
            initial_row_number = 0

        ordered_field_mapping = wine_item_ordered_field_mapping

        temp_fields = ['wine_temp_dir']

        super(WineItemHandlingForm, self).__init__(*args, **kwargs)

        self.wines = FieldItemCollectionManager(self, FieldItemClass=WinemakerWineItemField,
                                                field_prefix="wines_", field_match='wines_([0-9]+)_([0-9]+)',
                                                args_form=args, initial_row_number=initial_row_number,
                                                ordered_field_mapping=ordered_field_mapping, temp_fields=temp_fields)


class AdminWinemakerForm(forms.ModelForm):
    auto_id = 'wines'

    images_temp_dir_wm = forms.CharField(required=False, widget=forms.HiddenInput)
    image_ordering = forms.CharField(required=False, widget=forms.HiddenInput)
    current_translations = forms.CharField(required=False, widget=forms.HiddenInput)

    original_language = forms.ChoiceField(required=False, widget=forms.Select,
                                          label=_('Original language'),
                                          choices=get_original_language_choices())
    selected_language = forms.ChoiceField(required=False, widget=forms.Select,
                                          label=_('Selected language'),
                                          choices=get_selected_language_choices())

    class Meta:
        model = Winemaker
        fields = [
            # 'author',

            'name',
            'name_short',
            'description',
            'team_comments',
            'domain',
            'domain_short',

            'full_street_address',
            'street_address',
            'house_number',
            'zip_code',
            'city',
            'state',
            'country',
            'country_iso_code',
            'region',
            'phone_number',
            'website_url',
            'email',
            'latitude',
            'longitude',
            'pin_latitude',
            'pin_longitude',
            'social_facebook_url',
            'social_twitter_url',
            'social_instagram_url',
            'status',
            # A3-A4-A5:
            'is_organic',
            'is_biodynamic',
            'certified_by',
            'wine_trade',
            'plough_horse',
            'domain_description',
        ]

        labels = {
            "name": _("Winemaker"),
            "domain": _("Domain"),
            "name_short": _("Shortened Winemaker"),
            "domain_short": _("Shortened Domain"),
            "phone_number": _("Phone"),
            "region": _("Wine Region"),
            "website_url": _("URL Website"),
            "social_facebook_url": _("Facebook"),
            "social_twitter_url": _("Twitter"),
            "social_instagram_url": _("Instagram"),
            "email": _("Email"),
            "description": _("Description"),
            "full_street_address": _("Full street address"),
            "team_comments": _("Comments by team"),
            # A3-A4-A5:
            "is_organic": _("organic"),
            "is_biodynamic": _("biodynamic"),
            "certified_by": _("Certified by"),
            "wine_trade": _("trade wine"),
            "plough_horse": _("Plough horse"),
            "domain_description": _("Domain"),
        }

        widgets = {
            "description": Textarea(attrs={"placeholder": _("Type in your message")}),
            'team_comments': Textarea(attrs={"placeholder": _("Comments by team")}),

            "phone_number": TextInput(attrs={"placeholder": _("ex. Phone : (+33) 6 12 22 61 10")}),
            "region":  TextInput(attrs={"placeholder": _("ex : Provence")}),
            "website_url":  TextInput(attrs={"placeholder": _("Url")}),
            "social_facebook_url":  TextInput(attrs={"placeholder": _("Url")}),
            "social_twitter_url":  TextInput(attrs={"placeholder": _("Url")}),
            "social_instagram_url":  TextInput(attrs={"placeholder": _("Url")}),
            "email":  TextInput(attrs={"placeholder": _("Email")}),

            "is_organic": forms.CheckboxInput(),
            "is_biodynamic": forms.CheckboxInput(),
            "certified_by": forms.TextInput(attrs={"placeholder": _("ex : Certified by")}),
            "wine_trade": forms.CheckboxInput(),
            "plough_horse": forms.CheckboxInput(),
            "domain_description": forms.Textarea(attrs={"placeholder": _("Domain description")}),

            'full_street_address': forms.HiddenInput(),
            'street_address': forms.HiddenInput(),
            'house_number': forms.HiddenInput(),
            'zip_code': forms.HiddenInput(),
            'city': forms.HiddenInput(),
            'state': forms.HiddenInput(),
            'country': forms.HiddenInput(),
            'country_iso_code': forms.HiddenInput(),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'pin_latitude': forms.HiddenInput(),
            'pin_longitude': forms.HiddenInput(),
            'status': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        all_non_required = kwargs.pop('allNonRequired', False)

        not_required_fields = [
            'domain_short', 'name_short',
            'full_street_address', 'street_address', 'house_number', 'zip_code',
            'city', 'state', 'country', 'country_iso_code', 'region',
            'phone_number', 'website_url', 'email',
            'latitude', 'longitude',
            'pin_latitude', 'pin_longitude',
            'social_facebook_url', 'social_twitter_url', 'social_instagram_url',
            'status', 'validated_at', 'validated_by',
            'is_organic', 'is_biodynamic', 'certified_by', 'wine_trade',
            'plough_horse', 'domain_description'
        ]

        super(AdminWinemakerForm, self).__init__(*args, **kwargs)

        if self.instance and self.instance.domain_description_translations:
            self.fields['current_translations'].initial = json.dumps(self.instance.domain_description_translations)

        self.wines_coll = FieldItemCollectionManager(
            form=self,
            FieldItemClass=WinemakerWineItemField,
            field_prefix='wines_',
            field_match='wines_([0-9]+)_([0-9]+)',
            args_form=args,
            ordered_field_mapping=wine_item_ordered_field_mapping,
            temp_fields=['wine_temp_dir'])

        if all_non_required:
            not_required_fields = self.fields
        for nr_field in not_required_fields:
            if nr_field in self.fields:
                self.fields[nr_field].required = False

        self.fields['description'].strip = False

    def clean(self):
        cleaned_data = strip_cleaned_data(self.cleaned_data, ['name', 'city', 'street_address',
                                                              'region', 'domain', 'name_short', 'domain_short',
                                                              'certified_by'])
        if 'original_language' in cleaned_data:
            # original_language is for a separate AJAX
            # functionality, not for storing data
            del cleaned_data['original_language']
        if 'selected_language' in cleaned_data:
            # selected_language is for a separate AJAX
            # functionality, not for storing data
            del cleaned_data['selected_language']
        return cleaned_data


class AdminWinePostForm(forms.Form):
    image = forms.ImageField(required=False)
    wine_image = forms.ImageField(required=False)
    ref_image = forms.ImageField(required=False)

    name = forms.CharField(required=True, label=_("Wine post:"))
    name_short = forms.CharField(required=False, label=_("Wine shortened name:"))
    description = forms.CharField(required=False, strip=False, label=_("Description:"), widget=Textarea())
    team_comments = forms.CharField(required=False, label=_("Comments by team"), widget=Textarea())

    domain = forms.CharField(required=True, label=_("Domain:"))

    designation = forms.CharField(required=False, label=_("Wine Region:"))
    grape_variety = forms.CharField(required=False, label=_("Grape variety:"))
    color = forms.ChoiceField(required=True, label=_("Color:"), choices=WineColorE.pairs)
    year = forms.IntegerField(required=False, label=_("Year:"))
    is_sparkling = forms.BooleanField(required=False, label=_("Sparkling"))
    is_star_review = forms.BooleanField(required=False, label=_("Star Review"))
    is_parent_post = forms.BooleanField(required=False, label=_("Parent Post"))

    geolocation = forms.CharField(required=False, label=_("Geolocation:"))
    place_id = forms.IntegerField(widget=forms.HiddenInput, required=False)

    status = forms.IntegerField(widget=forms.HiddenInput, required=False)

    wine_trade = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    free_so2 = forms.CharField(widget=forms.TextInput, required=False, label="Free SO2 (mg/l)")
    total_so2 = forms.CharField(widget=forms.TextInput, required=False, label="Total SO2 (mg/l)")

    winemaker = forms.ModelChoiceField(required=True, queryset=Winemaker.active.all())
    original_winemaker_name = forms.CharField(required=False, label=_("Selected winemaker name:"))
    original_winemaker_open = forms.BooleanField(widget=forms.HiddenInput, required=False)
    is_organic = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    is_biodynamic = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    certified_by = forms.CharField(
        required=False,
        label=_("Certified by:"),
        widget=TextInput(
            attrs={
                "placeholder": _("Certified by:"),
                "class": "form-control"
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(AdminWinePostForm, self).__init__(*args, **kwargs)
        winemakers = Winemaker.active.none().only('status', 'name', 'domain', 'pk')
        self.fields['winemaker'].choices = winemakers_to_choices_with_draft_and_opt_none(winemakers)

    def clean(self):
        winemaker = self.cleaned_data.get('winemaker')
        if winemaker:
            winemakers = Winemaker.active.filter(id=winemaker.id).only('status', 'name', 'domain', 'pk')
            self.fields['winemaker'].choices = winemakers_to_choices_with_draft_and_opt_none(
                winemakers)
        cd = strip_cleaned_data(self.cleaned_data, ['name', 'name_short', 'domain', 'designation',
                                                    'grape_variety', 'certified_by'])
        if cd['free_so2'] and cd['free_so2'].find(','):
            cd['free_so2'] = cd['free_so2'].replace(',', '.')
        if cd['total_so2'] and cd['total_so2'].find(','):
            cd['total_so2'] = cd['total_so2'].replace(',', '.')
        return cd


class AdminGeneralPostForm(forms.ModelForm):
    image = forms.ImageField(required=False)
    GENERAL_POST_CHOICES = (
        (20, 'GENERAL (leave as such)'),
        (30, 'transfer to FOOD')
    )
    type = forms.ChoiceField(choices=GENERAL_POST_CHOICES)

    class Meta:
        model = Post
        fields = ['title', 'description', 'status', 'type']

        labels = {
            "title": _("Post:"),
            "description": _("Description:"),
        }

        widgets = {
            "description": Textarea(attrs={"placeholder": _("Type in your message")}),
            "status": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        allNonRequired = kwargs.pop('allNonRequired', False)

        not_required_fields = ['status']

        super(AdminGeneralPostForm, self).__init__(*args, **kwargs)

        if allNonRequired:
            not_required_fields = self.fields
        for nr_field in not_required_fields:
            self.fields[nr_field].required = False

        self.fields['description'].strip = False

    def clean(self):
        cleaned_data = strip_cleaned_data(self.cleaned_data, ['title'])

        return cleaned_data


class AdminFoodForm(AdminGeneralPostForm):
    def clean(self):
        cleaned_data = super(AdminFoodForm, self).clean()
        cleaned_data['type'] = PostTypeE.FOOD

        return cleaned_data


class CommentViewForm(forms.Form):
    description = forms.CharField(
        required=False, strip=False, label=_("Description"),
        widget=Textarea(attrs={
            "placeholder": _("Comment contents"),
            "readonly": True, "rows": 10, "cols": 90
            })
    )
    status = forms.IntegerField(widget=forms.HiddenInput, required=False)

    def clean(self):
        # cleaned_data = strip_cleaned_data(self.cleaned_data, ['description'])

        return self.cleaned_data


class AutocompleteAddressForm(forms.Form):
    lat = forms.CharField(required=True, label=None)
    lng = forms.CharField(required=True, label=None)
    lang = forms.CharField(required=True, label=None)


class AutocompleteAddressFormPlaceId(forms.Form):
    place_id = forms.CharField(required=True, label=None)
    lang = forms.CharField(required=True, label=None)


class EventAdminForm(forms.ModelForm):
    MAX_UPLOAD_SIZE = 2500000

    price = forms.CharField(required=False)
    external_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )

    tickets_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )

    wine_faire_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )

    loc_lat = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_pin_latitude'})
    )
    loc_lng = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_pin_longitude'})
    )

    loc_full_street_address = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'id': 'route', 'class': 'form-control'})
    )
    loc_city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'locality', 'class': 'form-control'
        })
    )
    loc_state = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'administrative_area_level_1', 'class': 'form-control'
        })
    )
    loc_zip_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'postal_code', 'class': 'form-control'
        })
    )
    loc_country = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'country', 'class': 'form-control'
        })
    )
    loc_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        }),
        label=_("Venue:")
    )

    image_event = forms.ImageField(required=False)
    gif_image_event = forms.ImageField(required=False)
    poster_image_event = forms.ImageField(required=False)

    type = forms.ChoiceField(
        required=True,
        label=_("Event type:"),
        choices=CalEventTypeE.pairs,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    external_author_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    external_submitter_email = forms.EmailField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()

        errors = {}

        if (int(cleaned_data['type']) == CalEventTypeE.EVENT and
                not cleaned_data.get('start_date')):
            errors['start_date'] = _('Start date is required for regular events.') # noqa

        if (int(cleaned_data['type']) == CalEventTypeE.EVENT and
                not cleaned_data.get('end_date')):
            errors['end_date'] = _('End date is required for regular events.')

        if (
            int(cleaned_data['type']) == CalEventTypeE.EVENT and
            not cleaned_data.get('loc_full_street_address') and
            not cleaned_data.get('loc_city')
        ):
            errors['type'] = _('Address is required for regular events.')

        image = cleaned_data.get('image_event')

        if (image and image.size > self.MAX_UPLOAD_SIZE):
            msg = _('Maximum File Size Limit is')
            limit = int(self.MAX_UPLOAD_SIZE / 1000)
            errors['image_event'] = '{} {} kB.'.format(msg, limit)

        gif_image = cleaned_data.get('gif_image_event')

        if (gif_image and gif_image.size > self.MAX_UPLOAD_SIZE):
            msg = _('Maximum File Size Limit is')
            limit = int(self.MAX_UPLOAD_SIZE / 1000)
            errors['gif_image_event'] = '{} {} kB.'.format(msg, limit)

        poster_image = cleaned_data.get('poster_image_event')

        if (poster_image and poster_image.size > self.MAX_UPLOAD_SIZE):
            msg = _('Maximum File Size Limit is')
            limit = int(self.MAX_UPLOAD_SIZE / 1000)
            errors['poster_image_event'] = '{} {} kB.'.format(msg, limit)

        if len(errors):
            raise forms.ValidationError(errors)

        return cleaned_data

    class Meta:
        model = CalEvent
        fields = ['title', 'description', 'status', 'loc_name',
                  'price', 'is_pro', 'is_featured', 'is_raisin_participating',
                  'start_date', 'end_date', 'loc_full_street_address',
                  'tickets_url', 'wine_faire_url',
                  'loc_city', 'loc_state', 'loc_zip_code', 'loc_country',
                  'loc_lat', 'loc_lng', 'type',
                  'external_url', 'use_external_link', 'external_author_name',
                  'external_submitter_email']

        labels = {
            "title": _("Event:"),
            "description": _("Description:"),
            'is_pro': _('Pro only'),
            'is_featured': _('Featured Event'),
            'is_raisin_participating': _('Raisin is participating'),
            'start_date': _("Start date:"),
            'end_date': _("End date:"),
            'price': _("Price:"),
            'tickets_url': _("Tickets link"),
            'wine_faire_url': _("Wine faire link"),
        }

        widgets = {
            "title": forms.TextInput(attrs={'class': 'form-control'}),
            "description": Textarea(
                attrs={"placeholder": _("Type in your message")}
            ),
            "status": forms.HiddenInput(),
            "is_pro": forms.CheckboxInput(attrs={'class': 'event-pro'}),
            "is_featured": forms.CheckboxInput(attrs={'class': 'event-pro'}),
            "is_raisin_participating": forms.CheckboxInput(attrs={'class': 'event-pro'}),
            "price": forms.TextInput(
                attrs={'class': 'form-control event-price'}
            ),
            "start_date": forms.TextInput(attrs={
                'class': 'form-control', 'id': 'datetimepicker1'
            }),
            "end_date": forms.TextInput(attrs={
                'class': 'form-control', 'id': 'datetimepicker2'
            })
        }


class DynamicChoiceField(forms.MultipleChoiceField):
    def __init__(self, choices=(), required=True, widget=None, label=None,
                 initial=None, help_text='', *args, **kwargs):
        super(DynamicChoiceField, self).__init__(
            required=required, widget=widget, label=label, initial=initial,
            help_text=help_text, *args, **kwargs
        )
        self.choices = choices

    def valid_value(self, value):
        return True


# password confirmation form
class ResetUserPasswordConfirmationForm(forms.Form):
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(
            attrs=dict(min_length=6, max_length=30, render_value=False)
        ),
        label=_("New password"),
        min_length=6,
        max_length=30
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(
            attrs=dict(min_length=6, max_length=30, render_value=False)
        ),
        label=_("New password (again)"),
        min_length=6,
        max_length=30
    )

    def clean_password1(self):
        return validate_password(self.cleaned_data, 'password1')

    def clean_password2(self):
        return validate_password(self.cleaned_data, 'password2')

    def clean(self):
        cleaned_data = super().clean()
        if (
            'password1' in cleaned_data and
            'password2' in cleaned_data
        ):
            if cleaned_data['password1'] != cleaned_data['password2']:
                raise forms.ValidationError({
                    'password1': [_("The two password fields did not match."), ],
                })

        return cleaned_data


# for post and place related lists
class PostRelatedListForm(forms.Form):
    limit = forms.IntegerField(required=False)

    page_comments = forms.IntegerField(required=False)
    page_likes = forms.IntegerField(required=False)
    page_drank_it_toos = forms.IntegerField(required=False)


# --------------------------------------- mass operations forms ------------------------------------------
class EventRelatedListForm(forms.Form):
    limit = forms.IntegerField(required=False)

    page_comments = forms.IntegerField(required=False)
    page_likes = forms.IntegerField(required=False)
    page_drank_it_toos = forms.IntegerField(required=False)
    page_attns = forms.IntegerField(required=False)


# --------------------------------------- mass operations forms ------------------------------------------

class MassOperationIdsPlaceForm(forms.Form):
    ids = forms.ModelMultipleChoiceField(
        queryset=Place.active.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class MassOperationIdsWinepostForm(forms.Form):
    ids = forms.ModelMultipleChoiceField(
        queryset=Post.objects.filter(type=PostTypeE.WINE),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class MassOperationIdsNewParentPostForm(forms.Form):
    new_parent_post_id = forms.IntegerField(required=False)
    new_winemaker_id = forms.IntegerField(required=False)
    is_parent_post = forms.BooleanField(required=False)
    is_star_review = forms.BooleanField(required=False)
    define_as_child = forms.BooleanField(required=False)
    nat_oth = forms.CharField(required=False)
    status = forms.CharField(required=False)

    ids = forms.ModelMultipleChoiceField(
        queryset=Post.objects.filter(type=PostTypeE.WINE),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class MassOperationIdsAnyPostForm(forms.Form):
    ids = forms.ModelMultipleChoiceField(
        queryset=Post.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class MassOperationIdsEstComForm(forms.Form):
    ids = forms.ModelMultipleChoiceField(
        queryset=Comment.objects.filter().exclude(place=None),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class MassOperationIdsWineForm(forms.Form):
    ids = forms.ModelMultipleChoiceField(
        queryset=Wine.active.filter(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class MassOperationIdsGeneralpostForm(forms.Form):
    ids = forms.ModelMultipleChoiceField(
        queryset=Post.active.filter(type__in=[
            PostTypeE.NOT_WINE, PostTypeE.FOOD
        ]),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class MassOperationIdsEventForm(forms.Form):
    ids = forms.ModelMultipleChoiceField(
        queryset=CalEvent.objects.filter(is_archived=False),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    
class MassOperationIdsWinemakerForm(forms.Form):
    ids = forms.ModelMultipleChoiceField(
        queryset=Winemaker.active.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class MassOperationIdsUserProfileForm(forms.Form):
    ids = forms.ModelMultipleChoiceField(
        queryset=UserProfile.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class MassOperationIdsCommentForm(forms.Form):
    ids = forms.ModelMultipleChoiceField(
        queryset=Comment.active.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class PublishedPlaceListForm(forms.Form):
    q = forms.CharField(required=False)
    page = forms.IntegerField(required=False)


class ChangeParentPostWinemakerListForm(forms.Form):
    q = forms.CharField(required=False)
    page = forms.IntegerField(required=False)
    edited_post_id = forms.IntegerField(required=False)


class UpdateOriginalWinemakerForm(forms.Form):
    winemaker_name = forms.CharField(required=True)
    winemaker_id = forms.IntegerField(required=True)


class ChangeParentPostWineListForm(forms.Form):
    winemaker_id = forms.IntegerField(required=False)


class ChangeParentPostForm(forms.Form):
    winepost_id = forms.IntegerField(required=True)
    new_parent_post_id = forms.IntegerField(required=True)


class OCRFileForm(forms.Form):
    image = forms.FileField(required=True)


class OCRIncludeForm(forms.Form):
    incs = DynamicChoiceField(choices=(), required=False)
    id = forms.IntegerField(required=False)
    moderated = forms.IntegerField(required=False)  # moderated
    # by human i.e. moderator manually changed status for row previously


class OCRUserApprovedTextForm(forms.Form):
    winelist_file_id = forms.IntegerField(required=True)
    text = forms.CharField(required=False)
    new_exclusion_word_row = forms.IntegerField(required=False)  # index of a
    # row from which a word was excluded by the moderator, which triggered the
    # re-evaluation. Required in the case of re-evaluation caused by word
    # exclusion only.


class FreeGlassEventForm(forms.Form):
    name = forms.CharField(required=False, label=_("Event name:"), widget=TextInput(
        attrs={"placeholder": _("Event name"),
               "class": "form-control"}))

    announcement_date = forms.CharField(required=True, label=_("Campaign announcement date:"), widget=TextInput(
        attrs={"placeholder": _("Campaign announcement date"),
               "class": "form-control"}))
    start_date = forms.CharField(required=True, label=_("Campaign starting date:"), widget=TextInput(
        attrs={"placeholder": _("Campaign starting date"),
               "class": "form-control"}))

    end_date = forms.CharField(required=True, label=_("Back to normal:"), widget=TextInput(
        attrs={"placeholder": _("Back to normal"),
               "class": "form-control"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class DeleteYearlyDataForm(forms.Form):
    winepost_id = forms.IntegerField(required=True)
    year = forms.IntegerField(required=True)


class UpdateYearlyDataForm(forms.Form):
    winepost_id = forms.IntegerField(required=True)
    # yearly_data = JsonStrField(required=False)
    cur_year = forms.IntegerField(required=False)
    cur_free_so2 = forms.CharField(required=False)
    cur_total_so2 = forms.CharField(required=False)
    cur_grape_variety = forms.CharField(required=False)

    def clean(self):
        cd = self.cleaned_data
        if cd['cur_free_so2'] and cd['cur_free_so2'].find(','):
            cd['cur_free_so2'] = cd['cur_free_so2'].replace(',', '.')
        if cd['cur_total_so2'] and cd['cur_total_so2'].find(','):
            cd['cur_total_so2'] = cd['cur_total_so2'].replace(',', '.')
        return cd


class FetchYearlyDataForm(forms.Form):
    winepost_id = forms.IntegerField(required=True)


class RefreshVuforiaImageForm(forms.Form):
    winepost_id = forms.IntegerField(required=True)


class SetAsVuforiaForm(forms.Form):
    winepost_id = forms.IntegerField(required=True)
    what = forms.CharField(required=True)

    def clean(self):
        cd = self.cleaned_data
        if cd['what'] not in ['primary', 'secondary']:
            raise ValidationError("Incorrect value for 'what': must be either 'primary' or 'secondary'")
        return cd


class TranslateDomainDescriptionForm(forms.Form):
    orig_lang = forms.CharField(required=True)
    contents = forms.CharField(required=False)
    winemaker_id = forms.IntegerField(required=False)


class UpdateDomainDescriptionForm(forms.Form):
    lang = forms.CharField(required=True)
    contents = forms.CharField(required=False)
    str_trans = forms.CharField(required=False)
    winemaker_id = forms.IntegerField(required=False)


class ClearDomainDescriptionTranslationsForm(forms.Form):
    winemaker_id = forms.IntegerField(required=False)


class VersionSettingsForm(forms.Form):
    # ios_min_model_version = forms.IntegerField(required=False,
    #                                            label="iOS min. model version")
    ios_min_app_version = forms.CharField(required=False,
                                          label="iOS min. app version (X.Y.Z)")
    ios_newest_app_version = forms.CharField(required=False,
                                             label="iOS newest app version")
    android_min_model_version = forms.IntegerField(required=False,
                                                   label="Android min. model version (versionCode)")
    android_min_build_version = forms.CharField(required=False,
                                                label="Android min. build version")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class CommentEditForm(forms.Form):
    id = forms.IntegerField(required=True)
    description = forms.CharField(required=False)
