# Generated by Django 3.2.13 on 2022-07-22 06:47

from django.conf import settings
from django.db import migrations, models
from web.utils.default_data import get_erased_user_uid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('news', '0005_auto_20220721_0941'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='news',
            name='external_modified_time',
        ),
        migrations.AlterField(
            model_name='featuredvenue',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET(get_erased_user_uid()), related_name='featured_venue_author', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='news',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET(get_erased_user_uid()), related_name='news_author', to=settings.AUTH_USER_MODEL),
        ),
    ]
