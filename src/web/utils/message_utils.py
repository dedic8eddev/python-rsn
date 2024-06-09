import datetime
import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode

from web.constants import SysMessageStatusE, SysMessageTypeE, UserTypeE
from web.models import SysMessage

from .tokens import CommonTokenGenerator

log = logging.getLogger(__name__)


class MessageSender(object):
    """
    Sends messages (EMAIL or SMS) via buffer
    """

    def __init__(self):
        pass

    def add(
        self, message_type, to_address, to_name, from_address,
        from_name, title, content
    ):
        message = SysMessage(
            message_type=message_type, to_address=to_address, to_name=to_name,
            from_address=from_address, from_name=from_name,
            title=title, content=content,
            send_attempts_number=0, status=SysMessageStatusE.PENDING
        )

        message.save()

    def send_message(self, message):
        is_sent = False

        to_list = [message.to_address]

        if message.message_type == SysMessageTypeE.EMAIL:
            if message.from_address:
                from_address = message.from_address
            else:
                from_address = settings.EMAIL_FROM
            ema = EmailMultiAlternatives(
                subject=message.title, body=message.content,
                from_email=from_address, to=to_list
            )
            message.send_attempts_number += 1
            message.last_attempt_date = datetime.datetime.now()
            message.save()
            try:
                ema.send()
                is_sent = True
            except Exception as e:
                log.debug(str(e))
        elif message.message_type == SysMessageTypeE.SMS:  # noqa TODO FIXME - not ready yet, not needed yet
            pass

        return is_sent

    def remove_message(self, message):
        message.delete()

    def send_messages(self, limit=None):
        messages = SysMessage.objects.filter(
            status=SysMessageStatusE.PENDING
        ).order_by('id')[:limit]

        for message in messages:
            is_sent = self.send_message(message)
            if is_sent:
                log.debug("message '%s' sent OK" % message)
                self.remove_message(message)
            else:
                log.debug("failed to send message '%s'" % message)


class EmailCollection(object):
    def send_reset_password_email(self, user, lang=None):
        titles = {
            'EN': 'Password reset requested',
            'FR': 'Réinitialiser mon mot de passe',
            'IT': 'Reimposta la mia password',
            'JA': 'パスワードを再設定'
        }
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        link_template = "%(site_url)s/%(prefix)spassword_reset/confirm/%(uid)s/%(token)s/"  # noqa
        link_context = {
            'site_url': settings.SITE_URL,
            'prefix': 'pro/' if user.type in [
                UserTypeE.OWNER, UserTypeE.USER
            ] else '',
            'uid': uid,
            'token': token
        }
        link = link_template % link_context
        context = {
            'username': user.username,
            'link': link,
            'site_url': settings.SITE_URL,
            'pro': user.type == UserTypeE.OWNER,
            'bgcolor': '#f5f6fa' if user.type == UserTypeE.OWNER else '#f6f7ea'
        }

        lang_to_use = 'EN'   # default lang
        if lang and lang in ['EN', 'FR', 'IT', 'JA']:
            lang_to_use = lang
        elif user.lang and user.lang in ['EN', 'FR', 'IT', 'JA']:
            lang_to_use = user.lang

        title = titles[lang_to_use]
        content_template_name = 'mail/registration/password_reset_email_{}.html'.format(lang_to_use)  # noqa
        log.debug("Sending message - LANG TO USE {}".format(lang_to_use))
        content = loader.render_to_string(content_template_name, context)

        from_email = 'pro' if user.type == UserTypeE.OWNER else 'contact'
        from_email += '@raisin.digital'

        ema = EmailMultiAlternatives(
            subject=title, body=strip_tags(content),
            from_email=from_email, to=[user.email]
        )

        ema.attach_alternative(content, "text/html")
        ema.send()

    def send_activation_email(self, user):
        titles = {
            'FR': 'Création de votre compte Raisin',
            'EN': 'Create your Raisin account'
        }

        token_generator = CommonTokenGenerator()
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.id))

        email = user.email
        establishment_name = user.place_owner.first().name
        username = user.username
        if user.lang and user.lang in ['EN', 'FR']:
            language = user.lang
        else:
            language = 'EN'
        title = titles.get(language, titles['EN'])

        link = settings.SITE_URL + reverse(
            'pro_set_password', args=[uid, token]
        )
        context = {
            'email': email,
            'establishment_name': establishment_name,
            'username': username,
            'link': link,
            'site_url': settings.SITE_URL
        }

        template_name = '{}{}.html'.format(
            'mail/registration/account_confirm_and_details_email_',
            language
        )
        content = loader.render_to_string(template_name, context)

        from_email = 'test@raisin.digital' if settings.DEBUG else 'pro@raisin.digital'  # noqa
        to_email = 'test-pro@raisin.digital' if settings.DEBUG else email

        ema = EmailMultiAlternatives(
            subject=title, body=strip_tags(content),
            from_email=from_email, to=[to_email],
            cc=[from_email]
        )

        ema.attach_alternative(content, "text/html")
        ema.send()
