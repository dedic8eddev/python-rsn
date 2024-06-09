import datetime as dt
import json
import logging
import uuid

import requests
from django.conf import settings

import web.models
from reports.models import BlockUser
from web.constants import PushNotifyTypeE, UserTypeE, PlaceStatusE
from web.utils.model_tools import beautify_place_name, strip_tags
from web.utils.upload_tools import aws_url

from .model_tools import cut_string

DONATION_NOTIFY_DELAY_MINUTES = 5
push_notify_log = logging.getLogger("pushnotify")


class SenderNotifier:
    # https://documentation.onesignal.com/reference

    NOTIFY_LIKE = 'like'
    NOTIFY_DRANK_IT_TOO = 'drank-it-too'
    NOTIFY_COMMENT = 'comment'
    NOTIFY_WINE_REVIEW = 'wine-review'
    NOTIFY_PLACE = 'place'  # TODO FIXME - not yet implemented in switches
    NOTIFY_MENTIONED_COMMENT = 'comment'
    NOTIFY_MENTIONED_DESC = 'desc'

    def send_msg(self, notifier, user_dest, msg, title, subtitle_by_lang,
                 send_after=None, push_id=None, for_admin_too=False):
        # An anonymous user can not perform actions, which results in
        # notifications
        if not notifier.is_authenticated:
            return False
        # if the notifier was blocked by user_dest, the notification should
        # not be sent.
        elif BlockUser.objects.filter(user=user_dest, block_user=notifier):
            return False

        is_admin_or_editor = user_dest.type in [UserTypeE.ADMINISTRATOR, UserTypeE.EDITOR]
        if is_admin_or_editor and user_dest.username != 'alp' and not push_id and not for_admin_too:
            user_type_name = UserTypeE.names[user_dest.type]
            push_notify_log.debug(f"user {user_dest.username} is an {user_type_name} - skipping notification sending")

            return False

        if push_id:
            push_user_id = push_id
        else:
            if not user_dest.push_user_id or user_dest.push_user_id == "":
                push_user_id = "648c7c2c-ac78-4d4a-aa90-1097809295f3"  # noqa Alek ID  - TODO FIXME, remove this later
            else:
                push_user_id = user_dest.push_user_id

        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': 'Basic ' + settings.PUSH_NOTIFY_REST_API_KEY,
        }

        msg['nid'] = str(uuid.uuid4())

        data = {
            'app_id': settings.PUSH_NOTIFY_APP_ID,
            'android_channel_id': settings.ANDROID_CHANNEL_ID,
            'contents': subtitle_by_lang,
            'data': msg,
            'include_player_ids': [push_user_id],
        }

        if send_after:
            data['send_after'] = send_after

        data_str = json.dumps(data)

        resp = requests.post(
            settings.PUSH_NOTIFY_API_URL, headers=headers, data=data_str
        )

        status_code = resp.status_code

        if status_code == 200:
            return True
        else:
            error_response_message = json.loads(resp.content)
            push_notify_log.debug(f"FAILED to send notification due to: {error_response_message}")

            return False

    def user_accepts_notification(self, user, type):
        if type == self.NOTIFY_LIKE:
            return True if user.notify_likes else False
        elif type == self.NOTIFY_DRANK_IT_TOO:
            return True if user.notify_drank_it_toos else False
        elif type == self.NOTIFY_COMMENT:
            return True if user.notify_comments else False
        elif type == self.NOTIFY_WINE_REVIEW:
            return True if user.notify_wine_reviewed else False
        elif type == self.NOTIFY_PLACE:
            return True  # noqa TODO FIXME - not yet implemented in switches, always returns True

    def send_mentioned_comment(self, user_dest, item, start_index):
        comment = item
        push_notify_log.debug(
            "send called - send_mentioned_comment for item ",
            vars(comment)
        )

        if item.post:
            parent_item = comment.post
            parent_id = parent_item.id
            parent_image_url = comment.post.get_main_image()

        elif item.place:
            parent_item = comment.place
            parent_id = parent_item.id
            parent_image_url = aws_url(comment.place.main_image)

        else:
            return False

        if parent_item.author.id == user_dest.id:
            pnl = 'The user {} mentioned in comment was the author of the parent item, skipping notification.'  # noqa
            push_notify_log.debug(
                pnl.format(user_dest.username), vars(comment)
            )
            return False

        user_place_data = self.get_owned_place_info(item)
        msg = {
            'typ': PushNotifyTypeE.NOTIFY_MENTIONED_COMMENT,
            'uid': str(comment.author_id),
            'avt': aws_url(comment.author.image),
            'usr': comment.author.username,
            'txt': cut_string(comment.description, 30),

            'pid': parent_id,
            'img': parent_image_url,
        }
        if user_place_data:
            msg['plcid'] = user_place_data.get('id')

        title = "New mention on comment"
        username = user_place_data.get('name') if user_place_data else "@{}".format(comment.author.username)
        subtitle_by_lang = {
            "en": "{} commented: {}".format(
                username,
                cut_string(comment.description, 30)
            ),
            "fr": "{} a commenté : {}".format(
                username,
                cut_string(comment.description, 30)
            ),
            "jp": "{} がコメントしました {}".format(
                username,
                cut_string(comment.description, 30)
            ),
        }

        notify = web.models.UserNotification(
            type=PushNotifyTypeE.NOTIFY_MENTIONED_COMMENT,
            contents=cut_string(comment.description, 30),
            post=comment.post if comment.post else None,
            place=comment.place if comment.place else None,
            start_comment_post=start_index if comment.post else None,
            start_comment_place=start_index if comment.place else None,
            user_dest=user_dest,
            user=comment.author,
            user_name=comment.author.username,
            created_time=dt.datetime.now(),
            status=1,
            is_archived=False,
        )
        notify.save()

        return self.send_msg(notify.user, user_dest, msg, title=title,
                             subtitle_by_lang=subtitle_by_lang)

    def send_mentioned_post(self, user_dest, item, start_index):
        push_notify_log.debug(
            'send called - send_mentioned_post for item ',
            vars(item)
        )

        user_place_data = self.get_owned_place_info(item)
        msg = {
            'typ': PushNotifyTypeE.NOTIFY_MENTIONED_NOT_COMMENT,
            'uid': str(item.author_id),
            'avt': aws_url(item.author.image),
            'usr': item.author.username,
            'txt': cut_string(item.description, 30),

            'pid': item.id,
            'img': item.get_main_image(),
        }
        if user_place_data:
            msg['plcid'] = user_place_data.get('id')

        title = "New mention on post"
        username = user_place_data.get('name') if user_place_data else "@{}".format(item.author.username)
        subtitle_by_lang = {
            'en': '{} mentioned you: {}'.format(
                username,
                cut_string(item.description, 30)
            ),
            'fr': '{} vous a mentionné : {}'.format(
                username,
                cut_string(item.description, 30)
            ),
            'jp': '{} があなたについて書きました {}'.format(
                username,
                cut_string(item.description, 30)
            ),
        }

        notify = web.models.UserNotification(
            type=PushNotifyTypeE.NOTIFY_MENTIONED_NOT_COMMENT,
            post=item,
            contents=cut_string(item.description, 30),
            start_comment_post=start_index,
            user_dest=user_dest,
            user=item.author,
            user_name=item.author.username,
            created_time=dt.datetime.now(),
            status=1,
            is_archived=False,
        )
        notify.save()

        return self.send_msg(notify.user, user_dest, msg, title=title,
                             subtitle_by_lang=subtitle_by_lang)

    def send_mentioned_place(self, user_dest, item, start_index):
        place = item

        push_notify_log.debug(
            'send called - send_mentioned_place for item ',
            vars(place)
        )

        user_place_data = self.get_owned_place_info(item)
        msg = {
            'typ': PushNotifyTypeE.NOTIFY_MENTIONED_NOT_COMMENT,
            'uid': str(place.author_id),
            'avt': aws_url(place.author.image),
            'usr': place.author.username,
            'txt': cut_string(strip_tags(place.description), 30),

            'pid': place.id,
            'img': aws_url(place.main_image),
        }
        if user_place_data:
            msg['plcid'] = user_place_data.get('id')

        title = "New mention on place"
        username = user_place_data.get('name') if user_place_data else "@{}".format(place.author.username)
        subtitle_by_lang = {
            'en': '{} mentioned you: {}'.format(
                username,
                cut_string(strip_tags(place.description), 30)
            ),
            'fr': '{} vous a mentionné : {}'.format(
                username,
                cut_string(strip_tags(place.description), 30)
            ),
            'jp': '{} があなたについて書きました {}'.format(
                username,
                cut_string(strip_tags(place.description), 30)
            ),
        }

        notify = web.models.UserNotification(
            type=PushNotifyTypeE.NOTIFY_MENTIONED_NOT_COMMENT,
            place=place,
            contents=cut_string(strip_tags(place.description), 30),
            start_comment_place=start_index,
            user_dest=user_dest,
            user=place.author,
            user_name=place.author.username,
            created_time=dt.datetime.now(),
            status=1,
            is_archived=False,
        )
        notify.save()

        return self.send_msg(notify.user, user_dest, msg, title=title,
                             subtitle_by_lang=subtitle_by_lang)

    def send_with_free_glass(self, user_dest, place):
        push_notify_log.debug(
            'send called - FREE GLASS - user %s (ID: %s), place %s (ID: %s)',
            user_dest.username, user_dest.id, place.name, place.id
        )

        user_place_data = self.get_owned_place_info(place)
        msg = {
            'typ': PushNotifyTypeE.NOTIFY_FREE_GLASS,
            'uid': str(user_dest.id),
            'avt': aws_url(user_dest.image),
            'usr': user_dest.username,
            'pid': place.id,
            'img': aws_url(place.main_image),
        }
        if user_place_data:
            msg['plcid'] = user_place_data.get('id')

        title = 'Free Glass!'

        subtitle_by_lang = {
            'en': 'Did you enjoy your free glass? If yes, click here to support us with a tip ;)',  # noqa
            'fr': 'Vous appréciez votre verre offert ? Alors cliquez ici pour nous soutenir en faisant un don ;)',  # noqa
            'jp': '自然派ワイン無料１杯をお楽しみいただけましたか？では、ここをクリックして、私たちへの支援に寄付をお願いします m(_ _)m',  # noqa
        }

        notify = web.models.UserNotification(
            type=PushNotifyTypeE.NOTIFY_FREE_GLASS,
            place=place,
            contents=cut_string(strip_tags(place.description), 100),
            user_dest=user_dest,
            user=user_dest,
            user_name=user_dest.username,
            created_time=dt.datetime.now(),
            status=1,
            is_archived=False,
        )
        notify.save()

        push_notify_log.debug('sending the notification')

        dt_now = dt.datetime.now()
        after_dt = (
            dt_now + dt.timedelta(minutes=45)
        ).strftime('%Y-%m-%d %H:%M:%S')

        return self.send_msg(notify.user, user_dest, msg, title=title,
                             subtitle_by_lang=subtitle_by_lang,
                             send_after=after_dt)

    def send_with_free_glass_test(self, user_dest, place, push_token):
        push_notify_log.debug(
            "send called - TEST FREE GLASS - user %s (ID: %s), place %s (ID: %s)",  # noqa
            user_dest.username, user_dest.id, place.name, place.id
        )

        user_place_data = self.get_owned_place_info(place)
        msg = {
            'typ': PushNotifyTypeE.NOTIFY_FREE_GLASS,
            'uid': str(user_dest.id),
            'avt': aws_url(user_dest.image),
            'usr': user_dest.username,
            'pid': place.id,
            'img': aws_url(place.main_image),
        }
        if user_place_data:
            msg['plcid'] = user_place_data.get('id')

        title = "Free Glass!"

        subtitle_by_lang = {
            'en': 'Did you enjoy your free glass? If yes, click here to support us with a tip ;)',  # noqa
            'fr': 'Vous appréciez votre verre offert ? Alors cliquez ici pour nous soutenir en faisant un don ;)',  # noqa
            'jp': '自然派ワイン無料１杯をお楽しみいただけましたか？では、ここをクリックして、私たちへの支援に寄付をお願いします m(_ _)m',  # noqa
        }

        notify = web.models.UserNotification(
            type=PushNotifyTypeE.NOTIFY_FREE_GLASS,
            place=place,
            contents=cut_string(strip_tags(place.description), 100),
            user_dest=user_dest,
            user=user_dest,
            user_name=user_dest.username,
            created_time=dt.datetime.now(),
            status=1,
            is_archived=False,
        )
        notify.save()

        push_notify_log.debug('sending the notification')

        return self.send_msg(notify.user, user_dest, msg, title=title,
                             subtitle_by_lang=subtitle_by_lang,
                             push_id=push_token)

    def send_with_free_glass_click(self, user_dest, place, wm):
        push_notify_log.debug(
            "send called - TEST FREE GLASS - user %s (ID: %s), place %s (ID: %s), WM %s (ID: %s)",  # noqa
            user_dest.username, user_dest.id,
            place.name if place else '-',
            place.id if place else '-',
            wm.name if wm else '-', wm.id if wm else '-'
        )

        if place:
            txt = cut_string(strip_tags(place.description), 100)
            img = aws_url(place.main_image)
        elif wm:
            txt = cut_string(wm.description, 100)
            img = aws_url(wm.main_image)
        else:
            return

        title = 'Free Glass!'

        subtitle_by_lang = {
            'en': 'Did you enjoy your free glass? If yes, click here to support us with a tip ;)',  # noqa
            'fr': 'Vous appréciez votre verre offert ? Alors cliquez ici pour nous soutenir en faisant un don ;)',  # noqa
            'jp': '自然派ワイン無料１杯をお楽しみいただけましたか？では、ここをクリックして、私たちへの支援に寄付をお願いします m(_ _)m',  # noqa
        }

        user_place_data = self.get_owned_place_info(place)
        msg = {
            'typ': PushNotifyTypeE.NOTIFY_FREE_GLASS,
            'uid': str(user_dest.id),
            'avt': aws_url(user_dest.image),
            'usr': user_dest.username,
            'pid': place.id if place else None,
            'wid': wm.id if wm else None,
            'img': img,
        }
        if user_place_data:
            msg['plcid'] = user_place_data.get('id')

        notify = web.models.UserNotification(
            type=PushNotifyTypeE.NOTIFY_FREE_GLASS,
            place=place if place else None,
            wm=wm if wm else None,
            contents=txt,
            user_dest=user_dest,
            user=user_dest,
            user_name=user_dest.username,
            created_time=dt.datetime.now(),
            status=1,
            is_archived=False,
        )
        notify.save()
        push_notify_log.debug('sending the notification')
        return self.send_msg(notify.user, user_dest, msg, title=title,
                             subtitle_by_lang=subtitle_by_lang,
                             for_admin_too=True)

    # --------------- sending of particular notifications --------------------
    # winepost was liked
    def send_like_on_winepost(self, like):
        user_dest = like.post.author

        push_notify_log.debug('send called - like data %s', vars(like))

        user_place_data = self.get_owned_place_info(like)
        msg = {
            'typ': PushNotifyTypeE.NOTIFY_LIKE_WINEPOST,
            'uid': str(like.author_id),
            'avt': aws_url(like.author.image),
            'usr': like.author.username,

            'pid': like.post.id,
            'img': like.post.get_main_image(),
        }
        if user_place_data:
            msg['plcid'] = user_place_data.get('id')

        push_notify_log.debug(
            '\n===== CALL ==============\nWHAT: send_like_on_winepost to %s ',
            {'msg': msg, 'rcv': user_dest.username}
        )

        title = "New Like"
        username = user_place_data.get('name') if user_place_data else "@{}".format(like.author.username)
        subtitle_by_lang = {
            'en': '{} likes your post'.format(username),
            'fr': '{} aime votre publication'.format(username),
            'jp': '{} があなたの投稿を気に入りました。'.format(username),
        }

        notify = web.models.UserNotification(
            type=PushNotifyTypeE.NOTIFY_LIKE_WINEPOST,
            post=like.post,
            contents=cut_string(like.post.description, 100),
            user_dest=user_dest,
            user=like.author,
            user_name=like.author.username,
            created_time=dt.datetime.now(),
            status=1,
            is_archived=False,
        )
        notify.save()

        if like.author == user_dest:
            push_notify_log.debug(
                'notification sender and adressee is one the same person - '
                'not sending, storing in history only'
            )
            return None
        if self.user_accepts_notification(user_dest, self.NOTIFY_LIKE):
            push_notify_log.debug('user accepts notification - sending')

            return self.send_msg(notify.user, user_dest, msg, title=title,
                                 subtitle_by_lang=subtitle_by_lang)
        else:
            push_notify_log.debug(
                'user DOES NOT accept notification - not sending, storing in history only'  # noqa
            )
            return None

    # winepost was drank-it-tooed
    def send_drank_it_too_on_winepost(self, drank_it_too):
        user_dest = drank_it_too.post.author

        push_notify_log.debug(
            'send called - drank_it_too data %s',
            vars(drank_it_too)
        )

        user_place_data = self.get_owned_place_info(drank_it_too)
        msg = {
            'typ': PushNotifyTypeE.NOTIFY_DRANK_IT_TOO,
            'uid': str(drank_it_too.author_id),
            'avt': aws_url(drank_it_too.author.image),
            'usr': drank_it_too.author.username,

            'pid': drank_it_too.post.id,
            'img': drank_it_too.post.get_main_image(),
        }
        if user_place_data:
            msg['plcid'] = user_place_data.get('id')

        push_notify_log.debug(
            '\n===== CALL ==============\nWHAT: send_drank_it_too_on_winepost to %s',  # noqa
            {'msg': msg, 'rcv': user_dest.username}
        )

        title = 'New Drank it too'
        username = user_place_data.get('name') if user_place_data else "@{}".format(drank_it_too.author.username)
        subtitle_by_lang = {
            'en': '{} drank this wine, too'.format(username),  # noqa
            'fr': '{} a déjà bu ce vin, aussi.'.format(username),  # noqa
            'jp': '{} もすでにこのワインを飲んでいます。'.format(username),  # noqa
        }

        notify = web.models.UserNotification(
            type=PushNotifyTypeE.NOTIFY_DRANK_IT_TOO,
            contents=cut_string(drank_it_too.post.description, 100),
            post=drank_it_too.post,
            user_dest=user_dest,
            user=drank_it_too.author,
            user_name=drank_it_too.author.username,
            created_time=dt.datetime.now(),
            status=1,
            is_archived=False,
        )
        notify.save()

        if drank_it_too.author == user_dest:
            push_notify_log.debug(
                'notification sender and addressee is one the same person - '
                'not sending, storing in history only'
            )
            return None
        if self.user_accepts_notification(user_dest, self.NOTIFY_DRANK_IT_TOO):
            push_notify_log.debug('user accepts notification - sending')
            return self.send_msg(notify.user, user_dest, msg, title=title,
                                 subtitle_by_lang=subtitle_by_lang)
        else:
            push_notify_log.debug(
                'user DOES NOT accept notification - not sending, storing in history only'  # noqa
            )
            return None

    # winepost was commented
    def send_comment_on_winepost(self, comment):
        user_dest = comment.post.author

        push_notify_log.debug(
            'send called - comment data %s',
            vars(comment)
        )
        push_notify_log.debug(
            'send called - user accepts notification - comment data %s',
            vars(comment)
        )
        user_place_data = self.get_owned_place_info(comment)
        msg = {
            'typ': PushNotifyTypeE.NOTIFY_COMMENT_WINEPOST,
            'uid': str(comment.author_id),
            'avt': aws_url(comment.author.image),
            'usr': comment.author.username,

            'pid': comment.post.id,
            'img': comment.post.get_main_image(),
            'txt': cut_string(comment.description, 100)
        }
        if user_place_data:
            msg['plcid'] = user_place_data.get('id')

        push_notify_log.debug(
            '\n===== CALL ============\nWHAT: send_comment_on_winepost to %s',
            {'msg': msg, 'rcv': user_dest.username}
        )

        title = 'New Comment'
        username = user_place_data.get('name') if user_place_data else "@{}".format(comment.author.username)
        subtitle_by_lang = {
            'en': '{} made a comment: {}'.format(
                username,
                cut_string(comment.description, 20)
            ),
            'fr': '{} a fait un commentaire: {}'.format(
                username,
                cut_string(comment.description, 20)
            ),
            'jp': '{}: {}'.format(
                username,
                cut_string(comment.description, 20)
            ),
        }

        notify = web.models.UserNotification(
            type=PushNotifyTypeE.NOTIFY_COMMENT_WINEPOST,
            contents=cut_string(comment.description, 100),
            post=comment.post,
            user_dest=user_dest,
            user=comment.author,
            user_name=comment.author.username,
            created_time=dt.datetime.now(),
            status=1,
            is_archived=False,
        )
        notify.save()

        if comment.author == user_dest:
            push_notify_log.debug(
                'notification sender and addressee is one the same person - '
                'not sending, storing in history only'
            )
            return None
        if self.user_accepts_notification(user_dest, self.NOTIFY_COMMENT):
            push_notify_log.debug('user accepts notification - sending')
            return self.send_msg(notify.user, user_dest, msg, title=title,
                                 subtitle_by_lang=subtitle_by_lang)
        else:
            push_notify_log.debug(
                'user DOES NOT accept notification - not sending, storing in history only'  # noqa
            )
            return None

    # winepost was marked as "star review"
    def send_star_review_on_winepost(self, star_review):
        user_dest = star_review.author
        dt_now_str = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        push_notify_log.debug(
            "%s : send_star_review_on_winepost called - star review data %s",
            (dt_now_str, vars(star_review))
        )

        msg = {
            'typ': PushNotifyTypeE.NOTIFY_STAR_REVIEW,
            'pid': star_review.id,
            'img': star_review.get_main_image()
        }

        push_notify_log.debug(
            "%s: ===== CALL =======\nWHAT: send_star_review_on_winepost to %s",
            dt_now_str, {'msg': msg, 'rcv': user_dest.username}
        )
        title = 'Star'

        subtitle_by_lang = {
            'en': 'Congratulations ! You won a STAR for discovering an '
                  'unregistered wine or having written a beautiful wine review!',  # noqa
            'fr': 'Félicitations ! Vous avez gagné une ÉTOILE pour avoir découvert '  # noqa
                  'un nouveau vin ou pour avoir écrit un bel article sur un vin!',  # noqa
            'jp': 'おめでとうございます!未登録のワイン発見、または素晴らしいワイン・'
                  'レヴューで、星を一つ獲得しました!',
        }

        notify = web.models.UserNotification(
            type=PushNotifyTypeE.NOTIFY_STAR_REVIEW,
            post=star_review,
            contents=cut_string(star_review.description, 100),
            user_dest=user_dest,
            user=user_dest,
            user_name=user_dest.username,
            created_time=dt.datetime.now(),
            status=1,
            is_archived=False,
        )
        notify.save()
        if self.user_accepts_notification(
            user_dest, self.NOTIFY_WINE_REVIEW
        ):
            push_notify_log.debug(
                '%s - user %s accepts notification - sending',
                dt_now_str, user_dest.id
            )

            return self.send_msg(notify.user, user_dest, msg, title=title,
                                 subtitle_by_lang=subtitle_by_lang)
        else:
            push_notify_log.debug(
                '%s - user %s DOES NOT accept notification - not sending, storing in history only',  # noqa
                dt_now_str, user_dest.id
            )

            return None

    # winepost was accepted
    def send_accepted_on_winepost(self, post):
        user_dest = post.author

        push_notify_log.debug(
            'send called - user accepts notification - accepted winepost data %s',  # noqa
            vars(post)
        )

        push_notify_log.debug(
            'send called - user accepts notification - accepted winepost data %s',  # noqa
            vars(post)
        )

        msg = {
            'typ': PushNotifyTypeE.NOTIFY_WINEPOST_ACCEPTED,
            'pid': post.id,
            'img': post.get_main_image(),
            'nam': post.title,
        }
        push_notify_log.debug(
            '\n===== CALL ============\nWHAT: send_accepted_on_winepost to %s',
            {'msg': msg, 'rcv': user_dest.username})

        title = 'Wine review: ACCEPTED / Congratulations'

        subtitle_by_lang = {
            'en': '{} has been included in our database.'.format(post.title),
            'fr': '{} à présent enregistré dans notre base de données.'.format(post.title),  # noqa
            'jp': '{} はすでにデータベースに上にあります。'.format(post.title),
        }

        notify = web.models.UserNotification(
            type=PushNotifyTypeE.NOTIFY_WINEPOST_ACCEPTED,
            contents=cut_string(post.description, 100),
            post=post,
            user_dest=user_dest,
            user=user_dest,
            user_name=user_dest.username,
            created_time=dt.datetime.now(),
            status=1,
            is_archived=False,
        )
        notify.save()

        if self.user_accepts_notification(user_dest, self.NOTIFY_WINE_REVIEW):
            push_notify_log.debug('user accepts notification - sending')

            return self.send_msg(notify.user, user_dest, msg, title=title,
                                 subtitle_by_lang=subtitle_by_lang)
        else:
            push_notify_log.debug(
                'user DOES NOT accept notification - not sending, storing in history only'  # noqa
            )
            return None

    # place was commented
    def send_comment_on_place(self, comment):
        user_dest = comment.place.author

        push_notify_log.debug(
            'send called - comment on place data %s', vars(comment)
        )

        parent = comment.place

        user_place_data = self.get_owned_place_info(comment)
        msg = {
            'typ': PushNotifyTypeE.NOTIFY_COMMENT_PLACE,
            'uid': str(comment.author.id),
            'avt': aws_url(comment.author.image),
            'usr': comment.author.username,

            'pid': parent.id,
            'img': aws_url(parent.main_image),
            'txt': cut_string(comment.description, 100),
        }
        if user_place_data:
            msg['plcid'] = user_place_data.get('id')

        push_notify_log.debug(
            '\n===== CALL ==============\nWHAT: send_comment_on_place to %s',
            {'msg': msg, 'rcv': user_dest.username}
        )

        title = 'New Comment'
        username = user_place_data.get('name') if user_place_data else "@{}".format(comment.author.username)
        subtitle_by_lang = {
            'en': '{} made a comment: {}'.format(
                username,
                cut_string(comment.description, 20)
            ),
            'fr': '{} a fait un commentaire :{}'.format(
                username,
                cut_string(comment.description, 20)
            ),
            'jp': '{}: {}'.format(
                username,
                cut_string(comment.description, 20)
            ),
        }

        notify = web.models.UserNotification(
            type=PushNotifyTypeE.NOTIFY_COMMENT_PLACE,
            place=comment.place,
            contents=cut_string(comment.description, 100),
            user_dest=user_dest,
            user=comment.author,
            user_name=comment.author.username,
            created_time=dt.datetime.now(),
            status=1,
            is_archived=False,
        )
        notify.save()

        if comment.author == user_dest:
            push_notify_log.debug(
                'notification sender and addressee is one the same person - '
                'not sending, storing in history only'
            )
            return None
        if self.user_accepts_notification(user_dest, self.NOTIFY_COMMENT):
            push_notify_log.debug('user accepts notification - sending')

            return self.send_msg(notify.user, user_dest, msg, title=title,
                                 subtitle_by_lang=subtitle_by_lang)
        else:
            push_notify_log.debug(
                'user DOES NOT accept notification - not sending, storing in history only'  # noqa
            )
            return None

    def send_like_on_place(self, like):
        user_dest = like.place.author
        place = like.place
        push_notify_log.debug(
            'send called - like on place data %s', vars(like)
        )

        user_place_data = self.get_owned_place_info(like)
        msg = {
            'typ': PushNotifyTypeE.NOTIFY_LIKE_PLACE,
            'uid': str(like.author_id),
            'avt': aws_url(like.author.image),
            'usr': like.author.username,

            'pid': place.id,
            'img': aws_url(place.main_image)
        }
        if user_place_data:
            msg['plcid'] = user_place_data.get('id')

        push_notify_log.debug(
            '\n===== CALL ==============\nWHAT: send_like_on_place to %s',
            {'msg': msg, 'rcv': user_dest.username}
        )

        title = 'New Like'
        username = user_place_data.get('name') if user_place_data else "@{}".format(like.author.username)
        subtitle_by_lang = {
            'en': '{} likes your post'.format(username),
            'fr': '{} aime votre publication'.format(username),
            'jp': '{} があなたの投稿を気に入りました。'.format(username),
        }

        notify = web.models.UserNotification(
            type=PushNotifyTypeE.NOTIFY_LIKE_PLACE,
            place=like.place,
            contents=cut_string(strip_tags(place.description), 100),
            user_dest=user_dest,
            user=like.author,
            user_name=like.author.username,
            created_time=dt.datetime.now(),
            status=1,
            is_archived=False,
        )
        notify.save()

        if like.author == user_dest:
            push_notify_log.debug(
                'notification sender and addressee is one the same person - '
                'not sending, storing in history only'
            )
            return None
        if self.user_accepts_notification(user_dest, self.NOTIFY_LIKE):
            push_notify_log.debug('user accepts notification - sending')

            return self.send_msg(notify.user, user_dest, msg, title=title,
                                 subtitle_by_lang=subtitle_by_lang)
        else:
            push_notify_log.debug(
                'send called - user DOES NOT accept notification - like on place data %s',  # noqa
                vars(like)
            )
            return None

    def send_accepted_on_place(self, place):
        user_dest = place.author

        push_notify_log.debug(
            'send called - accepted place data %s', vars(place)
        )

        msg = {
            'typ': PushNotifyTypeE.NOTIFY_PLACE_ACCEPTED,
            'pid': place.id,
            'img': aws_url(place.main_image),
            'nam': place.name,
        }

        push_notify_log.debug(
            '\n===== CALL ==============\nWHAT: send_accepted_on_place to %s',
            {'msg': msg, 'rcv': user_dest.username}
        )

        title = 'Place Review: ACCEPTED'

        subtitle_by_lang = {
            'en': 'Congratulations! {} has been included in our natural wine places index. Thanks for your help!'.format(  # noqa
                beautify_place_name(place.name)
            ),
            'fr': 'Félicitations ! {} est à présent enregistré dans notre index. Merci de votre aide ! Grâce '  # noqa
                  'à vous, la communauté grandit.'.format(beautify_place_name(place.name)),  # noqa
            'jp': 'おめでとうございます! {} が、一覧に登録されました。ご協力いただき、ありがとうございます!'.format(  # noqa
                beautify_place_name(place.name)
            ),
        }

        notify = web.models.UserNotification(
            type=PushNotifyTypeE.NOTIFY_PLACE_ACCEPTED,
            place=place,
            contents=cut_string(strip_tags(place.description), 100),
            user_dest=user_dest,
            user=user_dest,
            user_name=user_dest.username,
            created_time=dt.datetime.now(),
            status=1,
            is_archived=False,
        )
        notify.save()

        if self.user_accepts_notification(user_dest, self.NOTIFY_PLACE):
            push_notify_log.debug('user accepts notification - sending')

            return self.send_msg(notify.user, user_dest, msg, title=title,
                                 subtitle_by_lang=subtitle_by_lang)
        else:
            push_notify_log.debug(
                'user DOES NOT accept notification - not sending, storing in history only'  # noqa
            )
            return None

    def get_owned_place_info(self, instance):
        if instance and instance.author:
            return instance.author.place_owner.values('id', 'name').filter(
                status__in=[
                    PlaceStatusE.SUBSCRIBER,
                    PlaceStatusE.PUBLISHED]
            ).first()
