from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms import Textarea
from .models import FeaturedVenue, News, WebsitePage, LPB, Quote, Testimonial, Cheffe
import json
from web.constants import (get_original_language_choices,
                           get_selected_language_choices)


class MassOperationIdsNewsForm(forms.Form):
    ids = forms.ModelMultipleChoiceField(
        queryset=News.objects.filter(deleted=False),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class NewsAdminForm(forms.ModelForm):
    MAX_UPLOAD_SIZE = 2500000
    image = forms.ImageField(required=False)
    title = forms.CharField(max_length=200)
    meta_description = forms.CharField(max_length=300)
    content = forms.CharField()
    status = forms.IntegerField()
    language = forms.CharField()
    type = forms.CharField()

    def clean(self):
        cleaned_data = super().clean()
        errors = {}
        image = cleaned_data.get('image_event')
        if (image and image.size > self.MAX_UPLOAD_SIZE):
            msg = _('Maximum File Size Limit is')
            limit = int(self.MAX_UPLOAD_SIZE / 1000)
            errors['image'] = '{} {} kB.'.format(msg, limit)
        if len(errors):
            raise forms.ValidationError(errors)

        return cleaned_data

    class Meta:
        model = News
        fields = ['name']
        labels = {
            "title": _("Title (H1):"),
            "meta_description": _("META DESCRIPTION:"),
            "content": _("Content:"),
            'status': _("Status:"),
            'type': _("Type:")
        }

        widgets = {
            "title": forms.TextInput(attrs={'class': 'form-control'}),
            "meta_description": forms.TextInput(attrs={'class': 'form-control'}),
            "content": Textarea(
                attrs={"placeholder": _("Type in your message")}
            ),
            "status": forms.HiddenInput(),
            "language": forms.TextInput(),
            "type": forms.TextInput()
        }


class MassOperationIdsFeaturedVenueForm(forms.Form):
    ids = forms.ModelMultipleChoiceField(
        queryset=FeaturedVenue.objects.filter(deleted=False),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class FeaturedVenueAdminForm(forms.ModelForm):
    MAX_UPLOAD_SIZE = 2500000
    image = forms.ImageField(required=False)
    title = forms.CharField(max_length=200)
    meta_description = forms.CharField(max_length=300)
    content = forms.CharField()
    status = forms.IntegerField()
    language = forms.CharField()
    type = forms.CharField()

    def clean(self):
        cleaned_data = super().clean()
        errors = {}
        image = cleaned_data.get('image_event')
        if (image and image.size > self.MAX_UPLOAD_SIZE):
            msg = _('Maximum File Size Limit is')
            limit = int(self.MAX_UPLOAD_SIZE / 1000)
            errors['image'] = '{} {} kB.'.format(msg, limit)
        if len(errors):
            raise forms.ValidationError(errors)
        return cleaned_data

    class Meta:
        model = FeaturedVenue
        fields = ['name', 'connected_venue']
        labels = {
            "title": _("Title (H1):"),
            "meta_description": _("META DESCRIPTION:"),
            "content": _("Content:"),
            'status': _("Status:"),
            'type': _("Type:")
        }

        widgets = {
            "title": forms.TextInput(attrs={'class': 'form-control'}),
            "meta_description": forms.TextInput(attrs={'class': 'form-control'}),
            "content": Textarea(
                attrs={"placeholder": _("Type in your message")}
            ),
            "status": forms.HiddenInput(),
            "language": forms.TextInput(),
            "type": forms.TextInput()
        }


class MassOperationIdsWebsiteImageForm(forms.Form):
    ids = forms.ModelMultipleChoiceField(
        queryset=WebsitePage.objects.filter(deleted=False),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class WebsitePageAdminForm(forms.ModelForm):
    MAX_UPLOAD_SIZE = 2500000
    image = forms.ImageField(required=False)
    title = forms.CharField(max_length=200)
    meta_description = forms.CharField(max_length=300)
    content = forms.CharField()
    status = forms.IntegerField()
    language = forms.CharField()

    def clean(self):
        cleaned_data = super().clean()
        errors = {}
        image = cleaned_data.get('image_event')
        if (image and image.size > self.MAX_UPLOAD_SIZE):
            msg = _('Maximum File Size Limit is')
            limit = int(self.MAX_UPLOAD_SIZE / 1000)
            errors['image'] = '{} {} kB.'.format(msg, limit)
        if len(errors):
            raise forms.ValidationError(errors)
        return cleaned_data

    class Meta:
        model = FeaturedVenue
        fields = []
        labels = {
            "title": _("Title (H1):"),
            "meta_description": _("META DESCRIPTION:"),
            "content": _("Content:"),
            'status': _("Status:"),
        }

        widgets = {
            "title": forms.TextInput(attrs={'class': 'form-control'}),
            "meta_description": forms.TextInput(attrs={'class': 'form-control'}),
            "content": Textarea(
                attrs={"placeholder": _("Type in your message")}
            ),
            "status": forms.HiddenInput(),
            "language": forms.TextInput()
        }


class MassOperationIdsLPBForm(forms.Form):
    ids = forms.ModelMultipleChoiceField(
        queryset=LPB.objects.filter(deleted=False),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class LPBAdminForm(forms.ModelForm):
    MAX_UPLOAD_SIZE = 2500000
    image = forms.ImageField(required=False)
    title = forms.CharField(max_length=200)
    meta_description = forms.CharField(max_length=300)
    content = forms.CharField()
    status = forms.IntegerField()
    language = forms.CharField()

    def clean(self):
        cleaned_data = super().clean()
        errors = {}
        image = cleaned_data.get('image_event')
        if (image and image.size > self.MAX_UPLOAD_SIZE):
            msg = _('Maximum File Size Limit is')
            limit = int(self.MAX_UPLOAD_SIZE / 1000)
            errors['image'] = '{} {} kB.'.format(msg, limit)
        if len(errors):
            raise forms.ValidationError(errors)

        return cleaned_data

    class Meta:
        model = LPB
        fields = ['name']
        labels = {
            "title": _("Title (H1):"),
            "meta_description": _("META DESCRIPTION:"),
            "content": _("Content:"),
            'status': _("Status:")
        }

        widgets = {
            "title": forms.TextInput(attrs={'class': 'form-control'}),
            "meta_description": forms.TextInput(attrs={'class': 'form-control'}),
            "content": Textarea(
                attrs={"placeholder": _("Type in your message")}
            ),
            "status": forms.HiddenInput(),
            "language": forms.TextInput()
        }


class QuoteAdminForm(forms.ModelForm):
    MAX_UPLOAD_SIZE = 2500000
    image = forms.ImageField(required=False)
    quote = forms.CharField(widget=forms.widgets.Textarea(attrs={'class': 'form-control', "cols": "40", "rows": 10,
                                                                 'id': 'id_quote_textarea',
                                                                 "style": "overflow:auto;resize:none"
                                                                 }))
    current_translations = forms.CharField(required=False, widget=forms.HiddenInput)

    original_language = forms.ChoiceField(required=False, widget=forms.Select,
                                          label=_('Original language'),
                                          choices=get_original_language_choices())
    selected_language = forms.ChoiceField(required=False, widget=forms.Select,
                                          label=_('Selected language'),
                                          choices=get_selected_language_choices())
    status = forms.IntegerField()
    language = forms.CharField()

    def clean(self):
        cleaned_data = super().clean()
        errors = {}
        image = cleaned_data.get('image_event')
        if (image and image.size > self.MAX_UPLOAD_SIZE):
            msg = _('Maximum File Size Limit is')
            limit = int(self.MAX_UPLOAD_SIZE / 1000)
            errors['image'] = '{} {} kB.'.format(msg, limit)
        if len(errors):
            raise forms.ValidationError(errors)
        return cleaned_data

    class Meta:
        model = Quote
        fields = ['quote', 'connected_venue']
        labels = {
            "quote": _("Quote:"),
            'status': _("Status:"),
        }

        widgets = {
            "status": forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super(QuoteAdminForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.quote_translations:
            self.fields['current_translations'].initial = json.dumps(self.instance.quote_translations)


class MassOperationIdsQuoteForm(forms.Form):
    ids = forms.ModelMultipleChoiceField(
        queryset=Quote.objects.filter(deleted=False),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class TranslateQuoteForm(forms.Form):
    orig_lang = forms.CharField(required=True)
    contents = forms.CharField(required=False)
    quote_id = forms.IntegerField(required=False)


class UpdateQuoteForm(forms.Form):
    lang = forms.CharField(required=True)
    contents = forms.CharField(required=False)
    str_trans = forms.CharField(required=False)
    quote_id = forms.IntegerField(required=False)


class ClearQuoteTranslationsForm(forms.Form):
    quote_id = forms.IntegerField(required=False)


class TestimonialAdminForm(forms.ModelForm):
    MAX_UPLOAD_SIZE = 2500000
    image = forms.ImageField(required=False)
    username = forms.CharField(required=True, label=_("Username"))
    title = forms.CharField(required=True, label=_("Title"))
    # date = forms.TextInput(attrs={
    #             'class': 'form-control', 'id': 'datetimepicker1'
    #         })
    testimonial = forms.CharField(label=_("Review"),
                                  widget=forms.widgets.Textarea(attrs={'class': 'form-control',
                                                                       "cols": "40", "rows": 10,
                                                                       'id': 'id_testimonial_textarea',
                                                                       "style": "overflow:auto;resize:none"
                                                                       }))
    current_translations = forms.CharField(required=False, widget=forms.HiddenInput)

    original_language = forms.ChoiceField(required=False, widget=forms.Select,
                                          label=_('Original language'),
                                          choices=get_original_language_choices())
    selected_language = forms.ChoiceField(required=False, widget=forms.Select,
                                          label=_('Selected language'),
                                          choices=get_selected_language_choices())
    status = forms.IntegerField()
    language = forms.CharField()

    def clean(self):
        cleaned_data = super().clean()
        errors = {}
        image = cleaned_data.get('image_event')
        if (image and image.size > self.MAX_UPLOAD_SIZE):
            msg = _('Maximum File Size Limit is')
            limit = int(self.MAX_UPLOAD_SIZE / 1000)
            errors['image'] = '{} {} kB.'.format(msg, limit)
        if len(errors):
            raise forms.ValidationError(errors)
        return cleaned_data

    class Meta:
        model = Testimonial
        fields = ['testimonial', 'title', 'username', 'date']

        widgets = {
            "status": forms.HiddenInput(),
            'date': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'datetimepicker1'
            })
        }

    def __init__(self, *args, **kwargs):
        super(TestimonialAdminForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.testimonial_translations:
            self.fields['current_translations'].initial = json.dumps(self.instance.testimonial_translations)


class MassOperationIdsTestimonialForm(forms.Form):
    ids = forms.ModelMultipleChoiceField(
        queryset=Testimonial.objects.filter(deleted=False),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class TranslateTestimonialForm(forms.Form):
    orig_lang = forms.CharField(required=True)
    contents = forms.CharField(required=False)
    testimonial_id = forms.IntegerField(required=False)


class UpdateTestimonialForm(forms.Form):
    lang = forms.CharField(required=True)
    contents = forms.CharField(required=False)
    str_trans = forms.CharField(required=False)
    testimonial_id = forms.IntegerField(required=False)


class ClearTestimonialTranslationsForm(forms.Form):
    testimonial_id = forms.IntegerField(required=False)


class CheffeAdminForm(forms.ModelForm):
    MAX_UPLOAD_SIZE = 2500000
    image = forms.ImageField(required=False)
    fullname = forms.CharField(required=True, label=_("Cheffe or chef full name"))
    cheffe = forms.CharField(label=_("Description"),
                             widget=forms.widgets.Textarea(attrs={'class': 'form-control', "cols": "40", "rows": 10,
                                                                  'id': 'id_cheffe_textarea',
                                                                  "style": "overflow:auto;resize:none"
                                                                  }))
    current_translations = forms.CharField(required=False, widget=forms.HiddenInput)

    original_language = forms.ChoiceField(required=False, widget=forms.Select,
                                          label=_('Original language'),
                                          choices=get_original_language_choices())
    selected_language = forms.ChoiceField(required=False, widget=forms.Select,
                                          label=_('Selected language'),
                                          choices=get_selected_language_choices())
    status = forms.IntegerField()
    language = forms.CharField()

    def clean(self):
        cleaned_data = super().clean()
        errors = {}
        image = cleaned_data.get('image_event')
        if (image and image.size > self.MAX_UPLOAD_SIZE):
            msg = _('Maximum File Size Limit is')
            limit = int(self.MAX_UPLOAD_SIZE / 1000)
            errors['image'] = '{} {} kB.'.format(msg, limit)
        if len(errors):
            raise forms.ValidationError(errors)
        return cleaned_data

    class Meta:
        model = Cheffe
        fields = ['cheffe', 'connected_venue', 'fullname']

        widgets = {
            "status": forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super(CheffeAdminForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.cheffe_translations:
            self.fields['current_translations'].initial = json.dumps(self.instance.cheffe_translations)


class MassOperationIdsCheffeForm(forms.Form):
    ids = forms.ModelMultipleChoiceField(
        queryset=Cheffe.objects.filter(deleted=False),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class TranslateCheffeForm(forms.Form):
    orig_lang = forms.CharField(required=True)
    contents = forms.CharField(required=False)
    cheffe_id = forms.IntegerField(required=False)


class UpdateCheffeForm(forms.Form):
    lang = forms.CharField(required=True)
    contents = forms.CharField(required=False)
    str_trans = forms.CharField(required=False)
    cheffe_id = forms.IntegerField(required=False)


class ClearCheffeTranslationsForm(forms.Form):
    cheffe_id = forms.IntegerField(required=False)
