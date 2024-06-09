from __future__ import absolute_import
import datetime as dt
import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from google.api_core.exceptions import Forbidden
from google.cloud import translate
from web.constants import get_selected_languages
from news.forms import (ClearQuoteTranslationsForm, TranslateQuoteForm,
                        ClearCheffeTranslationsForm, ClearTestimonialTranslationsForm,
                        TranslateCheffeForm, TranslateTestimonialForm)
from news.models import Quote, Cheffe, Testimonial
from web.utils.views_common import get_current_user

log = logging.getLogger(__name__)


@csrf_exempt
@login_required
def translate_quote(request):
    user = get_current_user(request)
    client = translate.Client()
    if request.method == 'POST':
        form = TranslateQuoteForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            orig_lang = cd['orig_lang']
            contents_orig = cd['contents']
            quote_id = cd['quote_id']
            data_out = {
                'orig_lang': orig_lang,
                'orig_contents': contents_orig,
                'translations': {},
            }
            langs = get_selected_languages()
            langs.append(orig_lang)
            for lang in langs:
                if lang != orig_lang:
                    try:
                        contents_tr = client.translate(
                            contents_orig,
                            source_language=orig_lang,
                            target_language=lang,
                            format_='text'
                        )
                    except Forbidden as e:
                        return JsonResponse({
                            'status': 'error', 'data': e.message
                        }, status=403)
                    contents = contents_tr['translatedText']
                else:
                    contents = contents_orig

                url_author = reverse('edit_user', args=[user.id])
                data_out['translations'][lang] = {
                    'lang': lang,
                    'text': contents,
                    'author_id': user.id,
                    'author_username': user.username,
                    'modified_time': dt.datetime.now(),
                    'footer': '%s - by: <a href="%s">@%s</a>' % (
                        dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d'),
                        url_author,
                        user.username
                    )
                }

            # for already existing quotes only - for the
            # newly added ones we just return translations
            if quote_id:
                wm = Quote.objects.get(id=quote_id)
                wm.quote_translations = data_out
                for i in ['en', 'it', 'fr', 'es', 'ja']:
                    setattr(wm, f'quote_{i}', data_out['translations'][i.upper()]['text'])
                wm.default_quote = contents_orig
                wm.save()
                wm.refresh_from_db()
            result_data = {'status': 'OK', 'data': data_out}
            return JsonResponse(result_data)

    return JsonResponse({'status': 'error', 'data': ''}, status=403)


@csrf_exempt
@login_required
def clear_quote_translations(request):
    get_current_user(request)
    if request.method == 'POST':
        form = ClearQuoteTranslationsForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            quote_id = cd['quote_id']
            data_out = {}
            # for already existing quotes only - for the newly
            # added ones we just return translations
            if quote_id:
                wm = Quote.objects.get(id=quote_id)
                wm.quote_en = ""
                wm.quote_es = ""
                wm.quote_it = ""
                wm.quote_fr = ""
                wm.quote_ja = ""
                setattr(wm, f"quote_{wm.connected_venue.owner.lang.lower()}", wm.default_quote)
                wm.quote_translations = data_out
                wm.save()
                wm.refresh_from_db()
            result_data = {'status': 'OK', 'data': data_out}
            return JsonResponse(result_data)
    return JsonResponse({'status': 'error', 'data': {}})


@csrf_exempt
@login_required
def translate_testimonial(request):
    user = get_current_user(request)
    client = translate.Client()
    if request.method == 'POST':
        form = TranslateTestimonialForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            orig_lang = cd['orig_lang']
            contents_orig = cd['contents']
            testimonial_id = cd['testimonial_id']
            data_out = {
                'orig_lang': orig_lang,
                'orig_contents': contents_orig,
                'translations': {},
            }
            langs = get_selected_languages()
            langs.append(orig_lang)
            for lang in langs:
                if lang != orig_lang:
                    try:
                        contents_tr = client.translate(
                            contents_orig,
                            source_language=orig_lang,
                            target_language=lang,
                            format_='text'
                        )
                    except Forbidden as e:
                        return JsonResponse({
                            'status': 'error', 'data': e.message
                        }, status=403)
                    contents = contents_tr['translatedText']
                else:
                    contents = contents_orig

                url_author = reverse('edit_user', args=[user.id])
                data_out['translations'][lang] = {
                    'lang': lang,
                    'text': contents,
                    'author_id': user.id,
                    'author_username': user.username,
                    'modified_time': dt.datetime.now(),
                    'footer': '%s - by: <a href="%s">@%s</a>' % (
                        dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d'),
                        url_author,
                        user.username
                    )
                }

            # for already existing testimonials only - for the
            # newly added ones we just return translations
            if testimonial_id:
                wm = Testimonial.objects.get(id=testimonial_id)
                wm.testimonial_translations = data_out
                for i in ['en', 'it', 'fr', 'es', 'ja']:
                    setattr(wm, f'testimonial_{i}', data_out['translations'][i.upper()]['text'])
                wm.default_testimonial = contents_orig
                wm.save()
                wm.refresh_from_db()
            result_data = {'status': 'OK', 'data': data_out}
            return JsonResponse(result_data)

    return JsonResponse({'status': 'error', 'data': ''}, status=403)


