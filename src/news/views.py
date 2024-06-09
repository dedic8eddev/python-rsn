from asyncio.log import logger
import datetime as dt
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from web.constants import PostStatusE, StatusE
from web.models.images import EventImage
from web.models.models import CalEvent, UserProfile
from .constants import WEBSITE_PAGES, NewsStatus
from .forms import FeaturedVenueAdminForm, NewsAdminForm, WebsitePageAdminForm, LPBAdminForm, QuoteAdminForm, \
    CheffeAdminForm, TestimonialAdminForm
from .models import FeaturedVenue, FeaturedVenueImage, NewsImage, News, WebsitePage, \
    WebsitePageImage, LPBImage, LPB, Quote, QuoteImage, FeaturedQuote, Cheffe, CheffeImage, \
    Testimonial, TestimonialImage, FeaturedTestimonial, FeaturedCheffe
from web.views.admin.common import get_c
from django.db.models import Q
from django.http import JsonResponse
from web.forms.admin_forms import AjaxListForm
from web.utils.exceptions import WrongParametersError
from web.utils.upload_tools import aws_url
from web.utils.views_common import get_search_value, get_sorting
from web.views.ajax_lists.common import ajax_list_control_parameters_by_form
from web.forms.admin_forms import EventRelatedListForm
from web.models import Comment, LikeVote
from web.serializers.comments_likes import CommentSerializer, LikeVoteSerializer
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
import json
import requests
from django.core.files import File
from web.models.models import Place
from web.models.images import PlaceImage
from raisin.settings import RAISIN_NEW_WEBSITE


def get_counts():
    return {
        "news_count": News.objects.count(),
        "fv_count": FeaturedVenue.objects.count(),
        "lpb_count": LPB.objects.count(),
        "wp_count": WebsitePage.objects.count(),
    }


@login_required
def news(request):
    c = get_c(
        request=request, active='list_news',
        path='/news', add_new_url='add_news'
    )
    c['bc_path'] = [
        ('/', 'Home'),
        (reverse('list_news'), 'News'),
    ]
    c['counts'] = get_counts()
    return render(request, "lists/news.html", c)


def get_common_news_pdg_options(include_delete=True):
    opts_in = NewsStatus.names
    result = [
        {
            'value': NewsStatus.DRAFT,
            'name': opts_in[NewsStatus.DRAFT],
            'class': 'onhold', 'selclass': 'onhold'
        },
        {
            'value': NewsStatus.PUBLISHED,
            'name': opts_in[NewsStatus.PUBLISHED],
            'class': 'btincluded', 'selclass': 'included'
        },
    ]

    if include_delete:
        result.append(
            {
                'value': NewsStatus.DELETED,
                'name': _("Delete"),
                'class': 'btrefused', 'selclass': 'refused'
            }
        )

    return result


def get_language_options():
    result = [
        {
            'value': "en",
            'name': "English"
        },
        {
            'value': "fr",
            'name': "Français"
        },
        {
            'value': "ja",
            'name': "日本語"
        },
        {
            'value': "it",
            'name': "Italiano"
        },
        {
            'value': "es",
            'name': "Castellano"
        },
    ]
    return result


def get_type_options():
    result = [
        {
            'value': "news",
            'name': "News"
        },
        {
            'value': "featured_venue",
            'name': "Featured Venue"
        }
    ]
    return result


@csrf_protect
@login_required
def add_news(request):
    c = get_c(request=request, active='list_news', path='/add')
    c['bc_path'] = [
        ('/', 'Home'),
        (reverse('list_news'), 'News'),
        (reverse('add_news'), "Add")
    ]
    news = News(author=c['current_user'])

    if request.method == 'POST':
        form = NewsAdminForm(request.POST, instance=news)
        if form.is_valid():
            cd = form.cleaned_data
            images = request.FILES.getlist('image')
            news.last_editor = c['current_user']
            news.updated_at = dt.datetime.now()
            news.name = cd['title']
            setattr(news, f"title_{cd['language']}", cd['title'])
            setattr(news, f"meta_description_{cd['language']}", cd['meta_description'])
            setattr(news, f"content_{cd['language']}", cd['content'])
            setattr(news, f"status_{cd['language']}", cd['status'])
            news.save()
            if images:
                news_image = NewsImage(image_file=images[0], event_id=news.id)
                news_image.save()
                news.image = news_image

            news.save()
            news.refresh_from_db()

            messages.add_message(
                request, messages.INFO, "News {} saved.".format(news.name)
            )

            return redirect('edit_news', news.id, cd['language'])
    else:
        form = NewsAdminForm(instance=news, initial={"status": NewsStatus.DRAFT, 'language': "en", "type": "news"})
    c['form'] = form
    c['news'] = news
    c['languages'] = get_language_options()
    c['action_url'] = reverse('add_news')
    c['pdg_title'] = "[New News]"
    c["pdg_options"] = get_common_news_pdg_options(include_delete=False)
    c["max_upload_size"] = int(NewsAdminForm.MAX_UPLOAD_SIZE / 1000)
    return render(request, "edit/news.html", c)


@csrf_protect
@login_required
def edit_news(request, id, language):
    news = News.objects.get(id=id)
    bc_path = [
        ('/', 'Home'),
        (reverse('list_news'), 'News'),
        (reverse('edit_news', args=[id, language]), news.name),
    ]
    c = get_c(
        request=request, active='list_news',
        path=None, bc_path_alt=bc_path
    )
    if request.method == 'POST':
        form = NewsAdminForm(request.POST, instance=news)
        if form.is_valid():
            cd = form.cleaned_data
            images = request.FILES.getlist('image')
            news.last_editor = c['current_user']
            news.updated_at = dt.datetime.now()
            if cd['status'] == NewsStatus.DELETED:
                setattr(news, f"title_{cd['language']}", "")
                setattr(news, f"meta_description_{cd['language']}", "")
                setattr(news, f"content_{cd['language']}", "")
                setattr(news, f"status_{cd['language']}", NewsStatus.DRAFT)
            else:
                setattr(news, f"title_{cd['language']}", cd['title'])
                setattr(news, f"meta_description_{cd['language']}", cd['meta_description'])
                setattr(news, f"content_{cd['language']}", cd['content'])
                setattr(news, f"status_{cd['language']}", cd['status'])
            if cd['language'] != language:
                setattr(news, f"title_{language}", "")
                setattr(news, f"meta_description_{language}", "")
                setattr(news, f"content_{language}", "")
                setattr(news, f"status_{language}", NewsStatus.DRAFT)
            news.save()
            if images:
                news_image = NewsImage(image_file=images[0], event_id=news.id)
                news_image.save()
                news.image = news_image
            news.save()
            if cd['type'] == "featured_venue":
                featured_venue = FeaturedVenue()
                for i in news._meta.fields:
                    if i.name not in ['image', 'id']:
                        if i.name.startswith("status"):
                            setattr(featured_venue, f"status_{language}", NewsStatus.DRAFT)
                        else:
                            setattr(featured_venue, i.name, getattr(news, i.name))
                featured_venue.save()
                if news.image:
                    featured_venue_image = FeaturedVenueImage()
                    featured_venue_image.featured_venue = featured_venue
                    for i in news.image._meta.fields:
                        if i.name not in ['featured_venue', 'id', "news"]:
                            setattr(featured_venue_image, i.name, getattr(news.image, i.name))
                    featured_venue_image.save()
                    featured_venue.image = featured_venue_image
                    featured_venue.save()
                news.comments.all().update(news=None, featured_venue=featured_venue)
                news.deleted = True
                news.is_archived = True
                news.save()
                news.refresh_from_db()

                messages.add_message(request, messages.INFO, "Featured Venue {} updated.".format(featured_venue.name))
                return redirect('edit_featured_venue', featured_venue.id, cd['language'])
            news.refresh_from_db()

            messages.add_message(request, messages.INFO, "News {} updated.".format(news.name))
            return redirect('edit_news', news.id, cd['language'])
    else:
        form = NewsAdminForm(instance=news,
                             initial={'language': language,
                                      "status": getattr(news, "status_" + language),
                                      "title": getattr(news, "title_" + language),
                                      "meta_description": getattr(news, "meta_description_" + language),
                                      "content": getattr(news, "content_" + language),
                                      "type": "news"})
    c['form'] = form
    c['news'] = news
    c['languages'] = [i for i in get_language_options() if i['value'] != language]
    c['current_language'] = [i for i in get_language_options() if i['value'] == language][0]
    c['types'] = get_type_options()
    c['action_url'] = reverse('edit_news', args=[news.id, language])
    c['pdg_title'] = f"{news.name} : <b>{[i for i in get_language_options() if i['value'] == language][0]['name']}</b>"
    c["pdg_options"] = get_common_news_pdg_options(include_delete=True)
    c["max_upload_size"] = int(NewsAdminForm.MAX_UPLOAD_SIZE / 1000)
    c['saved_by'] = news.last_editor
    c['saved_at'] = news.created_at
    c['updated_at'] = news.updated_at
    authority = None if news.external_id else news.author
    c['authority_name'] = authority.username if authority else 'External user'
    c['authority_id'] = authority.id if authority else None
    c['authority_avatar_url'] = aws_url(authority.image, thumb=True) if authority else None
    c['image'] = aws_url(news.image)
    slug = getattr(news, "slug_" + language)
    c['new_raisin_url'] = f"{RAISIN_NEW_WEBSITE}/{language}/news/{slug}/"
    return render(request, "edit/news.html", c)


# /ajax/news/items
@csrf_exempt
@login_required
def get_news_items(request):
    page = None
    limit = None
    order_dir = 'desc'
    order_by = '-updated_at'
    start = None
    length = None
    search_value = None
    col_map = {
        0: 'id',
        1: None,
        2: 'created_at',
        3: None,
        4: 'name',  # name
        5: None,
        6: None,
        7: None,
        8: None
    }

    if request.method == 'POST':
        form = AjaxListForm(request.POST)
        search_value = get_search_value(request)
        order_by = get_sorting(request, col_map, order_by, order_dir)
        if form.is_valid():
            cd = form.cleaned_data
            start = cd['start']
            length = cd['length']
            (page, limit, order_by_old, order_dir_old) = ajax_list_control_parameters_by_form(cd)
        else:
            raise WrongParametersError(_("Wrong parameters."), form)

    filter_criteria = Q()

    if search_value is not None:
        filter_criteria = (
            Q(meta_description_en__unaccent__icontains=search_value) |
            Q(title_en__unaccent__icontains=search_value) |
            Q(meta_description_fr__unaccent__icontains=search_value) |
            Q(title_fr__unaccent__icontains=search_value) |
            Q(meta_description_it__unaccent__icontains=search_value) |
            Q(title_it__unaccent__icontains=search_value) |
            Q(meta_description_es__unaccent__icontains=search_value) |
            Q(title_es__unaccent__icontains=search_value) |
            Q(meta_description_ja__unaccent__icontains=search_value) |
            Q(title_ja__unaccent__icontains=search_value) |
            Q(name__unaccent__icontains=search_value) |
            Q(author__username__unaccent__icontains=search_value)
        )
    if limit:
        offset_0 = page * limit - limit
        offset_n = page * limit
    elif start is not None and length is not None:
        offset_0 = start
        offset_n = start + length
    else:
        offset_0 = None
        offset_n = None

    qs = News.objects.filter(filter_criteria).filter(deleted=False)

    total_count = qs.count()
    news_ = qs.order_by(order_by)[offset_0:offset_n]
    items_out = []

    for news in news_:
        img_template = '<a href="{}" data-toggle="lightbox"><img width="70" height="70" src="{}" /></a>'
        img_html = img_template.format(
            aws_url(news.image), aws_url(news.image, thumb=True)
        )
        author_template = '<img width="35" height="35" src="{}" data-src="{}" alt="{}" style="border-radius:50%">'
        if news.author:
            author_img_html = author_template.format(
                aws_url(news.author.image, thumb=True),
                aws_url(news.author.image, thumb=True),
                news.author.username
            )
        else:
            author_img_html = ""
        checkbox_template = '<input id="colors-%d-toggle-1" name="ids" value="{id}" type="checkbox">'
        checkbox = checkbox_template.format(id=news.id)
        _string1 = '<a href="/news/edit/'
        _string = ' data-toggle="tooltip" title="" data-placement="bottom"> <i class="fa fa-edit"></i> </a>'
        status_en = f'{_string1}{news.id}/en" class="{get_status(news.status_en, news.content_en)}"{_string}'
        status_fr = f'{_string1}{news.id}/fr" class="{get_status(news.status_fr, news.content_fr)}"{_string}'
        status_ja = f'{_string1}{news.id}/ja" class="{get_status(news.status_ja, news.content_ja)}"{_string}'
        status_it = f'{_string1}{news.id}/it" class="{get_status(news.status_it, news.content_it)}"{_string}'
        status_es = f'{_string1}{news.id}/es" class="{get_status(news.status_es, news.content_es)}"{_string}'
        item_out = {
            'checkbox_id': checkbox,
            'news_img_html': img_html,
            'author_img_html': author_img_html,
            'title': news.name,
            'type': "<button class='badge' style='margin: 2px;'>News</button>",
            'date': news.created_at.strftime('%d %b %Y %H:%M'),
            'status_en': status_en,
            'status_fr': status_fr,
            'status_ja': status_ja,
            'status_it': status_it,
            'status_es': status_es
        }
        if news.created_at:
            item_out['external_created_time'] = news.created_at.strftime(
                '%d %b %Y, %H:%M'
            )

        items_out.append(item_out)
    return JsonResponse({
        "data": items_out,
        "iTotalRecords": total_count,
        "iTotalDisplayRecords": total_count,
    })


