# Generated by Django 2.0 on 2022-01-11 05:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0031_auto_20211116_0824'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cmsadmincomment',
            options={'ordering': ('-created',)},
        ),
    ]
