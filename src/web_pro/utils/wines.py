from datetime import datetime

from django.conf import settings

from web.constants import (PostStatusE, PostTypeE, WineColorE,
                           WinemakerStatusE, WineStatusE,
                           get_post_status_for_wine_status, UserTypeE)
from web.models import Post, PostImage, UserProfile, Wine, WineImage, Winemaker
from web.utils.common_winepost import set_other_posts_as_non_parents
from web.utils.model_tools import get_float_dot_or_comma, make_winepost_title
from web.utils.views_common import is_privileged_account
from web_pro.utils.common import get_owner_user, get_user_venue


class WineModelOperator:
    def __init__(self, request):
        self.user = get_owner_user(request)
        self.request_user = request.user
        self.data = self.prepare_data(request)
        self.file = request.FILES
        self.venue = get_user_venue(request.user.id, request)

    def get_post_object(self):
        return Post.active.get(id=self.data['postId'])

    def prepare_data(self, request):
        data = request.POST.dict() or request.GET.dict()
        changed_wine_name = data.get('n-ame-typeahead', '')
        if changed_wine_name:
            data['wineName'] = changed_wine_name
        return data

    def get_anchor(self):
        if self.data['postType'] == 'delete':
            return ''

        wine_color = self.data.get('wineColor', None)
        if not wine_color:
            post = self.get_post_object()
            return '#sparkling' if post.wine.is_sparkling else post.wine.color

        return '#sparkling' if self.data.get(
            'isSparkling', None
        ) else '#' + WineColorE.names[int(wine_color)].lower()

    def get_parameters(self, cast_to_int=False):
        color = self.data.get('wineColor', [])
        year = self.data.get('wineYear', [])
        is_sparkling = self.data.get('isSparkling', [])
        if cast_to_int:
            return int(color), int(year), is_sparkling

        return color, year, is_sparkling

    def get_or_create_winemaker(self):
        created = False
        winemaker_name = self.data['wineWinemaker']
        domain = self.data['wineDomain']
        winemaker = Winemaker.active.filter(
            name__unaccent__iexact=winemaker_name
        ).first()

        if not winemaker:
            winemaker = Winemaker(
                name=winemaker_name,
                domain=domain,
                author=self.request_user,
                status=WinemakerStatusE.DRAFT
            )
            winemaker.save()
            winemaker.refresh_from_db()
            created = True

        return winemaker, created

    def get_wine_criteria(self, winemaker, with_wine_id=False):
        color, year, is_sparkling = self.get_parameters(cast_to_int=True)
        criteria = {
            'name__unaccent__iexact': self.data['wineName'],
            'grape_variety__unaccent__iexact': self.data['wineGrapeVariety'],
            'domain__unaccent__iexact': self.data['wineDomain'],
            'color': color,
            'is_sparkling': bool(is_sparkling),
            'winemaker': winemaker,
        }

        if with_wine_id and self.data.get('wineId'):
            criteria['id'] = self.data['wineId']

        return criteria

    def create_new_wine(self, winemaker):
        color, year, is_sparkling = self.get_parameters(cast_to_int=True)

        wine = Wine(
            author=self.request_user,
            status=WineStatusE.ON_HOLD,
            name=self.data['wineName'],
            domain=self.data['wineDomain'],
            grape_variety=self.data['wineGrapeVariety'],
            color=color,
            year=year,
            is_sparkling=bool(is_sparkling),
            winemaker=winemaker
        )
        wine.save()
        wine.refresh_from_db()

        return wine

    def create_winepost(self, wine, wp_status, is_parent_post=True):
        color, year, is_sparkling = self.get_parameters(cast_to_int=True)

        winepost = Post(
            author=self.request_user,
            status=wp_status,
            type=PostTypeE.WINE,
            is_parent_post=is_parent_post,
            title=make_winepost_title(self.data['wineName'], year),
            grape_variety=self.data['wineGrapeVariety'],
            wine=wine,
            wine_year=year,
            free_so2=None,
            total_so2=None,
            place=self.venue if self.venue else None,
            team_comments=self.data['wineComment'],
            price=self.get_safe_price(self.data['wine-price']),
            currency=self.user.currency if self.user.currency else 'EUR',
        )
        winepost.save()
        winepost.refresh_from_db()

        return winepost

    def update_wine_object(self, wine, winemaker):
        wine.winemaker = winemaker
        wine.name = self.data.get('wineName', wine.name)
        wine.domain = self.data.get('wineDomain', wine.domain)
        wine.grape_variety = self.data.get(
            'wineGrapeVariety', wine.grape_variety
        )

        color, year, is_sparkling = self.get_parameters()
        wine.is_sparkling = bool(is_sparkling)
        wine.year = int(year) if year else wine.year
        wine.color = int(color) if color else wine.color
        wine.modified_time = datetime.now()

        wine.save()
        wine.refresh_from_db()

    def remove_image(self, post):
        if post.is_parent_post and post.wine.main_image:
            post.wine.main_image.archive()
            post.wine.main_image = None

        if post.main_image:
            post.main_image.archive()
            post.main_image = None

    def update_image(self, post, file, parent=True):
        if parent:
            main_image = WineImage(
                image_file=file, wine=post.wine, author=self.request_user
            )
            main_image.save()
            post.wine.main_image = main_image

        main_image_post = PostImage(
            image_file=file, post=post, author=self.request_user
        )
        main_image_post.save()
        post.main_image = main_image_post

    def edit_child_post(self, winepost, winemaker):
        new_wine = winepost.wine.clone_as_new_draft()
        self.update_wine_object(new_wine, winemaker)

        winepost.wine = new_wine
        winepost.team_comments = self.data.get(
            'wineComment', winepost.team_comments
        )
        winepost.is_parent_post = True

    def add_wine_post(self):
        wine = None
        file = self.file.get('imageFile', [])
        winemaker, wm_created = self.get_or_create_winemaker()

        if not wm_created:
            # if wineId was provided in POST we first check whether the wine
            # with such id exists and whether its data matches with the
            # values from the form inputs.
            if self.data.get('wineId'):
                criteria = self.get_wine_criteria(winemaker, with_wine_id=True)
                wine = Wine.active.filter(**criteria).order_by('-id').first()
                # the wine with specified wineId AND matching criteria was
                # NOT found - searching for wine
                # which data matches the values from the form inputs.
                if not wine:
                    criteria = self.get_wine_criteria(
                        winemaker, with_wine_id=False
                    )
                    wine = Wine.active.filter(**criteria).order_by('-id').first()  # noqa
            # wineId was NOT set - we just search for the wine which data
            # matches the values from the form inputs.
            else:
                criteria = self.get_wine_criteria(
                    winemaker, with_wine_id=False
                )
                wine = Wine.active.filter(**criteria).order_by('-id').first()

        if wine:
            is_parent_post = False
            wp_status = get_post_status_for_wine_status(wine.status)
        else:
            is_parent_post = True
            wp_status = PostStatusE.DRAFT
            wine = self.create_new_wine(winemaker)

        winepost = self.create_winepost(
            wine, wp_status, is_parent_post=is_parent_post
        )

        if not winepost:
            return {}

        if file:
            self.update_image(winepost, file, parent=is_parent_post)
            winepost.save()
            winepost.push_to_timeline(
                is_new=True, is_sticky=is_privileged_account(winepost.author)
            )
            winepost.refresh_from_db()

    def get_safe_price(self, price):
        return get_float_dot_or_comma(price)

    def edit_wine_post(self):
        file = self.file.get('imageFile', [])
        picture_removed_value = self.data.get('picture-removed', '')
        picture_removed = True if picture_removed_value == '1' else False

        post = self.get_post_object()

        if post.status == PostStatusE.DRAFT or \
                self.request_user.type == UserTypeE.ADMINISTRATOR or \
                self.request_user.type == UserTypeE.EDITOR:
            winemaker, wm_created = self.get_or_create_winemaker()

            if post.is_parent_post:
                self.update_wine_object(post.wine, winemaker)
                set_other_posts_as_non_parents(post.wine, post)
            else:
                self.edit_child_post(post, winemaker)

            post.title = f"{post.wine.name} {post.wine_year}" if post.wine_year else post.wine.name  # noqa
            # post must be SAVED before file operations can be done on it;
            # in the case of changing wine for example
            post.save()
            post.refresh_from_db()

            post.team_comments = self.data.get('wineComment', post.team_comments) # noqa

        elif self.request_user.type == UserTypeE.OWNER:
            winemaker, wm_created = self.get_or_create_winemaker()
            if post.is_parent_post:
                color, year, is_sparkling = self.get_parameters()
                post.wine.year = int(year) if year else post.wine.year
                post.wine.save()
                post.wine.refresh_from_db()
                set_other_posts_as_non_parents(post.wine, post)
            else:
                self.edit_child_post(post, winemaker)

            post.title = f"{post.wine.name} {post.wine_year}" if post.wine_year else post.wine.name  # noqa
            # post must be SAVED before file operations can be done on it;
            # in the case of changing wine for example
            post.save()
            post.refresh_from_db()

        # file replacement/removal locked on the Front-end
        # for non ADMINISTRATORS
        if file:
            self.update_image(post, file, parent=post.is_parent_post)
        elif picture_removed:
            self.remove_image(post)

        post.wine_year = post.wine.year
        post.modified_time = datetime.now()
        post.price = self.get_safe_price(self.data.get('wine-price'))
        post.currency = self.user.currency if self.user.currency else 'EUR'

        post.save()
        post.refresh_from_db()

    def delete_wine_post(self):
        post = self.get_post_object()
        if (
            post.is_parent_post and
            settings.MOVE_PARENT_POSTS_ON_APP_DELETE and
            settings.ADMIN_PROFILE_USERNAME
        ):
            admin_profile = UserProfile.active.filter(
                username=settings.ADMIN_PROFILE_USERNAME
            ).first()
            if admin_profile:
                post.author = admin_profile
                post.place_id = None
                post.save()
                post.delete_related_items()
                post.delete_from_timeline()
            else:
                post.archive()
        else:
            post.archive()
            post.refresh_from_db()


def get_wine_post_data(post_id, user):
    wine_info = {}
    post = Post.active.get(id=post_id, type=PostTypeE.WINE)
    wine = post.wine

    obj_attributes = (
        'name', 'domain', 'color', 'is_sparkling', 'grape_variety'
    )

    for obj_attribute in obj_attributes:
        wine_info[obj_attribute] = getattr(wine, obj_attribute)

    wine_info['winemakers'] = wine.winemaker.name
    wine_info['comment'] = post.team_comments
    wine_info['price'] = post.price
    wine_info['year'] = post.wine_year
    wine_info['all_editable'] = user.type == UserTypeE.ADMINISTRATOR

    return {'result': wine_info}