def get_status(status, content):
    if content == "" or content is None:
        return "edit_icon_list empty_content"
    elif int(status) == 20:
        return "edit_icon_list success"
    else:
        return "edit_icon_list incomplete"


# common function for fetching the list - news
def news_related_list_common(
    request, news, RelatedEntityClass, form_entity_page_field
):
    page = 1
    limit = None
    offset_0 = None
    offset_n = None

    if request.method == 'POST':
        form = EventRelatedListForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            limit = cd['limit'] if cd['limit'] else limit
            page = cd[form_entity_page_field] if cd[form_entity_page_field] else page  # noqa

    if limit:
        offset_0 = page * limit - limit
        offset_n = page * limit - limit

    # if offsets are not set (limit == None),
    # then we just have [None:None] which is OK
    items = RelatedEntityClass.objects.filter(is_archived=False,
                                              news=news).select_related('news', 'author')[offset_0:offset_n]
    if RelatedEntityClass.__name__ == 'Comment':
        return CommentSerializer(items, many=True).data, len(items)
    else:
        return LikeVoteSerializer(items, many=True).data, len(items)


# /ajax/event/related-lists/{id}
@csrf_exempt
@login_required
def news_related_lists(request, id):
    c = {}
    parent_item = News.objects.get(id=id)

    comments, comment_number = news_related_list_common(
        request, parent_item, Comment, 'page_comments'
    )

    c["is_new"] = False
    c["parent_item"] = parent_item

    c["comments"] = comments
    c["comment_number"] = comment_number

    c["show_like_section"] = False
    return render(request, "news.related-lists.html", c)


@login_required
def featured_venue(request):
    c = get_c(
        request=request, active='list_featured_venues',
        path='/featured-venue', add_new_url='add_featured_venue'
    )
    c['bc_path'] = [
        ('/', 'Home'),
        (reverse('list_featured_venues'), 'Featured Venues')
    ]
    c['counts'] = get_counts()
    return render(request, "lists/featured-venue.html", c)


@csrf_protect
@login_required
def add_featured_venue(request):
    c = get_c(request=request, active='list_featured_venue', path='/add')
    c['bc_path'] = [
        ('/', 'Home'),
        (reverse('list_featured_venues'), 'Featured Venue'),
        (reverse('add_featured_venue'), "Add")
    ]
    featured_venue = FeaturedVenue(author=c['current_user'])
    if request.method == 'POST':
        form = FeaturedVenueAdminForm(request.POST, instance=featured_venue)
        if form.is_valid():
            cd = form.cleaned_data
            images = request.FILES.getlist('image')
            featured_venue.last_editor = c['current_user']
            featured_venue.updated_at = dt.datetime.now()
            featured_venue.name = cd['title']
            setattr(featured_venue, f"title_{cd['language']}", cd['title'])
            setattr(featured_venue, f"meta_description_{cd['language']}", cd['meta_description'])
            setattr(featured_venue, f"content_{cd['language']}", cd['content'])
            setattr(featured_venue, f"status_{cd['language']}", cd['status'])
            featured_venue.save()
            if images:
                featured_venue_image = FeaturedVenueImage(image_file=images[0], featured_venue_id=featured_venue.id)
                featured_venue_image.save()
                featured_venue.image = featured_venue_image
            featured_venue.save()
            featured_venue.refresh_from_db()
            messages.add_message(
                request, messages.INFO, "Featured Venue {} saved.".format(featured_venue.name)
            )
            return redirect('edit_featured_venue', featured_venue.id, cd['language'])
    else:
        form = FeaturedVenueAdminForm(instance=featured_venue, initial={"status": NewsStatus.DRAFT,
                                                                        'language': "en", "type": "featured_venue"})
    c['form'] = form
    c['featured_venue'] = featured_venue
    c['languages'] = get_language_options()
    c['action_url'] = reverse('add_featured_venue')
    c['pdg_title'] = "[New Featured Venue]"
    c["pdg_options"] = get_common_news_pdg_options(include_delete=False)
    c["max_upload_size"] = int(FeaturedVenueAdminForm.MAX_UPLOAD_SIZE / 1000)
    return render(request, "edit/featured-venue.html", c)


@csrf_protect
@login_required
def edit_featured_venue(request, id, language):
    featured_venue = FeaturedVenue.objects.get(id=id)
    bc_path = [
        ('/', 'Home'),
        (reverse('list_featured_venues'), 'Featured Venue'),
        (reverse('edit_featured_venue', args=[id, language]), featured_venue.name),
    ]
    c = get_c(
        request=request, active='list_featured_venues',
        path=None, bc_path_alt=bc_path
    )
    if request.method == 'POST':
        form = FeaturedVenueAdminForm(request.POST, instance=featured_venue)
        if form.is_valid():
            cd = form.cleaned_data
            images = request.FILES.getlist('image')
            featured_venue.last_editor = c['current_user']
            featured_venue.updated_at = dt.datetime.now()
            if cd['status'] == NewsStatus.DELETED:
                setattr(featured_venue, f"title_{cd['language']}", "")
                setattr(featured_venue, f"meta_description_{cd['language']}", "")
                setattr(featured_venue, f"content_{cd['language']}", "")
                setattr(featured_venue, f"status_{cd['language']}", NewsStatus.DRAFT)
            else:
                setattr(featured_venue, f"title_{cd['language']}", cd['title'])
                setattr(featured_venue, f"meta_description_{cd['language']}", cd['meta_description'])
                setattr(featured_venue, f"content_{cd['language']}", cd['content'])
                setattr(featured_venue, f"status_{cd['language']}", cd['status'])
            if cd['language'] != language:
                setattr(featured_venue, f"title_{language}", "")
                setattr(featured_venue, f"meta_description_{language}", "")
                setattr(featured_venue, f"content_{language}", "")
                setattr(featured_venue, f"status_{language}", NewsStatus.DRAFT)
            featured_venue.save()

            if images:
                featured_venue_image = FeaturedVenueImage(image_file=images[0], featured_venue_id=featured_venue.id)
                featured_venue_image.save()
                featured_venue.image = featured_venue_image

            featured_venue.save()
            if cd['type'] == "news":
                news = News()
                for i in featured_venue._meta.fields:
                    if i.name not in ['image', 'id']:
                        if i.name.startswith("status"):
                            setattr(news, f"status_{language}", NewsStatus.DRAFT)
                        else:
                            setattr(news, i.name, getattr(featured_venue, i.name))
                news.save()
                if featured_venue.image:
                    news_image = NewsImage()
                    news_image.event = news
                    for i in featured_venue.image._meta.fields:
                        if i.name not in ['featured_venue', 'id', "news"]:
                            setattr(news_image, i.name, getattr(featured_venue.image, i.name))
                    news_image.save()
                    news.image = news_image
                    news.save()
                featured_venue.comments.all().update(news=news, featured_venue=None)
                featured_venue.deleted = True
                featured_venue.is_archived = True
                featured_venue.save()
                featured_venue.refresh_from_db()

                messages.add_message(request, messages.INFO, "News {} updated.".format(news.name))
                return redirect('edit_news', news.id, cd['language'])
            featured_venue.refresh_from_db()

            messages.add_message(
                request, messages.INFO, "Featured Venue {} updated.".format(featured_venue.name)
            )
            return redirect('edit_featured_venue', featured_venue.id, cd['language'])
    else:
        form = FeaturedVenueAdminForm(instance=featured_venue, initial={
            'language': language,
            "status": getattr(featured_venue, "status_" + language),
            "title": getattr(featured_venue, "title_" + language),
            "meta_description": getattr(featured_venue, "meta_description_" + language),
            "content": getattr(featured_venue, "content_" + language),
            "type": "featured_venue"
        })
    c['form'] = form
    c['featured_venue'] = featured_venue
    connected_venue = featured_venue.connected_venue
    if connected_venue:
        cv_obj = {
            'id': connected_venue.id,
            'name': connected_venue.name,
            'street_address': '{}'.format(
                connected_venue.street_address
            ) if connected_venue.street_address else '',
            'zip_code': ', {}'.format(connected_venue.zip_code) if connected_venue.zip_code else '',
            'city': ', {}'.format(connected_venue.city) if connected_venue.city else '',
            'country': ', {}'.format(connected_venue.country) if connected_venue.country else '',
            'type': f' ({"Bar" if connected_venue.is_bar else ""}\
                      {",Restaurant" if connected_venue.is_restaurant else ""}\
                      {",Wine Shop" if connected_venue.is_wine_shop else ""})'.replace("(,", "(")
        }
    c['connected_venue'] = None if not connected_venue else cv_obj
    c['languages'] = [i for i in get_language_options() if i['value'] != language]
    c['current_language'] = [i for i in get_language_options() if i['value'] == language][0]
    c['action_url'] = reverse('edit_featured_venue', args=[featured_venue.id, language])
    c['pdg_title'] = f"{featured_venue.name} : \
                       <b>{[i for i in get_language_options() if i['value'] == language][0]['name']}</b>"
    c["pdg_options"] = get_common_news_pdg_options(include_delete=True)
    c["max_upload_size"] = int(FeaturedVenueAdminForm.MAX_UPLOAD_SIZE / 1000)
    c['saved_by'] = featured_venue.last_editor
    c['saved_at'] = featured_venue.created_at
    c['updated_at'] = featured_venue.updated_at
    authority = featured_venue.author
    c['authority_name'] = authority.username if authority else 'External user'
    c['authority_id'] = authority.id if authority else None
    c['authority_avatar_url'] = aws_url(authority.image, thumb=True) if authority else None
    c['image'] = aws_url(featured_venue.image)
    c['types'] = get_type_options()
    slug = getattr(featured_venue, "slug_" + language)
    c['new_raisin_url'] = f"{RAISIN_NEW_WEBSITE}/{language}/featured-venue/{slug}/"
    return render(request, "edit/featured-venue.html", c)


