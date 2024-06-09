# Generated by Django 3.2.13 on 2022-07-05 17:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from web.utils.default_data import get_erased_user_uid


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0042_auto_20220701_1020'),
    ]

    operations = [
        migrations.AlterField(
            model_name='abstractimage',
            name='author',
            field=models.ForeignKey(null=True, on_delete=models.SET(get_erased_user_uid()), to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='calevent',
            name='author',
            field=models.ForeignKey(on_delete=models.SET(get_erased_user_uid()), to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='calevent',
            name='last_modifier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cal_event_last_modifier', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='calevent',
            name='validated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_validated_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='cmsadmincomment',
            name='author',
            field=models.ForeignKey(on_delete=models.SET(get_erased_user_uid()), to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(on_delete=models.SET(get_erased_user_uid()), related_name='comments_authored', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='comment',
            name='in_reply_to',
            field=models.ForeignKey(null=True, on_delete=models.SET(get_erased_user_uid()), related_name='comments_where_replied_to', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='drankittoo',
            name='author',
            field=models.ForeignKey(on_delete=models.SET(get_erased_user_uid()), related_name='drank_it_toos_authored', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='like',
            name='author',
            field=models.ForeignKey(on_delete=models.SET(get_erased_user_uid()), to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='likevote',
            name='author',
            field=models.ForeignKey(on_delete=models.SET(get_erased_user_uid()), related_name='like_votes_authored', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='place',
            name='author',
            field=models.ForeignKey(on_delete=models.SET(get_erased_user_uid()), to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='place',
            name='expert',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='place_expert', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='place',
            name='last_modifier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='place_last_modifier', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='place',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='place_owner', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='place',
            name='validated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='place_validated_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='post',
            name='author',
            field=models.ForeignKey(on_delete=models.SET(get_erased_user_uid()), related_name='posts_authored', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='post',
            name='expert',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='post_expert', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='post',
            name='last_modifier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='post_last_modifier', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='timelineitem',
            name='author',
            field=models.ForeignKey(on_delete=models.SET(get_erased_user_uid()), related_name='timeline_item_author', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='timelineitem',
            name='user_item',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='usernotification',
            name='user',
            field=models.ForeignKey(on_delete=models.SET(get_erased_user_uid()), related_name='user_notification_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='image',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='web.userimage'),
        ),
        migrations.AlterField(
            model_name='wine',
            name='author',
            field=models.ForeignKey(on_delete=models.SET(get_erased_user_uid()), to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='wine',
            name='validated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='wine_validated_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='winelistfile',
            name='author',
            field=models.ForeignKey(null=True, on_delete=models.SET(get_erased_user_uid()), to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='winemaker',
            name='author',
            field=models.ForeignKey(on_delete=models.SET(get_erased_user_uid()), to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='winemaker',
            name='last_modifier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='winemaker_last_modifier', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='winemaker',
            name='validated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='wm_validated_by', to=settings.AUTH_USER_MODEL),
        ),
    ]
