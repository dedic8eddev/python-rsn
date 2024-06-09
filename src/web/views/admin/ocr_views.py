import logging
import os

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, mixins
from rest_framework.permissions import IsAuthenticated

from my_celery.tasks import ocr_recognize, \
    ocr_calculate_and_save_user_edited_text
from web.constants import WineListStatusE
from web.forms.admin_forms import OCRFileForm, OCRIncludeForm, \
    OCRUserApprovedTextForm
from web.models import WineList, WineListFile, NWLAExcludedWord
from web.serializers.nwla import ExcludedWordSerializer
from web.utils.ocr.scores import recalc_by_row_score
from web.utils.ocr_tools import get_text_rows, get_score
from web.utils.views_common import get_current_user
from web.views.admin.common import get_c

log = logging.getLogger(__name__)


# /ocr
@login_required
def ocrpoc(request):
    bc_path = [
        ('/', 'Home'),
        (reverse('ocrpoc'), 'OCR')
    ]
    c = get_c(request=request, active='ocrpoc', path=None, bc_path_alt=bc_path)

    all_scores = []
    is_result = False
    filename = None

    if request.method == 'GET':
        form = OCRFileForm()

        c["form"] = form
        c['all_scores'] = all_scores
        c['filename'] = filename
        c['is_result'] = is_result
        c['action_url'] = reverse('ocrpoc')
        return render(request, "ocr/ocrpoc.html", c)


# /ajax/ocr-recognize-task-create/
@login_required
@csrf_exempt
def ocr_recognize_task_create(request):
    user = get_current_user(request)

    if request.method == 'POST':
        form = OCRFileForm(request.POST, request.FILES)
        if form.is_valid():
            images = request.FILES.getlist('image')
            if images:
                wl_params = {
                    'status': WineListStatusE.ON_HOLD
                }

                winelist = WineList.objects.create(**wl_params)
                request.session['winelist_id'] = winelist.id

                file_data = {
                    'author': user,
                    'winelist': winelist,
                    'image_file': images[0]
                }

                file = WineListFile(**file_data)
                file.save()
                ocr_celery_task = ocr_recognize.delay(file.id)
                return JsonResponse(
                    {
                        'ocr_recognize_celery_task_id': ocr_celery_task.id,
                        'winelist_file_id': file.id
                    }
                )
        else:
            return JsonResponse(
                {'details': 'winelist file content is invalid. Try another '
                            'file!'
                 },
                status=400)


# /ajax/ocr-calc-task-create/
@login_required
@csrf_exempt
def ocr_calc_task_create(request):
    if request.method == 'POST':
        form = OCRUserApprovedTextForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            wl_file_id = cd['winelist_file_id']
            wl_file = WineListFile.active.get(pk=wl_file_id)

            if cd.get('text'):  # initial evaluation and editing text
                # for already uploaded and evaluated wine list uses text
                # argument to alter text.
                # Re-evaluation does not use text argument.

                # clean moderated indexes because initial text can be
                # changed in case of non-initial evaluation
                if wl_file.winelist.total_score_data:
                    for item in wl_file.winelist.total_score_data.get('rows_out'):
                        item['moderated'] = False
                    wl_file.winelist.save()

                # save ocr-text in case of initial evaluation
                ocr_text = cd['text'].strip().replace('\t', ' ').replace('\n\n', '\n').replace('  ', ' ')
                ocr_text_split = [x.strip() for x in ocr_text.splitlines() if x not in ['', ' ']]
                wl_file.item_text_rows = ocr_text_split
                wl_file.save()

            # Pass the index of the row, if exists, in which the word was
            # excluded to trigger current re-evaluation.
            new_exclusion_word_row = cd.get('new_exclusion_word_row') if \
                cd.get('new_exclusion_word_row') else None

            # calculate score
            ocr_celery_task = ocr_calculate_and_save_user_edited_text.delay(
                wl_file_id,
                new_exclusion_word_row
            )
            return JsonResponse(
                {
                    'ocr_calc_celery_task_id': ocr_celery_task.id,
                    'winelist_file_id': wl_file_id
                }
            )
        else:
            return JsonResponse(
                {'details': 'form is not valid / incoming data is invalid'},
                status=400)


# /ajax/ocr-recognize-task-status/
@login_required
def ocr_recognize_task_status(request):
    if request.method == 'GET':
        task_id = request.GET['ocr_celery_task_id']
        task_status = ocr_recognize.AsyncResult(task_id).status
        return JsonResponse(
            {
                'ocr_recognize_celery_task_id': task_id,
                'ocr_recognize_celery_task_status': task_status
            }
        )


# /ajax/ocr-calc-task-status/
@login_required
def ocr_calc_task_status(request):
    if request.method == 'GET':
        task_id = request.GET['ocr_celery_task_id']
        task_status = ocr_calculate_and_save_user_edited_text.AsyncResult(
            task_id).status
        return JsonResponse(
            {
                'ocr_calc_celery_task_id': task_id,
                'ocr_calc_celery_task_status': task_status
            }
        )


# /ajax/ocr-recognize-task-result/
@login_required
def ocr_recognize_task_result(request):
    if request.method == 'GET':
        wl_file_id = request.GET['winelist_file_id']
        wl_file = WineListFile.active.get(id=wl_file_id)

        return JsonResponse(
            {
                'winelist_file_id': wl_file_id,
                'ocred_text_rows': wl_file.item_text_rows
            }
        )


