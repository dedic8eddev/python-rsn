from django.utils.translation import ugettext_lazy as _

from web.constants import WinemakerStatusE, SpecialStatusE


class WinemakerHelper:

    # a list of wine post statuses to display on a mobile application
    app_winemaker_display_statuses = [WinemakerStatusE.VALIDATED]

    # the list of winemaker statuses for autocomplete parent post selector
    parent_post_selector_statuses = [
        WinemakerStatusE.VALIDATED,
        WinemakerStatusE.IN_DOUBT,
        WinemakerStatusE.BIO_ORGANIC,
        WinemakerStatusE.REFUSED,
        WinemakerStatusE.TO_INVESTIGATE,
    ]

    @classmethod
    def get_original_name(cls, winemaker):
        """
        Get original winemaker name

        :param winemaker: Winemaker object
        """
        original_name = None

        if winemaker.status in [WinemakerStatusE.DRAFT, WinemakerStatusE.IN_DOUBT]:
            original_name = winemaker.name

        return original_name

    @staticmethod
    def get_pdg_options():
        """
        Get drop down options for winemakers page:
            - naturals
            - others
        """

        options = [
            {
                'value': WinemakerStatusE.DRAFT,
                'name': _("Draft"),
                'class': 'btonhold',
                'selclass': 'onhold'
            },
            {
                'value': WinemakerStatusE.VALIDATED,
                'name': _("Natural"),
                'class': 'btincluded',
                'selclass': 'included'
            },
            {
                'value': WinemakerStatusE.BIO_ORGANIC,
                'name': _("Bio-organic"),
                'class': 'btbioorg',
                'selclass': 'bioorg'
            },
            {
                'value': WinemakerStatusE.TO_INVESTIGATE,
                'name': _("To investigate"),
                'class': 'bt_to_investigate',
                'selclass': 'to_investigate'
            },
            {
                'value': WinemakerStatusE.IN_DOUBT,
                'name': _("In doubt"),
                'class': 'btindoubt',
                'selclass': 'indoubt'
            },
            {
                'value': WinemakerStatusE.REFUSED,
                'name': _("Not natural"),
                'class': 'btrefused',
                'selclass': 'refused'
            },
            {
                'value': SpecialStatusE.DELETE,
                'name': _("Delete"),
                'class': 'btdelete',
                'selclass': 'delete'
            },
            {
                'value': SpecialStatusE.DUPLICATE,
                'name': _("Duplicate"),
                'class': 'btduplicate',
                'selclass': 'duplicate'
            },
        ]

        return options
