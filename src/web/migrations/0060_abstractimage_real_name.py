# Generated by Django 3.2.13 on 2022-08-12 10:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0059_merge_20220728_0957'),
    ]

    operations = [
        migrations.AddField(
            model_name='abstractimage',
            name='real_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
