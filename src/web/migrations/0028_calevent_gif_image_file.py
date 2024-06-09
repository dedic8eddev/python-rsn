# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-05-21 21:17
from __future__ import unicode_literals

from django.db import migrations, models
import web.utils.filenames


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0027_auto_20210514_1050'),
    ]

    operations = [
        migrations.AddField(
            model_name='calevent',
            name='gif_image_file',
            field=models.ImageField(blank=True, null=True, upload_to=web.utils.filenames.update_event_gif_filename),
        ),
    ]
