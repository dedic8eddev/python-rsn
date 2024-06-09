from my_chargebee.models import Subscription
from web.constants import PlaceStatusE


class PlaceHelper:

    # a list of place statuses to be displayed on a mobile application
    app_place_display_statuses = [
        PlaceStatusE.PUBLISHED,
        PlaceStatusE.SUBSCRIBER
    ]

    # a list of place subscribing statuses
    place_subscribing_statuses = [
        Subscription.ACTIVE,
        Subscription.IN_TRIAL,
        Subscription.FUTURE,
        Subscription.NON_RENEWING,
        Subscription.PAUSED
    ]
