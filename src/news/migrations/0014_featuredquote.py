# Generated by Django 3.2.13 on 2022-11-21 14:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0062_auto_20220916_0720'),
        ('news', '0013_quote_quote_translations'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeaturedQuote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.PositiveIntegerField(default=1)),
                ('quote', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='web.place')),
            ],
        ),
    ]