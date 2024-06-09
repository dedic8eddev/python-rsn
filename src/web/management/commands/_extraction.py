from abc import ABC, abstractmethod
from pathlib import Path
from django.conf import settings


class DBExtraction(ABC):

    EXTRACTION_DIR = 'extraction'

    @abstractmethod
    def extract(self, *args, **kwargs):
        pass

    def output_dir(self):
        # prepare output directory
        output_dir = Path(settings.APP_ROOT) / self.EXTRACTION_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        return output_dir
