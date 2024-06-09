import json
import re

from django import forms
from django.core.exceptions import ValidationError
from django.http import QueryDict
from django.template import loader
from django.utils.translation import ugettext_lazy as _

from web.constants import WineColorE

wine_item_ordered_field_mapping = ['name', 'name_short', 'designation',
                                   'grape_variety', 'color', 'year',
                                   'is_sparkling', 'wine_temp_dir', 'ordering']


class FieldItemCollectionManager(object):
    w_array = []

    def __init__(
        self, form, FieldItemClass, ordered_field_mapping, field_prefix,
        field_match, args_form=None, temp_fields=[], initial_row_number=0,
        item_params={}
    ):
        self.form = form
        self.form_fields = form.fields

        self.ordered_field_mapping = ordered_field_mapping
        self.temp_fields = temp_fields

        self.field_prefix = field_prefix
        self.field_match = field_match

        self.ItemClass = FieldItemClass
        self.initial_row_number = initial_row_number
        self.item_params = item_params

        if args_form and isinstance(args_form[0], QueryDict):
            self.set_items_from_request(args_form[0])

    def clear_items(self):
        self.w_array = []

    def add_clean_item(self, fv_to_set = {}):
        values = []
        for field in wine_item_ordered_field_mapping:
            if field in fv_to_set:
                values.append(fv_to_set[field])
            else:
                values.append('')
        self.add_item(values)

    def add_item(self, item):
        i = len(self.w_array)

        row_number = i + int(self.initial_row_number)

        if self.item_params:
            item_params = self.item_params
        else:
            item_params = {}

        item_field_name = self.field_prefix + str(row_number)
        item_params['row_number'] = row_number

        self.form_fields[item_field_name] = self.ItemClass(**item_params)
        self.form_fields[item_field_name].initial = item
        item_obj = self.form_fields[item_field_name]

        item_data = {
            'value': item,
            'object': item_obj,
            'bound_object': item_obj.get_bound_field(
                self.form, item_field_name
            ),
            'row_number': row_number,
            'field_name': item_field_name,
        }

        self.w_array.append(item_data)

        return item_data

    def init_items(self):
        self.w_array = []

    def set_items(self, items):
        self.init_items()
        for item in items:
            self.add_item(item)

    def set_items_from_model(self, model_items):
        self.init_items()

        for model in model_items:
            item_out = []
            for field in self.ordered_field_mapping:
                if field not in self.temp_fields:
                    item_out.append(getattr(model, field))

            self.add_item(item_out)

    def set_items_from_request(self, req_dict):
        self.init_items()

        items_by_row_col = {}

        for key, value in req_dict.items():
            x = re.search(self.field_match, key)

            if x:
                groups = x.groups()
                row = int(groups[0])
                col = int(groups[1])

                if row not in items_by_row_col:
                    items_by_row_col[row] = {}

                if col not in items_by_row_col[row]:
                    items_by_row_col[row][col] = value

        keys = sorted(items_by_row_col.keys())
        for key in keys:
            row_out = []

            for field_index, field_name in enumerate(
                self.ordered_field_mapping
            ):
                if field_index in items_by_row_col[key].keys():
                    row_out.append(items_by_row_col[key][field_index])
                else:
                    row_out.append(False)

            self.add_item(row_out)

    def items_as_model_entities(self, ModelClass, user=None, defaults={},
                                id_field='id', fields_extra_data=[]):
            model_items_out = []

            for item_data in self.w_array:
                item = item_data['value']
                data_map = {}
                extra_data = {}

                if defaults:
                    for field, value in defaults.items():
                        if field in fields_extra_data:
                            extra_data[field] = value
                        else:
                            data_map[field] = value

                for i, field in enumerate(self.ordered_field_mapping):
                    if i < len(item) and field not in self.temp_fields:
                        if field in fields_extra_data:
                            extra_data[field] = item[i]
                        else:
                            data_map[field] = item[i]

                if id_field and id_field in data_map and data_map[id_field]:
                    model_entity = ModelClass.active.get(**{id_field: data_map[id_field]})
                    for field, value in data_map.items():
                        setattr(model_entity, field, value)
                else:
                    model_entity = ModelClass(**data_map)

                model_item_row = {
                    'model_item': model_entity,
                    'extra_data': extra_data,
                }

                model_items_out.append(model_item_row)

            return model_items_out

    def items(self):
        return self.w_array


