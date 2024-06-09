from django.db.models import Q

from web.constants import PostTypeE
from web.models import Place, Post, UserImage
from web_pro.utils.common import get_owner_user, get_user_venue


class SettingsOperator:
    def __init__(self, request):
        self.request = request
        self.user = get_owner_user(request)
        self.venue = get_user_venue(self.user, request)
        self.files = request.FILES

    def get_phone_number(self):
        place = Place.active.filter(author=self.user).first()
        return place.phone_number if place else None

    def update_user_image(self, file):
        main_image = UserImage(
            image_file=file, user=self.user, author=self.user
        )
        main_image.save()
        self.user.image = main_image

    def remove_user_image(self):
        if self.user.image:
            self.user.image.archive()
            self.user.image = None

    def update_owner_details(self):
        owner_image = self.files.get('ownerImage', '')
        lang = self.request.POST.get('lang', 'en')
        currency = self.request.POST.get('currency', 'EUR')
        picture_removed_value = self.request.POST.get('picture-removed', '')
        picture_removed = True if picture_removed_value == '1' else False

        user_profile = self.user
        user_profile.lang = lang
        if currency != user_profile.currency:
            q_feat = Q(type=PostTypeE.WINE)
            q = Q(venues__id=self.venue.id) & q_feat
            posts = Post.objects.all().filter(q)
            for post in posts:
                post.currency = currency
                post.debug_save()
        user_profile.currency = currency

        if owner_image:
            self.update_user_image(owner_image)
        elif picture_removed:
            self.remove_user_image()

        user_profile.save()

    def update_company_image(self, file):
        main_image = UserImage(
            image_file=file, user=self.user, author=self.user
        )
        main_image.save()
        self.user.company_image = main_image

    def remove_company_image(self):
        if self.user.company_image:
            self.user.company_image.archive()
            self.user.company_image = None

    def update_company_details(self):
        company_image = self.files.get('companyImage', '')
        picture_removed_value = self.request.POST.get(
            'company-picture-removed', ''
        )

        picture_removed = True if picture_removed_value == '1' else False
        if company_image:
            self.update_company_image(company_image)
        elif picture_removed:
            self.remove_company_image()

        user = self.user
        user.save()
