import re

from web.utils.enum import EnumMetaclass


class Language:
    """
    Language constants
    """
    FR = 'fr'
    EN = 'en'
    IT = 'it'


# class for all entity types using "status" field except Winemaker
class StatusE(metaclass=EnumMetaclass):
    DRAFT = 10
    PUBLISHED = 20


class PlaceStatusE(metaclass=EnumMetaclass):
    DRAFT = 10
    IN_REVIEW = 12
    INFO_REQUIRED = 13
    IN_DOUBT = 15
    NOT_ELIGIBLE = 16
    ELIGIBLE = 17
    SUBSCRIBER = 18
    TO_PUBLISH = 19
    PUBLISHED = 20
    CLOSED = 35


class PlaceTypeE(metaclass=EnumMetaclass):
    RESTAURANT = 10
    BAR = 20
    WINE_SHOP = 30


class PlaceImageAreaE(metaclass=EnumMetaclass):
    FRONT = 10
    INTERIOR = 20
    AT_WORK = 30
    TEAM = 40
    ARCHIVED = 50


class PlaceSubscrTypeE(metaclass=EnumMetaclass):
    SUBSCRIBED_TO_BE_RECOMMEND = 10
    PREVIOUSLY_RECOMMENDED = 20


class PlaceSourceInfoE(metaclass=EnumMetaclass):
    SUBMITTED_ON_PRO_WEBSITE = 10
    SUBMITTED_ON_APP = 20
    REGISTERED_ON_CHARGEBEE = 30
    REGISTERED_ON_CMS = 40


class WinemakerStatusE(metaclass=EnumMetaclass):
    DRAFT = 10
    IN_DOUBT = 15
    VALIDATED = 20  # NATURAL
    REFUSED = 25
    BIO_ORGANIC = 30  # NEW STATUS
    TO_INVESTIGATE = 45


class WinemakerTypeE(metaclass=EnumMetaclass):
    NATURAL = 10
    OTHER = 20


# Winemaker type statuses
wm_type_statuses = {
    WinemakerTypeE.NATURAL: [WinemakerStatusE.VALIDATED],
    WinemakerTypeE.OTHER: [WinemakerStatusE.DRAFT,
                           WinemakerStatusE.IN_DOUBT,
                           WinemakerStatusE.REFUSED,
                           WinemakerStatusE.BIO_ORGANIC,
                           WinemakerStatusE.TO_INVESTIGATE],
}


class WineColorE(metaclass=EnumMetaclass):
    RED = 10
    WHITE = 20
    PINK = 30
    ORANGE = 40


class WineListStatusE(metaclass=EnumMetaclass):
    ON_HOLD = 10
    OK = 20
    BG = 30
    BG_PROCESSING = 40
    FAILED = 50


class UserStatusE(metaclass=EnumMetaclass):
    ACTIVE = 10
    INACTIVE = 20
    BANNED = 25


class UserTypeE(metaclass=EnumMetaclass):
    USER = 10
    EDITOR = 20
    ADMINISTRATOR = 30
    OWNER = 40


class UserOriginE(metaclass=EnumMetaclass):
    """
    the way User registered in the Raisin
    """
    MOBILE_APP = 10  # submitted through the app
    PRO_WEBSITE = 20  # through Raisin Pro. website - when Subscription Flow
    # will be ready
    CHARGEBEE = 30  # done by Administrator
    CMS = 40  # done by Administrator


class PostTypeE(metaclass=EnumMetaclass):
    WINE = 10
    NOT_WINE = 20
    FOOD = 30


class VenueWineTypeE(object):
    WHITE = 'white'
    RED = 'red'
    PINK = 'pink'
    ORANGE = 'orange'
    SPARKLING = 'sparkling'


venue_wine_type_to_color_is_sparkling = {
    VenueWineTypeE.WHITE: [WineColorE.WHITE, False],
    VenueWineTypeE.RED: [WineColorE.RED, False],
    VenueWineTypeE.PINK: [WineColorE.PINK, False],
    VenueWineTypeE.ORANGE: [WineColorE.ORANGE, False],
    VenueWineTypeE.SPARKLING: [None, True],
}


class WineStatusE(metaclass=EnumMetaclass):
    ON_HOLD = 10
    IN_DOUBT = 15   # api_status = 10 and in_doubt =True
    VALIDATED = 20
    REFUSED = 25
    HIDDEN = 40
    # extra statuses
    BIO_ORGANIC = 30  # NEW STATUS
    DELETED = 35  # api_status=10 and is_archived=True
    TO_INVESTIGATE = 45


class PostStatusE(metaclass=EnumMetaclass):
    DRAFT = 10
    IN_DOUBT = 15
    PUBLISHED = 20     # NATURAL
    REFUSED = 25       # NOT NATURAL
    HIDDEN = 40        # --- NOT USED ---
    # extra statuses
    BIO_ORGANIC = 30   # NEW STATUS
    DELETED = 35       # is_archived=True
    TO_INVESTIGATE = 45


