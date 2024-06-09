from django.urls import re_path, path
from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

from web.views import views
from web.views.admin import (donation_views, event_views,
                             free_glass_event_views, gen_post_views, ocr_views,
                             place_views, user_views, version_views,
                             winemaker_views, winepost_views)
from web.views.api.v2.formitable import (AppInstallView, AppUnInstallView)


urlpatterns = [
    re_path(r'^$', place_views.places, name="list_places"),

    # Authentication #####
    re_path(r'^login$', views.login, name="login"),
    re_path(r'^logout/$', views.logout, name="logout"),
    re_path(
        r'^password_reset/confirm/(?P<uid>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})/$',  # noqa
        user_views.reset_password_confirm,
        name='reset_password_confirm'
    ),
    re_path(
        r'^password_reset$',
        views.reset_pasword_login_screen,
        name='reset_password_login_screen'
    ),

    # Places #####
    re_path(r'^place/add', place_views.add_place, name="add_place"),
    re_path(
        r'^place/edit/(?P<id>[0-9A-Za-z_\-]+)$',
        place_views.edit_place,
        name="edit_place"
    ),
    re_path(r'^places/est-com$', place_views.est_comments, name="list_est_comments"),  # noqa
    re_path(
        r'^places/est-com/view/(?P<id>[0-9A-Za-z_\-]+)$',
        place_views.view_comment,
        name="view_comment"
    ),
    re_path(r'^subscribers', place_views.places_subscribers,
      name="list_places_subscribers"),  # noqa, TODO if remove

    # Right panel #####
    re_path(r'^right-panel/place/edit/(?P<pk>[0-9]+)/$',
            place_views.PlaceDetail.as_view(),
            name="right-panel_place_detail"),
    re_path(r'^right-panel/place/subscription/(?P<pk>[0-9]+)$',
            place_views.PlaceSubscriptionDetail.as_view(),
            name="right-panel_subscription_detail"),
    re_path(r'^right-panel/place/owner/edit/(?P<pk>[0-9]+)$',
            place_views.PlaceOwnerDetail.as_view(),
            name="right-panel_owner_detail"),
    re_path(r'^right-panel/user-by-email',
            user_views.UserByEmailList.as_view(),
            name="right-panel_user_by_email_detail"),
    re_path(r'^right-panel/check-subscription',
            place_views.CheckSubscription.as_view(),
            name="right-panel_check_subscription"),

    # Wineposts #####
    re_path(r'^wineposts$', winepost_views.wineposts, name="list_wineposts"),
    re_path(
        r'^winepost/edit/(?P<id>[0-9A-Za-z_\-]+)$',
        winepost_views.edit_winepost,
        name="edit_winepost"
    ),
    re_path(
        r'^winepost/referees/(?P<id>[0-9A-Za-z_\-]+)/$',
        winepost_views.winepost_referees, name="list_winepost_referees"
    ),
    re_path(r'^all-referees/$', winepost_views.all_referees, name="list_referees_all"),  # noqa
    re_path(
        r'^winepost/star-reviews/(?P<id>[0-9A-Za-z_\-]+)/$',
        winepost_views.winepost_star_reviews,
        name="list_winepost_star_reviews"
    ),
    re_path(
        r'^all-star-reviews/$',
        winepost_views.all_star_reviews,
        name="list_star_reviews_all"
    ),
    re_path(
        r'^winemaker/referees/(?P<id>[0-9A-Za-z_\-]+)/$',
        winepost_views.winemaker_referees,
        name="winemaker_referees"
    ),
    re_path(
        r'^winemaker/star-reviews/(?P<id>[0-9A-Za-z_\-]+)/$',
        winepost_views.winemaker_star_reviews,
        name="winemaker_star_reviews"
    ),

    # Winemaker #####
    re_path(r'^winemakers$', winemaker_views.winemakers, name="list_wm_all"),
    # re_path(r'^naturals$', winemaker_views.naturals, name="list_wm_naturals"),
    # re_path(r'^others$', winemaker_views.others, name="list_wm_others"),
    re_path(
        r'^winemaker/add',
        winemaker_views.add_winemaker,
        name="add_winemaker"
    ),
    # re_path(
    #     r'^winemaker/add/natural',
    #     winemaker_views.add_winemaker_natural,
    #     name="add_winemaker_natural"
    # ),
    # re_path(
    #     r'^winemaker/add/other',
    #     winemaker_views.add_winemaker_other,
    #     name="add_winemaker_other"
    # ),
    re_path(
        r'^winemaker/edit/(?P<id>[0-9A-Za-z_\-]+)$',
        winemaker_views.edit_winemaker,
        name="edit_winemaker"
    ),

    # General posts #####


    re_path(r'^food$', gen_post_views.food, name="list_food"),
    re_path(r'^posts$', gen_post_views.generalposts, name="list_generalposts"),
    re_path(r'^food/add/$', gen_post_views.add_food, name="add_food"),
    re_path(r'^post/add', gen_post_views.add_generalpost, name="add_generalpost"),
    re_path(
        r'^food/edit/(?P<id>[0-9A-Za-z_\-]+)$',
        gen_post_views.edit_food,
        name="edit_food"
    ),
    re_path(
        r'^post/edit/(?P<id>[0-9A-Za-z_\-]+)$',
        gen_post_views.edit_generalpost,
        name="edit_generalpost"
    ),

    # Events #####
    re_path(r'^events', event_views.events, name="list_events"),
    re_path(r'^event/add/$', event_views.add_event, name="add_event"),
    re_path(
        r'^event/edit/(?P<id>[0-9A-Za-z_\-]+)$',
        event_views.edit_event,
        name="edit_event"
    ),
    re_path(
        r'^places/est-free-glass$',
        free_glass_event_views.est_free_glass,
        name="list_est_free_glass"
    ),
    re_path(
        r'^free-glass-events/edit$',
        free_glass_event_views.edit_free_glass_event,
        name="edit_free_glass_event"
    ),

    # Users #####
    re_path(r'^users$', user_views.users, name="list_users"),
    re_path(r'^user/add', user_views.add_user, name="add_user"),
    re_path(
        r'^user/edit/(?P<id>[0-9A-Za-z_\-]+)/$',
        user_views.edit_user,
        name="edit_user"
    ),

    # OCR #####
    re_path(r'^ocr$', ocr_views.ocrpoc, name="ocrpoc"),
    # ------------------------- AJAX OCR --------------------------------------
    re_path(r'^ajax/ocr-recognize-task-create/$',
            ocr_views.ocr_recognize_task_create,
            name="ocrrecognizetaskcreate"),
    re_path(r'^ajax/ocr-recognize-task-status/$',
            ocr_views.ocr_recognize_task_status,
            name="ocrrecognizetaskstat"),
    re_path(r'^ajax/ocr-calc-task-create/$',
            ocr_views.ocr_calc_task_create,
            name="ocrcalctaskcreate"),
    re_path(r'^ajax/ocr-calc-task-status/$',
            ocr_views.ocr_calc_task_status,
            name="ocrcalctaskstat"),
    re_path(r'^ajax/ocr-recognize-task-result/$',
            ocr_views.ocr_recognize_task_result,
            name="ocrrecognizeresult"),
    re_path(r'^ajax/ocr-calc-task-result/$', ocr_views.ocr_calc_result,
            name="ocrcalcresult"),
    re_path(r'^ajax/ocr-recalc$', ocr_views.ocr_recalc, name="ocr_recalc"),
    re_path(r'^ajax/ocr/recalc$', ocr_views.ocrrecalc, name="ocrrecalc"),
    re_path(r'^ajax/ocred-text$', ocr_views.ocred_text, name="ocredtext"),
    re_path(r'^ajax/ocr-save$', ocr_views.ocr_save_edited_wl, name="ocrsave"),
    # ------------------------- AJAX NWLA -------------------------------------
    re_path(r'^ajax/nwla/excluded-keywords/(?P<pk>[0-9]*)$',
            ocr_views.ExcludedKeyword.as_view(),
            name="excludedkeyword"),

    # Version settings #####
    re_path(
        r'^version-settings/',
        version_views.edit_version_settings,
        name='edit_version_settings'
    ),

    re_path(r'^donations', donation_views.donations, name='list_donations'),

    re_path(r'^admin/', admin.site.urls),  # TODO: is this used?
    re_path(
        'favicon.ico',
        RedirectView.as_view(
            url=staticfiles_storage.url('assets/img/favicon.ico')
        )
    ),
    path('formitable/app/install', AppInstallView.as_view(),
         name="formitable_install"),
    path('formitable/app/uninstall', AppUnInstallView.as_view(),
         name='formitable_uninstall'),
]
