from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from web.views.admin.common import get_c


@login_required
def donations(request):
    c = get_c(request=request, active='list_donations', path='/', add_new_url=None)
    return render(request, "lists/donations.html", c)
