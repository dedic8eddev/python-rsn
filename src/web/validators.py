import re

from django.core import validators
import six
from django.utils.deconstruct import deconstructible
from django.utils.translation import ugettext_lazy as _
from web.constants import ValidationErrorE


@deconstructible
class RaisinASCIIUsernameValidator(validators.RegexValidator):
    regex = r'^[\w-]+$'
    message = _(
        'Enter a valid username. This value may contain only letters, '
        'numbers, and _/- character.'
    )
    flags = re.ASCII if six.PY3 else 0


@deconstructible
class RaisinUnicodeUsernameValidator(validators.RegexValidator):
    regex = r'^[\w-]+$'
    message = _(
        'Enter a valid username. This value may contain only letters, '
        'numbers, and _/- character.'
    )
    code = ValidationErrorE.INVALID_USERNAME
    flags = re.UNICODE if six.PY2 else 0
