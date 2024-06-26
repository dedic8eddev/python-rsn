# flake8: noqa
# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-11-03 20:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0021_auto_20201022_0834'),
    ]

    operations = [
        migrations.RenameField(
            model_name='wine',
            old_name='total_comment_number',
            new_name='comment_number',
        ),
        migrations.RenameField(
            model_name='wine',
            old_name='total_drank_it_too_number',
            new_name='drank_it_too_number',
        ),
        migrations.RenameField(
            model_name='wine',
            old_name='total_likevote_number',
            new_name='likevote_number',
        ),
        migrations.RenameField(
            model_name='winemaker',
            old_name='total_comment_number',
            new_name='comment_number',
        ),
        migrations.RenameField(
            model_name='winemaker',
            old_name='total_drank_it_too_number',
            new_name='drank_it_too_number',
        ),
        migrations.RenameField(
            model_name='winemaker',
            old_name='total_likevote_number',
            new_name='likevote_number',
        ),
        migrations.AddField(
            model_name='calevent',
            name='comment_number',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='calevent',
            name='likevote_number',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='drankittoo',
            name='wine',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='drank_it_toos', to='web.Wine'),
        ),
        migrations.AlterField(
            model_name='post',
            name='wine',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='web.Wine'),
        ),
    ]