def check_test_x(value):
    return value


class WinemakerWineItemWidget(forms.widgets.MultiWidget):
    # required since Django 1.11:
    template_name = "base/elements/edit/winemaker.wine.widget.html"

    def set_field_errors(self, errors):

        self.field_errors = errors

        for i, error in enumerate(self.field_errors):
            if error:
                self.widgets[i].attrs['class'] = self.error_class

    def set_general_errors(self, errors):
        self.general_errors = errors

    def __init__(self, widgets=None, attrs=None, row_number=None, is_new=False, error_class='form-control error-field'):
        self.row_number = row_number
        self.is_new = is_new

        self.field_errors = []
        self.general_errors = []
        self.error_class = error_class

        widgets_mapped = {
            'name': forms.TextInput(attrs={"class": "form-control", "id": "wine",
                                           "placeholder": "ex : L'Antidote"}),  # name
            'name_short': forms.TextInput(attrs={"class": "form-control", "id": "wine_name_short",
                                                 "placeholder": "ex : L'Antidote"}),  # name_short
            'designation': forms.TextInput(attrs={"class": "form-control", "id": "designation",
                                                  "placeholder": "ex : Bandol"}),  # designation
            'grape_variety': forms.TextInput(attrs={"class": "form-control", "id": "grape-variety",
                                                    "placeholder": "ex : Mourvedre"}),  # grape_variety

            'color': forms.Select(choices=WineColorE.pairs),  # color
            'year': forms.NumberInput(attrs={"class": "form-control", "id": "year",
                                             "placeholder": "ex : 2010"}),  # year
            'is_sparkling': forms.CheckboxInput(attrs={'value': 1}, check_test=check_test_x),  # is_sparkling

            # 'id':            forms.HiddenInput(),                                                        # id
            'wine_temp_dir': forms.HiddenInput(),  # wine_temp_dir
            'ordering':      forms.HiddenInput(),  # ordering
        }

        # self.widgets = widgets
        widgets = [widgets_mapped[key] for key in wine_item_ordered_field_mapping]
        super(WinemakerWineItemWidget, self).__init__(widgets, attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['row_number'] = self.row_number
        return context

    # no longer used in Django 1.11, ref:
    # https://stackoverflow.com/questions/46452755/
    #     migrating-django-from-1-9-to-1-11-trouble-with-multivaluefield-and-multiwidget/46492191#46492191
    # def format_output(self, rendered_widgets):
    #     template = loader.get_template('base/elements/edit/winemaker.wine.widget.html')
    #     context = {
    #         'widgets': rendered_widgets,
    #         'field_errors': self.field_errors,
    #         'general_errors': self.general_errors,
    #         'row_number': self.row_number,
    #         'is_new': self.is_new,
    #     }
    #
    #     return template.render(context)

    def decompress(self, value):
        if not value:
            return []

        return json.loads(value)


class WinemakerWineItemField(forms.MultiValueField):

    def init_general_errors(self):
        self.general_errors = []

    def init_field_errors(self):
        self.field_errors = [[] for i in range(0, len(self.fields))]
        self.widget.set_field_errors(self.field_errors)

    def add_field_error(self, field_i, error):
        self.field_errors[field_i].append(str(error))
        self.widget.set_field_errors(self.field_errors)

    def add_general_error(self, error):
        self.general_errors.append(error)
        self.widget.set_general_errors(self.general_errors)

    def __init__(self, row_number=None, is_new=False, *args, **kwargs):
        self.field_errors = []
        self.general_errors = []

        self.widget = WinemakerWineItemWidget(row_number=row_number, is_new=is_new)

        fields_mapped = {
            'name':       forms.CharField(required=True),
            'name_short': forms.CharField(required=False),
            'designation': forms.CharField(required=False),
            'grape_variety': forms.CharField(required=True),

            'color': forms.ChoiceField(required=False, choices=WineColorE.pairs),
            'year': forms.IntegerField(required=False),
            'is_sparkling': forms.BooleanField(required=False),

            # 'id': forms.IntegerField(required=False),
            'wine_temp_dir': forms.CharField(required=False),
            'ordering': forms.CharField(required=False),
        }
        error_messages = {
            'incomplete': _('You must fill all the fields and select a wine color'),
        }

        self.fields = [fields_mapped[key] for key in wine_item_ordered_field_mapping]

        super(WinemakerWineItemField, self).__init__(self.fields, require_all_fields=False, *args, **kwargs)

    def are_all_empty(self, value):
        result = True

        # 0, 1, 2, 4
        # indexes_to_check = [0, 2, 3, 5]
        indexes_to_check = []

        for index in indexes_to_check:
            if value[index] and not value[index] in self.empty_values:
                result = False

        return result

    def clean(self, value):
        self.init_field_errors()
        self.init_general_errors()

        if self.are_all_empty(value):
            return self.compress([])

        """
        Validates every value in the given list. A value is validated against
        the corresponding Field in self.fields.

        For example, if this MultiValueField was instantiated with
        fields=(DateField(), TimeField()), clean() would call
        DateField.clean(value[0]) and TimeField.clean(value[1]).
        """

        clean_data = []
        errors = []

        # value not set (empty result) or value is a tuple or a list
        if not value or isinstance(value, (list, tuple)):
            # value not set or all values are empty
            if not value or not [v for v in value if v not in self.empty_values]:
                # field is required - can't pass
                if self.required:
                    self.add_general_error(self.error_messages['required'])
                # field is not required - shall pass as empty field
                else:
                    return self.compress([])
        else:
            # invalid value - not decompressed or otherwise broken
            self.add_general_error(self.error_messages['invalid'])
            raise ValidationError(self.error_messages['invalid'], code='invalid')

        # not empty, not broken - iterate all fields
        for i, field in enumerate(self.fields):
            try:
                field_value = value[i]
            except IndexError:
                field_value = None

            # value of the field "i" is empty
            if field_value in self.empty_values:

                if self.require_all_fields:
                    # all fields are required, but one is empty - add error
                    if self.required:
                        self.add_field_error(i, self.error_messages['required'])
                # field is required, there is no requirement for all fields
                elif field.required:
                    # Otherwise, add an 'incomplete' error to the list of
                    # collected errors and skip field cleaning, if a required
                    # field is empty.
                    # errors.append(field.error_messages['incomplete'])
                    self.add_field_error(i, field.error_messages['required'])

                    continue
            try:
                clean_data.append(field.clean(field_value))
            except ValidationError as e:
                # Collect all validation errors in a single list, which we'll
                # raise at the end of clean(), rather than raising a single
                # exception for the first error we encounter. Skip duplicates.
                # errors.extend(m for m in e.error_list)
                self.add_field_error(i, [m for m in e.error_list])
                # errors.extend(m for m in e.error_list if m not in errors)

        if errors or self.general_errors or len([f for f in self.field_errors if f])>0:
            raise ValidationError("errors were found: %s %s %s" % (errors, self.general_errors, self.field_errors))

        out = self.compress(clean_data)
        self.validate(out)
        self.run_validators(out)
        return out

    def compress(self, data_list):
        return data_list


def validate_password(data, key):
    password = data.get(key)

    if not password:
        msg = 'Password can not be empty.'
        raise ValidationError(_(msg))

    if len(password) < 6 or len(password) > 30:
        msg = 'Password must be between 6 and 30 characters.'
        raise ValidationError(_(msg))

    letters = set(password)

    lower = any(letter.islower() for letter in letters)
    upper = any(letter.isupper() for letter in letters)
    number = any(letter.isdigit() for letter in letters)

    if not upper or not lower or not number:
        msg = (
            'Password must contain a mix of lowercase letters, '
            'uppercase letters and numbers.'
        )

        raise ValidationError(_(msg))

    return data[key]
