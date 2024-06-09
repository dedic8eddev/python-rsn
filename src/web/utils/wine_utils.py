from django.conf import settings
from django.templatetags.static import static
from django.utils.translation import ugettext_lazy as _

from web.constants import PostStatusE


def get_winepost_status_data(status):
    """
    Get wineposts status data
    """
    status_images = get_wine_status_images()
    if status in status_images:
        return status_images[status]
    else:
        return None


def get_wine_status_image(status):
    status_images = get_wine_status_images()
    if status in status_images:
        return status_images[status]['badge']
    else:
        return ""


def get_wine_status_images():
    tmpl = 'pro_assets/img/icon-{}.png'

    return {
        PostStatusE.PUBLISHED: {
            'badge': settings.SITE_URL + static(tmpl.format('natural')),
            'description': _('WINE MADE BY A NATURAL WINEMAKER'),
            'status_short': 'natural',
            'style_color': '#AD0D3A'
        },
        PostStatusE.BIO_ORGANIC: {
            'badge': settings.SITE_URL + static(tmpl.format('bio-en')),
            'description': _('THIS IS AN ORGANIC AND/OR BIODYNAMIC WINE'),
            'status_short': 'organic',
            'style_color': "#9b9b9b"
        },
        PostStatusE.REFUSED: {
            'badge': settings.SITE_URL + static(tmpl.format('conventional')),
            'description': _("IT'S A CONVENTIONAL WINE!"),
            'status_short': 'conventional',
            'style_color': "#9b9b9b"
        },
        PostStatusE.DRAFT: {
            'badge': settings.SITE_URL + static(tmpl.format('draft')),
            'description': _("IT'S A CONVENTIONAL WINE!"),
            'status_short': 'draft',
            'style_color': "#9b9b9b"
        },
        PostStatusE.IN_DOUBT: {
            'badge': settings.SITE_URL + static(tmpl.format('doubtful')),
            'description': _('NOT SURE ABOUT THIS WINE...'),
            'status_short': 'doubt',
            'style_color': "#9b9b9b"
        }
    }
