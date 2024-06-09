import datetime

from django.db.models import Q
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from web.constants import PostTypeE, UserTypeE
from web.models import Place, Post
from web.serializers.wineposts import FoodPostSerializer, WinePostSerializer


class WinePostViewSet(viewsets.ModelViewSet):
    serializer_class = WinePostSerializer
    queryset = Post.active.filter(wine_id__isnull=False)

    def get_queryset(self):
        t = PostTypeE.WINE
        qs = Post.active.filter(
            type=t,
            wine_id__isnull=False
        )
        place_id = self.request.query_params.get('place_id')
        color = self.request.query_params.get('color')

        sort_by = self.request.query_params.get('sort_by')
        direction = self.request.query_params.get('direction', 'ASC')
        search_keyword = self.request.query_params.get('search_keyword')

        wines_page = self.request.query_params.get('wines_page')

        if place_id:
            try:
                place = Place.objects.get(pk=place_id)
            except Place.DoesNotExist:
                return Post.objects.none()

            qs = qs.filter(place_id=place_id)

            if wines_page == 'wines_by_users':
                owner_filter = Q(author__type=UserTypeE.USER)
            else:
                owner_filter = Q(author=place.owner) | Q(author__type=UserTypeE.ADMINISTRATOR) # noqa

            qs = qs.filter(owner_filter)
        if color:
            if color == 'sparkling':
                qs = qs.filter(wine__is_sparkling=True)
            else:
                # this will exclude all sparking wines from any other colors tab
                qs = qs.filter(wine__color=color).exclude(wine__is_sparkling=True)

        if search_keyword:
            qs = qs.filter(
                Q(wine__name__unaccent__icontains=search_keyword) |
                Q(wine__domain__unaccent__icontains=search_keyword) |
                Q(wine__winemaker__name_short__unaccent__icontains=search_keyword) |  # noqa
                Q(wine__winemaker__name__unaccent__icontains=search_keyword) |
                Q(wine_year__unaccent__icontains=search_keyword)
            )

        if sort_by:
            if sort_by == 'date':
                sorting_string = '-modified_time'
            elif sort_by in ['name', 'domain']:
                sorting_string = '{}{}'.format('wine__', sort_by)
            elif sort_by == 'winemaker':
                sorting_string = 'wine__winemaker__name'

            if direction == 'DESC' and sort_by != 'date':
                sorting_string = '-' + sorting_string
        else:
            sorting_string = '-modified_time'

        return qs.order_by(sorting_string).select_related('wine').all()


class FoodPostViewSet(viewsets.ModelViewSet):
    serializer_class = FoodPostSerializer
    queryset = Post.active.filter(type=PostTypeE.FOOD)

    def get_queryset(self):
        qs = Post.active.filter(type=PostTypeE.FOOD)
        place_id = self.request.query_params.get('place_id')

        sort_by = self.request.query_params.get('sort_by')
        direction = self.request.query_params.get('direction', 'ASC')
        search_keyword = self.request.query_params.get('search_keyword')

        if place_id:
            try:
                place = Place.objects.get(pk=place_id)
            except Place.DoesNotExist:
                return Post.objects.none()

            qs = qs.filter(place_id=place_id)

            qs = qs.filter(
                Q(author=place.owner) | Q(author__type=UserTypeE.ADMINISTRATOR)
            )

        if search_keyword:
            qs = qs.filter(
                Q(title__unaccent__icontains=search_keyword) |
                Q(description__unaccent__icontains=search_keyword)
            )

        if sort_by:
            if sort_by == 'date':
                sorting_string = '-modified_time'
            elif sort_by in ['title', 'description']:
                sorting_string = sort_by

                if direction == 'DESC':
                    sorting_string = '-' + sorting_string
        else:
            sorting_string = '-modified_time'

        return qs.order_by(sorting_string).all()


# /pro/ajax/v2/is-it-an-already-posted-wine
class PostedWineView(APIView):
    def get(self, *args, **kwargs):
        wine_name = self.request.query_params.get('wine_name')
        winemaker_name = self.request.query_params.get('winemaker_name')
        place_id = int(self.request.query_params.get('place_id'))

        if not (
                wine_name and
                winemaker_name and
                place_id and place_id > 0
        ):
            return Response(
                {'detail': 'Incorrect query parameters.',
                 'status_code': 400}
            )
        wine_name = wine_name.strip()
        winemaker_name = winemaker_name.strip()
        place = Place.active.get(pk=place_id)
        posts = place.posts
        year = None
        if self.request.query_params.get('year'):
            year = int(self.request.query_params.get('year'))
            if not 1900 < year <= datetime.datetime.now().year:
                return Response(
                    {'detail': 'The year value is not allowed. Use the value '
                               'for the year 1900 to the present.',
                     'status_code': 400}
                )

        if posts and year:
            existed_posts = posts.filter(
                is_archived=False,
                type=PostTypeE.WINE,
                author=place.owner,
                wine__name__unaccent__iexact=wine_name,
                wine__winemaker__name__unaccent__iexact=winemaker_name,
                wine_year=year
            )
        elif posts:
            existed_posts = posts.filter(
                is_archived=False,
                type=PostTypeE.WINE,
                author=place.owner,
                wine__name__unaccent__iexact=wine_name,
                wine__winemaker__name__unaccent__iexact=winemaker_name
            )
        else:
            return Response(
                {'detail': 'There are no wineposts for this place_id.',
                 'status_code': 404}
            )
        if existed_posts:
            return Response({'detail': True, 'status_code': 200})
        else:
            return Response({'detail': False, 'status_code': 200})
