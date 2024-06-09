from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from web.constants import (ApiErrorCodeE, ApiResultStatusE, AppEnvE, PostTypeE,
                           WineColorE)
from web.forms.common import strip_cleaned_data
from web.models import Place, Post, UserProfile
from web.utils.exceptions import ApiError
from web.utils.mentions import strip_description_update_user_mentions_indexes

###
# API FORMS
###


# --------------------------------------- API list forms ------------------------------------------
class PlaceListGeoForm(forms.Form):
    lat = forms.FloatField(required=False)
    lng = forms.FloatField(required=False)
    max = forms.FloatField(required=False)
    get_hours = forms.BooleanField(required=False)


class RandomFoodsWinesGeoForm(forms.Form):
    latitude = forms.FloatField(required=False)
    longitude = forms.FloatField(required=False)
    limit = forms.FloatField(required=False)
    refresh = forms.BooleanField(required=False)


class ListForm(forms.Form):
    last_id = forms.IntegerField(required=False)
    start = forms.IntegerField(required=False)
    limit = forms.IntegerField(required=False)
    order = forms.CharField(required=False)
    order_by = forms.CharField(required=False)


class NotificationListForm(ListForm):
    pass


class TimeLineItemsForm(ListForm):
    pass


class EventsTimeLineForm(ListForm):
    pass


class EventsMapForm(ListForm):
    pass


class EventsSearchForm(ListForm):
    query = forms.CharField(required=False)


class WineItemsForm(ListForm):
    winemaker_id = forms.IntegerField(required=False)


class WineSimiliarItemsForm(ListForm):
    wine_name = forms.CharField(required=True)


class WinemakerItemsForm(ListForm):
    query = forms.CharField(required=False)


class CommentListForm(ListForm):
    post_id = forms.IntegerField(required=False)
    place_id = forms.IntegerField(required=False)
    user_id = forms.CharField(required=False)
    username = forms.CharField(required=False)
    wine_id = forms.CharField(required=False)
    event_id = forms.CharField(required=False)

    def clean(self):
        if ('post_id' not in self.cleaned_data or not self.cleaned_data['post_id']) \
                and ('place_id' not in self.cleaned_data or not self.cleaned_data['place_id']) \
                and ('user_id' not in self.cleaned_data or not self.cleaned_data['user_id']) \
                and ('username' not in self.cleaned_data or not self.cleaned_data['username']) \
                and ('wine_id' not in self.cleaned_data or not self.cleaned_data['wine_id']) \
                and ('event_id' not in self.cleaned_data or not self.cleaned_data['event_id']):
            raise forms.ValidationError({
                'post_id': [_("Valid 'post_id' or 'place_id' or 'user_id' or 'username' or 'wine_id' or 'event_id' "
                              "field is required."), ]
            })
        return self.cleaned_data


class LikeVotePostOrPlaceForm(forms.Form):
    post_id = forms.IntegerField(required=False)
    place_id = forms.IntegerField(required=False)
    event_id = forms.CharField(required=False)

    def clean(self):
        if ('post_id' not in self.cleaned_data or not self.cleaned_data['post_id']) \
                and ('place_id' not in self.cleaned_data or not self.cleaned_data['place_id']) \
                and ('event_id' not in self.cleaned_data or not self.cleaned_data['event_id']):
            raise forms.ValidationError({
                'post_id': [_("Valid 'post_id' or 'place_id' or 'event_id' field is required."), ]
            })
        return self.cleaned_data


class LikeVoteListForm(ListForm):
    post_id = forms.IntegerField(required=False)
    place_id = forms.IntegerField(required=False)
    user_id = forms.CharField(required=False)
    username = forms.CharField(required=False)
    wine_id = forms.CharField(required=False)
    event_id = forms.CharField(required=False)

    def clean(self):
        if ('post_id' not in self.cleaned_data or not self.cleaned_data['post_id']) \
                and ('place_id' not in self.cleaned_data or not self.cleaned_data['place_id']) \
                and ('user_id' not in self.cleaned_data or not self.cleaned_data['user_id']) \
                and ('username' not in self.cleaned_data or not self.cleaned_data['username']) \
                and ('wine_id' not in self.cleaned_data or not self.cleaned_data['wine_id']) \
                and ('event_id' not in self.cleaned_data or not self.cleaned_data['event_id']):
            raise forms.ValidationError({
                'post_id': [_("Valid 'post_id' or 'place_id' or 'event_id' or 'user_id' or 'username' or "
                              "'wine_id' field is required."), ]
            })
        return self.cleaned_data


