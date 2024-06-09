from django.conf.urls import include, url
from django.urls import path

from rest_framework import routers

from web.views.api import (api_attendee_views, api_autocomplete_views,
                           api_comment_views, api_donation_views,
                           api_drank_it_too_views, api_event_views,
                           api_free_glass_event_views, api_image_views,
                           api_likevote_views, api_place_views, api_post_views,
                           api_search_views, api_timeline_views,
                           api_user_views,
                           api_version_views, api_wine_views,
                           api_winemaker_views, v2, save_image)
from web.views.api.v2.places import PlacesGeoViewSet, GoogleAPIKeyView
from web.views.api.v2.winemakers import WinemakerViewSet
from web.views.api.v2.wineposts import (WinepostList,
                                        WinepostGeolocatedList,
                                        FilteredWinepostGeolocatedList)
from web.views.api.v2.events import EventInfoAPIView, EventFaireAPIView
from web.views.api.v2.users import UserDeleteAPIView, UserBlockApiView, BlockedUserApiListView, BlockUserDeleteApiView,\
    AvailableEmailAPIView, AvailableUsernameAPIView


router = routers.DefaultRouter()

router.register(r'winemakers', WinemakerViewSet)
router.register(r'places', PlacesGeoViewSet)

# find any wineposts for the main search screen
router.register(r'find-wineposts', WinepostList)

# find only geolocated wineposts
router.register(r'find-wineposts/geolocated', WinepostGeolocatedList)

# find geolocated wineposts for the scanned image data
router.register(r'find-wineposts-filtered/geolocated', FilteredWinepostGeolocatedList)

