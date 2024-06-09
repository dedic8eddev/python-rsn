from django.db.models import OuterRef, Q, Subquery
from rest_framework import viewsets

from web.constants import UserTypeE
from web.models import Comment, LikeVote, Place, UserProfile
from web.serializers.places import (CommentSerializer, PlaceCommentSerializer,
                                    PlaceLikeSerializer, PlaceReviewSerializer)


class PlaceLikeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PlaceLikeSerializer
    queryset = LikeVote.objects.none()

    def get_sorting_string(self, sort_by, direction):
        if not sort_by:
            return '-created_time'

        config = {
            'date': '-created_time',
            'name': 'author__full_name',
            'username': 'author__username',
        }

        sorting_string = config[sort_by]

        if direction != 'DESC' or sort_by == 'date':
            return sorting_string

        return '-' + sorting_string

    def get_queryset(self):
        # unique users!!!
        place_id = self.request.query_params.get('place_id', None)
        sort_by = self.request.query_params.get('sort_by', None)
        direction = self.request.query_params.get('direction', 'ASC')
        search_keyword = self.request.query_params.get('search_keyword', None)

        if not place_id:
            return LikeVote.objects.none()

        qs = LikeVote.objects.filter(place_id=place_id)

        if search_keyword:
            qs = qs.filter(
                Q(place_id=place_id) & Q(is_archived=False) &
                Q(
                    Q(author__username__unaccent__icontains=search_keyword) |
                    Q(author__full_name__unaccent__icontains=search_keyword)
                )
            )
        else:
            qs = qs.filter(place_id=place_id, is_archived=False)

        sorting_string = self.get_sorting_string(sort_by, direction)

        return qs.order_by(sorting_string).select_related('author').all()


class PlaceReviewViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PlaceReviewSerializer
    queryset = UserProfile.objects.none()

    def get_sorting_string(self, sort_by, direction):
        if not sort_by:
            return '-newest_comment_date'

        config = {
            'date': '-newest_comment_date',
            'name': 'full_name',
            'username': 'username',
        }

        sorting_string = config[sort_by]

        if direction != 'DESC' or sort_by == 'date':
            return sorting_string

        return '-' + sorting_string

    def get_queryset(self):
        place_id = self.request.query_params.get('place_id', None)
        sort_by = self.request.query_params.get('sort_by', None)
        direction = self.request.query_params.get('direction', 'ASC')
        search_keyword = self.request.query_params.get('search_keyword', None)

        if not place_id:
            return UserProfile.objects.none()

        try:
            place = Place.objects.get(pk=place_id)
        except Place.DoesNotExist:
            return UserProfile.objects.none()

        newest_comments = Comment.objects.filter(
            author_id=OuterRef('id'),
            is_archived=False,
            place_id=place_id,
        ).exclude(author_id=place.owner.id).order_by('-created_time')

        qs = UserProfile.objects.annotate(
            newest_comment_date=Subquery(
                newest_comments.values('created_time')[:1]
            ),
            newest_comment_text=Subquery(
                newest_comments.values('description')[:1]
            )
        ).filter(
            newest_comment_date__isnull=False
        ).exclude(
            place__owner__place__id=place_id
        )

        if search_keyword:
            qs = qs.filter(
                Q(username__unaccent__icontains=search_keyword) |
                Q(full_name__unaccent__icontains=search_keyword) |
                Q(newest_comment_text__unaccent__icontains=search_keyword)
            )

        sorting_string = self.get_sorting_string(sort_by, direction)

        return qs.order_by(sorting_string).all()


class PlaceCommentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PlaceCommentSerializer
    queryset = Comment.objects.none()

    def get_queryset(self):
        place_id = self.request.query_params.get('place_id', None)
        user_id = self.request.query_params.get('user_id', None)

        if not place_id or not user_id:
            return Comment.objects.none()

        try:
            place = Place.objects.get(pk=place_id)
            UserProfile.objects.get(pk=user_id)
        except (Place.DoesNotExist, UserProfile.DoesNotExist):
            return Comment.objects.none()

        return Comment.objects.filter(
            Q(
                Q(author_id=place.owner.id, in_reply_to=user_id) | Q(author_id=user_id)  # noqa
            ) & Q(is_archived=False, place_id=place_id)
        ).order_by('created_time').all()


class OwnerCommentViewset(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    queryset = Comment.objects.none()

    def get_queryset(self):
        place_id = self.request.query_params.get('place_id', None)
        user = self.request.user

        if not place_id:
            return Comment.objects.filter(author_id=user.id)

        try:
            place = Place.objects.get(pk=place_id)
        except Place.DoesNotExist:
            return Comment.objects.none()

        if (user.type != UserTypeE.OWNER) or (user.id != place.owner.id):
            return Comment.objects.none()

        return Comment.objects.filter(
            author_id=user.id,
            is_archived=False,
            place_id=place_id
        ).order_by('created_time').all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)
