import datetime as dt
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from web.models import FreeGlassEvent, Place
from web.views.admin.common import get_c
from web.forms.admin_forms import FreeGlassEventForm


# /free-glass-events/edit
@login_required
@csrf_protect
def edit_free_glass_event(request):
    c = get_c(request=request, active='edit_free_glass_event', path='/free-glass-event', add_new_url=None)

    evts = FreeGlassEvent.active.all()
    if evts:
        evt = evts[0]
    else:
        evt = FreeGlassEvent(
            author=request.user,
            start_date=dt.date(year=2018, month=9, day=1),
            end_date=dt.date(year=2018, month=9, day=30),
            announcement_date=dt.date(year=2018, month=8, day=20),
            name="Free Glass of Natural Wine"
        )
        evt.save()
        evt.refresh_from_db()

    data_in = {
        'name': evt.name,
        'start_date': evt.start_date.strftime('%Y-%m-%d') if evt.start_date else None,
        'end_date': evt.end_date.strftime('%Y-%m-%d') if evt.end_date else None,
        'announcement_date': evt.announcement_date.strftime('%Y-%m-%d') if evt.announcement_date else None,
        # 'map_fullscreen_end_date': evt.map_fullscreen_end_date.strftime('%Y-%m-%d'),
    }

    if request.method == 'POST':
        form = FreeGlassEventForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            evt.name = cd['name']
            evt.start_date = cd['start_date']
            evt.end_date = cd['end_date']
            # evt.map_fullscreen_end_date = cd['map_fullscreen_end_date']
            evt.announcement_date = cd['announcement_date']

            evt.save()
            evt.refresh_from_db()
    else:
        form = FreeGlassEventForm(data=data_in)

    c['form'] = form
    c["pdg_title"] = evt.name
    c["pdg_author"] = evt.author
    c["saved_by"] = evt.author
    c["saved_at"] = evt.modified_time
    c["pdg_created_at"] = evt.created_time
    c["pdg_validated_at"] = evt.created_time
    c["pdg_validated_by"] = evt.created_time
    c['total_records_places'] = Place.active.all().count()

    return render(request, "edit/free-glass-event.html", c)


# /est-free-glass
@login_required
def est_free_glass(request):
    bc_path = [
        ('/', 'Home'),
        (reverse('list_places'), 'places'),
        (reverse('list_est_free_glass'), 'Free Glass'),
    ]

    c = get_c(request=request, active='list_places', sub_active='list_est_comments',
              path="places/est-com",
              bc_path_alt=bc_path,
              add_new_url=None)

    c['total_records_places'] = Place.active.all().count()
    return render(request, "lists/est-free-glass.html", c)
