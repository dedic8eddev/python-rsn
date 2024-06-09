# Generated by Django 2.2.28 on 2022-05-02 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cities', '0017_auto_20220502_0252'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='cities/authors/'),
        ),
        migrations.AlterField(
            model_name='city',
            name='alt_names',
            field=models.ManyToManyField(blank=True, to='cities.AlternativeName'),
        ),
        migrations.AlterField(
            model_name='city',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='cities/'),
        ),
        migrations.AlterField(
            model_name='continent',
            name='alt_names',
            field=models.ManyToManyField(blank=True, to='cities.AlternativeName'),
        ),
        migrations.AlterField(
            model_name='continent',
            name='code',
            field=models.CharField(blank=True, db_index=True, max_length=2, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='continent',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='cities/'),
        ),
        migrations.AlterField(
            model_name='country',
            name='alt_names',
            field=models.ManyToManyField(blank=True, to='cities.AlternativeName'),
        ),
        migrations.AlterField(
            model_name='country',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='cities/'),
        ),
        migrations.AlterField(
            model_name='district',
            name='alt_names',
            field=models.ManyToManyField(blank=True, to='cities.AlternativeName'),
        ),
        migrations.AlterField(
            model_name='district',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='cities/'),
        ),
        migrations.AlterField(
            model_name='postalcode',
            name='alt_names',
            field=models.ManyToManyField(blank=True, to='cities.AlternativeName'),
        ),
        migrations.AlterField(
            model_name='postalcode',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='cities/'),
        ),
        migrations.AlterField(
            model_name='region',
            name='alt_names',
            field=models.ManyToManyField(blank=True, to='cities.AlternativeName'),
        ),
        migrations.AlterField(
            model_name='region',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='cities/'),
        ),
        migrations.AlterField(
            model_name='subregion',
            name='alt_names',
            field=models.ManyToManyField(blank=True, to='cities.AlternativeName'),
        ),
        migrations.AlterField(
            model_name='subregion',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='cities/'),
        ),
        migrations.AlterField(
            model_name='urbanarea',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='cities/'),
        ),
    ]
