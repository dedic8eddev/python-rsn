# Generated by Django 3.2.13 on 2022-08-22 09:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0060_abstractimage_real_name'),
        ('news', '0006_auto_20220722_0647'),
    ]

    operations = [
        migrations.AddField(
            model_name='featuredvenue',
            name='connected_venue',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='web.place'),
        ),
    ]