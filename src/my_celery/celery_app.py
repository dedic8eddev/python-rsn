from __future__ import absolute_import, unicode_literals

import os

import django
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'raisin.settings')
django.setup()

app = Celery('raisin')
app.config_from_object('django.conf:settings', namespace='CELERY')


# Load task modules from all registered Django apps.
app.autodiscover_tasks()
