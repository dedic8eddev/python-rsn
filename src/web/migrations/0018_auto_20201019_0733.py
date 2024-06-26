# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-10-19 07:33
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0017_auto_20201013_0834'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments_authored', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='drankittoo',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='drank_it_toos_authored', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='drankittoo',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='drank_it_toos', to='web.Post'),
        ),
        migrations.AlterField(
            model_name='likevote',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='like_votes_authored', to=settings.AUTH_USER_MODEL),
        ),
    ]
