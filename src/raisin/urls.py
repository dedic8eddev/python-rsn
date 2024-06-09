"""raisin URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import include, url, re_path
from django.conf.urls.static import static

from my_chargebee.urls import urlpatterns as urls_chargebee
from web.urls import urlpatterns as urls_cms
from news.urls import urlpatterns as urls_news
from news.url_ajax_list import urls_ajax_lists as urls_ajax_lists_news
from web.urls_ajax_lists import urls_ajax_lists
from web.urls_backend_api import urls_backend_api
from web.views import views
from web_pro.urls import urlpatterns as urls_pro

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

handler403 = views.handle_403_not_permitted
handler404 = views.handle_404_not_found
handler500 = views.handle_500

urlpatterns = []
urlpatterns += urls_cms
urlpatterns += urls_news

urlpatterns += url(r'^ajax/', include(urls_ajax_lists)),
urlpatterns += url(r'^ajax/', include(urls_ajax_lists_news)),
urlpatterns += url(r'^api/', include(urls_backend_api)),
urlpatterns += url(r'^pro/', include(urls_pro)),
urlpatterns += urls_chargebee
urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
) + static(
    settings.STATIC_URL,
    document_root=settings.STATIC_ROOT
) + static(
    settings.WK_URL,
    document_root=settings.WK_ROOT
)
urlpatterns_cities = [
    url(r'^cities/', include('cities.urls')),
    url(r'^api/', include('cities.api.urls')),
]
urlpatterns += urlpatterns_cities

urlpatterns_reports = [
    url(r'^reports/', include('reports.urls')),
    url(r'^api/', include('reports.api.urls')),
]
urlpatterns += urlpatterns_reports

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns


schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns += [
   re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
   re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]