@csrf_exempt
@login_required
def clear_testimonial_translations(request):
    get_current_user(request)
    if request.method == 'POST':
        form = ClearTestimonialTranslationsForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            testimonial_id = cd['testimonial_id']
            data_out = {}
            # for already existing testimonials only - for the newly
            # added ones we just return translations
            if testimonial_id:
                wm = Testimonial.objects.get(id=testimonial_id)
                wm.testimonial_en = ""
                wm.testimonial_es = ""
                wm.testimonial_it = ""
                wm.testimonial_fr = ""
                wm.testimonial_ja = ""
                setattr(wm, f"testimonial_{wm.connected_venue.owner.lang.lower()}", wm.default_testimonial)
                wm.testimonial_translations = data_out
                wm.save()
                wm.refresh_from_db()
            result_data = {'status': 'OK', 'data': data_out}
            return JsonResponse(result_data)
    return JsonResponse({'status': 'error', 'data': {}})


@csrf_exempt
@login_required
def translate_cheffe(request):
    user = get_current_user(request)
    client = translate.Client()
    if request.method == 'POST':
        form = TranslateCheffeForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            orig_lang = cd['orig_lang']
            contents_orig = cd['contents']
            cheffe_id = cd['cheffe_id']
            data_out = {
                'orig_lang': orig_lang,
                'orig_contents': contents_orig,
                'translations': {},
            }
            langs = get_selected_languages()
            langs.append(orig_lang)
            for lang in langs:
                if lang != orig_lang:
                    try:
                        contents_tr = client.translate(
                            contents_orig,
                            source_language=orig_lang,
                            target_language=lang,
                            format_='text'
                        )
                    except Forbidden as e:
                        return JsonResponse({
                            'status': 'error', 'data': e.message
                        }, status=403)
                    contents = contents_tr['translatedText']
                else:
                    contents = contents_orig

                url_author = reverse('edit_user', args=[user.id])
                data_out['translations'][lang] = {
                    'lang': lang,
                    'text': contents,
                    'author_id': user.id,
                    'author_username': user.username,
                    'modified_time': dt.datetime.now(),
                    'footer': '%s - by: <a href="%s">@%s</a>' % (
                        dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d'),
                        url_author,
                        user.username
                    )
                }

            # for already existing cheffes only - for the
            # newly added ones we just return translations
            if cheffe_id:
                wm = Cheffe.objects.get(id=cheffe_id)
                wm.cheffe_translations = data_out
                for i in ['en', 'it', 'fr', 'es', 'ja']:
                    setattr(wm, f'cheffe_{i}', data_out['translations'][i.upper()]['text'])
                wm.default_cheffe = contents_orig
                wm.save()
                wm.refresh_from_db()
            result_data = {'status': 'OK', 'data': data_out}
            return JsonResponse(result_data)

    return JsonResponse({'status': 'error', 'data': ''}, status=403)


@csrf_exempt
@login_required
def clear_cheffe_translations(request):
    get_current_user(request)
    if request.method == 'POST':
        form = ClearCheffeTranslationsForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            cheffe_id = cd['cheffe_id']
            data_out = {}
            # for already existing cheffes only - for the newly
            # added ones we just return translations
            if cheffe_id:
                wm = Cheffe.objects.get(id=cheffe_id)
                wm.cheffe_en = ""
                wm.cheffe_es = ""
                wm.cheffe_it = ""
                wm.cheffe_fr = ""
                wm.cheffe_ja = ""
                setattr(wm, f"cheffe_{wm.connected_venue.owner.lang.lower()}", wm.default_cheffe)
                wm.cheffe_translations = data_out
                wm.save()
                wm.refresh_from_db()
            result_data = {'status': 'OK', 'data': data_out}
            return JsonResponse(result_data)
    return JsonResponse({'status': 'error', 'data': {}})


@csrf_exempt
@login_required
def testimonials_autocomplete(request):
    items = [{"text": f"{i.default_username} - {i.default_title}",
              "id": i.id}for i in Testimonial.objects.filter(
                  testimonial_fetured__isnull=True, deleted=False, is_archived=False).distinct()]
    return JsonResponse({'items': items})
