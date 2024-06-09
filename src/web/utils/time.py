import datetime as dt
import arrow

from django.utils.translation import get_language

import pendulum
import pytz

from web.constants import Language


def get_current_date():
    return dt.datetime.now()


def get_datetime_from_string(dt_str):
    dt_obj = None
    try:
        dt_obj = dt.datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S%z')  # with timezone of format +HHMM
    except ValueError:
        pass
    except Exception:
        pass
    if dt_obj:
        return dt_obj

    try:
        dt_obj = dt.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S%z')  # with timezone of format +HHMM
    except ValueError:
        pass
    except Exception:
        pass
    if dt_obj:
        return dt_obj

    try:
        dt_obj = dt.datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S')  # without timezone, just YYYY-mm-ddTHH:MM:SS
    except ValueError:
        pass
    except Exception:
        pass
    if dt_obj:
        return dt_obj

    try:
        dt_obj = dt.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')  # without timezone, just YYYY-mm-ddTHH:MM:SS
    except ValueError:
        pass
    except Exception:
        pass
    if dt_obj:
        return dt_obj

    try:
        dt_obj = dt.datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%SZ')  # without timezone, just YYYY-mm-ddTHH:MM:SSZ
    except ValueError:
        pass
    except Exception:
        pass
    if dt_obj:
        return dt_obj

    try:
        dt_obj = dt.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%SZ')  # without timezone, just YYYY-mm-ddTHH:MM:SSZ
    except ValueError:
        pass
    except Exception:
        pass
    if dt_obj:
        return dt_obj

    try:
        dt_obj = dt.datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S.%f')  # without timezone, just YYYY-mm-ddTHH:MM.msec
    except ValueError:
        pass
    except Exception:
        pass
    if dt_obj:
        return dt_obj

    try:
        dt_obj = dt.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S.%f')  # without timezone, just YYYY-mm-ddTHH:MM.msec
    except ValueError:
        pass
    except Exception:
        pass
    if dt_obj:
        return dt_obj

    try:
        dt_obj = dt.datetime.strptime(dt_str, '%Y-%m-%d')  # without timezone, just YYYY-mm-dd
    except ValueError:
        pass
    except Exception:
        pass
    if dt_obj:
        return dt_obj

    return None


def conv_cet_to_utc(date_naive):
    if isinstance(date_naive, str):
        date_naive = get_datetime_from_string(date_naive)  # "%Y-%m-%dT%H:%M:%S"

    if not isinstance(date_naive, dt.datetime):
        return date_naive

    date_from = pytz.timezone('CET').localize(date_naive, is_dst=False)
    date_to = date_from.astimezone(pytz.timezone('UTC'))
    return date_to


def conv_utc_to_cet(date_naive):
    if isinstance(date_naive, str):
        date_naive = get_datetime_from_string(date_naive)  # "%Y-%m-%dT%H:%M:%S"

    if not isinstance(date_naive, dt.datetime):
        return date_naive

    date_utc = pytz.timezone('UTC').localize(date_naive, is_dst=False)
    date_cet = date_utc.astimezone(pytz.timezone('CET'))
    return date_cet


def get_offset_for_tz_name(tz_name):
    if not tz_name:
        return '+0000'

    dt_now = pendulum.now(tz=tz_name)
    return dt_now.strftime("%z")


def get_dt_now_pendulum(tz_name=None):
    if tz_name:
        dt_now = pendulum.now(tz=tz_name)
    else:
        dt_now = pendulum.now(tz='CET')  # fallback
    return dt_now


def dt_from_str_pendulum(dt_str, tz_name=None):
    dt_obj = None
    try:
        dt_obj = pendulum.from_format(dt_str, 'YYYY-MM-DDTHH:mm:ssZZ')  # with timezone of format +HHMM
    except ValueError:
        pass
    except Exception:
        pass
    if dt_obj:
        return dt_obj

    try:
        dt_obj = pendulum.from_format(dt_str, 'YYYY-MM-DD HH:mm:ssZZ')  # with timezone of format +HHMM
    except ValueError:
        pass
    except Exception:
        pass
    if dt_obj:
        return dt_obj

    try:
        dt_obj = pendulum.from_format(dt_str, 'YYYY-MM-DDTHH:mm:ss')  # without timezone, just YYYY-mm-ddTHH:MM:SS
    except ValueError:
        pass
    except Exception:
        pass
    if dt_obj:
        return dt_obj

    try:
        dt_obj = pendulum.from_format(dt_str, 'YYYY-MM-DD HH:mm:ss')  # without timezone, just YYYY-mm-ddTHH:MM:SS
    except ValueError:
        pass
    except Exception:
        pass
    if dt_obj:
        return dt_obj

    try:
        dt_obj = pendulum.from_format(dt_str, 'YYYY-MM-DD')  # without timezone, just YYYY-mm-dd
    except ValueError:
        pass
    except Exception:
        pass
    if dt_obj:
        return dt_obj

    return None


def dt_to_str_pendulum(dt_obj, dt_format="%Y-%m-%dT%H:%M:%S%z"):
    return dt_obj.strftime(dt_format)


def pendulum_datetime(year, month, day, hour, minute, second, tz=None):
    if hour == 24:
        hour = 23
        minute = 59
        second = 59

    if tz:
        return pendulum.datetime(year, month, day, hour, minute, second, tz=tz)
    else:
        return pendulum.datetime(year, month, day, hour, minute, second)


def get_datetime_human(datetime_obj):
    """
    Get string representation of datetime object in human readable format
    """
    try:
        # get accept language
        language = get_language()

        # exclude the letter "E" after the number in the date in french, which we don't use in France.
        # choose different datetime format
        # format example: '3 mars 2019'
        if language == Language.FR:
            datetime_human = arrow.get(datetime_obj).format('D MMM YYYY', locale=language)
        elif language == Language.IT:
            datetime_human = arrow.get(datetime_obj).format('D MMM YYYY', locale=language)
        else:
            # format example: '3rd Mar 2019'
            datetime_human = arrow.get(datetime_obj).format('Do MMM YYYY', locale=language)
        return datetime_human
    except ValueError:
        return arrow.get(datetime_obj).format('Do MMM YYYY', locale='en')
