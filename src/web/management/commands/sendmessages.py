import logging
from django.core.management.base import BaseCommand
from web.utils.message_utils import MessageSender


log = logging.getLogger("command")


class Command(BaseCommand):
    args = ""
    help = "Sends all messages from web_sysmessage buffer"

    def handle(self, *args, **options):
        log.debug("Sending all messages from the buffer... ")
        ms = MessageSender()
        ms.send_messages()
        log.debug("Sending all messages from the buffer finished.")