# /ajax/ocr-calc-task-result/
@login_required
def ocr_calc_result(request):
    if request.method == 'GET':
        wl_file_id = request.GET['winelist_file_id']
        wl_file = WineListFile.active.get(id=wl_file_id)

        return JsonResponse(
            {
                'filename': wl_file.image_file.name,
                'all_scores': wl_file.winelist.total_score_data
            }
        )


# /ajax/ocred-text/
@login_required
@csrf_exempt
def ocred_text(request):
    user = get_current_user(request)

    if request.method == 'POST':
        form = OCRFileForm(request.POST, request.FILES)
        if form.is_valid():
            images = request.FILES.getlist('image')
            if images:
                wl_params = {
                    'status': WineListStatusE.ON_HOLD
                }

                winelist = WineList.objects.create(**wl_params)
                request.session['winelist_id'] = winelist.id

                file_data = {
                    'author': user,
                    'winelist': winelist,
                    'image_file': images[0]
                }

                file = WineListFile(**file_data)
                file.save()
                ocred_text_rows = get_text_rows(file.image_file)
                file.item_text_rows = ocred_text_rows
                file.save()
                return JsonResponse(
                    {
                        'winelist_file_id': file.id,
                        'ocred_text_rows': ocred_text_rows
                    }
                )


# /ajax/ocr-save
# save a winelist edited by user and calculate a score for it
@login_required
@csrf_exempt
def ocr_save_edited_wl(request):
    if request.method == 'POST':
        form = OCRUserApprovedTextForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            wl_file_id = cd['winelist_file_id']
            wl_file = WineListFile.active.get(pk=wl_file_id)

            if cd.get('text'):  # initial evaluation and editing text
                # for already uploaded and evaluated wine list uses text
                # argument to alter text
                # re-evaluation does not use text argument

                # clean moderated indexes because initial text can be
                # changed in case of non-initial evaluation
                if wl_file.winelist.total_score_data:
                    for item in wl_file.winelist.total_score_data.get(
                            'rows_out'):
                        item['moderated'] = False
                    wl_file.winelist.save()

                # save ocr-text in case of initial evaluation
                wl_file.item_text_rows = cd['text'].splitlines()
                wl_file.save()

            # Pass the index of the row, if exists, in which the word was
            # excluded to trigger current re-evaluation.
            new_exclusion_word_row = cd.get('new_exclusion_word_row') if \
                cd.get('new_exclusion_word_row') else None

            # calculate score
            moderated_indexes = {}
            if wl_file.winelist.total_score_data:
                for item in wl_file.winelist.total_score_data.get('rows_out'):
                    if item.get('moderated'):
                        moderated_indexes.update({item['ind']: item['status']})
            sc = get_score(wl_file.item_text_rows,
                           moderated_indexes=moderated_indexes,
                           new_exclusion_word_row=new_exclusion_word_row)
            sc['file'] = os.path.basename(wl_file.image_file.name)
            wl_file.winelist.total_score_data = sc
            wl_file.winelist.save()
            if sc:
                return JsonResponse(
                    {
                        'filename': sc['file'],
                        'all_scores': [sc]
                    }
                )


# /ajax/ocr-recalc
# just instead of /ajax/ocr/recalc
# because of another output format
@login_required
def ocr_recalc(request):
    if request.method == 'POST':
        form = OCRIncludeForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            winelist_id = request.session.get('winelist_id', None)
            if not winelist_id:
                return JsonResponse({'Error:': 'no winelist_id'})
            wl = WineList.objects.get(pk=winelist_id)
            sc = recalc_by_row_score(wl.total_score_data, cd['incs'])
            if sc:
                return JsonResponse(
                    {
                        'filename': sc['file'],
                        'all_scores': [sc]
                    }
                )


# /ajax/ocr/recalc
@csrf_exempt
@login_required
def ocrrecalc(request):
    c = {'all_scores': None, 'file': None}
    if request.method == 'POST':
        form = OCRIncludeForm(request.POST, request.FILES)

        if form.is_valid():
            cd = form.cleaned_data
            winelist_id = request.session.get('winelist_id', None)

            if not winelist_id:
                return render(request, "ocr/results.html", c)

            wl = WineList.objects.get(pk=winelist_id)
            sc = recalc_by_row_score(wl.total_score_data, cd['incs'])
            if sc:
                c['filename'] = sc['file']
                c['all_scores'] = [sc]
    return render(request, "ocr/results.html", c)


# ajax/nwla/excluded-keywords/{pk}
class ExcludedKeyword(mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      mixins.DestroyModelMixin,
                      generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = None
    serializer_class = ExcludedWordSerializer
    queryset = NWLAExcludedWord.objects.all()

    @swagger_auto_schema(
        security=[],
        operation_summary='Return NWLA exceptions.',
        operation_description='Return all NWLA excluded keywords.'
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @swagger_auto_schema(
        security=[],
        request_body=ExcludedWordSerializer,
        operation_summary='Create NWLA exception.',
        operation_description='Create a new word to be excepted from NWLA '
                              'processing.'
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    @swagger_auto_schema(
        security=[],
        operation_summary='Delete NWLA exception.',
        operation_description='Remove any keyword previously excluded from '
                              'NWLA processing by this keyword\'s ID.'
    )
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
