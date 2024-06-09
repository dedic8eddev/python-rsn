# Generated by Django 3.2.13 on 2022-11-18 12:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0062_auto_20220916_0720'),
        ('news', '0011_auto_20221118_1033'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quote',
            name='connected_venue',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='venue_quote', to='web.place'),
        ),
        migrations.AlterField(
            model_name='quote',
            name='default_quote',
            field=models.TextField(blank=True, verbose_name='default quote'),
        ),
    ]