post_statuses_for_wine_status = {
    WineStatusE.ON_HOLD: PostStatusE.DRAFT,
    WineStatusE.IN_DOUBT: PostStatusE.IN_DOUBT,
    WineStatusE.VALIDATED: PostStatusE.PUBLISHED,
    WineStatusE.REFUSED: PostStatusE.REFUSED,
    WineStatusE.HIDDEN: PostStatusE.HIDDEN,
    WineStatusE.BIO_ORGANIC: PostStatusE.BIO_ORGANIC,
    WineStatusE.DELETED: PostStatusE.DELETED,
    WineStatusE.TO_INVESTIGATE: PostStatusE.TO_INVESTIGATE
}

# used in wine adding in the winemaker edition
wine_statuses_for_winemaker_status = {
    WinemakerStatusE.VALIDATED: PostStatusE.PUBLISHED,
    WinemakerStatusE.DRAFT: PostStatusE.DRAFT,
    WinemakerStatusE.REFUSED: PostStatusE.REFUSED,
    WinemakerStatusE.BIO_ORGANIC: PostStatusE.BIO_ORGANIC,
    WinemakerStatusE.IN_DOUBT: PostStatusE.IN_DOUBT,
    WinemakerStatusE.TO_INVESTIGATE: PostStatusE.TO_INVESTIGATE,
}


def get_post_status_for_wine_status(wine_status):
    """
    Get post status by wine status

    :param wine_status: The wine status
    """
    if post_statuses_for_wine_status[wine_status]:
        return post_statuses_for_wine_status[wine_status]
    else:
        return PostStatusE.DRAFT


def get_wine_status_for_winemaker_status(wm_status):
    """
    Get wine status by winemaker status

    :param wm_status: The winemaker status
    """
    if wine_statuses_for_winemaker_status[wm_status]:
        return wine_statuses_for_winemaker_status[wm_status]
    else:
        return PostStatusE.DRAFT


class ApiErrorCodeE(metaclass=EnumMetaclass):
    WRONG_AUTH_INVALID_CREDENTIALS = 93
    WRONG_AUTH_INVALID_TOKEN = 97
    WRONG_AUTH_DOES_NOT_EXIST = 112
    WRONG_AUTH_CREDENTIALS_NOT_PROVIDED = 1120

    WRONG_AUTH_CREDENTIALS_MALFORMED_SPACES = 1121
    WRONG_AUTH_CREDENTIALS_MALFORMED_BASE64 = 1122
    WRONG_AUTH_INACTIVE_OR_DELETED = 1123

    MAX_FAILED_ATTEMPTS_REACHED = 1200

    RESULT_ALREADY_EXISTS = 98
    RESULT_ALREADY_EXISTS_USERNAME = 115
    RESULT_ALREADY_EXISTS_EMAIL = 116
    INVALID_USERNAME_SYNTAX = 1099
    INVALID_EMAIL_SYNTAX = 1109
    FIELD_IS_REQUIRED = 1119
    USER_NOT_FOUND = 1500
    INVALID_REGISTER = 2000


class ApiResultE(metaclass=EnumMetaclass):
    INTERNAL_ERROR = 99
    INVALID_DATA = 2


class ApiResultStatusE(metaclass=EnumMetaclass):
    STATUS_OK = 100
    RESULT_EMPTY = 110

    WRONG_PARAMETERS = 101
    RESULT_ERROR = 102
    RESULT_ALREADY_EXISTS = 103

    RESULT_ALREADY_EXISTS_USERNAME = 115
    RESULT_ALREADY_EXISTS_EMAIL = 116

    WRONG_AUTH = 111
    WRONG_AUTH_DOES_NOT_EXIST = 111   # 112
    WRONG_AUTH_CREDENTIALS_NOT_PROVIDED = 111
    INVALID_REGISTER = 2000


class SysMessageTypeE(metaclass=EnumMetaclass):
    EMAIL = 10
    SMS = 20


class SysMessageStatusE(metaclass=EnumMetaclass):
    PENDING = 10
    SENT = 20


class TimeLineItemTypeE(metaclass=EnumMetaclass):
    USER = 10
    POST = 20
    PLACE = 30


class CalEventStatusE(metaclass=EnumMetaclass):
    PUBLISHED = 20
    DRAFT = 10