# /ajax/featured_venue/items
@csrf_exempt
@login_required
def get_featured_venue_items(request):
    page = None
    limit = None
    order_dir = 'desc'
    order_by = '-updated_at'

    start = None
    length = None
    search_value = None
    col_map = {
        0: 'id',
        1: None,
        2: 'created_at',
        3: None,
        4: 'name',
        5: None,
        6: None,
        7: None,
        8: None,
        9: None
    }

    if request.method == 'POST':
        form = AjaxListForm(request.POST)
        search_value = get_search_value(request)
        order_by = get_sorting(request, col_map, order_by, order_dir)
        if form.is_valid():
            cd = form.cleaned_data
            start = cd['start']
            length = cd['length']
            (page, limit, order_by_old, order_dir_old) = ajax_list_control_parameters_by_form(cd)
        else:
            raise WrongParametersError(_("Wrong parameters."), form)

    filter_criteria = Q()

    if search_value is not None:
        filter_criteria = (
            Q(meta_description_en__unaccent__icontains=search_value) |
            Q(title_en__unaccent__icontains=search_value) |
            Q(meta_description_fr__unaccent__icontains=search_value) |
            Q(title_fr__unaccent__icontains=search_value) |
            Q(meta_description_it__unaccent__icontains=search_value) |
            Q(title_it__unaccent__icontains=search_value) |
            Q(meta_description_es__unaccent__icontains=search_value) |
            Q(title_es__unaccent__icontains=search_value) |
            Q(meta_description_ja__unaccent__icontains=search_value) |
            Q(title_ja__unaccent__icontains=search_value) |
            Q(name__unaccent__icontains=search_value) |
            Q(author__username__unaccent__icontains=search_value)
        )
    if limit:
        offset_0 = page * limit - limit
        offset_n = page * limit
    elif start is not None and length is not None:
        offset_0 = start
        offset_n = start + length
    else:
        offset_0 = None
        offset_n = None

    qs = FeaturedVenue.objects.filter(filter_criteria).filter(deleted=False)

    total_count = qs.count()
    featured_venue_ = qs.order_by(order_by)[offset_0:offset_n]
    items_out = []

    for featured_venue in featured_venue_:
        img_template = '<a href="{}" data-toggle="lightbox"><img width="70" height="70" src="{}" /></a>'
        img_html = img_template.format(
            aws_url(featured_venue.image), aws_url(featured_venue.image, thumb=True)
        )
        author_template = '<img width="35" height="35" src="{}" data-src="{}" alt="{}" style="border-radius:50%">'
        if featured_venue.author:
            author_img_html = author_template.format(
                aws_url(featured_venue.author.image, thumb=True),
                aws_url(featured_venue.author.image, thumb=True),
                featured_venue.author.username
            )
        else:
            author_img_html = ""
        types = ""
        if featured_venue.connected_venue:
            if featured_venue.connected_venue.is_bar:
                types += '<button class="badge bar" style="margin: 2px;">Bar</button>'
            if featured_venue.connected_venue.is_restaurant:
                types += '<button class="badge restaurant" style="margin: 2px;">Restaurat</button>'
            if featured_venue.connected_venue.is_wine_shop:
                types += '<button class="badge wineshop" style="margin: 2px;">Wine Shop</button>'
        checkbox_template = '<input id="colors-%d-toggle-1" name="ids" value="{id}" type="checkbox">'
        checkbox = checkbox_template.format(id=featured_venue.id)
        _string1 = '<a href="/featured-venues/edit/'
        _string = ' data-toggle="tooltip" title="" data-placement="bottom"> <i class="fa fa-edit"></i> </a>'
        status_en = f'{_string1}{featured_venue.id}/en"\
                      class="{get_status(featured_venue.status_en, featured_venue.content_en)}"{_string}'
        status_fr = f'{_string1}{featured_venue.id}/fr"\
                      class="{get_status(featured_venue.status_fr, featured_venue.content_fr)}"{_string}'
        status_ja = f'{_string1}{featured_venue.id}/ja"\
                      class="{get_status(featured_venue.status_ja, featured_venue.content_ja)}"{_string}'
        status_it = f'{_string1}{featured_venue.id}/it"\
                      class="{get_status(featured_venue.status_it, featured_venue.content_it)}"{_string}'
        status_es = f'{_string1}{featured_venue.id}/es"\
                      class="{get_status(featured_venue.status_es, featured_venue.content_es)}"{_string}'
        item_out = {
            'checkbox_id': checkbox,
            'featured_venue_img_html': img_html,
            'author_img_html': author_img_html,
            'title': featured_venue.name,
            'type': types,
            'date': featured_venue.created_at.strftime('%d %b %Y %H:%M'),
            'status_en': status_en,
            'status_fr': status_fr,
            'status_ja': status_ja,
            'status_it': status_it,
            'status_es': status_es
        }
        if featured_venue.created_at:
            item_out['external_created_time'] = featured_venue.created_at.strftime(
                '%d %b %Y, %H:%M'
            )

        items_out.append(item_out)
    return JsonResponse({
        "data": items_out,
        "iTotalRecords": total_count,
        "iTotalDisplayRecords": total_count,
    })


# common function for fetching the list - featured_venue
def featured_venue_related_list_common(
    request, featured_venue, RelatedEntityClass, form_entity_page_field
):
    page = 1
    limit = None
    offset_0 = None
    offset_n = None

    if request.method == 'POST':
        form = EventRelatedListForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            limit = cd['limit'] if cd['limit'] else limit
            page = cd[form_entity_page_field] if cd[form_entity_page_field] else page  # noqa

    if limit:
        offset_0 = page * limit - limit
        offset_n = page * limit - limit

    # if offsets are not set (limit == None),
    # then we just have [None:None] which is OK
    items = RelatedEntityClass.objects.filter(
        featured_venue=featured_venue
    ).select_related('featured_venue', 'author')[offset_0:offset_n]

    if RelatedEntityClass.__name__ == 'Comment':
        return CommentSerializer(items, many=True).data, len(items)
    else:
        return LikeVoteSerializer(items, many=True).data, len(items)


