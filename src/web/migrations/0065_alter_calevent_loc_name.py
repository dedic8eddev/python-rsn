# Generated by Django 3.2.16 on 2022-11-24 16:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0064_auto_20221124_1422'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calevent',
            name='loc_name',
            field=models.TextField(blank=True, max_length=255, null=True),
        ),
    ]