from django.conf.urls import url

from my_chargebee import views

urlpatterns = [
    url(r'^webhooks/', views.chargebee_webhook, name='chargebee_webhooks'),
]