urls_backend_api = [
    # Free glass
    url(
        r'^free-glass-events/get-event-info$',
        api_free_glass_event_views.get_free_glass_event,
        name='get_free_glass_event_api'),
    url(
        r'^free-glass-events/i-got/add',
        api_free_glass_event_views.add_got_free_glass,
        name='add_got_free_glass_api'
    ),
    url(
        r'^free-glass-events/get-my/add',
        api_free_glass_event_views.add_get_my_free_glass,
        name='add_get_my_free_glass_api'
    ),
    url(
        r'^free-glass-events/get-my/check',
        api_free_glass_event_views.get_get_my_free_glass,
        name='get_get_my_free_glass_api'
    ),
    url(
        r'^free-glass-events/i-got/del',
        api_free_glass_event_views.delete_got_free_glass,
        name='delete_got_free_glass_api'
    ),
    url(
        r'^free-glass-events/i-got/list',
        api_free_glass_event_views.get_got_free_glass_list,
        name='got_free_glass_list_api'
    ),
    url(
        r'^free-glass-events/i-got/check',
        api_free_glass_event_views.get_i_got_free_glass,
        name='i_got_free_glass_api'
    ),

    # Donations
    url(
        r'^donations/apple/receipt',
        api_donation_views.donations_apple_receipt,
        name='donations_apple_receipt_api'),

    url(
        r'^donations/checknotify',
        api_donation_views.donations_checknotify,
        name='donations_checknotify_api'),

    url(
        r'^donations/apple/products',
        api_donation_views.get_products_apple,
        name='donations_apple_products_api'),

    url(
        r'^donations/android/products',
        api_donation_views.get_products_android,
        name='donations_android_products_api'),

    url(
        r'^donations/android/receipt',
        api_donation_views.donations_android_receipt,
        name='donations_android_receipt_api'),

    url(
        r'^donations/android/callback',
        api_donation_views.donations_android_callback,
        name='donations_android_callback_api'),

    url(
        r'^donations/android/getpush$',
        api_donation_views.donations_android_get_push,
        name='donations_android_get_push_api'),
    url(
        r'^donations/click$',
        api_donation_views.donations_click,
        name='donations_click_api'),

    # Checks
    url(r'^app/ios/check', api_version_views.AppIOSVersion.as_view(), name='app_ios_check_api'),  # noqa
    url(r'^app/android/check', api_version_views.app_android_check, name='app_android_check_api'),  # noqa
    url(r'^users/push/update$', api_user_views.update_push_data, name='update_push_data_api'),  # noqa
    url(r'^users/lang/update', api_user_views.update_lang_data, name='update_lang_data_api'),  # noqa

    # Users/auth
    url(r'^users/login$', api_user_views.create_refresh_token, name='create_refreshtoken_api'),  # noqa
    url(r'^users/logout$', api_user_views.delete_refresh_token, name='delete_refreshtoken_api'),  # noqa
    url(r'^users/refresh-token$', api_user_views.refresh_refresh_token, name='refresh_refreshtoken_api'),  # noqa
    url(r'^users/register$', api_user_views.create_user_profile, name='create_user_api'),  # noqa
    url(r'^users/resetpass$', api_user_views.reset_password, name='reset_password_api'),  # noqa
    url(
        r'^notifications/list$',
        api_user_views.get_notifications_list,
        name='get_notifications_list_api'
    ),

    url(r'^users/profile/own/update$', api_user_views.update_user_profile_own, name='update_user_api'),  # noqa
    url(r'^users/profile/own/get$', api_user_views.get_user_own, name='get_user_own_api'),  # noqa
    url(r'^users/profile/any/get$', api_user_views.UserProfileAnyView.as_view(), name='get_user_any_api'),  # noqa
    url(r'^users/profile/own/delete$', api_user_views.delete_user_own, name='delete_user_own_api'),  # noqa

    url(r'^users/profile/delete$', UserDeleteAPIView.as_view(), name='delete_user_account_api'),  # noqa

    url(r'^timeline/items$', api_timeline_views.TimelineItemsView.as_view(), name='get_timeline_items_api'),  # noqa
    url(
        r'^timeline/item/newest$',
        api_timeline_views.get_newest_timeline_item,
        name='get_newest_timeline_item_api'
    ),
    path('users/block', UserBlockApiView.as_view(), name='block-user-create'),
    path('users/block/', BlockedUserApiListView.as_view(), name='blocked-users-list'),
    path('users/block/<int:pk>', BlockUserDeleteApiView.as_view(), name='block-user-delete'),
    path('users/available/username/', AvailableUsernameAPIView.as_view(), name='available-username'),
    path('users/available/email/', AvailableEmailAPIView.as_view(), name='available-email'),

    # Wines
    url(r'^wine/items$', api_wine_views.get_wine_items, name='get_wine_items_api'),  # noqa
    url(r'^wine/similiar/items', api_wine_views.get_wine_similiar_items, name='get_wine_similiar_items_api'),  # noqa
    # url(r'^winemaker/items$', api_winemaker_views.get_winemaker_items,
    # name='get_winemaker_items_api'),  # deprecated but still in code
    url(r'^winemaker/items$', v2.winemakers.WinemakersView.as_view(),
        name='get_winemaker_items_api'),  # noqa
    url(r'^wine/profile$', api_wine_views.WineProfileView.as_view(), name='get_wine_profile_api'),  # noqa
    url(
        r'^winemaker/profile$',
        api_winemaker_views.WinemakerProfileView.as_view(),
        name='get_winemaker_profile_api'
    ),
    # Places
    url(r'^places/place$', api_place_views.PlaceGetView.as_view(), name='get_place_api'),  # noqa
    url(r'^places/place/add$', api_place_views.add_place, name='add_place_api'),  # noqa
    url(r'^places/place/edit', api_place_views.edit_place, name='edit_place_api'),  # noqa
    url(r'^places/delete', api_place_views.delete_place, name='delete_place_api'),  # noqa
    url(r'^posts/delete', api_post_views.delete_post, name='delete_post_api'),
    url(r'^places/google_api_key$', GoogleAPIKeyView.as_view(), name='google_api_key'),
    # url(r'^places/geo', api_place_views.get_place_list_geo, name='get_place_list_geo_api'),  # noqa
    # url(
    #     r'^places/open-closed-status',
    #     api_place_views.get_place_list_open_closed_status,
    #     name='get_place_list_open_closed_status_api'
    # ),
    url(r'^places/geo', api_place_views.PlaceListGeoView.as_view(),
        name='get_place_list_geo_api'),
    # noqa
    url(
        r'^places/open-closed-status',
        api_place_views.PlaceListOpenClosedStatusView.as_view(),
        name='get_place_list_open_closed_status_api'
    ),
    url(
        r'^places/wines-foods-closest-venues$',
        api_place_views.WinesFoodsClosestVenuesView.as_view(),
        name='get_wines_foods_closest_venues_api'
    ),
    url(
        r'^places/place/all-wines$',
        api_place_views.WinesForPlaceView.as_view(),
        name='get_all_wines_for_place_api'
    ),
    url(
        r'^places/place/all-foods$',
        api_place_views.FoodsForPlaceView.as_view(),
        name='get_all_foods_for_place_api'
    ),
    url(
        r'^places/place/is-it-an-already-posted-wine',
        api_place_views.PostedWineView.as_view(),
        name='is_it_an_already_posted_wine_api'
    ),

    # Posts
    url(r'^posts/wine/add$', api_post_views.add_winepost, name='add_winepost_api'),  # noqa
    url(r'^posts/wine/addnew$', api_post_views.add_winepost_new, name='add_winepost_new_api'),  # noqa
    url(r'^posts/wine/edit', api_post_views.edit_winepost, name='edit_winepost_api'),  # noqa
    url(r'^posts/general/edit', api_post_views.edit_general_post, name='edit_general_post_api'),  # noqa

    url(r'^posts/list$', api_post_views.get_post_list, name='get_post_list_api'),  # noqa
    url(r'^posts/post$', api_post_views.PostView.as_view(), name='get_post_api'),  # noqa
    url(r'^posts/general/add$', api_post_views.add_general_post, name='add_general_post_api'),  # noqa

    url(
        r'^posts/count-vuforia-scans',
        api_post_views.VuforiaScansCountView.as_view(),
        name='count_vuforia_scans_api'
    ),

    # Events
    url(r'^events/timeline$', api_event_views.EventTimelineView.as_view(), name='get_events_timeline_api'),  # noqa
    url(r'^events/carousel$', api_event_views.EventCarouselView.as_view(), name='get_events_carousel_api'),  # noqa
    url(r'^events/details$', api_event_views.EventDetailView.as_view(), name='get_event_details_api'),  # noqa

    url(r'^events/attendees/add', api_attendee_views.add_attendee, name='events_add_attendee_api'),  # noqa
    url(r'^events/attendees/delete', api_attendee_views.delete_attendee, name='events_delete_attendee_api'),  # noqa
    url(r'^events/attendees$', api_attendee_views.get_attendees_list, name='events_get_attendees_list_api'),  # noqa

    url(r'^events/map', api_event_views.EventsMapView.as_view(), name='events_get_events_map_api'),  # noqa

    url(r'^event/create/info', EventInfoAPIView.as_view(), name='event_create_info'),  # noqa

    url(r'^events/faire', EventFaireAPIView.as_view(), name='events_faire'),  # noqa

    # Comments and likes
    url(r'^comments/list$', api_comment_views.CommentListView.as_view(), name='get_comments_list_api'),  # noqa
    url(r'^comments/add$', api_comment_views.add_comment, name='add_comment_api'),  # noqa
    url(r'^comments/update$', api_comment_views.update_comment, name='update_comment_api'),  # noqa
    url(r'^comments/delete$', api_comment_views.delete_comment, name='delete_comment_api'),  # noqa
    path("comments/<int:pk>", api_comment_views.CommentDeleteApiView.as_view(), name="comment-delete-api-new"),

    url(r'^likes/list$', api_likevote_views.LikeVoteListView.as_view(), name='get_likevotes_list_api'),  # noqa
    url(r'^likes/get-i-like$', api_likevote_views.get_i_like, name='get_i_like_api'),  # noqa
    url(r'^likes/add$', api_likevote_views.add_likevote, name='add_likevote_api'),  # noqa
    url(r'^likes/delete$', api_likevote_views.delete_likevote, name='delete_likevote_api'),  # noqa

    url(r'^drankittoos/add$', api_drank_it_too_views.add_drank_it_too, name='add_drank_it_too_api'),  # noqa
    url(r'^drankittoos/delete$', api_drank_it_too_views.delete_drank_it_too, name='delete_drank_it_too_api'),  # noqa
    url(r'^drankittoos/list$', api_drank_it_too_views.get_drank_it_toos_list, name='get_drank_it_toos_list_api'),  # noqa
    # noqa

    url(
        r'^images/listforitem$',
        api_image_views.get_images_for_item,
        name='get_images_for_item_api'
    ),
    url(
        r'^images/save-image/$',
        save_image.save_image,
        name='save_image'
    ),
    # Autocompletes
    url(
        r'^autocomplete/winemaker',
        api_autocomplete_views.AutocompleteWinemakerAPIListView.as_view(),
        name='autocomplete_winemaker_api'
    ),
    url(
        r'^autocomplete/domain',
        api_autocomplete_views.autocomplete_domain,
        name='autocomplete_domain_api'
    ),
    url(
        r'^autocomplete/wine',
        api_autocomplete_views.AutocompleteWineAPIListView.as_view(),
        name='autocomplete_wine_api'
    ),
    url(
        r'^autocomplete/place',
        api_autocomplete_views.autocomplete_place,
        name='autocomplete_place_api'
    ),
    url(
        r'^autocomplete/user',
        api_autocomplete_views.autocomplete_username,
        name='autocomplete_username_api'
    ),
    url(r'^search/posts$', api_search_views.SearchPostView.as_view(), name='search_posts_api'),  # noqa
    url(r'^search/users$', api_search_views.SearchUserView.as_view(), name='search_users_api'),  # noqa
    url(r'^search/events$', api_event_views.SearchEventView.as_view(), name='events_get_search_events_api'),  # noqa
    url(r'^', include(router.urls))
]
