import re
import json
from django import forms
from django.contrib import auth
from django.db.models import Q
from django.core.exceptions import ValidationError
from web.models import UserProfile


def strip_cleaned_data(cleaned_data, fields):
    for key in fields:
        if key in cleaned_data and cleaned_data[key] and isinstance(cleaned_data[key], str):
            cleaned_data[key] = cleaned_data[key].strip()
            cleaned_data[key] = re.sub('\s{2,}', ' ', cleaned_data[key])

    return cleaned_data


class AutocompleteQueryForm(forms.Form):
    query = forms.CharField(required=False)
    query_type = forms.CharField(required=False)
    min_letters = forms.IntegerField(required=False)
    winemaker = forms.IntegerField(required=False)


# API reset password
class ResetUserPasswordForm(forms.Form):
    username = forms.CharField(required=True)


class ResetUserPasswordByEmailUsernameForm(forms.Form):
    username = forms.CharField(
        label=u'Username', max_length=30, required=True,
        widget=forms.TextInput(attrs={'size': '40'}))


class ResetUserPasswordByEmailForm(forms.Form):
    email = forms.EmailField()


class LoginForm(forms.Form):
    error_css_class = 'error'
    required_css_class = 'required'

    username = forms.CharField(
        label=u'Username', required=True,
        widget=forms.TextInput(attrs={'size': '40'}))
    password = forms.CharField(
        label=u'Password', max_length=100, required=True,
        widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.user = None
        self.fields['username'].widget.attrs['placeholder'] = u'Username'
        self.fields['password'].widget.attrs['placeholder'] = u'Password'

    def clean_password(self):
        if 'username' in self.cleaned_data:
            username = self.cleaned_data['username']
            password = self.cleaned_data['password']
            try:
                user = UserProfile.objects.get((Q(username__iexact=username) | Q(email__iexact=username)) &
                                               Q(is_active=True))

                self.user = auth.authenticate(username=user.email, password=password)

                if self.user is None:
                    raise forms.ValidationError(u"Login error")

                return self.cleaned_data['password']
            except UserProfile.DoesNotExist:
                pass

        raise forms.ValidationError(u"Login error")


class JsonStrField(forms.Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        "Returns a DICT/LIST object."
        value = str(value).strip()
        if not value:
            return None
        try:
            json_value = json.loads(value)
        except ValueError:
            raise ValidationError("invalid JSON format", code='invalid')
        if not isinstance(json_value, list) and not isinstance(json_value, dict):
            raise ValidationError("invalid JSON format", code='invalid')

        return json_value

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        return attrs