class PushNotifyTypeE(metaclass=EnumMetaclass):
    NOTIFY_LIKE_WINEPOST = 10
    NOTIFY_DRANK_IT_TOO = 20
    NOTIFY_COMMENT_WINEPOST = 30
    NOTIFY_STAR_REVIEW = 40
    NOTIFY_STAR_REVIEW_AT_VALIDATION = 45
    NOTIFY_WINEPOST_ACCEPTED = 50

    NOTIFY_COMMENT_PLACE = 60
    NOTIFY_LIKE_PLACE = 70
    NOTIFY_PLACE_ACCEPTED = 80

    NOTIFY_MENTIONED_COMMENT = 90
    NOTIFY_MENTIONED_NOT_COMMENT = 100
    NOTIFY_FREE_GLASS = 120


class ParentItemTypeE(object):
    POST = 'post'
    PLACE = 'place'
    USER = 'user'
    CAL_EVENT = 'cal_event'


# todo fixme - zrobić enum dla typów znakowych
class AutocompleteQueryType(object):
    STARTS = 'starts'
    CONTAINS = 'contains'
    ENDS = 'ends'


class SpecialStatusE(metaclass=EnumMetaclass):
    DELETE = 300
    DUPLICATE = 500
    NOT_WINE = 1212
    CLOSE = 700
    WINEPOST_IN_DOUBT = 888
    PLACE_IN_DOUBT = 888

    UNBAN_USER = 900
    BAN_USER = 950


class CalEventTypeE(metaclass=EnumMetaclass):
    EVENT = 10
    BOOKS_MOVIES = 20


class DonationFrequencyE(metaclass=EnumMetaclass):
    ONCE = 10
    MONTHLY = 20


class DonationStatusE(metaclass=EnumMetaclass):
    ACTIVE = 10
    FINISHED = 20
    CANCELED = 30
    FAILED = 35


class DonationReceiptStatusE(metaclass=EnumMetaclass):
    OK = 10
    FAILED = 15


class AppEnvE(metaclass=EnumMetaclass):
    ANDROID = 1
    IOS = 2


class WinePostListForE(object):
    ALL = 'all'
    USERS = 'users'
    OWNERS = 'owners'
    GEOLOCATED = 'geolocated'


class PlaceListForE(object):
    ALL = 'all'
    FREE = 'free'
    SUBSCRIBERS = 'subscribers'
    NOT_CONNECTED = 'not_connected'
    IN_TRIAL = 'in_trial'
    STICKERS_TO_SEND = 'stickers_to_send'
    STICKERS = 'stickers'


def get_selected_languages():
    res = [
        'FR',
        'EN',
        'JA',
        'IT',
        'ES',
        'PT',
    ]
    return res


def get_selected_language_choices():
    res = [
        ('FR', 'FR'),
        ('EN', 'EN'),
        ('JA', 'JA'),
        ('IT', 'IT'),
        ('ES', 'ES'),
        ('PT', 'PT'),
    ]
    return res


def get_pro_language_choices():
    res = [
        (None, 'Not recognized'),
        ('FR', 'FR'),
        ('EN', 'EN'),
        ('JA', 'JA'),
        ('IT', 'IT'),
        ('ES', 'ES'),
        ('DE', 'DE'),
    ]
    return res


def get_original_language_choices():
    res = [
        (None, '--'),
        ('AF', 'AF'),
        ('AM', 'AM'),
        ('AR', 'AR'),
        ('AZ', 'AZ'),
        ('BE', 'BE'),
        ('BG', 'BG'),
        ('BN', 'BN'),
        ('BS', 'BS'),
        ('CA', 'CA'),
        ('CEB', 'CEB'),
        ('CO', 'CO'),
        ('CS', 'CS'),
        ('CY', 'CY'),
        ('DA', 'DA'),
        ('DE', 'DE'),
        ('EL', 'EL'),
        ('EN', 'EN'),
        ('EO', 'EO'),
        ('ES', 'ES'),
        ('ET', 'ET'),
        ('EU', 'EU'),
        ('FA', 'FA'),
        ('FI', 'FI'),
        ('FR', 'FR'),
        ('FY', 'FY'),
        ('GA', 'GA'),
        ('GD', 'GD'),
        ('GL', 'GL'),
        ('GU', 'GU'),
        ('HA', 'HA'),
        ('HAW', 'HAW'),
        ('HE**', 'HE**'),
        ('HI', 'HI'),
        ('HMN', 'HMN'),
        ('HR', 'HR'),
        ('HT', 'HT'),
        ('HU', 'HU'),
        ('HY', 'HY'),
        ('ID', 'ID'),
        ('IG', 'IG'),
        ('IS', 'IS'),
        ('IT', 'IT'),
        ('JA', 'JA'),
        ('JW', 'JW'),
        ('KA', 'KA'),
        ('KK', 'KK'),
        ('KM', 'KM'),
        ('KN', 'KN'),
        ('KO', 'KO'),
        ('KU', 'KU'),
        ('KY', 'KY'),
        ('LA', 'LA'),
        ('LB', 'LB'),
        ('LO', 'LO'),
        ('LT', 'LT'),
        ('LV', 'LV'),
        ('MG', 'MG'),
        ('MI', 'MI'),
        ('MK', 'MK'),
        ('ML', 'ML'),
        ('MN', 'MN'),
        ('MR', 'MR'),
        ('MS', 'MS'),
        ('MT', 'MT'),
        ('MY', 'MY'),
        ('NE', 'NE'),
        ('NL', 'NL'),
        ('NO', 'NO'),
        ('NY', 'NY'),
        ('PA', 'PA'),
        ('PL', 'PL'),
        ('PS', 'PS'),
        ('PT', 'PT'),
        ('RO', 'RO'),
        ('RU', 'RU'),
        ('SD', 'SD'),
        ('SI', 'SI'),
        ('SK', 'SK'),
        ('SL', 'SL'),
        ('SM', 'SM'),
        ('SN', 'SN'),
        ('SO', 'SO'),
        ('SQ', 'SQ'),
        ('SR', 'SR'),
        ('ST', 'ST'),
        ('SU', 'SU'),
        ('SV', 'SV'),
        ('SW', 'SW'),
        ('TA', 'TA'),
        ('TE', 'TE'),
        ('TG', 'TG'),
        ('TH', 'TH'),
        ('TL', 'TL'),
        ('TR', 'TR'),
        ('UK', 'UK'),
        ('UR', 'UR'),
        ('UZ', 'UZ'),
        ('VI', 'VI'),
        ('XH', 'XH'),
        ('YI', 'YI'),
        ('YO', 'YO'),
        ('ZH-CN', 'ZH-CN'),
        ('ZH-TW', 'ZH-TW'),
        ('ZU', 'ZU'),
    ]
    return res


