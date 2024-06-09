from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Case, CharField, Q, When
from django.http import JsonResponse
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, mixins, status
# from rest_framework.authentication import BasicAuthentication
from rest_framework.response import Response

# from web.authentication import CsrfExemptSessionAuthentication
from web.constants import PostTypeE
from web.forms.admin_forms import CommentEditForm
from web.models import Comment, CmsAdminComment
from web.serializers.comments_likes import AdminCommentReadSerializer, \
    AdminCommentCreateSerializer, AdminCommentEditSerializer
from web.utils.upload_tools import aws_url
from web.utils.views_common import get_current_user
from web.views.ajax_lists.common import (
    ajax_list_control_with_search_and_ordering, ajax_list_get_offsets)
from web.views.ajax_lists.formatting import format_img_html


# /ajax/comments/edit-update
@csrf_exempt
@login_required
def comments_edit_update(request):
    get_current_user(request)
    form1 = CommentEditForm(request.POST)
    if form1.is_valid():
        cd = form1.cleaned_data
        id = cd['id']
        desc = cd['description']
        comment = Comment.objects.get(id=id)
        comment.description = desc
        comment.save()
        comment.refresh_from_db()
        return JsonResponse({
            'id': id,
            'description': comment.description,
        })


# /ajax/comments/edit-open
@csrf_exempt
@login_required
def comments_edit_open(request):
    get_current_user(request)
    form1 = CommentEditForm(request.POST)
    if form1.is_valid():
        cd = form1.cleaned_data
        id = cd['id']
        comment = Comment.objects.get(id=id)
        return JsonResponse({
            'id': id,
            'description': comment.description,
        })


# /ajax/usercomment/items/{uid}
@csrf_exempt
@login_required
def get_usercomment_items(request, uid):
    get_current_user(request)
    col_map = {
        0: None,  # 'id',
        1: None,  # 'picture',
        2: 'modified_time',   # date
        3: 'object_name',  # name of place or winepost
        4: 'description',
        5: None,   # actions
    }

    page = None
    limit = None
    order_by = ['-modified_time']
    start = None
    length = None
    (
        page, limit, start, length, search_value, order_by
    ) = ajax_list_control_with_search_and_ordering(
        request,
        col_map=col_map
    )

    filters = Q(author_id=uid)

    if search_value is not None:
        search_filters = (
            Q(place__name__unaccent__contains=search_value) |
            Q(post__title__unaccent__contains=search_value) |
            Q(wine__name__unaccent__contains=search_value)
        )

        filters &= search_filters

    (offset_0, offset_n) = ajax_list_get_offsets(start, length, page, limit)

    comments = Comment.objects.annotate(
        object_name=Case(
            When(place_id__isnull=False, then='place__name'),
            When(cal_event_id__isnull=False, then='cal_event__title'),
            When(post_id__isnull=False, then='post__title'),
            When(
                Q(wine_id__isnull=False) & Q(post_id__isnull=True),
                then='wine__name'
            ),
            output_field=CharField()
        )
    ).filter(filters).order_by(*order_by)

    total_count = comments.count()
    comments = comments[offset_0:offset_n]
    items_out = []

    for comment in comments:
        actions = \
            '<a href="#" title="%(edit_title)s" id="edit_comment_%(comment_id)s" ' \
            'class="btn btn-xs btn-outline btn-danger add-tooltip" data-placement="top" data-toggle="tooltip" ' \
            'style="margin-right: 10px;"> <i class="fa fa-pencil"></i></a>' \
            '<a href="#" title="%(del_title)s" id="delete_comment_%(comment_id)s" ' \
            'class="btn btn-xs btn-outline btn-danger add-tooltip" data-placement="top" data-toggle="tooltip" >' \
            '<i class="fa fa-trash-o"></i></a>' % {'comment_id': comment.id,
                                                   'edit_title': _('Edit'),
                                                   'del_title': _('Delete')}

        cb = '<input id="colors-%d-toggle-1" name="ids" value="{}" type="checkbox" disabled="disabled">'  # noqa

        if comment.place:
            name = comment.place.name
            image_html = format_img_html(
                comment.place.main_image, alt_text=name
            )
            object_type = 'Place'
            object_url = reverse('edit_place', args=[comment.place_id])
        elif comment.cal_event:
            name = comment.event.title
            tpl = '<a href="{}" data-toggle="lightbox"><img width="70" height="70" src="{}" /></a>'  # noqa
            image_html = tpl.format(
                aws_url(comment.event.image),
                aws_url(comment.event.image, thumb=True)
            )
            object_url = reverse('edit_event', args=[comment.cal_event_id])
            object_type = 'Event'
        elif comment.post:
            name = comment.post.title
            image_html = format_img_html(
                comment.post.main_image, alt_text=name
            )
            object_type = 'Post'
            if comment.post.type == PostTypeE.FOOD:
                to_reverse = 'edit_foodpost'
            if comment.post.type == PostTypeE.NOT_WINE:
                to_reverse = 'edit_generalpost'
            if comment.post.type == PostTypeE.WINE:
                to_reverse = 'edit_winepost'

            object_url = reverse(to_reverse, args=[comment.post_id])
        else:
            name = comment.wine.name
            image_html = format_img_html(
                comment.wine.main_image, alt_text=name
            )
            object_type = 'Wine'
            object_url = '#'

        object_html = '<a href="{url}">[{type}]: {name}</a>'.format(
            url=object_url,
            type=object_type,
            name=name
        )

        items_out.append(
            {
                'checkbox_id': cb.format(comment.id),
                'img_html': image_html,
                'date': comment.modified_time.strftime('%d %b %Y %H:%M'),
                'name': object_html,
                'comment': comment.description,
                'actions': actions,
            }
        )

    return JsonResponse({
        "iTotalRecords": total_count,
        "iTotalDisplayRecords": total_count,
        "data": items_out
    })


