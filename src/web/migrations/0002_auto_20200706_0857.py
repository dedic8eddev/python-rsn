# flake8: noqa
# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-07-06 08:57
from __future__ import unicode_literals

import datetime
from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion
import web.models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApiUserStorage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.TextField(unique=True)),
                ('created_time', models.DateTimeField(default=datetime.datetime.now)),
                ('modified_time', models.DateTimeField(default=datetime.datetime.now, null=True)),
                ('stored_data', django.db.models.JSONField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='MonthlyStatsSubscriberPlace',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_time', models.DateTimeField(default=datetime.datetime.now)),
                ('modified_time', models.DateTimeField(default=datetime.datetime.now)),
                ('year', models.IntegerField()),
                ('month', models.IntegerField()),
                ('daily_stats', django.db.models.JSONField(null=True)),
                ('this_week_stats', django.db.models.JSONField(null=True)),
                ('last_week_stats', django.db.models.JSONField(null=True)),
                ('visits_total', models.IntegerField(default=0)),
                ('imp_total', models.IntegerField(default=0)),
                ('imp_home_venues_nearby', models.IntegerField(default=0)),
                ('imp_home_food', models.IntegerField(default=0)),
                ('imp_home_wines', models.IntegerField(default=0)),
                ('imp_map_thumb', models.IntegerField(default=0)),
                ('imp_venue_images_carousel', models.IntegerField(default=0)),
                ('imp_venue_food', models.IntegerField(default=0)),
                ('imp_venue_wines', models.IntegerField(default=0)),
                ('tap_venue_total', models.IntegerField(default=0)),
                ('tap_venue_website', models.IntegerField(default=0)),
                ('tap_venue_direction', models.IntegerField(default=0)),
                ('tap_venue_phone', models.IntegerField(default=0)),
                ('tap_venue_opening', models.IntegerField(default=0)),
                ('tap_from_total', models.IntegerField(default=0)),
                ('tap_from_venues_nearby', models.IntegerField(default=0)),
                ('tap_from_food', models.IntegerField(default=0)),
                ('tap_from_wines', models.IntegerField(default=0)),
                ('tap_from_map', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='OwnerSubscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_time', models.DateTimeField(default=datetime.datetime.now)),
                ('modified_time', models.DateTimeField(default=datetime.datetime.now, null=True)),
                ('is_archived', models.BooleanField(default=False)),
                ('customer_id', models.TextField()),
                ('first_name', models.TextField()),
                ('last_name', models.TextField()),
                ('company', models.TextField()),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.TextField()),
                ('subscription_id', models.TextField()),
                ('payment_status', models.IntegerField(choices=[(10, 'NO'), (20, 'NON_RENEWING'), (30, 'PAUSED'), (40, 'ACTIVE'), (50, 'IN_TRIAL'), (60, 'CANCELLED')])),
                ('plan', models.IntegerField(choices=[(10, 'STICKER_EUR_EN_25_EUR')])),
                ('plan_amount', models.TextField()),
                ('addons', models.TextField(blank=True, null=True)),
                ('next_billing_on', models.DateTimeField(blank=True, null=True)),
                ('next_billing_amount', models.FloatField(blank=True, null=True)),
                ('monthly_recurring_revenue', models.FloatField(blank=True, null=True)),
                ('monthly_recurring_revenue_currency', models.IntegerField(blank=True, choices=[(10, 'EUR'), (20, 'USD')], null=True)),
                ('payment_method_details', models.TextField(blank=True, choices=[(10, 'CREDIT_CARD')], null=True)),
                ('auto_collection', models.BooleanField(default=False)),
                ('billing_full_name', models.TextField(blank=True, null=True)),
                ('billing_company', models.TextField(blank=True, null=True)),
                ('billing_street_address', models.TextField(blank=True, null=True)),
                ('billing_city', models.TextField(blank=True, null=True)),
                ('billing_region', models.TextField(blank=True, null=True)),
                ('billing_country', models.TextField(blank=True, null=True)),
                ('billing_phone', models.TextField(blank=True, null=True)),
                ('billing_email', models.TextField(blank=True, null=True)),
                ('config_full_name', models.TextField(blank=True, null=True)),
                ('config_locale', models.TextField(blank=True, null=True)),
                ('config_preferred_online_currency', models.IntegerField(blank=True, choices=[(10, 'EUR'), (20, 'USD')], null=True)),
                ('config_billing_info', models.TextField(blank=True, null=True)),
                ('config_payment_method_details', models.TextField(blank=True, choices=[(10, 'CREDIT_CARD')], null=True)),
                ('config_auto_collection', models.BooleanField(default=False)),
            ],
        ),
        migrations.AlterModelManagers(
            name='userprofile',
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
                ('active', web.models.ArchivingUserManager()),
            ],
        ),
        migrations.AddField(
            model_name='place',
            name='closing_dates',
            field=django.db.models.JSONField(null=True),
        ),
        migrations.AddField(
            model_name='place',
            name='impression_number',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='place',
            name='is_30_p_natural_already',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='place',
            name='is_venue',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='place',
            name='opening_hours',
            field=django.db.models.JSONField(null=True),
        ),
        migrations.AddField(
            model_name='place',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='place_owner', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='place',
            name='tz_dst',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='place',
            name='tz_name',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='place',
            name='tz_offset',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='place',
            name='visit_number',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='placeimage',
            name='area_ordering',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='placeimage',
            name='image_area',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='currency',
            field=models.CharField(max_length=5, null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='impression_number',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='post',
            name='price',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='tap_number',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='post',
            name='venue',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='post_venue', to='web.Place'),
        ),
        migrations.AddField(
            model_name='post',
            name='venues',
            field=models.ManyToManyField(related_name='post_venue_m2m', to='web.Place'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='currency',
            field=models.CharField(max_length=5, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='is_owner',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='plan_payment_status',
            field=models.IntegerField(choices=[(10, 'UNPAID'), (20, 'PAID'), (30, 'OVERDUE'), (40, 'SUSPENDED')], null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='purchased_plan_type',
            field=models.IntegerField(choices=[(10, 'FREE'), (20, 'PREMIUM'), (30, 'ANNUAL')], null=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='type',
            field=models.IntegerField(choices=[(10, 'WINE'), (20, 'NOT_WINE'), (30, 'FOOD')]),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='type',
            field=models.IntegerField(choices=[(10, 'USER'), (20, 'EDITOR'), (30, 'ADMINISTRATOR'), (40, 'OWNER')]),
        ),
        migrations.AddField(
            model_name='ownersubscription',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='userprof_owner_subscription', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='monthlystatssubscriberplace',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stats_owner_place_owner', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='monthlystatssubscriberplace',
            name='place',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stats_owner_place_owner', to='web.Place'),
        ),
        migrations.AddField(
            model_name='monthlystatssubscriberplace',
            name='post',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stats_owner_place_owner', to='web.Post'),
        ),
        migrations.AddField(
            model_name='apiuserstorage',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='api_storage_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='monthlystatssubscriberplace',
            unique_together=set([('place', 'year', 'month')]),
        ),
    ]