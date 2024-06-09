import logging
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from web.models import Wine

kw_log = logging.getLogger("command_keywords")


class Command(BaseCommand):
    args = ""
    help = "updates the relevancy keywords list"

    def handle(self, *args, **options):
        current_keywords = settings.RELEVANCY_KEYWORDS if settings.RELEVANCY_KEYWORDS else []  # noqa

        kw_log.debug("searching for and updating relevancy keywords")
        kw_log.debug("there were {} keywords before operation ".format(
            len(current_keywords)
        ))

        for item in Wine.active.all():
            if not item.grape_variety:
                continue

            grape_variety_str = item.grape_variety
            grape_variety_list = grape_variety_str.split(',')

            if grape_variety_list:
                for gv in grape_variety_list:
                    gv = gv.strip()
                    if gv not in current_keywords:
                        kw_log.debug("adding keyword %s" % gv)
                        current_keywords.append(gv)

        with open(
            settings.RELEVANCY_KEYWORDS_FILEPATH_TMP, 'w', encoding='utf-8'
        ) as ktf:
            ktf.writelines("%s\n" % keyword for keyword in current_keywords)
            ktf.close()

            kw_log.debug(
                "saving keywords in the temp file {} ".format(
                    settings.RELEVANCY_KEYWORDS_FILEPATH_TMP
                )
            )
            if os.path.exists(settings.RELEVANCY_KEYWORDS_FILEPATH_TMP):
                kw_log.debug(
                    "moving the temp file {} to {} ".format(
                        settings.RELEVANCY_KEYWORDS_FILEPATH_TMP,
                        settings.RELEVANCY_KEYWORDS_FILEPATH
                    )
                )
                os.rename(
                    settings.RELEVANCY_KEYWORDS_FILEPATH_TMP,
                    settings.RELEVANCY_KEYWORDS_FILEPATH
                )
            else:
                kw_log.debug("ERROR OCCURED - temporary file {} does NOT exist".format(
                    settings.RELEVANCY_KEYWORDS_FILEPATH_TMP)
                )
