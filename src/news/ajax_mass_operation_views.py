from __future__ import absolute_import
import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .constants import NewsStatus
from .forms import MassOperationIdsFeaturedVenueForm, MassOperationIdsNewsForm, \
    MassOperationIdsLPBForm, MassOperationIdsQuoteForm, MassOperationIdsCheffeForm, \
    MassOperationIdsTestimonialForm
from .models import FeaturedVenue, News, LPB, Quote, Cheffe, Testimonial
from web.utils.views_common import get_current_user

log = logging.getLogger(__name__)


def news_mass_operation_status(request, FormClass, status):
    data = {"ids": []}
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            for item in cd['ids']:
                if item.deleted:
                    continue
                data["ids"].append(item.id)
                item.change_status(modifier_user=request.user, status=status)
    return {
        "status": "OK",
        "data": data
    }


def merge(request, FormClass, ModelClass):
    data = {"ids": []}
    form = FormClass(request.POST)
    item_list = []

    if form.is_valid():
        cd = form.cleaned_data
        item_list = cd['ids']
    main = item_list.order_by("-id").first()
    for item in item_list:
        if int(item.status_en) == NewsStatus.PUBLISHED:
            main.status_en = NewsStatus.PUBLISHED
        if int(item.status_es) == NewsStatus.PUBLISHED:
            main.status_es = NewsStatus.PUBLISHED
        if int(item.status_fr) == NewsStatus.PUBLISHED:
            main.status_fr = NewsStatus.PUBLISHED
        if int(item.status_it) == NewsStatus.PUBLISHED:
            main.status_it = NewsStatus.PUBLISHED
        if int(item.status_ja) == NewsStatus.PUBLISHED:
            main.status_ja = NewsStatus.PUBLISHED
        if item.title_en:
            main.title_en = item.title_en
        if item.title_es:
            main.title_es = item.title_es
        if item.title_fr:
            main.title_fr = item.title_fr
        if item.title_it:
            main.title_it = item.title_it
        if item.title_ja:
            main.title_ja = item.title_ja
        if item.meta_description_en:
            main.meta_description_en = item.meta_description_en
        if item.meta_description_es:
            main.meta_description_es = item.meta_description_es
        if item.meta_description_fr:
            main.meta_description_fr = item.meta_description_fr
        if item.meta_description_it:
            main.meta_description_it = item.meta_description_it
        if item.meta_description_ja:
            main.meta_description_ja = item.meta_description_ja
        if item.content_en:
            main.content_en = item.content_en
        if item.content_es:
            main.content_es = item.content_es
        if item.content_fr:
            main.content_fr = item.content_fr
        if item.content_it:
            main.content_it = item.content_it
        if item.content_ja:
            main.content_ja = item.content_ja
        if item.id != main.id:
            item.deleted = True
            item.is_archived = True
            item.save()
    main.last_editor = request.user
    main.save()
    data["ids"] = [main.id, ]
    return JsonResponse({
        "status": "OK",
        "data": data,
        "count": ModelClass.objects.filter(deleted=False).count()
    })


# /ajax/news/publish
@csrf_exempt
@login_required
def news_publish(request):
    get_current_user(request)
    result = news_mass_operation_status(request, MassOperationIdsNewsForm, NewsStatus.PUBLISHED)
    result['count'] = News.objects.filter(deleted=False).count()
    return JsonResponse(result)


# /ajax/news/delete
@csrf_exempt
@login_required
def news_delete(request):
    get_current_user(request)
    result = news_mass_operation_status(request, MassOperationIdsNewsForm, NewsStatus.DELETED)
    result['count'] = News.objects.filter(deleted=False).count()
    return JsonResponse(result)


# /ajax/news/unpublish
@csrf_exempt
@login_required
def news_unpublish(request):
    get_current_user(request)
    result = news_mass_operation_status(request, MassOperationIdsNewsForm, NewsStatus.DRAFT)
    result['count'] = News.objects.filter(deleted=False).count()
    return JsonResponse(result)


# /ajax/lpb/publish
@csrf_exempt
@login_required
def lpb_publish(request):
    get_current_user(request)
    result = news_mass_operation_status(request, MassOperationIdsLPBForm, NewsStatus.PUBLISHED)
    result['count'] = LPB.objects.filter(deleted=False).count()
    return JsonResponse(result)


# /ajax/lpb/delete
@csrf_exempt
@login_required
def lpb_delete(request):
    get_current_user(request)
    result = news_mass_operation_status(request, MassOperationIdsLPBForm, NewsStatus.DELETED)
    result['count'] = LPB.objects.filter(deleted=False).count()
    return JsonResponse(result)


