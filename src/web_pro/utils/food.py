from datetime import datetime

from web.constants import PostStatusE, PostTypeE
from web.models import Post, PostImage
from web_pro.utils.common import get_owner_user, get_user_venue


class FoodModelOperator:
    def __init__(self, request):
        self.data = request.POST.dict()
        self.user = get_owner_user(request)
        self.file = request.FILES
        self.venue = get_user_venue(request.user.id, request)

    def get_food_post_object(self):
        return Post.objects.get(id=self.data['foodId'])

    def create_food_post(self):
        food_post = Post(
            author=self.user,
            status=PostStatusE.PUBLISHED,
            type=PostTypeE.FOOD,
            title=self.data['foodName'],
            description=self.data['foodDescription'],
            place=self.venue,
            published_time=datetime.now()
        )
        food_post.save()
        food_post.refresh_from_db()

        return food_post

    def add_food_post(self):
        file = self.file.get('imageFile', [])
        post = self.create_food_post()

        if file:
            self.update_image(post, file)

        post.save()

    def edit_food_post(self):
        file = self.file.get('imageFile', [])
        picture_removed_value = self.data.get('picture-removed', '')
        picture_removed = picture_removed_value == '1'

        post = self.get_food_post_object()

        post.title = self.data.get('foodName', post.title)
        post.description = self.data.get('foodDescription', post.description)
        post.modified_time = datetime.now()

        if file:
            self.update_image(post, file)
        elif picture_removed:
            self.remove_image(post)

        post.save()

    def delete_food_post(self):
        post = self.get_food_post_object()
        post.archive()

    def remove_image(self, post):
        if post.main_image:
            post.main_image.archive()
            post.main_image = None

    def update_image(self, post, file):
        main_image = PostImage(
            image_file=file, post=post, author=self.user
        )
        main_image.save()
        post.main_image = main_image
