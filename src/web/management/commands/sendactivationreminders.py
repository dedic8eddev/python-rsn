import logging
from django.core.management.base import BaseCommand
from datetime import timedelta, date
from django.conf import settings
from web.models import UserProfile
from web.constants import UserStatusE
from web.utils.message_utils import EmailCollection


log = logging.getLogger("command")


class Command(BaseCommand):
    args = ""
    help = "creates activation reminders to be sent by the closest message sender call"

    def handle(self, *args, **options):
        log.debug("Activation reminders - checking whether inactive users due to be reminded found")
        reminder_due_date = date.today() - timedelta(settings.ACTIVATION_REMINDER_DAYS_INTERVAL)
        log.debug("reminder due date: %s max activation reminders: %d" % (reminder_due_date,
                                                                          settings.MAX_ACTIVATION_REMINDERS))
        inactive_users_to_be_reminded = UserProfile.active.filter(
            status=UserStatusE.INACTIVE,
            activation_reminder_sent_number__lt=settings.MAX_ACTIVATION_REMINDERS,
            activation_reminder_sent_last_date__lte=reminder_due_date
        )

        if inactive_users_to_be_reminded:
            log.debug("Inactive users to be reminded found: %d" % len(inactive_users_to_be_reminded))
            for user in inactive_users_to_be_reminded:
                log.debug("creating a reminder for user %s" % user.username)
                EmailCollection().send_activation_email(user)
                user.activation_reminder_sent_last_date = date.today()
                user.activation_reminder_sent_number += 1
                user.save()
            log.debug("creating all reminders finished. ")
        else:
            log.debug("no users to be reminded found - finished.")
