from __future__ import absolute_import

import datetime as dt
import json
import logging
import uuid

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from google.api_core.exceptions import Forbidden
from google.cloud import translate

from web.constants import get_selected_languages
from web.forms.admin_forms import (ClearDomainDescriptionTranslationsForm,
                                   TranslateDomainDescriptionForm,
                                   UpdateDomainDescriptionForm,
                                   WineItemHandlingForm)
from web.forms.common import ResetUserPasswordForm
from web.models import UserProfile, Winemaker
from web.utils.message_utils import EmailCollection
from web.utils.views_common import get_current_user

log = logging.getLogger(__name__)


@csrf_exempt
@login_required
def get_add_wine_widget(request, initial_row_number=0):
    get_current_user(request)

    tpl = 'base/elements/edit/winemaker.wine-add-widget.form.html'
    c = {}

    form = WineItemHandlingForm(None, initial_row_number=initial_row_number)

    wine_temp_dir = uuid.uuid4()
    form.wines.init_items()
    form.wines.add_clean_item(fv_to_set={"wine_temp_dir": wine_temp_dir})

    c['form'] = form

    return render(request, tpl, c)


@csrf_exempt
@login_required
def reset_password(request):
    if request.method == 'POST':
        action = request.POST.get('action', None)
        form = ResetUserPasswordForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']

            # will throw DoesNotExist error catched by api_handling if
            # user does not exist, it was intended so
            users = UserProfile.active.filter(email=username)
            if users:
                user = users[0]
            else:
                users = UserProfile.active.filter(username=username)
                if users:
                    user = users[0]
                else:
                    return JsonResponse({'status': 'ERROR'})

            if not action:
                EmailCollection().send_reset_password_email(user)
            elif action == 'resend_activation':
                EmailCollection().send_activation_email(user)

            result_data = {'status': 'OK'}
            return JsonResponse(result_data)


@csrf_exempt
@login_required
def translate_domain_description(request):
    user = get_current_user(request)
    client = translate.Client()
    if request.method == 'POST':
        form = TranslateDomainDescriptionForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            orig_lang = cd['orig_lang']
            contents_orig = cd['contents']
            winemaker_id = cd['winemaker_id']
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

            # for already existing winemakers only - for the
            # newly added ones we just return translations
            if winemaker_id:
                wm = Winemaker.objects.get(id=winemaker_id)
                wm.domain_description_translations = data_out
                wm.domain_description = contents_orig
                wm.save()
                wm.refresh_from_db()

            result_data = {'status': 'OK', 'data': data_out}
            return JsonResponse(result_data)

    return JsonResponse({'status': 'error', 'data': ''}, status=403)


@csrf_exempt
@login_required
def update_domain_description_translations(request):
    user = get_current_user(request)
    if request.method == 'POST':
        form = UpdateDomainDescriptionForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            lang = cd['lang']
            contents = cd['contents']
            str_trans = cd['str_trans']

            if not str_trans or str_trans == "":
                return JsonResponse(
                    {"exception": "No data in str_trans is provided."},
                    status=400
                )

            data_out = json.loads(str_trans)
            data_out['translations'][lang]['text'] = contents
            data_out['translations'][lang]['author_id'] = user.id
            data_out['translations'][lang]['author_username'] = user.username
            data_out['translations'][lang]['modified_time'] = dt.datetime.now()

            for l, item in data_out['translations'].items():  # noqa: E741
                url_author = reverse('edit_user', args=[item['author_id']])
                data_out['translations'][l][
                    'footer'
                ] = '%s - by: <a href="%s">@%s</a>' % (
                    dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d'),
                    url_author,
                    item['author_username']
                )

            # turned off on Bretin's request at 26.06.2019
            # if winemaker_id:  # for already existing winemakers only -
            #  for the newly
            #     # added ones we just return translations
            #     wm = Winemaker.objects.get(id=winemaker_id)
            #     wm.domain_description_translations = data_out
            #     wm.save()
            #     wm.refresh_from_db()
            result_data = {'status': 'OK', 'data': data_out}
            return JsonResponse(result_data)
    return JsonResponse({'status': 'error', 'data': {}})


@csrf_exempt
@login_required
def clear_domain_description_translations(request):
    get_current_user(request)
    if request.method == 'POST':
        form = ClearDomainDescriptionTranslationsForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            winemaker_id = cd['winemaker_id']
            data_out = {}
            # for already existing winemakers only - for the newly
            # added ones we just return translations
            if winemaker_id:
                wm = Winemaker.objects.get(id=winemaker_id)
                wm.domain_description_translations = data_out
                wm.save()
                wm.refresh_from_db()
            result_data = {'status': 'OK', 'data': data_out}
            return JsonResponse(result_data)
    return JsonResponse({'status': 'error', 'data': {}})
