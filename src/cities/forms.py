from django import forms
from .models import (Author, City, District)
from web.models import UserProfile


class CountrySearchFrom(forms.Form):
    name = forms.CharField(required=True, label='country name')


class CitySearchForm(forms.Form):
    name = forms.CharField(required=True, label='city name')


class RegionSearchForm(forms.Form):
    name = forms.CharField(required=True, label='region name')


class VenueSearchFrom(forms.Form):
    name = forms.CharField(required=True, label='venue name')


class DistrictSearchFrom(forms.Form):
    name = forms.CharField(required=True, label='district name')


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ('name', 'url', 'description', 'image')


class LastEditorForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['website_url', 'image', 'description', 'full_name']


class DistrictCreateForm(forms.Form):
    city = forms.IntegerField(required=True)
    new_district = forms.CharField(required=True)

    def save(self):
        city = City.objects.get(id=self.cleaned_data.get('city'))
        district = District(
            city=city,
            name=self.cleaned_data.get('new_district'),
            location=city.location,
            population=0
        )
        district.save()