class AttendeeListForm(ListForm):
    event_id = forms.CharField(required=True)


class DrankItTooListForm(ListForm):
    post_id = forms.IntegerField(required=False)
    user_id = forms.CharField(required=False)
    username = forms.CharField(required=False)
    wine_id = forms.CharField(required=False)

    def clean(self):
        if ('post_id' not in self.cleaned_data or not self.cleaned_data['post_id']) \
                and ('user_id' not in self.cleaned_data or not self.cleaned_data['user_id']) \
                and ('username' not in self.cleaned_data or not self.cleaned_data['username']) \
                and ('wine_id' not in self.cleaned_data or not self.cleaned_data['wine_id']):
            raise forms.ValidationError({
                'post_id': [_("Valid 'post_id' or 'user_id' or 'username' or 'wine_id' field is required."), ]
            })
        return self.cleaned_data


class PostListForm(ListForm):
    type = forms.ChoiceField(required=False, choices=PostTypeE.pairs)

    user_id = forms.CharField(required=False)
    username = forms.CharField(required=False)
    wine_id = forms.CharField(required=False)
    is_star_review = forms.BooleanField(required=False)
    post_ids = forms.ModelMultipleChoiceField(
        queryset=Post.active.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class ImagesListForm(forms.Form):
    post_id = forms.IntegerField(required=False)
    place_id = forms.IntegerField(required=False)
    wine_id = forms.IntegerField(required=False)
    winemaker_id = forms.IntegerField(required=False)
    user_id = forms.CharField(required=False)

    def clean(self):
        required_one = ['post_id', 'place_id', 'wine_id', 'winemaker_id', 'user_id']
        required_found = False

        for field in required_one:
            if field in self.cleaned_data and self.cleaned_data[field]:
                required_found = True
                break

        if not required_found:
            raise forms.ValidationError({required_one[0]: [_("Valid %s required.") % ' or '.join(required_one), ]})

        return self.cleaned_data
# --------------------------------------- END OF API list forms ------------------------------------------


# --------------------------------------- API item creation/edition forms --------------------------------
class UpdatePushFieldsForm(forms.Form):
    push_user_id = forms.CharField(required=True)
    push_user_token = forms.CharField(required=False)


class UpdateUserLangForm(forms.Form):
    lang = forms.CharField(required=False)


class AppIosCheckForm(forms.Form):
    app_version = forms.CharField(required=True)
    build_version = forms.CharField(required=False)


class AppAndroidCheckForm(forms.Form):
    model_version = forms.IntegerField(required=True)
    # app_version = forms.CharField(required=True)
    # build_version = forms.CharField(required=True)


class UserProfileCreateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['password', 'email', 'username']

    def __init__(self, *args, **kwargs):
        allNonRequired = kwargs.pop('allNonRequired', False)
        not_required_fields = []

        super(UserProfileCreateForm, self).__init__(*args, **kwargs)

        if allNonRequired:
            not_required_fields = self.fields
        for nr_field in not_required_fields:
            self.fields[nr_field].required = False

    def clean_email(self):
        value = self.cleaned_data['email']

        try:
            if self.instance and self.instance.email == value:
                return value
        except AttributeError:
            pass

        try:
            UserProfile.objects.get(email__iexact=value)
            msg = 'Email already exists.'
            raise ApiError(msg, ApiErrorCodeE.RESULT_ALREADY_EXISTS_EMAIL)
        except UserProfile.DoesNotExist:
            return value

    def clean_username(self):
        value = self.cleaned_data['username']
        try:
            if self.instance and self.instance.username == value:
                return value
        except AttributeError:
            pass

        try:
            UserProfile.objects.get(username__exact=value)
            msg = 'Username already exists.'
            raise ApiError(msg, ApiResultStatusE.RESULT_ALREADY_EXISTS_USERNAME)
        except UserProfile.DoesNotExist:
            return value


def clean_mentions_fn(self):
    if self.cleaned_data['mentions']:
        if 'mentions' not in self.cleaned_data or not self.cleaned_data['mentions']:
            return None

        for mention in self.cleaned_data['mentions']:
            if not isinstance(mention, dict):
                raise ValidationError("invalid mention format", code='invalid')

            if 'user_name' not in mention or 'user_id' not in mention or 'start_index' not in mention:
                raise ValidationError("invalid mention format", code='invalid')

    return self.cleaned_data['mentions']


class JsonField(forms.Field):
    def __init__(self, *args, **kwargs):
        super(JsonField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        "Returns a DICT/LIST object."

        if not value:
            return None

        if not isinstance(value, list) and not isinstance(value, dict):
            raise ValidationError("invalid JSON format", code='invalid')

        return value

    def widget_attrs(self, widget):
        attrs = super(JsonField, self).widget_attrs(widget)
        return attrs


class CommentCreateForm(forms.Form):
    tl_id = forms.IntegerField(required=False)
    post_id = forms.IntegerField(required=False)
    place_id = forms.IntegerField(required=False)
    event_id = forms.CharField(required=False)
    description = forms.CharField(required=True, strip=False)
    mentions = JsonField(required=False)

    clean_mentions = clean_mentions_fn

    def clean(self):
        if ('post_id' not in self.cleaned_data or not self.cleaned_data['post_id']) \
                and ('tl_id' not in self.cleaned_data or not self.cleaned_data['tl_id']) \
                and ('place_id' not in self.cleaned_data or not self.cleaned_data['place_id']) \
                and ('event_id' not in self.cleaned_data or not self.cleaned_data['event_id']):
            raise forms.ValidationError({'post_id':
                                         [_("Valid 'post_id' or 'tl_id' or 'place_id' or 'event_id' "
                                            "field is required."), ]})
        return self.cleaned_data


class CommentUpdateForm(forms.Form):
    comment_id = forms.IntegerField(required=True)
    description = forms.CharField(required=True, strip=False)
    mentions = JsonField(required=False)

    clean_mentions = clean_mentions_fn


class GotFreeGlassCreateForm(forms.Form):
    place_id = forms.IntegerField(required=True)


class DonationsClickForm(forms.Form):
    place_id = forms.IntegerField(required=False)
    winemaker_id = forms.IntegerField(required=False)

    def clean(self):
        if ('winemaker_id' not in self.cleaned_data or not self.cleaned_data['winemaker_id']) \
                and ('place_id' not in self.cleaned_data or not self.cleaned_data['place_id']):
            raise forms.ValidationError({'place_id':
                                        [_("Valid 'winemaker_id' or 'place_id'"
                                         "field is required."), ]})
        return self.cleaned_data


class GotFreeGlassGetForm(GotFreeGlassCreateForm):
    pass


class GotFreeGlassListForm(ListForm):
    place_id = forms.IntegerField(required=True)


class AppleDonationsReceiptForm(ListForm):
    product_id = forms.CharField(required=False)
    qty = forms.CharField(required=False)
    transaction_id = forms.CharField(required=False)
    receipt_data = forms.CharField(required=True)
    is_sandbox = forms.BooleanField(required=False)

    # date_from = forms.CharField(required=True)
    # date_to = forms.CharField(required=True)
    # frequency = forms.ChoiceField(required=True, choices=DonationFrequencyE.pairs)
    # status = forms.ChoiceField(required=True, choices=DonationStatusE.pairs)
    # value = forms.FloatField(required=True)
    # currency = forms.CharField(required=True)

    def clean(self):
        cd = self.cleaned_data
        return cd


class AndroidPushReceiptForm(ListForm):
    push_data = JsonField(required=True)


class LikeVoteCreateForm(forms.Form):
    post_id = forms.IntegerField(required=False)
    place_id = forms.IntegerField(required=False)
    tl_id = forms.IntegerField(required=False)
    event_id = forms.CharField(required=False)

    def clean(self):
        if ('post_id' not in self.cleaned_data or not self.cleaned_data['post_id']) \
                and ('tl_id' not in self.cleaned_data or not self.cleaned_data['tl_id']) \
                and ('place_id' not in self.cleaned_data or not self.cleaned_data['place_id']) \
                and ('event_id' not in self.cleaned_data or not self.cleaned_data['event_id']):
            raise forms.ValidationError({'post_id': [_("Valid 'post_id' or 'tl_id' or 'place_id' or "
                                                       "'event_id' field is required."), ]})
        return self.cleaned_data


class AttendeeCreateForm(forms.Form):
    event_id = forms.CharField(required=True)
    is_user_there = forms.BooleanField(required=False)


class DrankItTooCreateForm(forms.Form):
    post_id = forms.IntegerField(required=False)
    tl_id = forms.IntegerField(required=False)

    def clean(self):
        if ('post_id' not in self.cleaned_data or not self.cleaned_data['post_id']) \
                and ('tl_id' not in self.cleaned_data or not self.cleaned_data['tl_id']):
            raise forms.ValidationError({
                'post_id': [_("Valid 'post_id' field is required."), ]
            })
        return self.cleaned_data


class WinepostCreateNewForm(forms.Form):
    name = forms.CharField(required=False)
    description = forms.CharField(required=False, strip=False)

    domain = forms.CharField(required=False)
    designation = forms.CharField(required=False)
    grape_variety = forms.CharField(required=False)
    region = forms.CharField(required=False)
    color = forms.ChoiceField(required=False, choices=WineColorE.pairs)
    year = forms.CharField(required=False)
    is_sparkling = forms.BooleanField(required=False)

    winemaker_name = forms.CharField(required=False)
    winemaker_id = forms.IntegerField(required=False)

    place_id = forms.IntegerField(required=False)
    foursquare_place_name = forms.CharField(required=False)
    foursquare_place_url = forms.CharField(required=False)

    price = forms.FloatField(required=False)
    similiar_wine_exists = forms.BooleanField(required=False)
    similiar_wine_id = forms.IntegerField(required=False)
    is_scanned = forms.BooleanField(required=False)
    wine_id = forms.IntegerField(required=False)
    # vuf_wine_id = forms.IntegerField(required=False)

    mentions = JsonField(required=False)
    clean_mentions = clean_mentions_fn

    def clean(self):
        cd = self.cleaned_data
        if ('winemaker_name' not in cd or not cd['winemaker_name']) \
                and ('winemaker_id' not in cd or not cd['winemaker_id'])\
                and not ('is_scanned' in cd and cd['is_scanned'] and 'wine_id' in cd and cd['wine_id']):
            raise forms.ValidationError({'winemaker_name': [
                _("Valid 'winemaker_name' or 'winemaker_id' or "
                  "('is_scanned'=True and wine_id set) is required."), ]})
        cd = strip_cleaned_data(cd, ['name', 'domain', 'designation', 'grape_variety', 'region', 'year',
                                     'winemaker_name'])
        cd = strip_description_update_user_mentions_indexes(cd)
        return cd


class WinepostCreateForm(forms.Form):
    name = forms.CharField(required=True)
    description = forms.CharField(required=False, strip=False)

    domain = forms.CharField(required=False)
    designation = forms.CharField(required=False)
    grape_variety = forms.CharField(required=False)
    region = forms.CharField(required=False)
    color = forms.ChoiceField(required=False, choices=WineColorE.pairs)
    year = forms.CharField(required=False)
    is_sparkling = forms.BooleanField(required=False)

    winemaker_name = forms.CharField(required=False)
    winemaker_id = forms.IntegerField(required=False)

    place_id = forms.IntegerField(required=False)
    foursquare_place_name = forms.CharField(required=False)
    foursquare_place_url = forms.CharField(required=False)

    similiar_wine_exists = forms.BooleanField(required=False)
    is_scanned = forms.BooleanField(required=False)
    similiar_wine_id = forms.IntegerField(required=False)
    vuf_wine_id = forms.IntegerField(required=False)

    mentions = JsonField(required=False)
    clean_mentions = clean_mentions_fn

    def clean(self):
        if ('winemaker_name' not in self.cleaned_data or not self.cleaned_data['winemaker_name']) \
                and ('winemaker_id' not in self.cleaned_data or not self.cleaned_data['winemaker_id']):
            raise forms.ValidationError({
                'winemaker_name': [_("Valid 'winemaker_name' or 'winemaker_id' field is required."), ]
            })

        cleaned_data = strip_cleaned_data(self.cleaned_data,
                                          ['name', 'domain', 'designation', 'grape_variety', 'region', 'year',
                                           'winemaker_name'])

        cleaned_data = strip_description_update_user_mentions_indexes(cleaned_data)

        return cleaned_data


class WinepostEditForm(forms.Form):
    post_id = forms.IntegerField(required=False)
    tl_id = forms.IntegerField(required=False)

    name = forms.CharField(required=True)
    description = forms.CharField(required=False, strip=False)

    domain = forms.CharField(required=False)
    designation = forms.CharField(required=False)
    grape_variety = forms.CharField(required=False)
    region = forms.CharField(required=False)
    color = forms.ChoiceField(required=False, choices=WineColorE.pairs)
    year = forms.CharField(required=False)
    is_sparkling = forms.BooleanField(required=False)

    winemaker_name = forms.CharField(required=False)
    winemaker_id = forms.IntegerField(required=False)

    place_id = forms.IntegerField(required=False)
    foursquare_place_name = forms.CharField(required=False)
    foursquare_place_url = forms.CharField(required=False)
    vuf_wine_id = forms.IntegerField(required=False)

    mentions = JsonField(required=False)
    clean_mentions = clean_mentions_fn

    def clean(self):
        if ('post_id' not in self.cleaned_data or not self.cleaned_data['post_id']) \
                and ('tl_id' not in self.cleaned_data or not self.cleaned_data['tl_id']):
            raise forms.ValidationError({
                'post_id': [_("Valid 'post_id' or 'tl_id' field is required."), ]
            })

        cleaned_data = strip_cleaned_data(self.cleaned_data,
                                          ['name', 'domain', 'designation', 'grape_variety', 'region', 'year',
                                           'winemaker_name'])

        cleaned_data = strip_description_update_user_mentions_indexes(cleaned_data)
        if 'color' not in cleaned_data or not cleaned_data['color']:
            cleaned_data['color'] = None

        return cleaned_data


class GeneralPostCreateForm(forms.Form):
    title = forms.CharField(required=True)
    description = forms.CharField(required=False, strip=False)

    place_id = forms.IntegerField(required=False)
    foursquare_place_name = forms.CharField(required=False)
    foursquare_place_url = forms.CharField(required=False)
    post_type = forms.CharField(required=False)

    mentions = JsonField(required=False)
    clean_mentions = clean_mentions_fn

    def clean(self):
        cleaned_data = strip_cleaned_data(self.cleaned_data, ['title'])
        cleaned_data = strip_description_update_user_mentions_indexes(cleaned_data)

        return cleaned_data


class GeneralPostEditForm(forms.Form):
    post_id = forms.IntegerField(required=False)
    tl_id = forms.IntegerField(required=False)

    title = forms.CharField(required=True)
    description = forms.CharField(required=False, strip=False)

    place_id = forms.IntegerField(required=False)
    foursquare_place_name = forms.CharField(required=False)
    foursquare_place_url = forms.CharField(required=False)

    mentions = JsonField(required=False)
    clean_mentions = clean_mentions_fn

    def clean(self):
        if ('post_id' not in self.cleaned_data or not self.cleaned_data['post_id']) \
                and ('tl_id' not in self.cleaned_data or not self.cleaned_data['tl_id']):
            raise forms.ValidationError({
                'post_id': [_("Valid 'post_id' or 'tl_id' field is required."), ]}
            )

        cleaned_data = strip_cleaned_data(self.cleaned_data, ['title'])
        cleaned_data = strip_description_update_user_mentions_indexes(cleaned_data)

        return cleaned_data


class PlaceCreateForm(forms.ModelForm):
    mentions = JsonField(required=False)
    clean_mentions = clean_mentions_fn

    def get_is_30_p_natural_already(self, obj):
        return not obj.is_30_p_natural_already

    class Meta:
        model = Place
        fields = ['name', 'type', 'is_bar', 'is_restaurant', 'is_wine_shop',
                  'description', 'street_address', 'house_number', 'zip_code',
                  'city', 'country', 'country_iso_code', 'phone_number',
                  'website_url', 'email', 'latitude', 'longitude',
                  # 'pin_latitude', 'pin_longitude',
                  'is_30_p_natural_already', 'social_facebook_url',
                  'social_twitter_url', 'social_instagram_url']

    def __init__(self, *args, **kwargs):
        allNonRequired = kwargs.pop('allNonRequired', False)

        not_required_fields = [
            'type', 'is_bar', 'is_restaurant', 'is_wine_shop',
            'street_address', 'house_number', 'zip_code', 'city', 'country',
            'country_iso_code', 'phone_number', 'website_url', 'email',
            'latitude', 'longitude', 'is_30_p_natural_already',
            # 'pin_longitude', 'pin_latitude',
            'social_facebook_url', 'social_twitter_url', 'social_instagram_url',
        ]

        super(PlaceCreateForm, self).__init__(*args, **kwargs)

        if allNonRequired:
            not_required_fields = self.fields
        for nr_field in not_required_fields:
            self.fields[nr_field].required = False

        self.fields['description'].strip = False

    def clean(self):
        cleaned_data = strip_cleaned_data(self.cleaned_data, ['name', 'city', 'street_address'])

        if cleaned_data['latitude'] is None:
            cleaned_data['latitude'] = 0

        if cleaned_data['longitude'] is None:
            cleaned_data['longitude'] = 0

        return cleaned_data
# --------------------------------------- END OF API item creation/edition forms ---------------------------


class PlaceEditForm(forms.ModelForm):
    tl_id = forms.IntegerField(required=False)
    place_id = forms.IntegerField(required=False)

    mentions = JsonField(required=False)
    clean_mentions = clean_mentions_fn

    class Meta:
        model = Place
        fields = ['name', 'type',
                  'is_bar',
                  'is_restaurant',
                  'is_wine_shop',

                  'description',
                  'street_address', 'house_number', 'zip_code',
                  'city', 'country', 'country_iso_code',
                  'phone_number', 'website_url', 'email',
                  'latitude', 'longitude',
                  'pin_latitude', 'pin_longitude',
                  'social_facebook_url', 'social_twitter_url', 'social_instagram_url',
                  ]

    def __init__(self, *args, **kwargs):
        allNonRequired = kwargs.pop('allNonRequired', False)

        not_required_fields = [
            'type', 'is_bar', 'is_restaurant', 'is_wine_shop',
            'street_address', 'house_number', 'zip_code',
            'city', 'country', 'country_iso_code',
            'phone_number', 'website_url', 'email',
            'latitude', 'longitude',
            'social_facebook_url', 'social_twitter_url', 'social_instagram_url',
        ]

        super(PlaceEditForm, self).__init__(*args, **kwargs)

        if allNonRequired:
            not_required_fields = self.fields
        for nr_field in not_required_fields:
            self.fields[nr_field].required = False

        self.fields['description'].strip = False

    def clean(self):
        if ('tl_id' not in self.cleaned_data or not self.cleaned_data['tl_id']) \
                and ('place_id' not in self.cleaned_data or not self.cleaned_data['place_id']):
            raise forms.ValidationError({
                'place_id': [_("Valid 'tl_id' or 'place_id' "
                               "field is required."), ]
            })

        cleaned_data = strip_cleaned_data(self.cleaned_data, ['name', 'city', 'street_address'])

        return cleaned_data
# --------------------------------------- END OF API item creation/edition forms ---------------------------


# --------------------------------------- API item deletion forms ------------------------------------------


class GotFreeGlassDeleteForm(forms.Form):
    id = forms.IntegerField(required=False)
    place_id = forms.IntegerField(required=False)

    def clean(self):
        if ('id' not in self.cleaned_data or not self.cleaned_data['id']) \
                and ('place_id' not in self.cleaned_data or not self.cleaned_data['place_id']):
            raise forms.ValidationError({
                'id': [_("Valid 'id' or 'place_id' field is required."), ]
            })
        return self.cleaned_data


class DrankItTooDeleteForm(forms.Form):
    drank_it_too_id = forms.IntegerField(required=False)
    tl_id = forms.IntegerField(required=False)
    post_id = forms.IntegerField(required=False)

    def clean(self):
        if ('drank_it_too_id' not in self.cleaned_data or not self.cleaned_data['drank_it_too_id']) \
                and ('tl_id' not in self.cleaned_data or not self.cleaned_data['tl_id']) \
                and ('post_id' not in self.cleaned_data or not self.cleaned_data['post_id']):
            raise forms.ValidationError({
                'drank_it_too_id': [_(
                    "Valid 'drank_it_too_id' or 'tl_id' or 'post_id' field is required."
                ), ]
            })
        return self.cleaned_data


class LikeVoteDeleteForm(forms.Form):
    likevote_id = forms.IntegerField(required=False)
    tl_id = forms.IntegerField(required=False)
    post_id = forms.IntegerField(required=False)
    place_id = forms.IntegerField(required=False)
    event_id = forms.CharField(required=False)

    def clean(self):
        if ('likevote_id' not in self.cleaned_data or not self.cleaned_data['likevote_id']) \
                and ('tl_id' not in self.cleaned_data or not self.cleaned_data['tl_id']) \
                and ('place_id' not in self.cleaned_data or not self.cleaned_data['place_id']) \
                and ('post_id' not in self.cleaned_data or not self.cleaned_data['post_id']) \
                and ('event_id' not in self.cleaned_data or not self.cleaned_data['event_id']):
            raise forms.ValidationError({
                'likevote_id': [_("Valid 'likevote_id' or 'tl_id' or 'place_id' or 'post_id' or 'event_id' "
                                  "field is required."), ]
            })
        return self.cleaned_data


class AttendeeDeleteForm(forms.Form):
    event_id = forms.CharField(required=False)
    attendee_id = forms.CharField(required=False)

    def clean(self):
        if ('attendee_id' not in self.cleaned_data or not self.cleaned_data['attendee_id']) \
                and ('event_id' not in self.cleaned_data or not self.cleaned_data['event_id']):
            raise forms.ValidationError({
                'likevote_id': [_("Valid 'attendee_id' or 'event_id' field is required."), ]
            })
        return self.cleaned_data


class CommentDeleteForm(forms.Form):
    comment_id = forms.IntegerField(required=False)
    tl_id = forms.IntegerField(required=False)

    def clean(self):
        if ('comment_id' not in self.cleaned_data or not self.cleaned_data['comment_id']) \
                and ('tl_id' not in self.cleaned_data or not self.cleaned_data['tl_id']):
            raise forms.ValidationError({
                'comment_id': [_("Valid 'comment_id' or 'tl_id' field is required."), ]
            })
        return self.cleaned_data
# --------------------------------------- END OF API item deletion forms -----------------------------------


# --------------------------------------- API item get forms -----------------------------------------------
class UserProfileOptionsForm(forms.Form):
    get_likes = forms.BooleanField(required=False)
    get_drank_it_toos = forms.BooleanField(required=False)
    get_comments = forms.BooleanField(required=False)
    get_general_posts = forms.BooleanField(required=False)
    get_wineposts = forms.BooleanField(required=False)
    get_star_reviews = forms.BooleanField(required=False)
    get_posts = forms.BooleanField(required=False)

    like_last_id = forms.IntegerField(required=False)
    dit_last_id = forms.IntegerField(required=False)
    post_last_id = forms.IntegerField(required=False)
    sr_last_id = forms.IntegerField(required=False)

    limit = forms.IntegerField(required=False)


class UserProfileAnyOptionsForm(UserProfileOptionsForm):
    user_id = forms.CharField(required=False)
    username = forms.CharField(required=False)


class TimeLineOneItemForm(forms.Form):
    post_id = forms.IntegerField(required=False)
    place_id = forms.IntegerField(required=False)
    tl_id = forms.IntegerField(required=False)
    wine_id = forms.IntegerField(required=False)

    def clean(self):
        if ('post_id' not in self.cleaned_data or not self.cleaned_data['post_id']) \
                and ('tl_id' not in self.cleaned_data or not self.cleaned_data['tl_id']) \
                and ('place_id' not in self.cleaned_data or not self.cleaned_data['place_id']) \
                and ('wine_id' not in self.cleaned_data or not self.cleaned_data['wine_id']):
            raise forms.ValidationError({'post_id':
                                        [_("Valid 'post_id' or 'tl_id' or 'place_id' or 'wine_id' field is required."), ]})
        return self.cleaned_data


class EventDetailsForm(forms.Form):
    event_id = forms.IntegerField(required=True)


class PostGetForm(forms.Form):
    post_id = forms.IntegerField(required=True)


class PostDeleteForm(forms.Form):
    post_id = forms.IntegerField(required=False)
    tl_id = forms.IntegerField(required=False)

    def clean(self):
        if ('post_id' not in self.cleaned_data or not self.cleaned_data['post_id']) \
                and ('tl_id' not in self.cleaned_data or not self.cleaned_data['tl_id']):
            raise forms.ValidationError(
                {'post_id': [_("Valid 'post_id' or 'tl_id' field is required."), ]}
            )
        return self.cleaned_data


class PlaceDeleteForm(forms.Form):
    place_id = forms.IntegerField(required=False)
    tl_id = forms.IntegerField(required=False)

    def clean(self):
        if ('place_id' not in self.cleaned_data or not self.cleaned_data['place_id']) \
                and ('tl_id' not in self.cleaned_data or not self.cleaned_data['tl_id']):
            raise forms.ValidationError(
                {'place_id': [_("Valid 'place_id' or 'tl_id' field is required."), ]})
        return self.cleaned_data


class WineProfileForm(forms.Form):
    wine_id = forms.IntegerField(required=True)


class WinemakerProfileForm(forms.Form):
    winemaker_id = forms.IntegerField(required=True)


class PlaceGetForm(forms.Form):
    place_id = forms.IntegerField(required=True)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['password', 'email', 'full_name', 'description', 'website_url', 'username',
                  'notify_likes', 'notify_drank_it_toos', 'notify_comments', 'notify_wine_reviewed'
                  ]

    def __init__(self, *args, **kwargs):
        allNonRequired = kwargs.pop('allNonRequired', False)
        not_required_fields = ['password', 'username', 'website_url', 'notify_likes', 'notify_drank_it_toos',
                               'notify_comments', 'notify_wine_reviewed']
        super(UserProfileForm, self).__init__(*args, **kwargs)

        if allNonRequired:
            not_required_fields = self.fields
        for nr_field in not_required_fields:
            self.fields[nr_field].required = False

    def clean_email(self):
        value = self.cleaned_data['email']

        if not value:
            return None

        if self.instance:
            users_count = UserProfile.objects.filter(email__iexact=value).exclude(id=self.instance.id).count()
        else:
            users_count = UserProfile.objects.filter(email__iexact=value).count()

        if users_count > 0:
            msg = 'Email already exists.'
            raise ApiError(msg, ApiResultStatusE.RESULT_ALREADY_EXISTS_EMAIL)
        else:
            return value

    def clean_username(self):
        value = self.cleaned_data['username']

        if not value:
            return None

        if self.instance:
            users_count = UserProfile.objects.filter(username__iexact=value).exclude(id=self.instance.id).count()
        else:
            users_count = UserProfile.objects.filter(username__iexact=value).count()

        if users_count > 0:
            msg = 'Username already exists.'
            raise ApiError(msg, ApiResultStatusE.RESULT_ALREADY_EXISTS_USERNAME)
        else:
            return value
# --------------------------------------- END OF API item get forms ----------------------------------------


class RefreshTokenForm(forms.Form):
    refresh_token = forms.CharField(max_length=40, label='token', required=True)


class FileUploadForm(forms.Form):
    images = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False)
    data = forms.CharField(required=False)


class PlaceFileUploadForm(forms.Form):
    images = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False)
    wlfiles = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False)
    data = forms.CharField(required=False)


class SearchQueryForm(forms.Form):
    query = forms.CharField(required=False)
    query_type = forms.CharField(required=False)
    force_winepost_name_only = forms.BooleanField(required=False)
    min_letters = forms.IntegerField(required=False)


class CountVuforiaScansForm(forms.Form):
    env = forms.ChoiceField(required=False, choices=AppEnvE.pairs)


class WinesForPlaceForm(forms.Form):
    place_id = forms.IntegerField(required=True)
    type = forms.CharField(required=False)


class FoodsForPlaceForm(forms.Form):
    place_id = forms.IntegerField(required=True)


class PlaceOpenClosedStatusForm(forms.Form):
    place_id = forms.IntegerField(required=False)
