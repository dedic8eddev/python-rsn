from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from web.constants import PostStatusE, SpecialStatusE
from web.forms.admin_forms import EventAdminForm
from web.models import CalEvent, EventImage
from web.utils.upload_tools import aws_url
from web.views.admin.common import get_c
from django.templatetags.static import static


# /events
@login_required
def events(request):
    c = get_c(
        request=request, active='list_events',
        path='/', add_new_url='add_event'
    )

    return render(request, 'lists/events.html', c)


def _get_common_pdg_options(include_delete=True):
    opts_in = PostStatusE.names
    result = [
        {
            'value': PostStatusE.DRAFT,
            'name': opts_in[PostStatusE.DRAFT],
            'class': 'onhold', 'selclass': 'onhold'
        },
        {
            'value': PostStatusE.PUBLISHED,
            'name': opts_in[PostStatusE.PUBLISHED],
            'class': 'btincluded', 'selclass': 'included'
        },
    ]

    if include_delete:
        result.append(
            {
                'value': SpecialStatusE.DELETE,
                'name': _("Delete"),
                'class': 'btrefused', 'selclass': 'refused'
            }
        )

    return result


# /event/add
@login_required
@csrf_protect
def add_event(request):
    c = get_c(request=request, active='list_events', path='/add')
    event = CalEvent(author=c['current_user'], status=PostStatusE.DRAFT)

    if request.method == 'POST':
        form = EventAdminForm(request.POST, instance=event)
        if form.is_valid():
            cd = form.cleaned_data

            images = request.FILES.getlist('image_event')
            if request.FILES.getlist('gif_image_event'):
                event.gif_image_file = request.FILES.getlist(
                    'gif_image_event')[0]
            event.last_modifier = c['current_user']
            event.modified_time = datetime.now()

            if request.FILES.getlist('poster_image_event'):
                event.poster_image_file = request.FILES.getlist(
                    'poster_image_event')[0]

            if cd['status'] == PostStatusE.PUBLISHED:
                event.validated_by = request.user
                event.validated_at = datetime.now()

            event.save()

            if images:
                event_image = EventImage(image_file=images[0], event=event)
                event_image.save()
                event.image = event_image

            event.save()
            event.refresh_from_db()

            messages.add_message(
                request, messages.INFO, "Event {} saved.".format(event.title)
            )

            return redirect('edit_event', event.id)
    else:
        form = EventAdminForm(instance=event)

    c['form'] = form
    c['event'] = event
    c['google_api_key'] = settings.GOOGLE_API_KEY
    c['action_url'] = reverse('add_event')
    c['pdg_title'] = "[New event]"
    c["pdg_options"] = _get_common_pdg_options(include_delete=False)
    c["max_upload_size"] = int(EventAdminForm.MAX_UPLOAD_SIZE / 1000)

    return render(request, "edit/event.html", c)


# /event/edit/{id}
@login_required
@csrf_protect
def edit_event(request, id):
    event = CalEvent.active.get(id=id)
    bc_path = [
        ('/', 'Home'),
        (reverse('list_events'), 'Wineposts'),
        (reverse('edit_event', args=[id]), event.title),
    ]

    c = get_c(
        request=request, active='list_events',
        path=None, bc_path_alt=bc_path
    )

    if request.method == 'POST':
        old_status = event.status
        form = EventAdminForm(request.POST, request.FILES, instance=event)

        if form.is_valid():
            cd = form.cleaned_data

            images = request.FILES.getlist('image_event')
            if request.FILES.getlist('poster_image_event'):
                event.poster_image_file = request.FILES.getlist(
                    'poster_image_event')[0]
            if request.FILES.getlist('gif_image_event'):
                event.gif_image_file = request.FILES.getlist(
                    'gif_image_event')[0]
            event.last_modifier = c['current_user']
            event.modified_time = datetime.now()

            if (
                cd['status'] == PostStatusE.PUBLISHED and
                old_status != PostStatusE.PUBLISHED
            ):
                event.validated_by = request.user
                event.validated_at = datetime.now()

            if images:
                event_image = EventImage(image_file=images[0], event=event)
                event_image.save()
                event.image = event_image

            event.save()
            event.refresh_from_db()

            messages.add_message(
                request, messages.INFO, "Event {} saved.".format(event.title)
            )

            return redirect('edit_event', event.id)
    else:
        form = EventAdminForm(instance=event)
    default_poster_image = settings.SITE_URL + static("assets/img/poster-placeholder.png")
    default_image = settings.SITE_URL + static("assets/img/horizontal-image-placeholder.png")
    default_gif_image = settings.SITE_URL + static("assets/img/animated-gif.png")
    c['form'] = form
    c['event'] = event
    c['loc_lat'] = event.loc_lat
    c['loc_lng'] = event.loc_lng
    c['image'] = aws_url(event.image, horizontal=True) if event.image else \
        default_image
    c['poster_image'] = aws_url(event.poster_image_file.name, poster=True) if \
        event.poster_image_file.name else default_poster_image
    c['gif_image'] = aws_url(event.gif_image_file.name) if \
        event.gif_image_file.name else default_gif_image
    c['google_api_key'] = settings.GOOGLE_API_KEY
    c['action_url'] = reverse('edit_event', args=[id])
    c['pdg_title'] = event.title

    c['saved_by'] = event.last_modifier
    c['saved_at'] = event.modified_time
    c['pdg_options'] = _get_common_pdg_options(include_delete=True)

    authority = event.validated_by if event.validated_by else event.last_modifier
    c['authority'] = authority if authority else None
    c['authority_name'] = authority.username if authority else 'External user'
    c['authority_id'] = authority.id if authority else None
    c['authority_avatar_url'] = aws_url(authority.image, thumb=True) \
        if authority else None
    c['max_upload_size'] = int(EventAdminForm.MAX_UPLOAD_SIZE / 1000)

    return render(request, "edit/event.html", c)