class SettingE(metaclass=EnumMetaclass):
    IOS_MIN_MODEL_VERSION = 10
    IOS_MIN_APP_VERSION = 15
    IOS_NEWEST_APP_VERSION = 20
    ANDROID_MIN_MODEL_VERSION = 30
    ANDROID_MIN_BUILD_VERSION = 40


class SettingTypeE(metaclass=EnumMetaclass):
    INTEGER = 10
    FLOAT = 20
    TEXT = 30


class ValidationErrorE(metaclass=EnumMetaclass):
    NULL = 1
    BLANK = 2
    INVALID = 3
    INVALID_CHOICE = 4
    UNIQUE = 5
    UNIQUE_FOR_DATE = 6
    REQUIRED = 7
    MAX_LENGTH = 8
    MIN_LENGTH = 9
    MAX_VALUE = 10
    MIN_VALUE = 11
    MAX_DIGITS = 12
    MAX_DECIMAL_PLACES = 13
    MAX_WHOLE_DIGITS = 14
    MISSING = 15
    EMPTY = 16
    INVALID_LIST = 17
    INCOMPLETE = 18
    INVALID_DATE = 19
    INVALID_TIME = 20
    LIST = 21
    INVALID_PK_VALUE = 22
    INVALID_USERNAME = 1099


def get_setting_field_per_type(s_type):
    defs = {
        SettingTypeE.INTEGER: 'int_value',
        SettingTypeE.FLOAT: 'float_value',
        SettingTypeE.TEXT: 'text_value',
    }
    return defs[s_type] if s_type in defs else None


def get_setting_type_by_key(key):
    defs = {
        SettingE.IOS_MIN_APP_VERSION: SettingTypeE.TEXT,
        SettingE.IOS_MIN_MODEL_VERSION: SettingTypeE.INTEGER,
        SettingE.IOS_NEWEST_APP_VERSION: SettingTypeE.TEXT,
        SettingE.ANDROID_MIN_MODEL_VERSION: SettingTypeE.INTEGER,
        SettingE.ANDROID_MIN_BUILD_VERSION: SettingTypeE.TEXT,
    }
    return defs[key] if key in defs else None


def enum_name_by_value(enum_class, value, fallback=None):
    if isinstance(value, str) and value.isnumeric():
        value = int(value)
    return enum_class.names[value] if value in enum_class.names else fallback


def enum_name_by_value_pretty(
    enum_class, value, fallback=None, pretty_format=' - '
):
    if isinstance(value, str) and value.isnumeric():
        value = int(value)
    name = re.sub(
        '[_]',
        pretty_format,
        enum_class.names[value]
    ) if value in enum_class.names else fallback
    return name


user_admin_types = [UserTypeE.ADMINISTRATOR, UserTypeE.EDITOR]

MOBILE_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

PLACE_IMAGES_LIMIT = 6
PLACE_GEO_CACHE_KEY = "placegeo{}"

LANGUAGES = {
    'en': 'English',
    'fr': 'Français',
    'ja': '日本語',
    'it': 'Italiano',
    'es': 'Castellano'
}