# /ajax/lpb/unpublish
@csrf_exempt
@login_required
def lpb_unpublish(request):
    get_current_user(request)
    result = news_mass_operation_status(request, MassOperationIdsLPBForm, NewsStatus.DRAFT)
    result['count'] = LPB.objects.filter(deleted=False).count()
    return JsonResponse(result)


# /ajax/featured_venue/publish
@csrf_exempt
@login_required
def featured_venue_publish(request):
    get_current_user(request)
    result = news_mass_operation_status(request, MassOperationIdsFeaturedVenueForm, NewsStatus.PUBLISHED)
    result['count'] = FeaturedVenue.objects.filter(deleted=False).count()
    return JsonResponse(result)


# /ajax/featured_venue/publish
@csrf_exempt
@login_required
def featured_venue_delete(request):
    get_current_user(request)
    result = news_mass_operation_status(request, MassOperationIdsFeaturedVenueForm, NewsStatus.DELETED)
    result['count'] = FeaturedVenue.objects.filter(deleted=False).count()
    return JsonResponse(result)


# /ajax/featured_venue/unpublish
@csrf_exempt
@login_required
def featured_venue_unpublish(request):
    get_current_user(request)
    result = news_mass_operation_status(request, MassOperationIdsFeaturedVenueForm, NewsStatus.DRAFT)
    result['count'] = FeaturedVenue.objects.filter(deleted=False).count()
    return JsonResponse(result)


# /ajax/featured-venue/merge
@csrf_exempt
@login_required
def featured_venue_merge(request):
    get_current_user(request)
    return merge(request, MassOperationIdsFeaturedVenueForm, ModelClass=FeaturedVenue)


# /ajax/featured-venue/merge
@csrf_exempt
@login_required
def news_merge(request):
    get_current_user(request)
    return merge(request=request, FormClass=MassOperationIdsNewsForm, ModelClass=News)


# /ajax/quote/publish
@csrf_exempt
@login_required
def quote_publish(request):
    get_current_user(request)
    result = news_mass_operation_status(request, MassOperationIdsQuoteForm, NewsStatus.PUBLISHED)
    result['count'] = Quote.objects.filter(deleted=False).count()
    return JsonResponse(result)


# /ajax/quote/publish
@csrf_exempt
@login_required
def quote_delete(request):
    get_current_user(request)
    result = news_mass_operation_status(request, MassOperationIdsQuoteForm, NewsStatus.DELETED)
    result['count'] = Quote.objects.filter(deleted=False).count()
    return JsonResponse(result)


# /ajax/quote/unpublish
@csrf_exempt
@login_required
def quote_unpublish(request):
    get_current_user(request)
    result = news_mass_operation_status(request, MassOperationIdsQuoteForm, NewsStatus.DRAFT)
    result['count'] = Quote.objects.filter(deleted=False).count()
    return JsonResponse(result)


# /ajax/cheffe/publish
@csrf_exempt
@login_required
def cheffe_publish(request):
    get_current_user(request)
    result = news_mass_operation_status(request, MassOperationIdsCheffeForm, NewsStatus.PUBLISHED)
    result['count'] = Cheffe.objects.filter(deleted=False).count()
    return JsonResponse(result)


# /ajax/cheffe/publish
@csrf_exempt
@login_required
def cheffe_delete(request):
    get_current_user(request)
    result = news_mass_operation_status(request, MassOperationIdsCheffeForm, NewsStatus.DELETED)
    result['count'] = Cheffe.objects.filter(deleted=False).count()
    return JsonResponse(result)


# /ajax/cheffe/unpublish
@csrf_exempt
@login_required
def cheffe_unpublish(request):
    get_current_user(request)
    result = news_mass_operation_status(request, MassOperationIdsCheffeForm, NewsStatus.DRAFT)
    result['count'] = Cheffe.objects.filter(deleted=False).count()
    return JsonResponse(result)


# /ajax/testimonial/publish
@csrf_exempt
@login_required
def testimonial_publish(request):
    get_current_user(request)
    result = news_mass_operation_status(request, MassOperationIdsTestimonialForm, NewsStatus.PUBLISHED)
    result['count'] = Testimonial.objects.filter(deleted=False).count()
    return JsonResponse(result)


# /ajax/testimonial/publish
@csrf_exempt
@login_required
def testimonial_delete(request):
    get_current_user(request)
    result = news_mass_operation_status(request, MassOperationIdsTestimonialForm, NewsStatus.DELETED)
    result['count'] = Testimonial.objects.filter(deleted=False).count()
    return JsonResponse(result)


# /ajax/testimonial/unpublish
@csrf_exempt
@login_required
def testimonial_unpublish(request):
    get_current_user(request)
    result = news_mass_operation_status(request, MassOperationIdsTestimonialForm, NewsStatus.DRAFT)
    result['count'] = Testimonial.objects.filter(deleted=False).count()
    return JsonResponse(result)
