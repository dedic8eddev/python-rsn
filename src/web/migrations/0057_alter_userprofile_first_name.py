# Generated by Django 3.2.13 on 2022-07-20 07:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0056_auto_20220715_0630'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='first_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='first name'),
        ),
    ]
