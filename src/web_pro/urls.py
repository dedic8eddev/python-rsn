from django.urls import include, re_path
from django.views.generic.base import RedirectView

from my_chargebee.views import get_invoice_pdf_url

from rest_framework import routers

from web.views.ajax.v2.places import (OwnerCommentViewset, PlaceCommentViewSet,
                                      PlaceLikeViewSet, PlaceReviewViewSet)
from web.views.ajax.v2.wineposts import FoodPostViewSet, WinePostViewSet, \
    PostedWineView
from web_pro.views.ajax.ajax_data import (get_establishment_data,
                                          get_establishment_images,
                                          get_opening_hours_and_holidays)
from web_pro.views.ajax.ajax_lists import get_invoices, get_typeahead_data
from web_pro.views.tabs.dashboard_views import dashboard
from web_pro.views.tabs.food_views import food, post_food
from web_pro.views.tabs.place_views import (establishment, image_upload,
                                            post_establishment_delete_img,
                                            post_establishment_info,
                                            post_establishment_presentation,
                                            post_establishment_remove_logo,
                                            post_establishment_update_logo,
                                            post_opening_hours)
from web_pro.views.tabs.reviews_likes_views import (get_total_unread,
                                                    read_all_for_user,
                                                    reviews_likes)
from web_pro.views.tabs.settings_views import (pro_settings,
                                               pro_settings_password,
                                               update_company_details,
                                               update_owner_details)
from web_pro.views.tabs.wine_views import (get_wine_post, post_wine, wines,
                                           wines_by_users)
from web_pro.views.user_views import (pro_reset_password_confirm,
                                      pro_set_password)
from web_pro.views.views import (pro_login, pro_logout,
                                 pro_reset_password_login_screen)
from web_pro.views.tabs.feedback_canny_views import (
    get_feedback_canny)

router = routers.DefaultRouter()
router.register(r'wineposts', WinePostViewSet)
router.register(r'foodposts', FoodPostViewSet)
router.register(r'place-likes', PlaceLikeViewSet)
router.register(r'place-reviews', PlaceReviewViewSet)
router.register(r'place-comments', PlaceCommentViewSet)
router.register(r'owner-comments', OwnerCommentViewset)


urlpatterns = [
    # temporary path
    re_path(r'^$', pro_login, name='pro_login'),
    re_path(r'^login$', RedirectView.as_view(
        pattern_name='pro_login', permanent=False
    )),
    re_path(r'^dashboard/(?P<pid>\d+)$', dashboard, name='pro_dashboard'),
    re_path(r'^dashboard$', dashboard, name='pro_dashboard'),
    re_path(r'^logout$', pro_logout, name='pro_logout'),
    re_path(
        r'^forgot_password$',
        pro_reset_password_login_screen,
        name='pro_reset_password_login_screen'
    ),
    re_path(
        r'^password_reset/confirm/(?P<uid>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})/$',  # noqa
        pro_reset_password_confirm,
        name='pro_reset_password_confirm'
    ),
    re_path(
        r'^set-password-form/(?P<uid>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{'r'1,13}-[0-9A-Za-z]{1,32})/$',  # noqa
        pro_set_password, name='pro_set_password'
    ),

    re_path(r'^wines/(?P<pid>\d+)$', wines, name='pro_wines'),
    re_path(r'^wines$', wines, name='pro_wines'),
    re_path(r'^wines/post$', post_wine, name='pro_post_wine'),
    re_path(
        r'^winepost/(?P<post_id>\d+)/$',
        get_wine_post,
        name='pro_get_winepost'
    ),
    re_path(r'^ajax/v2/is-it-an-already-posted-wine$',
            PostedWineView.as_view(),
            name='is_it_an_already_posted_wine'
            ),

    re_path(
        r'^wines_by_users/(?P<pid>\d+)$',
        wines_by_users,
        name='pro_wines_by_users'
    ),

    re_path(r'^food/(?P<pid>\d+)$', food, name='pro_food'),
    re_path(r'^food$', food, name='pro_food'),
    re_path(r'^food/post$', post_food, name='pro_post_food'),

    re_path(
        r'^reviews/(?P<pid>\d+)$',
        reviews_likes,
        name='pro_reviews_and_likes'
    ),
    re_path(r'^reviews$', reviews_likes, name='pro_reviews_and_likes'),
    re_path(
        r'^reviews/(?P<pid>\d+)/read-all-for-user/(?P<uid>[0-9A-Za-z_\-]+)/$',  # noqa
        read_all_for_user,
        name='pro_read_all_for_user'
    ),
    re_path(
        r'^reviews/(?P<pid>\d+)/get-total-unread/$',
        get_total_unread,
        name='pro_get_total_unread'
    ),

    re_path(
        r'^establishment/(?P<pid>\d+)$',
        establishment,
        name='pro_establishment'
    ),
    re_path(
        r'^establishment$',
        establishment,
        name='pro_establishment'
    ),
    re_path(
        r'^establishment/hours$',
        post_opening_hours,
        name='pro_establishment_hours'
    ),
    re_path(
        r'^establishment/info$',
        post_establishment_info,
        name='pro_establishment_info'
    ),
    re_path(
        r'^establishment/presentation/(?P<pid>\d+)$',
        post_establishment_presentation,
        name='pro_establishment_presentation'
    ),
    re_path(
        r'^establishment/remove-logo/(?P<pid>\d+)$',
        post_establishment_remove_logo,
        name='pro_establishment_remove_logo'
    ),
    re_path(
        r'^establishment/update-logo/(?P<pid>\d+)$',
        post_establishment_update_logo,
        name='pro_establishment_update_logo'
    ),
    re_path(
        r'^establishment/delete-img/(?P<pid>\d+)$',
        post_establishment_delete_img,
        name='pro_establishment_delete_img'
    ),
    re_path(
        r'^establishment/image$',
        image_upload,
        name='pro_establishment_image'
    ),
    re_path(
        r'^establishment/get_images/$',
        get_establishment_images,
        name='pro_establishment_get_images'
    ),
    re_path(r'^settings/(?P<pid>\d+)$', pro_settings, name='pro_settings'),
    re_path(r'^settings$', pro_settings, name='pro_settings'),
    re_path(
        r'^settings/owner-details$',
        update_owner_details,
        name='pro_settings_owner_details'
    ),
    re_path(
        r'^settings-password/(?P<pid>\d+)$',
        pro_settings_password,
        name='pro_settings_password'
    ),
    re_path(
        r'^settings/company-details$',
        update_company_details,
        name='pro_settings_company_details'
    ),
    re_path(
        r'^feedback/(?P<pid>\d+)$',
        get_feedback_canny,
        name='pro_canny_feedback'
    ),

    # AJAX
    re_path(
        r'^ajax/typeahead/(?P<option>\w{0,50})/$',
        get_typeahead_data,
        name='pro_typeahead'
    ),
    re_path(
        r'^ajax/establishment/opening-hours/$',
        get_opening_hours_and_holidays,
        name='pro_opening_hours'
    ),
    re_path(
        r'^ajax/establishment/data/$',
        get_establishment_data,
        name='pro_establishment_data'
    ),
    re_path(
        r'^ajax/settings/invoices/$',
        get_invoices,
        name='pro_invoices'
    ),
    re_path(
        r'^ajax/settings/invoice/pdf/$',
        get_invoice_pdf_url,
        name='pro_invoice_pdf_url'
    ),
    re_path(r'^ajax/v2/', include(router.urls)),
]
