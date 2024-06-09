from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.translation import ugettext as _

from web.models import Comment, CommentReadReceipt, Place, UserProfile
from web.utils.upload_tools import aws_url
from web_pro.utils.common import handle_provided_place_id, prepare_sidebar_data


# pro/reviews
@login_required(login_url='pro_login')
def reviews_likes(request, pid=None):
    res = handle_provided_place_id(request, pid)
    if res['redirect']:
        return res['redirect']

    context = prepare_sidebar_data(request, 'reviews')
    context['pid'] = pid
    context['establishment_owner_text'] = _('Establishment Owner')
    owner = Place.objects.get(pk=pid).owner
    context['establishment_owner_image'] = aws_url(
        owner.image, thumb=True
    ) if owner else None

    return render(request, "admin/reviews.html", context)


# pro/reviews/pid/read-all-for-user/uid
@login_required(login_url='pro_login')
def read_all_for_user(request, pid=None, uid=None):
    res = handle_provided_place_id(request, pid)

    if res['redirect']:
        return res['redirect']

    venue = Place.objects.get(pk=pid)

    try:
        UserProfile.objects.get(pk=uid)
    except UserProfile.DoesNotExist:
        return JsonResponse({}, status=404)

    if request.user != venue.owner:
        # logged in as an administrator, should not change the read reciepts
        return JsonResponse({})

    comments = Comment.objects.filter(
        place_id=venue.id,
        author=uid,
        is_archived=False,
        read_receipts=None
    )

    for comment in comments:
        CommentReadReceipt.objects.create(
            comment=comment,
            user=request.user
        )

    return JsonResponse({})


# pro/reviews/pid/get-total-unread/
@login_required(login_url='pro_login')
def get_total_unread(request, pid=None):
    res = handle_provided_place_id(request, pid)

    if res['redirect']:
        return JsonResponse({}, status=404)

    comments = Comment.objects.filter(
        place_id=pid,
        in_reply_to=None,
        is_archived=False,
        read_receipts=None
    ).count()

    return JsonResponse({'total': comments})
