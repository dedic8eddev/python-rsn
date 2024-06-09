# Generated by Django 3.2.13 on 2022-11-22 05:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0014_featuredquote'),
    ]

    operations = [
        migrations.AlterField(
            model_name='featuredquote',
            name='quote',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quote_fetured', to='news.quote'),
        ),
    ]
