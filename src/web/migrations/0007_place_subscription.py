# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-08-13 12:37
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('my_chargebee', '0003_auto_20200805_0757'),
        ('web', '0006_auto_20200811_1547'),
    ]

    operations = [
        migrations.AddField(
            model_name='place',
            name='subscription',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='my_chargebee.Subscription'),
        ),
    ]
