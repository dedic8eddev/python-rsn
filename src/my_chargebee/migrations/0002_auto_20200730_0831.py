# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-07-30 08:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('my_chargebee', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='vat_number',
            field=models.CharField(max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='status',
            field=models.CharField(choices=[('future', 'future'), ('in_trial', 'in_trial'), ('active', 'active'), ('non_renewing', 'non_renewing'), ('paused', 'paused'), ('cancelled', 'cancelled')], max_length=20),
        ),
    ]
