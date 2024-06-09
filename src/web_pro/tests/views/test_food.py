import pytest
from django.urls import reverse

from web.factories import FoodPostFactory
from web.models import Post
from web.tests.api.utils import assert_response_status_code
from web_pro.tests.test_data.food import FoodPostData


@pytest.mark.django_db
class TestAddFood:
    def setup(self):
        self.url = reverse('pro_post_food')
        self.data = FoodPostData()

    def test_not_logged_in(self, client):
        payload = self.data.get_add_food_payload()
        response = client.post(self.url, payload)
        assert not Post.objects.all()
        assert response.url == '/login?next=/pro/food/post'

    def test_no_add_parameter(self, client, logged_user):
        payload = self.data.get_add_food_payload()
        payload.pop('postType')
        response = client.post(self.url, payload)
        assert not Post.objects.all()
        assert response.url == '/pro/food'

    def test_adding(self, client, logged_user):
        payload = self.data.get_add_food_payload()
        response = client.post(self.url, payload)
        assert_response_status_code(response, 302)
        added_food_post = Post.objects.all()[0]
        assert added_food_post.description == payload['foodName']

    def test_adding_existing(self, client, logged_user):
        food_post = get_food_post(logged_user)
        payload = self.data.get_add_existing_food_payload(food_post)

        response = client.post(self.url, payload)
        assert_response_status_code(response, 302)

        food_posts = Post.objects.all()

        assert len(food_posts) == 2
        assert food_posts[0].description == food_posts[1].description


@pytest.mark.django_db
class TestEditFood:
    def setup(self):
        self.url = reverse('pro_post_food')
        self.data = FoodPostData()

    def test_not_logged_in(self, client):
        payload = self.data.get_food_template('edit')
        response = client.post(self.url, payload)
        assert response.url == '/login?next=/pro/food/post'

    def test_editing(self, client, logged_user):
        food_post = get_food_post(logged_user)
        payload = self.data.get_edit_food_payload(food_post)

        response = client.post(self.url, payload)
        assert_response_status_code(response, 302)

        posts = Post.objects.all()

        assert len(posts) == 1
        assert posts[0].description == payload['foodDescription']

    def test_editing_parent_post(self, client, logged_user):
        food_post = get_food_post(logged_user, is_parent_post=True)
        payload = self.data.get_edit_food_payload(food_post)

        response = client.post(self.url, payload)
        assert_response_status_code(response, 302)

        posts = Post.objects.all()

        assert len(posts) == 1
        assert posts[0].description == payload['foodDescription']


@pytest.mark.django_db
class TestDeleteFood:
    def setup(self):
        self.url = reverse('pro_post_food')
        self.data = FoodPostData()

    def test_delete(self, client, logged_user):
        food_post = get_food_post(logged_user)
        payload = self.data.get_delete_food_payload(food_post)

        response = client.post(self.url, payload)
        assert_response_status_code(response, 302)

        post = Post.objects.all()[0]
        assert post.is_archived

    def test_delete_parent_post(self, client, logged_user):
        food_post = get_food_post(logged_user, is_parent_post=True)
        payload = self.data.get_delete_food_payload(food_post)

        response = client.post(self.url, payload)
        assert_response_status_code(response, 302)

        post = Post.objects.all()[0]
        assert post.is_archived


def get_food_post(logged_user, is_parent_post=False):
    food_post = FoodPostFactory(author=logged_user)
    if is_parent_post:
        food_post.is_parent_post = True
        food_post.save()
    return food_post
