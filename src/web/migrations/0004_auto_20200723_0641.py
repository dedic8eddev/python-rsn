# flake8: noqa
# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-07-23 06:41
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0003_auto_20200707_0612'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentReadReceipt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_time', models.DateTimeField(default=datetime.datetime.now)),
                ('modified_time', models.DateTimeField(default=datetime.datetime.now)),
                ('comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='read_receipts', to='web.Comment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='read_receipts', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='commentreadreceipt',
            unique_together=set([('comment', 'user')]),
        ),
        migrations.AddField(
            model_name='comment',
            name='in_reply_to',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='comments_where_replied_to', to=settings.AUTH_USER_MODEL),
        ),
    ]
