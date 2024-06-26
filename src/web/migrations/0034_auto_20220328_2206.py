# Generated by Django 2.2.16 on 2022-03-28 22:06

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0033_userprofile_formitable_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='place',
            name='media_post_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='place',
            name='media_post_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='place',
            name='missing_info',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='place',
            name='sticker_sent_dates',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.DateField(), blank=True, null=True, size=None),
        ),
        migrations.AddField(
            model_name='place',
            name='type_sub',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='origin',
            field=models.IntegerField(choices=[(10, 'MOBILE_APP'), (20, 'PRO_WEBSITE'), (30, 'CHARGEBEE'), (40, 'CMS')], null=True),
        ),
    ]
