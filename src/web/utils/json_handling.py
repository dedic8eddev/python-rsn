import json
import datetime as dt
import uuid
from collections import Iterable
from django.utils.functional import Promise
from django.utils.encoding import force_text


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        elif isinstance(obj, dt.datetime):
            # return obj.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            return obj.strftime("%Y-%m-%dT%H:%M:%SZ")
        elif isinstance(obj, dt.time):
            # return obj.strftime("%H:%M:%S.%f")
            return obj.strftime("%H:%M:%S")
        elif isinstance(obj, dt.date):
            return obj.strftime("%Y-%m-%d")
        elif isinstance(obj, Iterable):
            return tuple(obj)
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        return json.JSONEncoder.default(self, obj)
