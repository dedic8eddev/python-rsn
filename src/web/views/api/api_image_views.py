from __future__ import absolute_import

import logging

from django.utils.translation import ugettext_lazy as _

from web.constants import PostTypeE
from web.forms.api_forms import ImagesListForm
from web.models import Place, Post, UserProfile, Wine, Winemaker
from web.serializers.comments_likes import ImageSerializer
from web.serializers.places import FullPlaceSerializer
from web.serializers.posts import FullPostSerializer, FullWineSerializer
from web.serializers.users import UserSerializer
from web.serializers.winemakers import LongWinemakerSerializerLegacy
from web.utils.api_handling import signed_api
from web.utils.exceptions import ResultEmpty, WrongParametersError
from web.utils.views_common import prevent_using_non_active_account

log = logging.getLogger(__name__)


# /api/images/listforitem
@signed_api(FormClass=ImagesListForm, token_check=True)
def get_images_for_item(request):
    user = request.user

    prevent_using_non_active_account(user)

    parent_item = None
    parent_item_dict = None

    # try:
    if request.method == 'POST':
        form = request.form

        if form.is_valid():
            cd = form.cleaned_data

            if cd['post_id']:
                parent_item = Post.active.get(id=cd['post_id'])
                parent_item_dict = FullPostSerializer(
                    parent_item,
                    context={
                        'request': request,
                        'include_wine_data': True,
                        'include_winemaker_data': True
                    }
                ).data
            elif cd['place_id']:
                parent_item = Place.active.get(id=cd['place_id'])
                parent_item_dict = FullPlaceSerializer(
                    parent_item, context={'request': request}
                ).data
            elif cd['wine_id']:
                parent_item = Wine.active.get(id=cd['wine_id'])
                parent_item_dict = FullWineSerializer(
                    parent_item, context={
                        'request': request, 'include_winemaker_data': True
                    }
                ).data
            elif cd['winemaker_id']:
                parent_item = Winemaker.active.get(id=cd['winemaker_id'])
                parent_item_dict = LongWinemakerSerializerLegacy(
                    parent_item
                ).data
            elif cd['user_id']:
                parent_item = UserProfile.active.get(id=cd['user_id'])
                parent_item_dict = UserSerializer(parent_item).data
            else:
                raise WrongParametersError(_("Wrong parameters."), form)

            ordering = 'id' if 'user_id' in cd else 'ordering'
            images = parent_item.images.order_by(ordering)

            if cd['post_id']:
                if parent_item.type == PostTypeE.WINE and parent_item.wine:
                    wine_images = parent_item.wine.images.filter(
                        is_archived=False
                    ).order_by("ordering")

                    if wine_images and images:
                        images = [im for im in images] + [im for im in wine_images]  # noqa
                    elif wine_images:
                        images = wine_images

            if not images:
                raise ResultEmpty

            return {
                'images': ImageSerializer(images, many=True).data,
                'parent_item': parent_item_dict,
            }
        else:
            raise WrongParametersError(_("Wrong parameters."), form)
