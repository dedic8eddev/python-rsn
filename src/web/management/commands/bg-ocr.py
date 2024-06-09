import logging
import time

from django.core.management.base import BaseCommand

from web.constants import WineListStatusE
from web.models import WineListFile
from web.utils.ocr.db import (fetch_validated_winemakers,
                              fetch_validated_wines_with_wms)
from web.utils.ocr_tools import get_text_rows, get_score

log_cmd = logging.getLogger("command")


class Command(BaseCommand):
    args = ""
    help = "Continously fetches and processes the WL-WF pairs."

    def handle(self, *args, **options):
        while True:
            winemakers = fetch_validated_winemakers()
            wines_with_wms = fetch_validated_wines_with_wms()
            wl_files = WineListFile.active.filter(
                winelist__status=WineListStatusE.BG,
                winelist__is_archived=False
            )[:100]

            wines = wines_with_wms['items']
            wines_by_wm = wines_with_wms['items_by_wm']

            log_cmd.info("Found {} files in background to be OCR-ed".format(
                wl_files.count())
            )

            if not wl_files:
                time.sleep(5)
            else:
                for wl_file in wl_files:
                    log_cmd.info("OCR-ing image file: {} ".format(
                        str(wl_file.image_file))
                    )
                    text_rows = get_text_rows(wl_file.image_file)
                    score = get_score(
                        text_rows,
                        winemakers=winemakers,
                        wines=wines,
                        wines_by_wm=wines_by_wm
                    )
                    wl_file.item_text_rows = text_rows
                    wl_file.save()

                    wl_file.winelist.total_score_data = score
                    wl_file.winelist.status = WineListStatusE.OK
                    wl_file.winelist.save()

                    log_cmd.info("Result for file {}: {}%".format(
                        str(wl_file.image_file), score['score_percent'])
                    )
