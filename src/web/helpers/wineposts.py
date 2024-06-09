from django.utils.translation import ugettext_lazy as _
from django.urls import reverse

from web.constants import PostStatusE, SpecialStatusE, WinemakerStatusE


class WinepostHelper:

    # a list of wine post statuses to display on a mobile application
    app_winepost_display_statuses = [
        PostStatusE.IN_DOUBT, PostStatusE.PUBLISHED, PostStatusE.BIO_ORGANIC
    ]

    @classmethod
    def get_winepost_domain(cls, post):
        """
        Get winepost domain

        :param post: Post object
        """
        domain = post.wine.domain
        if post.wine.winemaker.status in [WinemakerStatusE.DRAFT, WinemakerStatusE.IN_DOUBT]:
            if domain == post.wine.winemaker.domain:
                domain = "%s [DRAFT]" % post.wine.winemaker.domain

        return domain

    @classmethod
    def get_active_endpoint_url_name(cls, post, is_natural: bool):
        """
        Get active winepost endpoint url name to handle
            - when post is a parent post
            - otherwise

        :param post: Post object
        :param is_natural: Whether the winepost winemaker is natural
        """
        if post.is_parent_post:
            url_name = "list_wm_all"
        else:
            url_name = 'list_wineposts'

        return url_name

    @classmethod
    def get_add_winemaker_endpoint_url_name(cls, is_natural: bool):
        """
        Get add winemaker endpoint url

        :param is_natural: Whether the winepost winemaker is natural
        """
        # url_name = "add_winemaker_natural" if is_natural else "add_winemaker_other"
        url_name = "add_winemaker"
        return url_name

    @classmethod
    def get_bc_path(cls, post, active_url_name):
        """
        Get path list of mappings

        :param post: Post object
        :param active_url_name: The winepost active endpoint url name
        """
        if post.is_parent_post:
            path = [
                ('/', 'Home'),
                (reverse(active_url_name), 'Winemakers'),
                (reverse('edit_winemaker', args=[post.wine.winemaker_id]), post.wine.winemaker.name),
                (reverse('edit_winepost', args=[post.id]), post.wine.name),
            ]
        else:
            path = [
                ('/', 'Home'),
                (reverse('list_wineposts'), 'Wineposts'),
                (reverse('edit_winepost', args=[post.id]), post.wine.name),
            ]

        return path

    @staticmethod
    def get_pdg_options():
        """
        Get drop down options for wineposts page.
        """
        options = [
            {
                'value': PostStatusE.DRAFT,
                'name': _("Draft"),
                'class': 'btonhold',
                'selclass': 'onhold'
            },
            {
                'value': PostStatusE.PUBLISHED,
                'name': _("Natural"),
                'class': 'btincluded',
                'selclass': 'included'
            },
            {
                'value': PostStatusE.BIO_ORGANIC,
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
                'value': PostStatusE.REFUSED,
                'name': _("Not Natural"),
                'class': 'btrefused',
                'selclass': 'refused'
            },
            {
                'value': PostStatusE.IN_DOUBT,
                'name': _("In doubt"),
                'class': 'btindoubt',
                'selclass': 'indoubt'
            },
            {
                'value': SpecialStatusE.DELETE,
                'name': _("Deleted"),
                'class': 'btdelete',
                'selclass': 'delete'
            },
            {
                'value': SpecialStatusE.DUPLICATE,
                'name': _("Duplicate"),
                'class': 'btduplicate',
                'selclass': 'duplicate'
            },
            {
                'value': SpecialStatusE.NOT_WINE,
                'name': _("Not wine"),
                'class': 'btnotwine',
                'selclass': 'notwine'
            },
        ]

        return options