# /ajax/admincomments/items/{content_type_id}/{object_id}
class CommentList(generics.ListCreateAPIView):
    """
    List first level comments for object or create new comment for object
    """
    # authentication_classes = (
    #     CsrfExemptSessionAuthentication, BasicAuthentication)
    serializer_class = AdminCommentReadSerializer
    pagination_class = None

    def get_queryset(self, *args, **kwargs):
        content_type_model_name = self.kwargs.get('content_type_model_name')
        content_type_model_name = content_type_model_name.lower()
        content_type_id = ContentType.objects.get(model=content_type_model_name).id
        object_id = self.kwargs.get('object_id')
        comments = CmsAdminComment.objects.filter(
            content_type_id=content_type_id,
            object_id=object_id).order_by('-id')
        return comments

    def get_serializer_class(self, read=False):
        if self.request.method == 'POST':
            return AdminCommentCreateSerializer
        return self.serializer_class

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        context = {'comment_data': {}}
        comment_data = context['comment_data']
        content_type_model_name = kwargs.get('content_type_model_name')
        content_type_model_name = content_type_model_name.lower()
        content_type_id = ContentType.objects.get(model=content_type_model_name).id
        comment_data["content_type_id"] = content_type_id
        comment_data["object_id"] = kwargs.get('object_id')
        comment_data["author_id"] = request.user.id
        serializer = self.get_serializer_class()
        serializer = serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=False)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


# /ajax/admincomments/{pk}
class CommentDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin, generics.GenericAPIView):
    serializer_class = AdminCommentEditSerializer
    queryset = CmsAdminComment.objects.all()

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        if self.get_object().author == request.user:
            return self.update(request, *args, **kwargs)
        else:
            return Response('Custom error: Non-author user tries to update '
                            'a comment.', status=status.HTTP_403_FORBIDDEN)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return Response('Custom error: Non-author user tries to delete '
                            'a comment.', status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