# /ajax/featured_venue/related-lists/{id}
@csrf_exempt
@login_required
def featured_venue_related_lists(request, id):
    c = {}
    parent_item = FeaturedVenue.objects.get(id=id)

    comments, comment_number = featured_venue_related_list_common(
        request, parent_item, Comment, 'page_comments'
    )
    c["is_new"] = False
    c["parent_item"] = parent_item
    c["comments"] = comments
    c["comment_number"] = comment_number
    c["likevotes"], c["likevote_number"] = featured_venue_related_list_common(
        request, parent_item, LikeVote, 'page_likes'
    )
    c["show_like_section"] = True
    return render(request, "news.related-lists.html", c)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def sync_news_from_wordpress(request):
    content = json.loads(request.FILES['news_file'].read())
    comment_content = json.loads(request.FILES['comments_file'].read())
    authors = content['rss']['channel']['author']
    items = content['rss']['channel']['item']
    existing_ids = [item['external_id']
                    for item in News.objects.all_with_deleted().filter(external_id__isnull=False).values("external_id")]
    languages = ['English', "日本語", "Français", "Italiano"]
    LANGUAGES = {'English': "en", "日本語": "ja", "Français": "fr", "Italiano": 'it'}
    attachments = [{"id": item['post_id'], "url": item['attachment_url']['__cdata']}
                   for item in items if item['post_type']['__cdata'] == "attachment"]
    posts = []
    author_user = UserProfile.objects.get(id="9b18b1e5-7a28-4a17-975c-34165bfd8218")
    for item in items:
        if item['post_type']['__cdata'] == "post"\
           and str(item['post_id']) not in existing_ids and type(item['category']) is not dict:
            attachment = [i['meta_value']['__cdata'] for i in item['postmeta']
                          if (type(i) is dict and "meta_key" in i
                              and "__cdata" in i['meta_key'] and i['meta_key']['__cdata'] == "_thumbnail_id")]
            language = LANGUAGES[[i['__cdata'] for i in item['category']
                                  if (type(i) is dict and "__cdata" in i and i['__cdata'] in languages)][0]]
            author = [i for i in authors if i['author_login']['__cdata'] == item['creator']['__cdata']][0]
            _attachment = None if len(attachment) == 0 else [d['url']
                                                             for d in attachments if d['id'] == int(attachment[0])][0]
            news = News(
                external_id=item['post_id'],
                name=item['title'],
                external_image_url=_attachment,
                external_created_time=item['post_date_gmt']['__cdata'],
                external_post_title=item['title'],
                external_post_content=item["encoded"][0]['__cdata'],
                external_language=language,
                external_author_name=author['author_display_name'],
                external_author_id=author['author_id'],
                external_url=item["link"],
                author=author_user
            )
            setattr(news, f"status_{language}", NewsStatus.DRAFT)
            setattr(news, f"title_{language}", item['title'])
            setattr(news, f"meta_description_{language}", item['title'])
            setattr(news, f"content_{language}", item["encoded"][0]['__cdata'])
            news.save()
            if _attachment is not None:
                response = requests.get(_attachment)
                filename = _attachment.split("/")[-1]
                open(f"media/temp/news/{filename}", "wb").write(response.content)
                news_image = NewsImage(image_file=File(open(f"media/temp/news/{filename}",
                                                            'rb')), event_id=news.id)
                news_image.save()
                news.image = news_image
                news.save()
            news.refresh_from_db()
            posts.append(news.id)
            for comment in list(filter(lambda elem: elem['comment_post_ID'] == int(item['post_id']), comment_content)):
                Comment.objects.create(
                    is_archived=False,
                    created_time=comment['comment_date_gmt'],
                    modified_time=comment['comment_date_gmt'],
                    status=StatusE.DRAFT if comment['comment_approved'] == "0" else StatusE.PUBLISHED,
                    description=comment["comment_content"],
                    news=news,
                    author_id=author_user.id,
                    external_id=comment["comment_ID"],
                    external_description=comment["comment_content"],
                    external_author_id=str(comment["user_id"]),
                    external_author_email=comment["comment_author_email"],
                    external_author_name=comment["comment_author"])
    return Response({"length": len(posts), "posts": posts})


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def sync_events_from_wordpress(request):
    event_items = json.loads(request.FILES['events_file'].read())
    comment_content = json.loads(request.FILES['comments_file'].read())
    venue_items = json.loads(request.FILES['venues_file'].read())['rss']['channel']['item']
    existing_ids = [item['external_id'] for item in CalEvent.objects.filter(external_id__isnull=False
                                                                            ).values("external_id")]
    attachments = json.loads(request.FILES['attachment_file'].read())
    post_metas = json.loads(request.FILES['post_meta_file'].read())
    posts = []
    author_user = UserProfile.objects.get(id="9b18b1e5-7a28-4a17-975c-34165bfd8218")

    for item in event_items:
        if str(item['ID']) not in existing_ids:
            try:
                event_postmetas = [meta_item for meta_item in post_metas if meta_item['post_id'] == item['ID']]
                try:
                    start_date = dt.datetime.strptime([i['meta_value']
                                                       for i in event_postmetas
                                                       if (type(i) is dict and "meta_key" in i
                                                           and i['meta_key'] == "pec_date")][0], '%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    start_date = None
                    logger.error(e)
                try:
                    end_date_date = [i['meta_value'] for i in event_postmetas
                                     if (type(i) is dict
                                         and "meta_key" in i
                                         and i['meta_key'] == "pec_end_date")][0]
                    end_date_date = end_date_date if end_date_date != "" else str(str(start_date)[:10]).strip()
                    pec_end_time_hh = [i['meta_value'] for i in event_postmetas
                                       if (type(i) is dict and "meta_key" in i
                                           and i['meta_key'] == "pec_end_time_hh")][0]
                    pec_end_time_mm = [i['meta_value'] for i in event_postmetas
                                       if (type(i) is dict
                                           and "meta_key" in i
                                           and i['meta_key'] == "pec_end_time_mm")][0]
                    end_date = dt.datetime.strptime(f"{end_date_date} {pec_end_time_hh}:{pec_end_time_mm}:00",
                                                    '%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    logger.error(e)
                    end_date = None
                cal_event = CalEvent(
                    external_id=str(item['ID']),
                    title=str(item['post_title']),
                    description=str(item["post_content"]),
                    external_cal_title=str(item['post_title']),
                    external_created_time=item['post_date'],
                    external_cal_desc=str(item["post_title"]),
                    external_author_name=str(item["display_name"]),
                    external_author_id=str(item["user_id"]),
                    external_url=str(item["guid"]),
                    author=author_user,
                    start_date=start_date if start_date is not None and start_date != "" else None,
                    end_date=end_date if end_date is not None and end_date != "" else None,
                    status=PostStatusE.DRAFT
                )
                try:
                    venue_id = int(list(filter(lambda elem: elem['meta_key'] == "pec_location",
                                               event_postmetas))[0]['meta_value'])
                    venue = list(filter(lambda elem: elem['post_id'] == venue_id, venue_items))[0]
                except Exception as e:
                    venue_id = None
                    venue = None
                    logger.error(e)
                if venue:
                    pec_venue_map = list(filter(lambda elem: elem['meta_key']['__cdata'] == "pec_venue_map",
                                                venue['postmeta']))[0]['meta_value']['__cdata']
                    pec_venue_map_lnlat = str(list(filter(lambda elem:
                                                          elem['meta_key']['__cdata'] == "pec_venue_map_lnlat",
                                                          venue['postmeta']))[0]['meta_value']['__cdata'])
                    pec_venue_address = list(filter(lambda elem:
                                                    elem['meta_key']['__cdata'] == "pec_venue_address",
                                                    venue['postmeta']))[0]['meta_value']['__cdata']
                    venue_title = venue['title']
                    if len(pec_venue_map_lnlat.split(',')) == 2:
                        cal_event.loc_lat = str(pec_venue_map_lnlat.split(',')[0].strip())
                        cal_event.loc_lng = str(pec_venue_map_lnlat.split(',')[1].strip())
                    cal_event.loc_name = str(venue_title)
                    cal_event.loc_external_id = str(venue_id)
                    cal_event.loc_full_street_address = str(pec_venue_map)
                    cal_event.loc_street_address = str(pec_venue_address)
                cal_event.save()
                thumbnail = [i for i in event_postmetas
                             if (type(i) is dict and "meta_key" in i
                                 and i['meta_key'] == "_thumbnail_id")]
                if len(thumbnail) > 0:
                    attachment = [i for i in attachments if int(thumbnail[0]['meta_value']) == i["post_id"]]
                    _attachment = None if len(attachment) == 0 else str(attachment[0]['meta_value'])
                    if _attachment is not None:
                        response = requests.get(f"https://www.raisin.digital/wp-content/uploads/{_attachment}")
                        open(f"media/temp/events/{_attachment}", "wb").write(response.content)
                        event_image = EventImage(image_file=File(open(f"media/temp/events/{_attachment}",
                                                                      'rb')), event_id=cal_event.id)
                        event_image.save()
                        cal_event.image_id = event_image.id
                        cal_event.save()
                for comment in list(filter(lambda elem: elem['comment_post_ID'] == int(item['ID']),
                                           comment_content)):
                    Comment.objects.create(
                        author_id=author_user.id,
                        is_archived=False,
                        created_time=comment['comment_date_gmt'],
                        modified_time=comment['comment_date_gmt'],
                        status=StatusE.DRAFT if comment['comment_approved'] == "0" else StatusE.PUBLISHED,
                        description=comment["comment_content"],
                        cal_event=cal_event,
                        external_id=comment["comment_ID"],
                        external_description=comment["comment_content"],
                        external_author_id=str(comment["user_id"]),
                        external_author_email=comment["comment_author_email"],
                        external_author_name=comment["comment_author"])
                cal_event.refresh_from_db()
                posts.append(cal_event.id)
            except Exception as e:
                logger.error(e)
                posts.append({"id": item['ID'], "message": str(e)})
    return Response({"length": len(posts),
                     "posts": posts})


@login_required
def website_page(request):
    c = get_c(
        request=request, active='list_website_pages',
        path='/pages', add_new_url=None
    )
    c['bc_path'] = [
        ('/', 'Home'),
        (reverse('list_website_pages'), 'Website Pages')
    ]
    c['counts'] = get_counts()
    return render(request, "lists/website-page.html", c)


# /ajax/websitepage/items
@csrf_exempt
@login_required
def get_website_page_items(request):
    page = None
    limit = None
    order_dir = 'desc'
    order_by = '-updated_at'

    start = None
    length = None
    search_value = None
    col_map = {
        0: None,
        1: 'created_at',
        2: 'name',
        3: None,
        4: None,
        5: None,
        6: None,
        7: None
    }

    if request.method == 'POST':
        form = AjaxListForm(request.POST)
        search_value = get_search_value(request)
        order_by = get_sorting(request, col_map, order_by, order_dir)
        if form.is_valid():
            cd = form.cleaned_data
            start = cd['start']
            length = cd['length']
            (page, limit, order_by_old, order_dir_old) = ajax_list_control_parameters_by_form(cd)
        else:
            raise WrongParametersError(_("Wrong parameters."), form)

    filter_criteria = Q()

    if search_value is not None:
        filter_criteria = (
            Q(meta_description_en__unaccent__icontains=search_value) |
            Q(title_en__unaccent__icontains=search_value) |
            Q(meta_description_fr__unaccent__icontains=search_value) |
            Q(title_fr__unaccent__icontains=search_value) |
            Q(meta_description_it__unaccent__icontains=search_value) |
            Q(title_it__unaccent__icontains=search_value) |
            Q(meta_description_es__unaccent__icontains=search_value) |
            Q(title_es__unaccent__icontains=search_value) |
            Q(meta_description_ja__unaccent__icontains=search_value) |
            Q(title_ja__unaccent__icontains=search_value) |
            Q(name__unaccent__icontains=search_value) |
            Q(author__username__unaccent__icontains=search_value)
        )
    if limit:
        offset_0 = page * limit - limit
        offset_n = page * limit
    elif start is not None and length is not None:
        offset_0 = start
        offset_n = start + length
    else:
        offset_0 = None
        offset_n = None

    qs = WebsitePage.objects.filter(filter_criteria).filter(deleted=False)

    total_count = qs.count()
    website_page_ = qs.order_by(order_by)[offset_0:offset_n]
    items_out = []

    for website_page in website_page_:
        img_template = '<a href="{}" data-toggle="lightbox"><img width="70" height="70" src="{}" /></a>'
        img_html = img_template.format(
            aws_url(website_page.image), aws_url(website_page.image, thumb=True)
        )
        author_template = '<div data-toggle="tooltip" data-placement="top" \
            title="{}"><a href="{}"><img width="35" height="35" \
            src="{}" data-src="{}" alt="{}" style="border-radius:50%"></a></div>'
        if website_page.last_editor:
            author_img_html = author_template.format(
                website_page.last_editor.username,
                reverse('edit_user', args=[website_page.last_editor_id]),
                aws_url(website_page.last_editor.image, thumb=True),
                aws_url(website_page.last_editor.image, thumb=True),
                website_page.last_editor.username
            )
        else:
            author_img_html = author_template.format(
                website_page.author.username,
                reverse('edit_user', args=[website_page.last_editor_id]),
                aws_url(website_page.author.image, thumb=True),
                aws_url(website_page.author.image, thumb=True),
                website_page.author.username
            )
        _string1 = '<a href="/website-pages/edit/'
        _string = ' data-toggle="tooltip" title="" data-placement="bottom"> <i class="fa fa-edit"></i> </a>'
        status_en = f'{_string1}{website_page.id}/en"\
                      class="{get_status(website_page.status_en, website_page.content_en)}"{_string}'
        status_fr = f'{_string1}{website_page.id}/fr"\
                      class="{get_status(website_page.status_fr, website_page.content_fr)}"{_string}'
        status_ja = f'{_string1}{website_page.id}/ja"\
                      class="{get_status(website_page.status_ja, website_page.content_ja)}"{_string}'
        status_it = f'{_string1}{website_page.id}/it"\
                      class="{get_status(website_page.status_it, website_page.content_it)}"{_string}'
        status_es = f'{_string1}{website_page.id}/es"\
                      class="{get_status(website_page.status_es, website_page.content_es)}"{_string}'
        item_out = {
            'website_page_img_html': img_html,
            'author_img_html': author_img_html,
            'type': website_page.name,
            'date': website_page.created_at.strftime('%d %b %Y %H:%M'),
            'status_en': status_en,
            'status_fr': status_fr,
            'status_ja': status_ja,
            'status_it': status_it,
            'status_es': status_es
        }
        if website_page.created_at:
            item_out['external_created_time'] = website_page.created_at.strftime(
                '%d %b %Y, %H:%M'
            )

        items_out.append(item_out)
    return JsonResponse({
        "data": items_out,
        "iTotalRecords": total_count,
        "iTotalDisplayRecords": total_count,
    })


@csrf_protect
@login_required
def edit_website_page(request, id, language):
    website_page = WebsitePage.objects.get(id=id)
    bc_path = [
        ('/', 'Home'),
        (reverse('list_website_pages'), 'Pages'),
        (reverse('edit_website_page', args=[id, language]), website_page.name),
    ]
    c = get_c(
        request=request, active='list_website_pages',
        path=None, bc_path_alt=bc_path
    )
    if request.method == 'POST':
        form = WebsitePageAdminForm(request.POST, instance=website_page)
        if form.is_valid():
            cd = form.cleaned_data
            images = request.FILES.getlist('image')
            website_page.last_editor = c['current_user']
            website_page.updated_at = dt.datetime.now()
            setattr(website_page, f"title_{cd['language']}", cd['title'])
            setattr(website_page, f"meta_description_{cd['language']}", cd['meta_description'])
            setattr(website_page, f"content_{cd['language']}", cd['content'])
            setattr(website_page, f"status_{cd['language']}", cd['status'])
            website_page.save()

            if images:
                website_page_image = WebsitePageImage(image_file=images[0], website_page_id=website_page.id)
                website_page_image.save()
                website_page.image = website_page_image

            website_page.save()

            website_page.refresh_from_db()

            messages.add_message(
                request, messages.INFO, "Website Page {} updated.".format(website_page.name)
            )
            return redirect('edit_website_page', website_page.id, cd['language'])
    else:
        form = WebsitePageAdminForm(instance=website_page, initial={
            'language': language,
            "status": getattr(website_page, "status_" + language),
            "title": getattr(website_page, "title_" + language),
            "meta_description": getattr(website_page, "meta_description_" + language),
            "content": getattr(website_page, "content_" + language)
        })
    c['form'] = form
    c['website_page'] = website_page
    c['languages'] = [i for i in get_language_options() if i['value'] != language]
    c['current_language'] = [i for i in get_language_options() if i['value'] == language][0]
    c['action_url'] = reverse('edit_website_page', args=[website_page.id, language])
    c['pdg_title'] = f"{website_page.name} : \
                       <b>{[i for i in get_language_options() if i['value'] == language][0]['name']}</b>"
    c["pdg_options"] = get_common_news_pdg_options(include_delete=False)
    c["max_upload_size"] = int(WebsitePageAdminForm.MAX_UPLOAD_SIZE / 1000)
    c['saved_by'] = website_page.last_editor
    c['saved_at'] = website_page.created_at
    c['updated_at'] = website_page.updated_at
    authority = website_page.author
    c['authority_name'] = authority.username if authority else 'External user'
    c['authority_id'] = authority.id if authority else None
    c['authority_avatar_url'] = aws_url(authority.image, thumb=True) if authority else None
    c['image'] = aws_url(website_page.image)
    slug = WEBSITE_PAGES[website_page.p_code]['url']
    c['new_raisin_url'] = f"{RAISIN_NEW_WEBSITE}/{language}/{slug}/"
    return render(request, "edit/website-page.html", c)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def add_predifined_pages(request):
    olds = WebsitePage.objects.filter(deleted=False).filter(is_archived=False)
    author_user = UserProfile.objects.get(id="9b18b1e5-7a28-4a17-975c-34165bfd8218")
    for i in WEBSITE_PAGES.keys():
        if olds.filter(p_code=i).exists():
            pass
        else:
            WebsitePage.objects.create(p_code=i, author=author_user, name=WEBSITE_PAGES[i]['name'])
    return Response(True)


@login_required
def lpb(request):
    c = get_c(
        request=request, active='list_lpb',
        path='/lpb', add_new_url='add_lpb'
    )
    c['bc_path'] = [
        ('/', 'Home'),
        (reverse('list_lpb'), 'La Petite Boucle')
    ]
    c['counts'] = get_counts()
    return render(request, "lists/lpb.html", c)


@csrf_protect
@login_required
def add_lpb(request):
    c = get_c(request=request, active='list_lpb', path='/add')
    lpb = LPB(author=c['current_user'])
    c['bc_path'] = [
        ('/', 'Home'),
        (reverse('list_lpb'), 'La Petite Boucle'),
        (reverse('add_lpb'), "Add")
    ]
    if request.method == 'POST':
        form = LPBAdminForm(request.POST, instance=lpb)
        if form.is_valid():
            cd = form.cleaned_data
            images = request.FILES.getlist('image')
            lpb.last_editor = c['current_user']
            lpb.updated_at = dt.datetime.now()
            lpb.name = cd['title']
            setattr(lpb, f"title_{cd['language']}", cd['title'])
            setattr(lpb, f"meta_description_{cd['language']}", cd['meta_description'])
            setattr(lpb, f"content_{cd['language']}", cd['content'])
            setattr(lpb, f"status_{cd['language']}", cd['status'])
            lpb.save()
            if images:
                lpb_image = LPBImage(image_file=images[0], event_id=lpb.id)
                lpb_image.save()
                lpb.image = lpb_image

            lpb.save()
            lpb.refresh_from_db()

            messages.add_message(
                request, messages.INFO, "La Petite Boucle {} saved.".format(lpb.name)
            )

            return redirect('edit_lpb', lpb.id, cd['language'])
    else:
        form = LPBAdminForm(instance=lpb, initial={"status": NewsStatus.DRAFT, 'language': "en"})
    c['form'] = form
    c['lpb'] = lpb
    c['languages'] = get_language_options()
    c['action_url'] = reverse('add_lpb')
    c['pdg_title'] = "[New La Petite Boucle]"
    c["pdg_options"] = get_common_news_pdg_options(include_delete=False)
    c["max_upload_size"] = int(LPBAdminForm.MAX_UPLOAD_SIZE / 1000)
    return render(request, "edit/lpb.html", c)


@csrf_protect
@login_required
def edit_lpb(request, id, language):
    lpb = LPB.objects.get(id=id)
    bc_path = [
        ('/', 'Home'),
        (reverse('list_lpb'), 'La Petite Boucle'),
        (reverse('edit_lpb', args=[id, language]), lpb.name),
    ]
    c = get_c(
        request=request, active='list_lpb',
        path=None, bc_path_alt=bc_path
    )
    if request.method == 'POST':
        form = LPBAdminForm(request.POST, instance=lpb)
        if form.is_valid():
            cd = form.cleaned_data
            images = request.FILES.getlist('image')
            lpb.last_editor = c['current_user']
            lpb.updated_at = dt.datetime.now()
            if cd['status'] == NewsStatus.DELETED:
                setattr(lpb, f"title_{cd['language']}", "")
                setattr(lpb, f"meta_description_{cd['language']}", "")
                setattr(lpb, f"content_{cd['language']}", "")
                setattr(lpb, f"status_{cd['language']}", NewsStatus.DRAFT)
            else:
                setattr(lpb, f"title_{cd['language']}", cd['title'])
                setattr(lpb, f"meta_description_{cd['language']}", cd['meta_description'])
                setattr(lpb, f"content_{cd['language']}", cd['content'])
                setattr(lpb, f"status_{cd['language']}", cd['status'])
            if cd['language'] != language:
                setattr(lpb, f"title_{language}", "")
                setattr(lpb, f"meta_description_{language}", "")
                setattr(lpb, f"content_{language}", "")
                setattr(lpb, f"status_{language}", NewsStatus.DRAFT)
            lpb.save()
            if images:
                lpb_image = LPBImage(image_file=images[0], event_id=lpb.id)
                lpb_image.save()
                lpb.image = lpb_image
            lpb.save()
            lpb.refresh_from_db()

            messages.add_message(request, messages.INFO, "La Petite Boucle {} updated.".format(lpb.name))
            return redirect('edit_lpb', lpb.id, cd['language'])
    else:
        form = LPBAdminForm(instance=lpb,
                            initial={"language": language,
                                     "status": getattr(lpb, "status_" + language),
                                     "title": getattr(lpb, "title_" + language),
                                     "meta_description": getattr(lpb, "meta_description_" + language),
                                     "content": getattr(lpb, "content_" + language)})
    c['form'] = form
    c['lpb'] = lpb
    c['languages'] = [i for i in get_language_options() if i['value'] != language]
    c['current_language'] = [i for i in get_language_options() if i['value'] == language][0]
    c['action_url'] = reverse('edit_lpb', args=[lpb.id, language])
    c['pdg_title'] = f"{lpb.name} : <b>{[i for i in get_language_options() if i['value'] == language][0]['name']}</b>"
    c["pdg_options"] = get_common_news_pdg_options(include_delete=True)
    c["max_upload_size"] = int(LPBAdminForm.MAX_UPLOAD_SIZE / 1000)
    c['saved_by'] = lpb.last_editor
    c['saved_at'] = lpb.created_at
    c['updated_at'] = lpb.updated_at
    authority = lpb.author
    c['authority_name'] = authority.username if authority else 'External user'
    c['authority_id'] = authority.id if authority else None
    c['authority_avatar_url'] = aws_url(authority.image, thumb=True) if authority else None
    c['image'] = aws_url(lpb.image)
    return render(request, "edit/lpb.html", c)


# /ajax/lpb/items
@csrf_exempt
@login_required
def get_lpb_items(request):
    page = None
    limit = None
    order_dir = 'desc'
    order_by = '-updated_at'
    start = None
    length = None
    search_value = None
    col_map = {
        0: 'id',
        1: None,
        2: 'created_at',
        3: None,
        4: 'name',  # name
        5: None,
        6: None,
        7: None,
        8: None
    }

    if request.method == 'POST':
        form = AjaxListForm(request.POST)
        search_value = get_search_value(request)
        order_by = get_sorting(request, col_map, order_by, order_dir)
        if form.is_valid():
            cd = form.cleaned_data
            start = cd['start']
            length = cd['length']
            (page, limit, order_by_old, order_dir_old) = ajax_list_control_parameters_by_form(cd)
        else:
            raise WrongParametersError(_("Wrong parameters."), form)

    filter_criteria = Q()

    if search_value is not None:
        filter_criteria = (
            Q(meta_description_en__unaccent__icontains=search_value) |
            Q(title_en__unaccent__icontains=search_value) |
            Q(meta_description_fr__unaccent__icontains=search_value) |
            Q(title_fr__unaccent__icontains=search_value) |
            Q(meta_description_it__unaccent__icontains=search_value) |
            Q(title_it__unaccent__icontains=search_value) |
            Q(meta_description_es__unaccent__icontains=search_value) |
            Q(title_es__unaccent__icontains=search_value) |
            Q(meta_description_ja__unaccent__icontains=search_value) |
            Q(title_ja__unaccent__icontains=search_value) |
            Q(name__unaccent__icontains=search_value) |
            Q(author__username__unaccent__icontains=search_value)
        )
    if limit:
        offset_0 = page * limit - limit
        offset_n = page * limit
    elif start is not None and length is not None:
        offset_0 = start
        offset_n = start + length
    else:
        offset_0 = None
        offset_n = None

    qs = LPB.objects.filter(filter_criteria).filter(deleted=False)

    total_count = qs.count()
    lpb_ = qs.order_by(order_by)[offset_0:offset_n]
    items_out = []

    for lpb in lpb_:
        img_template = '<a href="{}" data-toggle="lightbox"><img width="70" height="70" src="{}" /></a>'
        img_html = img_template.format(
            aws_url(lpb.image), aws_url(lpb.image, thumb=True)
        )
        author_template = '<div data-toggle="tooltip" data-placement="top" \
            title="{}"><a href="{}"><img width="35" height="35" \
            src="{}" data-src="{}" alt="{}" style="border-radius:50%"></a></div>'
        if lpb.last_editor:
            author_img_html = author_template.format(
                lpb.last_editor.username,
                reverse('edit_user', args=[lpb.last_editor_id]),
                aws_url(lpb.last_editor.image, thumb=True),
                aws_url(lpb.last_editor.image, thumb=True),
                lpb.last_editor.username
            )
        else:
            author_img_html = author_template.format(
                lpb.author.username,
                reverse('edit_user', args=[lpb.last_editor_id]),
                aws_url(lpb.author.image, thumb=True),
                aws_url(lpb.author.image, thumb=True),
                lpb.author.username
            )
        checkbox_template = '<input id="colors-%d-toggle-1" name="ids" value="{id}" type="checkbox">'
        checkbox = checkbox_template.format(id=lpb.id)
        _string1 = '<a href="/lpb/edit/'
        _string = ' data-toggle="tooltip" title="" data-placement="bottom"> <i class="fa fa-edit"></i> </a>'
        status_en = f'{_string1}{lpb.id}/en" class="{get_status(lpb.status_en, lpb.content_en)}"{_string}'
        status_fr = f'{_string1}{lpb.id}/fr" class="{get_status(lpb.status_fr, lpb.content_fr)}"{_string}'
        status_ja = f'{_string1}{lpb.id}/ja" class="{get_status(lpb.status_ja, lpb.content_ja)}"{_string}'
        status_it = f'{_string1}{lpb.id}/it" class="{get_status(lpb.status_it, lpb.content_it)}"{_string}'
        status_es = f'{_string1}{lpb.id}/es" class="{get_status(lpb.status_es, lpb.content_es)}"{_string}'
        item_out = {
            'checkbox_id': checkbox,
            'lpb_img_html': img_html,
            'author_img_html': author_img_html,
            'title': lpb.name,
            'date': lpb.created_at.strftime('%d %b %Y %H:%M'),
            'status_en': status_en,
            'status_fr': status_fr,
            'status_ja': status_ja,
            'status_it': status_it,
            'status_es': status_es
        }
        if lpb.created_at:
            item_out['external_created_time'] = lpb.created_at.strftime(
                '%d %b %Y, %H:%M'
            )

        items_out.append(item_out)
    return JsonResponse({
        "data": items_out,
        "iTotalRecords": total_count,
        "iTotalDisplayRecords": total_count,
    })


@login_required
def quote(request):
    c = get_c(
        request=request, active='list_quotes',
        path='/quote', add_new_url='add_quote'
    )
    c['bc_path'] = [
        ('/', 'Home'),
        (reverse('list_quotes'), "Venues' Quotes")
    ]
    return render(request, "lists/quote.html", c)


@csrf_protect
@login_required
def add_quote(request):
    c = get_c(request=request, active='list_quotes', path='/add')
    c['bc_path'] = [
        ('/', 'Home'),
        (reverse('list_quotes'), "Venues' Quotes"),
        (reverse('add_quote'), "Add")
    ]
    quote = Quote(author=c['current_user'])
    if request.method == 'POST':
        form = QuoteAdminForm(request.POST, instance=quote)
        if form.is_valid():
            cd = form.cleaned_data
            images = request.FILES.getlist('image')
            quote.last_editor = c['current_user']
            quote.updated_at = dt.datetime.now()
            quote.default_quote = cd['quote']
            setattr(quote, f"quote_{cd['language']}", cd['quote'])
            setattr(quote, f"status_{cd['language']}", cd['status'])
            try:
                data_out = json.loads(cd['current_translations'])
                quote.quote_translations = data_out
                for i in ['en', 'it', 'fr', 'es', 'ja']:
                    setattr(quote, f'quote_{i}', data_out['translations'][i.upper()]['text'])
            except ValueError:
                pass
            quote.save()
            if images:
                quote_image = QuoteImage(image_file=images[0], quote_id=quote.id)
                quote_image.save()
                quote.image = quote_image
            quote.save()
            quote.refresh_from_db()
            messages.add_message(
                request, messages.INFO, "Quote {} saved.".format(quote.default_quote)
            )
            return redirect('edit_quote', quote.id, cd['language'])
    else:
        form = QuoteAdminForm(instance=quote,
                              initial={"status": NewsStatus.DRAFT, 'language': "en"})
    c['form'] = form
    c['quote'] = quote
    c['languages'] = get_language_options()
    c['action_url'] = reverse('add_quote')
    c['pdg_title'] = "[New Quote]"
    c["pdg_options"] = get_common_news_pdg_options(include_delete=False)
    c["max_upload_size"] = int(QuoteAdminForm.MAX_UPLOAD_SIZE / 1000)
    c['venue_id'] = None
    c['featured_quotes'] = FeaturedQuote.objects.all().order_by("order")
    return render(request, "edit/quote.html", c)


@csrf_protect
@login_required
def edit_quote(request, id, language):
    quote = Quote.objects.get(id=id)
    bc_path = [
        ('/', 'Home'),
        (reverse('list_quotes'), "Venues' Quotes"),
        (reverse('edit_quote', args=[id, language]), quote.default_quote),
    ]
    c = get_c(
        request=request, active='list_quotes',
        path=None, bc_path_alt=bc_path
    )
    if request.method == 'POST':
        form = QuoteAdminForm(request.POST, instance=quote)
        if form.is_valid():
            cd = form.cleaned_data
            images = request.FILES.getlist('image')
            quote.last_editor = c['current_user']
            quote.updated_at = dt.datetime.now()
            if cd['status'] == NewsStatus.DELETED:
                setattr(quote, f"quote_{cd['language']}", "")
                setattr(quote, f"status_{cd['language']}", NewsStatus.DRAFT)
            else:
                setattr(quote, f"quote_{cd['language']}", cd['quote'])
                setattr(quote, f"status_{cd['language']}", cd['status'])
            if cd['language'] != language:
                setattr(quote, f"quote_{language}", "")
                setattr(quote, f"status_{language}", NewsStatus.DRAFT)
            try:
                quote.quote_translations = json.loads(cd['current_translations'])
            except ValueError:
                pass
            quote.save()
            if images:
                quote_image = QuoteImage(image_file=images[0], quote_id=quote.id)
                quote_image.save()
                quote.image = quote_image
            quote.save()

            quote.refresh_from_db()

            messages.add_message(
                request, messages.INFO, "Quote {} updated.".format(quote.default_quote)
            )
            return redirect('edit_quote', quote.id, cd['language'])
    else:
        form = QuoteAdminForm(instance=quote, initial={
            'language': language,
            "status": getattr(quote, "status_" + language),
            "quote": getattr(quote, "quote_" + language)
        })
    c['form'] = form
    c['quote'] = quote
    connected_venue = quote.connected_venue
    if connected_venue:
        cv_obj = {
            'id': connected_venue.id,
            'name': connected_venue.name,
            'street_address': '{}'.format(
                connected_venue.street_address
            ) if connected_venue.street_address else '',
            'zip_code': ', {}'.format(connected_venue.zip_code) if connected_venue.zip_code else '',
            'city': ', {}'.format(connected_venue.city) if connected_venue.city else '',
            'country': ', {}'.format(connected_venue.country) if connected_venue.country else '',
            'type': f' ({"Bar" if connected_venue.is_bar else ""}\
                      {",Restaurant" if connected_venue.is_restaurant else ""}\
                      {",Wine Shop" if connected_venue.is_wine_shop else ""})'.replace("(,", "(")
        }
    c['connected_venue'] = None if not connected_venue else cv_obj
    c['languages'] = [i for i in get_language_options() if i['value'] != language]
    c['current_language'] = [i for i in get_language_options() if i['value'] == language][0]
    c['action_url'] = reverse('edit_quote', args=[quote.id, language])
    c['pdg_title'] = f"{quote.default_quote[:80]} : \
                       <b>{[i for i in get_language_options() if i['value'] == language][0]['name']}</b>"
    c["pdg_options"] = get_common_news_pdg_options(include_delete=True)
    c["max_upload_size"] = int(QuoteAdminForm.MAX_UPLOAD_SIZE / 1000)
    c['saved_by'] = quote.last_editor
    c['saved_at'] = quote.created_at
    c['updated_at'] = quote.updated_at
    authority = quote.author
    c['authority_name'] = authority.username if authority else 'External user'
    c['authority_id'] = authority.id if authority else None
    c['authority_avatar_url'] = aws_url(authority.image, thumb=True) if authority else None
    c['image'] = aws_url(quote.image)
    c['venue_id'] = connected_venue.id if connected_venue else None
    c['featured_quotes'] = FeaturedQuote.objects.all().order_by("order")
    return render(request, "edit/quote.html", c)


# /ajax/quote/items
@csrf_exempt
@login_required
def get_quote_items(request):
    page = None
    limit = None
    order_dir = 'desc'
    order_by = '-updated_at'

    start = None
    length = None
    search_value = None
    col_map = {
        0: 'id',
        1: None,
        2: 'created_at',
        3: None,
        4: 'default_quote',
        5: None,
        6: None,
        7: None,
        8: None,
        9: None
    }

    if request.method == 'POST':
        form = AjaxListForm(request.POST)
        search_value = get_search_value(request)
        order_by = get_sorting(request, col_map, order_by, order_dir)
        if form.is_valid():
            cd = form.cleaned_data
            start = cd['start']
            length = cd['length']
            (page, limit, order_by_old, order_dir_old) = ajax_list_control_parameters_by_form(cd)
        else:
            raise WrongParametersError(_("Wrong parameters."), form)

    filter_criteria = Q()

    if search_value is not None:
        filter_criteria = (
            Q(quote_en__unaccent__icontains=search_value) |
            Q(quote_fr__unaccent__icontains=search_value) |
            Q(quote_it__unaccent__icontains=search_value) |
            Q(quote_es__unaccent__icontains=search_value) |
            Q(quote_ja__unaccent__icontains=search_value) |
            Q(default_quote__unaccent__icontains=search_value) |
            Q(author__username__unaccent__icontains=search_value)
        )
    if limit:
        offset_0 = page * limit - limit
        offset_n = page * limit
    elif start is not None and length is not None:
        offset_0 = start
        offset_n = start + length
    else:
        offset_0 = None
        offset_n = None

    qs = Quote.objects.filter(filter_criteria).filter(deleted=False)

    total_count = qs.count()
    quote_ = qs.order_by(order_by)[offset_0:offset_n]
    items_out = []

    for quote in quote_:
        img_template = '<a href="{}" data-toggle="lightbox"><img width="70" height="70" src="{}" /></a>'
        img_html = img_template.format(
            aws_url(quote.image), aws_url(quote.image, thumb=True)
        )
        author_template = '<div data-toggle="tooltip" data-placement="top" \
            title="{}"><a href="{}"><img width="35" height="35" src="{}" \
                data-src="{}" alt="{}" style="border-radius:50%"></a></div>'
        if quote.last_editor:
            author_img_html = author_template.format(
                quote.last_editor.username,
                reverse('edit_user', args=[quote.last_editor_id]),
                aws_url(quote.last_editor.image, thumb=True),
                aws_url(quote.last_editor.image, thumb=True),
                quote.last_editor.username
            )
        else:
            author_img_html = author_template.format(
                quote.author.username,
                reverse('edit_user', args=[quote.last_editor_id]),
                aws_url(quote.author.image, thumb=True),
                aws_url(quote.author.image, thumb=True),
                quote.author.username
            )
        types = ""
        if quote.connected_venue:
            if quote.connected_venue.is_bar:
                types += '<button class="badge bar" style="margin: 2px;">Bar</button>'
            if quote.connected_venue.is_restaurant:
                types += '<button class="badge restaurant" style="margin: 2px;">Restaurat</button>'
            if quote.connected_venue.is_wine_shop:
                types += '<button class="badge wineshop" style="margin: 2px;">Wine Shop</button>'
        checkbox_template = '<input id="colors-%d-toggle-1" name="ids" value="{id}" type="checkbox">'
        checkbox = checkbox_template.format(id=quote.id)
        _string1 = '<a href="/quote/edit/'
        _string = ' data-toggle="tooltip" title="" data-placement="bottom"> <i class="fa fa-edit"></i> </a>'
        status_en = f'{_string1}{quote.id}/en"\
                      class="{get_status(quote.status_en, quote.quote_en)}"{_string}'
        status_fr = f'{_string1}{quote.id}/fr"\
                      class="{get_status(quote.status_fr, quote.quote_fr)}"{_string}'
        status_ja = f'{_string1}{quote.id}/ja"\
                      class="{get_status(quote.status_ja, quote.quote_ja)}"{_string}'
        status_it = f'{_string1}{quote.id}/it"\
                      class="{get_status(quote.status_it, quote.quote_it)}"{_string}'
        status_es = f'{_string1}{quote.id}/es"\
                      class="{get_status(quote.status_es, quote.quote_es)}"{_string}'
        item_out = {
            'checkbox_id': checkbox,
            'quote_img_html': img_html,
            'author_img_html': author_img_html,
            'quote': f"<div style='text-align: left;'>{quote.default_quote[:195]}</div>",
            'type': types,
            'date': quote.created_at.strftime('%d %b %Y %H:%M'),
            'status_en': status_en,
            'status_fr': status_fr,
            'status_ja': status_ja,
            'status_it': status_it,
            'status_es': status_es
        }

        items_out.append(item_out)
    return JsonResponse({
        "data": items_out,
        "iTotalRecords": total_count,
        "iTotalDisplayRecords": total_count,
    })


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def sync_venues_with_qoutes(request):
    venues = Place.active.filter(Q(is_bar=True) | Q(is_restaurant=True)).filter(
        subscription__isnull=False).exclude(Q(subscription__status="cancelled") |
                                            Q(description="") |
                                            Q(description='<p><br></p>'))
    author_user = UserProfile.objects.get(id="9b18b1e5-7a28-4a17-975c-34165bfd8218")
    for venue in venues:
        if not Quote.objects.filter(connected_venue=venue, deleted=False).exists():
            language = venue.owner.lang.lower()
            lang = language if language in ["en", "fr", "es", "ja", "it"] else "en"
            quote = Quote(
                default_quote=venue.description,
                author=author_user,
                connected_venue=venue
            )
            setattr(quote, f"status_{lang}", NewsStatus.DRAFT)
            setattr(quote, f"quote_{lang}", venue.description)
            quote.save()
            images = PlaceImage.objects.filter(place=venue)
            if images.count() > 0:
                _attachment = images.first() if images.count() == 1 else images[1]
                if _attachment is not None:
                    image_url = aws_url(_attachment.image_file)
                    response = requests.get(image_url)
                    filename = _attachment
                    open(f"media/temp/{filename}", "wb").write(response.content)
                    quote_image = QuoteImage(image_file=File(open(f"media/temp/{filename}",
                                                                  'rb')), quote_id=quote.id)
                    # open("/", "wb").write(response.content)
                    # quote_image = QuoteImage(image_file=File(open(image_url,
                    #                                             'rb')), quote_id=quote.id)
                    quote_image.save()
                    quote.image = quote_image
                    quote.save()
            quote.refresh_from_db()
    return Response({"length": len(venues)})


@csrf_exempt
@login_required
def add_featured_quote(request, id):
    quotes = Quote.objects.filter(connected_venue_id=id, deleted=False, is_archived=False)
    if quotes.exists():
        quote = quotes.first()
    else:
        return JsonResponse({'status': 'Failed', 'message': "Something went wrong."})
    if FeaturedQuote.objects.filter(quote_id=quote.id).exists():
        return JsonResponse({'status': 'Failed', 'message': "already exists"})
    fq = FeaturedQuote(
        quote_id=quote.id,
        order=FeaturedQuote.objects.count() + 1
    )
    fq.save()
    return JsonResponse({'status': 'OK', "data": get_featured_quote_list()})


@csrf_exempt
@login_required
def remove_featured_quotes(request):
    for id in json.loads(request.POST.get('ids')):
        FeaturedQuote.objects.get(id=int(id)).delete()
    num = 1
    for fq in FeaturedQuote.objects.all():
        fq.order = num
        num = num + 1
        fq.save()
    return JsonResponse({'status': 'OK', "data": get_featured_quote_list()})


@csrf_exempt
@login_required
def change_featured_quote_orders(request):
    num = 1
    for item in json.loads(request.POST.get('ids')):
        fq = FeaturedQuote.objects.get(id=int(item))
        fq.order = num
        fq.save()
        num = num + 1
    return JsonResponse({'status': 'OK', "data": get_featured_quote_list()})


def get_featured_quote_list():
    data = [{"id": i.id,
             "text": f"{i.quote.connected_venue.name} - {i.quote.connected_venue.display_full_address}",
             "order": i.order,
             "venue_id": i.quote.connected_venue_id} for i in FeaturedQuote.objects.all().order_by("order")]
    return data


@login_required
def cheffe(request):
    c = get_c(
        request=request, active='list_cheffes',
        path='/cheffe', add_new_url='add_cheffe'
    )
    c['bc_path'] = [
        ('/', 'Home'),
        (reverse('list_cheffes'), "Venues' Cheffes")
    ]
    return render(request, "lists/cheffe.html", c)


@csrf_protect
@login_required
def add_cheffe(request):
    c = get_c(request=request, active='list_cheffes', path='/add')
    c['bc_path'] = [
        ('/', 'Home'),
        (reverse('list_cheffes'), "Venues' Cheffes"),
        (reverse('add_cheffe'), "Add")
    ]
    cheffe = Cheffe(author=c['current_user'])
    if request.method == 'POST':
        form = CheffeAdminForm(request.POST, instance=cheffe)
        if form.is_valid():
            cd = form.cleaned_data
            images = request.FILES.getlist('image')
            cheffe.last_editor = c['current_user']
            cheffe.updated_at = dt.datetime.now()
            cheffe.default_cheffe = cd['cheffe']
            cheffe.default_fullname = cd['fullname']
            setattr(cheffe, f"cheffe_{cd['language']}", cd['cheffe'])
            setattr(cheffe, f"fullname_{cd['language']}", cd['fullname'])
            setattr(cheffe, f"status_{cd['language']}", cd['status'])
            try:
                data_out = json.loads(cd['current_translations'])
                cheffe.cheffe_translations = data_out
                for i in ['en', 'it', 'fr', 'es', 'ja']:
                    setattr(cheffe, f'cheffe_{i}', data_out['translations'][i.upper()]['text'])
            except ValueError:
                pass
            cheffe.save()
            if images:
                cheffe_image = CheffeImage(image_file=images[0], cheffe_id=cheffe.id)
                cheffe_image.save()
                cheffe.image = cheffe_image
            cheffe.save()
            cheffe.refresh_from_db()
            messages.add_message(
                request, messages.INFO, "Cheffe {} saved.".format(cheffe.default_fullname)
            )
            return redirect('edit_cheffe', cheffe.id, cd['language'])
    else:
        form = CheffeAdminForm(instance=cheffe,
                               initial={"status": NewsStatus.DRAFT, 'language': "en"})
    c['form'] = form
    c['cheffe'] = cheffe
    c['languages'] = get_language_options()
    c['action_url'] = reverse('add_cheffe')
    c['pdg_title'] = "[New Cheffe]"
    c["pdg_options"] = get_common_news_pdg_options(include_delete=False)
    c["max_upload_size"] = int(CheffeAdminForm.MAX_UPLOAD_SIZE / 1000)
    c['venue_id'] = None
    c['featured_cheffes'] = FeaturedCheffe.objects.all().order_by("order")
    return render(request, "edit/cheffe.html", c)


@csrf_protect
@login_required
def edit_cheffe(request, id, language):
    cheffe = Cheffe.objects.get(id=id)
    bc_path = [
        ('/', 'Home'),
        (reverse('list_cheffes'), "Venues' Cheffes"),
        (reverse('edit_cheffe', args=[id, language]), cheffe.default_fullname),
    ]
    c = get_c(
        request=request, active='list_cheffes',
        path=None, bc_path_alt=bc_path
    )
    if request.method == 'POST':
        form = CheffeAdminForm(request.POST, instance=cheffe)
        if form.is_valid():
            cd = form.cleaned_data
            images = request.FILES.getlist('image')
            cheffe.last_editor = c['current_user']
            cheffe.updated_at = dt.datetime.now()
            if cd['status'] == NewsStatus.DELETED:
                setattr(cheffe, f"cheffe_{cd['language']}", "")
                setattr(cheffe, f"fullname_{cd['language']}", "")
                setattr(cheffe, f"status_{cd['language']}", NewsStatus.DRAFT)
            else:
                setattr(cheffe, f"cheffe_{cd['language']}", cd['cheffe'])
                setattr(cheffe, f"fullname_{cd['language']}", cd['fullname'])
                setattr(cheffe, f"status_{cd['language']}", cd['status'])
            if cd['language'] != language:
                setattr(cheffe, f"cheffe_{language}", "")
                setattr(cheffe, f"fullname_{cd['language']}", "")
                setattr(cheffe, f"status_{language}", NewsStatus.DRAFT)
            if not cheffe.default_fullname:
                cheffe.default_fullname = cd['fullname']
            try:
                cheffe.cheffe_translations = json.loads(cd['current_translations'])
            except ValueError:
                pass
            cheffe.save()
            if images:
                cheffe_image = CheffeImage(image_file=images[0], cheffe_id=cheffe.id)
                cheffe_image.save()
                cheffe.image = cheffe_image
            cheffe.save()

            cheffe.refresh_from_db()

            messages.add_message(
                request, messages.INFO, "Cheffe {} updated.".format(cheffe.default_fullname)
            )
            return redirect('edit_cheffe', cheffe.id, cd['language'])
    else:
        form = CheffeAdminForm(instance=cheffe, initial={
            'language': language,
            "status": getattr(cheffe, "status_" + language),
            "cheffe": getattr(cheffe, "cheffe_" + language),
            "fullname": getattr(cheffe, "fullname_" + language)
        })
    c['form'] = form
    c['cheffe'] = cheffe
    connected_venue = cheffe.connected_venue
    if connected_venue:
        cv_obj = {
            'id': connected_venue.id,
            'name': connected_venue.name,
            'street_address': '{}'.format(
                connected_venue.street_address
            ) if connected_venue.street_address else '',
            'zip_code': ', {}'.format(connected_venue.zip_code) if connected_venue.zip_code else '',
            'city': ', {}'.format(connected_venue.city) if connected_venue.city else '',
            'country': ', {}'.format(connected_venue.country) if connected_venue.country else '',
            'type': f' ({"Bar" if connected_venue.is_bar else ""}\
                      {",Restaurant" if connected_venue.is_restaurant else ""}\
                      {",Wine Shop" if connected_venue.is_wine_shop else ""})'.replace("(,", "(")
        }
    c['connected_venue'] = None if not connected_venue else cv_obj
    c['languages'] = [i for i in get_language_options() if i['value'] != language]
    c['current_language'] = [i for i in get_language_options() if i['value'] == language][0]
    c['action_url'] = reverse('edit_cheffe', args=[cheffe.id, language])
    c['pdg_title'] = f"{cheffe.default_fullname} : \
                       <b>{[i for i in get_language_options() if i['value'] == language][0]['name']}</b>"
    c["pdg_options"] = get_common_news_pdg_options(include_delete=True)
    c["max_upload_size"] = int(CheffeAdminForm.MAX_UPLOAD_SIZE / 1000)
    c['saved_by'] = cheffe.last_editor
    c['saved_at'] = cheffe.created_at
    c['updated_at'] = cheffe.updated_at
    authority = cheffe.author
    c['authority_name'] = authority.username if authority else 'External user'
    c['authority_id'] = authority.id if authority else None
    c['authority_avatar_url'] = aws_url(authority.image, thumb=True) if authority else None
    c['image'] = aws_url(cheffe.image)
    c['venue_id'] = connected_venue.id if connected_venue else None
    c['featured_cheffes'] = FeaturedCheffe.objects.all().order_by("order")
    return render(request, "edit/cheffe.html", c)


# /ajax/cheffe/items
@csrf_exempt
@login_required
def get_cheffe_items(request):
    page = None
    limit = None
    order_dir = 'desc'
    order_by = '-updated_at'

    start = None
    length = None
    search_value = None
    col_map = {
        0: 'id',
        1: None,
        2: 'created_at',
        3: None,
        4: 'default_fullname',
        5: None,
        6: None,
        7: None,
        8: None,
        9: None
    }

    if request.method == 'POST':
        form = AjaxListForm(request.POST)
        search_value = get_search_value(request)
        order_by = get_sorting(request, col_map, order_by, order_dir)
        if form.is_valid():
            cd = form.cleaned_data
            start = cd['start']
            length = cd['length']
            (page, limit, order_by_old, order_dir_old) = ajax_list_control_parameters_by_form(cd)
        else:
            raise WrongParametersError(_("Wrong parameters."), form)

    filter_criteria = Q()

    if search_value is not None:
        filter_criteria = (
            Q(cheffe_en__unaccent__icontains=search_value) |
            Q(cheffe_fr__unaccent__icontains=search_value) |
            Q(cheffe_it__unaccent__icontains=search_value) |
            Q(cheffe_es__unaccent__icontains=search_value) |
            Q(cheffe_ja__unaccent__icontains=search_value) |
            Q(default_cheffe__unaccent__icontains=search_value) |
            Q(fullname_en__unaccent__icontains=search_value) |
            Q(fullname_fr__unaccent__icontains=search_value) |
            Q(fullname_it__unaccent__icontains=search_value) |
            Q(fullname_es__unaccent__icontains=search_value) |
            Q(fullname_ja__unaccent__icontains=search_value) |
            Q(default_fullname__unaccent__icontains=search_value) |
            Q(author__username__unaccent__icontains=search_value)
        )
    if limit:
        offset_0 = page * limit - limit
        offset_n = page * limit
    elif start is not None and length is not None:
        offset_0 = start
        offset_n = start + length
    else:
        offset_0 = None
        offset_n = None

    qs = Cheffe.objects.filter(filter_criteria).filter(deleted=False)

    total_count = qs.count()
    cheffe_ = qs.order_by(order_by)[offset_0:offset_n]
    items_out = []

    for cheffe in cheffe_:
        img_template = '<a href="{}" data-toggle="lightbox"><img width="70" height="70" src="{}" /></a>'
        img_html = img_template.format(
            aws_url(cheffe.image), aws_url(cheffe.image, thumb=True)
        )
        author_template = '<div data-toggle="tooltip" data-placement="top" \
            title="{}"><a href="{}"><img width="35" height="35" src="{}" \
                data-src="{}" alt="{}" style="border-radius:50%"></a></div>'
        if cheffe.last_editor:
            author_img_html = author_template.format(
                cheffe.last_editor.username,
                reverse('edit_user', args=[cheffe.last_editor_id]),
                aws_url(cheffe.last_editor.image, thumb=True),
                aws_url(cheffe.last_editor.image, thumb=True),
                cheffe.last_editor.username
            )
        else:
            author_img_html = author_template.format(
                cheffe.author.username,
                reverse('edit_user', args=[cheffe.last_editor_id]),
                aws_url(cheffe.author.image, thumb=True),
                aws_url(cheffe.author.image, thumb=True),
                cheffe.author.username
            )
        types = ""
        if cheffe.connected_venue:
            if cheffe.connected_venue.is_bar:
                types += '<button class="badge bar" style="margin: 2px;">Bar</button>'
            if cheffe.connected_venue.is_restaurant:
                types += '<button class="badge restaurant" style="margin: 2px;">Restaurat</button>'
            if cheffe.connected_venue.is_wine_shop:
                types += '<button class="badge wineshop" style="margin: 2px;">Wine Shop</button>'
        checkbox_template = '<input id="colors-%d-toggle-1" name="ids" value="{id}" type="checkbox">'
        checkbox = checkbox_template.format(id=cheffe.id)
        _string1 = '<a href="/cheffe/edit/'
        _string = ' data-toggle="tooltip" title="" data-placement="bottom"> <i class="fa fa-edit"></i> </a>'
        status_en = f'{_string1}{cheffe.id}/en"\
                      class="{get_status(cheffe.status_en, cheffe.cheffe_en)}"{_string}'
        status_fr = f'{_string1}{cheffe.id}/fr"\
                      class="{get_status(cheffe.status_fr, cheffe.cheffe_fr)}"{_string}'
        status_ja = f'{_string1}{cheffe.id}/ja"\
                      class="{get_status(cheffe.status_ja, cheffe.cheffe_ja)}"{_string}'
        status_it = f'{_string1}{cheffe.id}/it"\
                      class="{get_status(cheffe.status_it, cheffe.cheffe_it)}"{_string}'
        status_es = f'{_string1}{cheffe.id}/es"\
                      class="{get_status(cheffe.status_es, cheffe.cheffe_es)}"{_string}'
        item_out = {
            'checkbox_id': checkbox,
            'cheffe_img_html': img_html,
            'author_img_html': author_img_html,
            'cheffe': f"<div style='text-align: left;'>{cheffe.default_fullname}</div>",
            'type': types,
            'date': cheffe.created_at.strftime('%d %b %Y %H:%M'),
            'status_en': status_en,
            'status_fr': status_fr,
            'status_ja': status_ja,
            'status_it': status_it,
            'status_es': status_es
        }

        items_out.append(item_out)
    return JsonResponse({
        "data": items_out,
        "iTotalRecords": total_count,
        "iTotalDisplayRecords": total_count,
    })


@csrf_exempt
@login_required
def add_featured_cheffe(request, id):
    cheffes = Cheffe.objects.filter(connected_venue_id=id, deleted=False, is_archived=False)
    if cheffes.exists():
        cheffe = cheffes.first()
    else:
        return JsonResponse({'status': 'Failed', 'message': "Something went wrong."})
    if FeaturedCheffe.objects.filter(cheffe_id=cheffe.id).exists():
        return JsonResponse({'status': 'Failed', 'message': "already exists"})
    fq = FeaturedCheffe(
        cheffe_id=cheffe.id,
        order=FeaturedCheffe.objects.count() + 1
    )
    fq.save()
    return JsonResponse({'status': 'OK', "data": get_featured_cheffe_list()})


@csrf_exempt
@login_required
def remove_featured_cheffes(request):
    for id in json.loads(request.POST.get('ids')):
        FeaturedCheffe.objects.get(id=int(id)).delete()
    num = 1
    for fq in FeaturedCheffe.objects.all():
        fq.order = num
        num = num + 1
        fq.save()
    return JsonResponse({'status': 'OK', "data": get_featured_cheffe_list()})


@csrf_exempt
@login_required
def change_featured_cheffe_orders(request):
    num = 1
    for item in json.loads(request.POST.get('ids')):
        fq = FeaturedCheffe.objects.get(id=int(item))
        fq.order = num
        fq.save()
        num = num + 1
    return JsonResponse({'status': 'OK', "data": get_featured_cheffe_list()})


def get_featured_cheffe_list():
    data = [{"id": i.id,
             "text": f"{i.cheffe.connected_venue.name} - {i.cheffe.connected_venue.display_full_address}",
             "order": i.order,
             "venue_id": i.cheffe.connected_venue_id} for i in FeaturedCheffe.objects.all().order_by("order")]
    return data


@login_required
def testimonial(request):
    c = get_c(
        request=request, active='list_testimonials',
        path='/testimonial', add_new_url='add_testimonial'
    )
    c['bc_path'] = [
        ('/', 'Home'),
        (reverse('list_testimonials'), "Venues' Testimonials")
    ]
    return render(request, "lists/testimonial.html", c)


@csrf_protect
@login_required
def add_testimonial(request):
    c = get_c(request=request, active='list_testimonials', path='/add')
    c['bc_path'] = [
        ('/', 'Home'),
        (reverse('list_testimonials'), "Venues' Testimonials"),
        (reverse('add_testimonial'), "Add")
    ]
    testimonial = Testimonial(author=c['current_user'])
    if request.method == 'POST':
        form = TestimonialAdminForm(request.POST, instance=testimonial)
        if form.is_valid():
            cd = form.cleaned_data
            images = request.FILES.getlist('image')
            testimonial.last_editor = c['current_user']
            testimonial.updated_at = dt.datetime.now()
            testimonial.default_testimonial = cd['testimonial']
            testimonial.default_username = cd['username']
            testimonial.default_title = cd['title']
            testimonial.date = cd['date']
            setattr(testimonial, f"testimonial_{cd['language']}", cd['testimonial'])
            setattr(testimonial, f"title_{cd['language']}", cd['title'])
            setattr(testimonial, f"username_{cd['language']}", cd['username'])
            setattr(testimonial, f"status_{cd['language']}", cd['status'])
            try:
                data_out = json.loads(cd['current_translations'])
                testimonial.testimonial_translations = data_out
                for i in ['en', 'it', 'fr', 'es', 'ja']:
                    setattr(testimonial, f'testimonial_{i}', data_out['translations'][i.upper()]['text'])
            except ValueError:
                pass
            testimonial.save()
            if images:
                testimonial_image = TestimonialImage(image_file=images[0], testimonial_id=testimonial.id)
                testimonial_image.save()
                testimonial.image = testimonial_image
            testimonial.save()
            testimonial.refresh_from_db()
            messages.add_message(
                request, messages.INFO, "Testimonial {} saved.".format(testimonial.default_title)
            )
            return redirect('edit_testimonial', testimonial.id, cd['language'])
    else:
        form = TestimonialAdminForm(instance=testimonial,
                                    initial={"status": NewsStatus.DRAFT, 'language': "en"})
    c['form'] = form
    c['testimonial'] = testimonial
    c['languages'] = get_language_options()
    c['action_url'] = reverse('add_testimonial')
    c['pdg_title'] = "[New Testimonial]"
    c["pdg_options"] = get_common_news_pdg_options(include_delete=False)
    c["max_upload_size"] = int(TestimonialAdminForm.MAX_UPLOAD_SIZE / 1000)
    c['venue_id'] = None
    c['featured_testimonials'] = FeaturedTestimonial.objects.all().order_by("order")
    return render(request, "edit/testimonial.html", c)


@csrf_protect
@login_required
def edit_testimonial(request, id, language):
    testimonial = Testimonial.objects.get(id=id)
    bc_path = [
        ('/', 'Home'),
        (reverse('list_testimonials'), "Venues' Testimonials"),
        (reverse('edit_testimonial', args=[id, language]), testimonial.default_username),
    ]
    c = get_c(
        request=request, active='list_testimonials',
        path=None, bc_path_alt=bc_path
    )
    if request.method == 'POST':
        form = TestimonialAdminForm(request.POST, instance=testimonial)
        if form.is_valid():
            cd = form.cleaned_data
            images = request.FILES.getlist('image')
            testimonial.last_editor = c['current_user']
            testimonial.updated_at = dt.datetime.now()
            if cd['status'] == NewsStatus.DELETED:
                setattr(testimonial, f"testimonial_{cd['language']}", "")
                setattr(testimonial, f"username_{cd['language']}", "")
                setattr(testimonial, f"title_{cd['language']}", "")
                setattr(testimonial, f"status_{cd['language']}", NewsStatus.DRAFT)
            else:
                setattr(testimonial, f"testimonial_{cd['language']}", cd['testimonial'])
                setattr(testimonial, f"title_{cd['language']}", cd['title'])
                setattr(testimonial, f"username_{cd['language']}", cd['username'])
                setattr(testimonial, f"status_{cd['language']}", cd['status'])
            if cd['language'] != language:
                setattr(testimonial, f"testimonial_{language}", "")
                setattr(testimonial, f"username_{cd['language']}", "")
                setattr(testimonial, f"title_{cd['language']}", "")
                setattr(testimonial, f"status_{language}", NewsStatus.DRAFT)
            try:
                testimonial.testimonial_translations = json.loads(cd['current_translations'])
            except ValueError:
                pass
            testimonial.save()
            if images:
                testimonial_image = TestimonialImage(image_file=images[0], testimonial_id=testimonial.id)
                testimonial_image.save()
                testimonial.image = testimonial_image
            testimonial.save()

            testimonial.refresh_from_db()

            messages.add_message(
                request, messages.INFO, "Testimonial {} updated.".format(testimonial.default_title)
            )
            return redirect('edit_testimonial', testimonial.id, cd['language'])
    else:
        form = TestimonialAdminForm(instance=testimonial, initial={
            'language': language,
            "status": getattr(testimonial, "status_" + language),
            "testimonial": getattr(testimonial, "testimonial_" + language),
            "username": getattr(testimonial, "username_" + language),
            "title": getattr(testimonial, "title_" + language)
        })
    c['form'] = form
    c['testimonial'] = testimonial
    c['languages'] = [i for i in get_language_options() if i['value'] != language]
    c['current_language'] = [i for i in get_language_options() if i['value'] == language][0]
    c['action_url'] = reverse('edit_testimonial', args=[testimonial.id, language])
    c['pdg_title'] = f"{testimonial.default_username} : \
                       <b>{[i for i in get_language_options() if i['value'] == language][0]['name']}</b>"
    c["pdg_options"] = get_common_news_pdg_options(include_delete=True)
    c["max_upload_size"] = int(TestimonialAdminForm.MAX_UPLOAD_SIZE / 1000)
    c['saved_by'] = testimonial.last_editor
    c['saved_at'] = testimonial.created_at
    c['updated_at'] = testimonial.updated_at
    authority = testimonial.author
    c['authority_name'] = authority.username if authority else 'External user'
    c['authority_id'] = authority.id if authority else None
    c['authority_avatar_url'] = aws_url(authority.image, thumb=True) if authority else None
    c['image'] = aws_url(testimonial.image)
    c['featured_testimonials'] = FeaturedTestimonial.objects.all().order_by("order")
    return render(request, "edit/testimonial.html", c)


# /ajax/testimonial/items
@csrf_exempt
@login_required
def get_testimonial_items(request):
    page = None
    limit = None
    order_dir = 'desc'
    order_by = '-updated_at'

    start = None
    length = None
    search_value = None
    col_map = {
        0: 'id',
        1: None,
        2: 'created_at',
        3: None,
        4: 'default_username',
        5: None,
        6: None,
        7: None,
        8: None,
        8: None
    }

    if request.method == 'POST':
        form = AjaxListForm(request.POST)
        search_value = get_search_value(request)
        order_by = get_sorting(request, col_map, order_by, order_dir)
        if form.is_valid():
            cd = form.cleaned_data
            start = cd['start']
            length = cd['length']
            (page, limit, order_by_old, order_dir_old) = ajax_list_control_parameters_by_form(cd)
        else:
            raise WrongParametersError(_("Wrong parameters."), form)

    filter_criteria = Q()

    if search_value is not None:
        filter_criteria = (
            Q(testimonial_en__unaccent__icontains=search_value) |
            Q(testimonial_fr__unaccent__icontains=search_value) |
            Q(testimonial_it__unaccent__icontains=search_value) |
            Q(testimonial_es__unaccent__icontains=search_value) |
            Q(testimonial_ja__unaccent__icontains=search_value) |
            Q(default_testimonial__unaccent__icontains=search_value) |
            Q(title_en__unaccent__icontains=search_value) |
            Q(title_fr__unaccent__icontains=search_value) |
            Q(title_it__unaccent__icontains=search_value) |
            Q(title_es__unaccent__icontains=search_value) |
            Q(title_ja__unaccent__icontains=search_value) |
            Q(default_title__unaccent__icontains=search_value) |
            Q(username_en__unaccent__icontains=search_value) |
            Q(username_fr__unaccent__icontains=search_value) |
            Q(username_it__unaccent__icontains=search_value) |
            Q(username_es__unaccent__icontains=search_value) |
            Q(username_ja__unaccent__icontains=search_value) |
            Q(default_username__unaccent__icontains=search_value) |
            Q(author__username__unaccent__icontains=search_value)
        )
    if limit:
        offset_0 = page * limit - limit
        offset_n = page * limit
    elif start is not None and length is not None:
        offset_0 = start
        offset_n = start + length
    else:
        offset_0 = None
        offset_n = None

    qs = Testimonial.objects.filter(filter_criteria).filter(deleted=False)

    total_count = qs.count()
    testimonial_ = qs.order_by(order_by)[offset_0:offset_n]
    items_out = []

    for testimonial in testimonial_:
        img_template = '<a href="{}" data-toggle="lightbox"><img width="70" height="70" src="{}" /></a>'
        img_html = img_template.format(
            aws_url(testimonial.image), aws_url(testimonial.image, thumb=True)
        )
        author_template = '<div data-toggle="tooltip" data-placement="top" \
            title="{}"><a href="{}"><img width="35" height="35" src="{}" \
                data-src="{}" alt="{}" style="border-radius:50%"></a></div>'
        if testimonial.last_editor:
            author_img_html = author_template.format(
                testimonial.last_editor.username,
                reverse('edit_user', args=[testimonial.last_editor_id]),
                aws_url(testimonial.last_editor.image, thumb=True),
                aws_url(testimonial.last_editor.image, thumb=True),
                testimonial.last_editor.username
            )
        else:
            author_img_html = author_template.format(
                testimonial.author.username,
                reverse('edit_user', args=[testimonial.last_editor_id]),
                aws_url(testimonial.author.image, thumb=True),
                aws_url(testimonial.author.image, thumb=True),
                testimonial.author.username
            )
        checkbox_template = '<input id="colors-%d-toggle-1" name="ids" value="{id}" type="checkbox">'
        checkbox = checkbox_template.format(id=testimonial.id)
        _string1 = '<a href="/testimonial/edit/'
        _string = ' data-toggle="tooltip" title="" data-placement="bottom"> <i class="fa fa-edit"></i> </a>'
        status_en = f'{_string1}{testimonial.id}/en"\
                      class="{get_status(testimonial.status_en, testimonial.testimonial_en)}"{_string}'
        status_fr = f'{_string1}{testimonial.id}/fr"\
                      class="{get_status(testimonial.status_fr, testimonial.testimonial_fr)}"{_string}'
        status_ja = f'{_string1}{testimonial.id}/ja"\
                      class="{get_status(testimonial.status_ja, testimonial.testimonial_ja)}"{_string}'
        status_it = f'{_string1}{testimonial.id}/it"\
                      class="{get_status(testimonial.status_it, testimonial.testimonial_it)}"{_string}'
        status_es = f'{_string1}{testimonial.id}/es"\
                      class="{get_status(testimonial.status_es, testimonial.testimonial_es)}"{_string}'
        item_out = {
            'checkbox_id': checkbox,
            'testimonial_img_html': img_html,
            'author_img_html': author_img_html,
            'testimonial': f"<div style='text-align: left;'>{testimonial.default_username[:195]}</div>",
            'title': f"<div style='text-align: left;'>{testimonial.default_title[:195]}</div>",
            'date': testimonial.date.strftime('%d %b %Y'),
            'status_en': status_en,
            'status_fr': status_fr,
            'status_ja': status_ja,
            'status_it': status_it,
            'status_es': status_es
        }

        items_out.append(item_out)
    return JsonResponse({
        "data": items_out,
        "iTotalRecords": total_count,
        "iTotalDisplayRecords": total_count,
    })


@csrf_exempt
@login_required
def add_featured_testimonial(request, id):
    testimonials = Testimonial.objects.filter(id=id, deleted=False, is_archived=False)
    if testimonials.exists():
        testimonial = testimonials.first()
    else:
        return JsonResponse({'status': 'Failed', 'message': "Something went wrong."})
    if FeaturedTestimonial.objects.filter(testimonial_id=testimonial.id).exists():
        return JsonResponse({'status': 'Failed', 'message': "already exists"})
    fq = FeaturedTestimonial(
        testimonial_id=testimonial.id,
        order=FeaturedTestimonial.objects.count() + 1
    )
    fq.save()
    return JsonResponse({'status': 'OK', "data": get_featured_testimonial_list()})


@csrf_exempt
@login_required
def remove_featured_testimonials(request):
    for id in json.loads(request.POST.get('ids')):
        FeaturedTestimonial.objects.get(id=int(id)).delete()
    num = 1
    for fq in FeaturedTestimonial.objects.all():
        fq.order = num
        num = num + 1
        fq.save()
    return JsonResponse({'status': 'OK', "data": get_featured_testimonial_list()})


@csrf_exempt
@login_required
def change_featured_testimonial_orders(request):
    num = 1
    for item in json.loads(request.POST.get('ids')):
        fq = FeaturedTestimonial.objects.get(id=int(item))
        fq.order = num
        fq.save()
        num = num + 1
    return JsonResponse({'status': 'OK', "data": get_featured_testimonial_list()})


def get_featured_testimonial_list():
    data = [{"id": i.id,
             "text": f"{i.testimonial.default_username} - {i.testimonial.default_title}",
             "order": i.order}for i in FeaturedTestimonial.objects.all().order_by("order")]
    return data
