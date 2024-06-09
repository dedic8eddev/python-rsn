import logging

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from web.models import NWLAExcludedWord

log_cmd = logging.getLogger("command")


class Command(BaseCommand):
    help = "Uploads pre-defined list of NWLA exclusion keywords"

    def handle(self, *args, **options):
        words = [
            'ancestral',
            'blanc de blancs',
            'Blanc De Noir',
            'bourgogne',
            'Brut Réserve',
            'brutal',
            'Bulle',
            'cabernet franc',
            'castilla y Leon',
            'Champagne Brut',
            'chenin blanc',
            'cinsault',
            'cotes du jura',
            'cote du rhone',
            'Crémant De Loire',
            'Cuvée prestige',
            'ET',
            'France',
            'Franciacorta',
            'frizzante',
            'frères',
            'garnacha',
            'grand cru',
            'grenache noir',
            'grenache blanc',
            'Il',
            'Le Blanc',
            'Le Clos',
            'metodo classico',
            'Naturel',
            'Noir',
            'Not',
            'NV',
            'Penedes',
            'Pet Nat',
            'Pink',
            'pinot gris',
            'pinot noir',
            'red',
            'Red Wine',
            'Riesling Trocken',
            'Rioja',
            'rosato',
            'rose',
            'saint joseph',
            'sauvignon blanc',
            'spain',
            'sparkling',
            'sumoll',
            'vino bianco',
            'White Blend',
            'Zéro'
        ]

        words = list(set(words))  # to exclude duplicates
        for word in words:
            instance = NWLAExcludedWord(word=word)
            try:
                instance.full_clean()
            except ValidationError:
                log_cmd.info(f"ADD-NEW-NWLA-EXCLUSION-WORDS: the word:"
                             f" '{word}' is already present in DB.")
            else:
                instance.save()
                log_cmd.info(f"ADD-NEW-NWLA-EXCLUSION-WORDS: the word:"
                             f" '{word}' was succesfully added.")
        log_cmd.info("DONE.")
