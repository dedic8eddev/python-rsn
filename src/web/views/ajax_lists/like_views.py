from web.models import Like
from rest_framework.generics import ListCreateAPIView
from django.contrib.contenttypes.models import ContentType
from web.serializers.comments_likes import LikeReadSerializer, LikeCreateSerializer
from rest_framework.response import Response
from rest_framework import status


class LikeListView(ListCreateAPIView):
    model = Like
    queryset = Like.objects.all()
    serializer_class = LikeReadSerializer
    pagination_class = None

    def get_queryset(self, *args, **kwargs):
        content_type_model_name = self.kwargs.get('content_type_model_name')
        content_type_model_name = content_type_model_name.lower()
        content_type_id = ContentType.objects.get(model=content_type_model_name).id
        object_id = self.kwargs.get('object_id')
        likes = Like.objects.filter(
            content_type_id=content_type_id,
            object_id=object_id).order_by('-id')
        return likes

    def get_serializer_class(self, read=False):
        if self.request.method == 'POST':
            return LikeCreateSerializer
        return self.serializer_class

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        context = {'like_data': {}}
        like_data = context['like_data']
        content_type_model_name = kwargs.get('content_type_model_name')
        content_type_model_name = content_type_model_name.lower()
        content_type_id = ContentType.objects.get(model=content_type_model_name).id
        like_data["content_type_id"] = content_type_id
        like_data["object_id"] = kwargs.get('object_id')
        like_data["author_id"] = request.user.id
        serializer = self.get_serializer_class()
        serializer = serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=False)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
