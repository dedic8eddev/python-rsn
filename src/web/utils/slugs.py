import string
import random
from django.template.defaultfilters import slugify
from google.cloud import translate_v2 as translate


TRANSLATE_CLIENT = translate.Client()


def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def detect_language_and_translate(text):
    result = TRANSLATE_CLIENT.detect_language(text)
    language = result.get("language")
    if language and language not in ['en', 'es', 'fr', 'it']:
        result = TRANSLATE_CLIENT.translate(text, target_language='en')
        text = result.get('translatedText')
    return text


def unique_slug_generator(instance, new_slug=None, lang=None):
    if new_slug is not None:
        slug = new_slug
    else:
        if lang:
            title = getattr(instance, f"title_{lang}") if lang != "ja" else getattr(instance, "title_en")
            slug_str = title if title else instance.name

        else:
            slug_str = instance.name if hasattr(instance, 'name') else instance.title

        if slug_str:
            slug_str = detect_language_and_translate(slug_str)
        slug = slugify(slug_str)

    if slug == "":
        slug = random_string_generator(size=8)
    try:
        queryset = instance.__class__.objects.all_with_deleted()
    except Exception:
        queryset = instance.__class__.objects.all()
    if instance.id:
        queryset = queryset.exclude(id=instance.id)
    if instance.is_archived:
        slug = f"{slug}-{random_string_generator(size=2)}"
    if lang is not None:
        if lang == "en":
            qs_exists = queryset.filter(slug_en=slug).exists()
        elif lang == "es":
            qs_exists = queryset.filter(slug_es=slug).exists()
        elif lang == "it":
            qs_exists = queryset.filter(slug_it=slug).exists()
        elif lang == "fr":
            qs_exists = queryset.filter(slug_fr=slug).exists()
        else:
            qs_exists = queryset.filter(slug_ja=slug).exists()
    else:
        qs_exists = queryset.filter(slug=slug).exists()
    if qs_exists:
        new_slug = f"{slug}-{random_string_generator(size=2)}"
        return unique_slug_generator(instance, new_slug=new_slug, lang=lang)
    return slug
