from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^news$', views.news, name="list_news"),
    re_path(r'^news/edit/(?P<id>[0-9A-Za-z_\-]+)/(?P<language>[0-9A-Za-z_\-]+)$', views.edit_news, name="edit_news"),
    re_path(r'^news/add/$', views.add_news, name="add_news"),
    re_path(r'^featured-venues$', views.featured_venue, name="list_featured_venues"),
    re_path(r'^featured-venues/edit/(?P<id>[0-9A-Za-z_\-]+)/(?P<language>[0-9A-Za-z_\-]+)$',
            views.edit_featured_venue, name="edit_featured_venue"
            ),
    re_path(r'^featured-venues/add/$', views.add_featured_venue, name="add_featured_venue"),
    re_path(r'^api/sync-news-from-wordpress/$', views.sync_news_from_wordpress, name="sync_news_from_wordpress"),
    re_path(r'^api/add-predefined-pages/$', views.add_predifined_pages, name="add_predifined_pages"),
    re_path(r'^api/sync-event-from-wordpress/$', views.sync_events_from_wordpress, name="sync_events_from_wordpress"),
    re_path(r'^pages$', views.website_page, name="list_website_pages"),
    re_path(r'^website-pages/edit/(?P<id>[0-9A-Za-z_\-]+)/(?P<language>[0-9A-Za-z_\-]+)$',
            views.edit_website_page, name="edit_website_page"
            ),
    re_path(r'^lpb$', views.lpb, name="list_lpb"),
    re_path(r'^lpb/edit/(?P<id>[0-9A-Za-z_\-]+)/(?P<language>[0-9A-Za-z_\-]+)$', views.edit_lpb, name="edit_lpb"),
    re_path(r'^lpb/add/$', views.add_lpb, name="add_lpb"),
    re_path(r'^quote$', views.quote, name="list_quotes"),
    re_path(r'^quote/edit/(?P<id>[0-9A-Za-z_\-]+)/(?P<language>[0-9A-Za-z_\-]+)$',
            views.edit_quote, name="edit_quote"
            ),
    re_path(r'^quote/add/$', views.add_quote, name="add_quote"),
    re_path(r'^quote/add-featured/(?P<id>[0-9A-Za-z_\-]+)/', views.add_featured_quote, name="add_featured_quote"),
    re_path(r'^quote/remove-featured-quotes/',
            views.remove_featured_quotes, name="remove_featured_quotes"),
    re_path(r'^quote/change-featured-quote-order/',
            views.change_featured_quote_orders, name="change_featured_quote_orders"),
    re_path(r'^api/sync-venues-with-qoutes/$', views.sync_venues_with_qoutes, name="sync_venues_with_qoutes"),
    re_path(r'^cheffe$', views.cheffe, name="list_cheffes"),
    re_path(r'^cheffe/edit/(?P<id>[0-9A-Za-z_\-]+)/(?P<language>[0-9A-Za-z_\-]+)$',
            views.edit_cheffe, name="edit_cheffe"
            ),
    re_path(r'^cheffe/add/$', views.add_cheffe, name="add_cheffe"),
    re_path(r'^cheffe/add-featured/(?P<id>[0-9A-Za-z_\-]+)/', views.add_featured_cheffe,
            name="add_featured_cheffe"),
    re_path(r'^cheffe/remove-featured-cheffes/',
            views.remove_featured_cheffes, name="remove_featured_cheffes"),
    re_path(r'^cheffe/change-featured-cheffe-order/',
            views.change_featured_cheffe_orders, name="change_featured_cheffe_orders"),
    re_path(r'^testimonial$', views.testimonial, name="list_testimonials"),
    re_path(r'^testimonial/edit/(?P<id>[0-9A-Za-z_\-]+)/(?P<language>[0-9A-Za-z_\-]+)$',
            views.edit_testimonial, name="edit_testimonial"
            ),
    re_path(r'^testimonial/add/$', views.add_testimonial, name="add_testimonial"),
    re_path(r'^testimonial/add-featured/(?P<id>[0-9A-Za-z_\-]+)/', views.add_featured_testimonial,
            name="add_featured_testimonial"),
    re_path(r'^testimonial/remove-featured-testimonials/',
            views.remove_featured_testimonials, name="remove_featured_testimonials"),
    re_path(r'^testimonial/change-featured-testimonial-order/',
            views.change_featured_testimonial_orders, name="change_featured_testimonial_orders")
]
