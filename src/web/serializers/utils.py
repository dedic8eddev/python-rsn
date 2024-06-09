from collections import OrderedDict

from rest_framework import serializers
from rest_framework.fields import SkipField

from web.utils.mentions import format_mentions
from web.utils.model_object_tools import author_has_badge_data
from web.utils.upload_tools import aws_url


class ToReprMixin(object):
    def to_representation(self, instance):
        ret = OrderedDict()
        fields = [
            field for field in self.fields.values() if not field.write_only
        ]

        for field in fields:
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            if attribute is None and field.__class__.__name__ not in [
                'ImageUrlField', 'ImageUrlThumbField'
            ]:
                ret[field.field_name] = None
            else:
                ret[field.field_name] = field.to_representation(attribute)

        return ret


class ImageUrlField(serializers.Field):
    def to_representation(self, value):
        return aws_url(value)


class ImageUrlThumbField(serializers.Field):
    def to_representation(self, value):
        return aws_url(value, thumb=True)


class HasBadgeDataField(serializers.Field):
    def to_representation(self, value):
        if value is not None:
            return author_has_badge_data(
                p_once_expiry_date_ms=value.p_once_expiry_date_ms,
                p_monthly_expiry_date_ms=value.p_monthly_expiry_date_ms
            )[0]
        else:
            return False


class BadgeExpiryDateMsField(serializers.Field):
    def to_representation(self, value):
        if value is not None:
            return author_has_badge_data(
                p_once_expiry_date_ms=value.p_once_expiry_date_ms,
                p_monthly_expiry_date_ms=value.p_monthly_expiry_date_ms
            )[1]
        else:
            return None


class DistanceField(serializers.Field):
    def to_representation(self, value):
        if value.m < 250:
            # distance in meters (e.g. 13 m, 157 m)
            return str(value.m) + " m"

        if value.m < 1000:
            # round to nearest 250m (e.g. )
            return str(value.m // 250 * 250) + " m"

        if value.km < 1000:
            # round to nearest .25 km (e.g. 4.25 km, 85.5 km, 543.75 km)
            return str(round(value.km * 4) / 4) + " km"

        # round to nearest 50 km (e.g. 1050 km, 1500 km, 2250 km)
        return str(round(value.km // 50 * 50)) + " km"


class MentionsField(serializers.Field):
    def to_representation(self, value):
        return format_mentions(value) if value else []
