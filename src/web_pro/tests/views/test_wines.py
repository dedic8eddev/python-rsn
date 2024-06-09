import pytest
from django.urls import reverse

from web.factories import WinePostFactory, WineFactory, WineMakerFactory
from web.models import Wine, Post
from web_pro.tests.test_data.wine import WineTestData
from web_pro.tests.test_data.utils import Utils, get_image_name


@pytest.mark.django_db
class TestAddWine(Utils):
    def setup(self):
        self.url = reverse('pro_post_wine')
        self.data = WineTestData()

    def test_not_logged_in(self, client):
        payload = self.data.get_add_wine_payload(10)
        response = client.post(self.url, payload)
        assert not Wine.objects.all()
        assert response.url == '/login?next=/pro/wines/post'

    def test_no_add_parameter(self, client, logged_user):
        payload = self.data.get_add_wine_payload(10)
        payload.pop('postType')
        response = client.post(self.url, payload)
        assert not Wine.objects.all()
        assert response.url == '/pro/wines'

    def test_add_wine(self, client, logged_user):
        for e, wine_color in enumerate((10, 20, 30, 40, 40)):
            sparkling = True if e == 4 else False

            payload = self.data.get_add_wine_payload(wine_color, sparkling)
            self.assert_post_response(client, payload, 302)

            added_wine = Wine.objects.all()[e]
            assert_wine_post_fields(added_wine, payload)

        for post in Post.objects.all():
            assert post.is_parent_post

    def test_add_existing_wine(self, client, logged_user):
        winepost = get_winepost(logged_user)

        payload = self.data.get_add_existing_wine_payload(winepost)
        self.assert_post_response(client, payload, 302)

        wines = Wine.objects.all()
        posts = Post.objects.all()

        assert len(wines) == 1
        assert not posts[1].is_parent_post
        assert_wine_post_fields(wines[0], payload, posts[1])

    def test_add_wine_existing_winemaker(self, client, logged_user):
        winemaker = WineMakerFactory(author=logged_user)

        payload = self.data.get_add_wine_payload(10)
        payload['wineWinemaker'] = winemaker.name
        self.assert_post_response(client, payload, 302)

        wines = Wine.objects.all()
        posts = Post.objects.all()

        assert len(wines) == 1
        assert wines.first().name == payload['wineName']
        assert posts.first().is_parent_post
        assert_wine_post_fields(wines.first(), payload, posts.first(),  wine_image=True, post_image=False)

@pytest.mark.django_db
class _TestEditWine(Utils):
    def setup(self):
        self.url = reverse('pro_post_wine')
        self.data = WineTestData()

    def test_not_logged_in(self, client):
        payload = self.data.get_wine_template('edit')
        response = client.post(self.url, payload)
        assert response.url == '/login?next=/pro/wines/post'

    def test_color_editing(self, client, logged_user):
        winepost = get_winepost(logged_user)
        winemaker = get_winemaker(logged_user)

        colors = (20, 30, 40, 10)
        for color in colors:
            payload = self.data.get_edit_wine_payload(winepost, color=color, winemaker=winemaker)
            self.assert_post_response(client, payload, 302)

            posts = Post.objects.all()
            wines = Wine.objects.all()

            assert len(wines) == 2
            assert wines[1].name == payload['wineName']
            assert posts.first().wine == wines[1]

            assert len(wines) == 2
            assert_wine_post_fields(wines[1], payload, posts.first())

    def test_editing_parent_post(self, client, logged_user):
        winepost = get_winepost(logged_user, is_parent_post=True)

        colors = (20, 30, 40, 10)
        for color in colors:
            payload = self.data.get_edit_wine_payload(winepost, color=color)
            self.assert_post_response(client, payload, 302)

            posts = Post.objects.all()
            wines = Wine.objects.all()

            assert len(wines) == 1
            assert wines.first().name == payload['wineName']
            assert posts.first().wine == wines.first()

            assert len(wines) == 1
            assert_wine_post_fields(wines.first(), payload, posts.first())


@pytest.mark.django_db
class _TestDeleteWine(Utils):
    def setup(self):
        self.url = reverse('pro_post_wine')
        self.data = WineTestData()

    def test_delete(self, client, logged_user):
        winepost = get_winepost(logged_user)

        payload = self.data.get_delete_wine_payload(winepost)
        self.assert_post_response(client, payload, 302)

        post = Post.objects.all().first()
        assert post.is_archived

    def test_delete_parent_post(self, client, logged_user):
        winepost = get_winepost(logged_user, is_parent_post=True)

        payload = self.data.get_delete_wine_payload(winepost)
        self.assert_post_response(client, payload, 302)

        post = Post.objects.all().first()
        assert post.is_archived


def get_winepost(logged_user, is_parent_post=False):
    winepost = WinePostFactory(author=logged_user, wine=WineFactory(author=logged_user))
    if is_parent_post:
        winepost.is_parent_post = True
        winepost.save()
    return winepost


def get_winemaker(logged_user):
    return WineMakerFactory(author=logged_user)


def assert_image(image_name, object, validate=False):
    if image_name and validate:
        assert image_name in str(object.main_image)
    else:
        assert not object.main_image


def assert_wine_post_fields(wine, payload, post=None, wine_image=True, post_image=True):
    wine_keys = {
        'wineName': 'name',
        'wineDomain': 'domain',
        'wineYear': 'year',
        'wineColor': 'color',
        'wineGrapeVariety': 'grape_variety',
        'isSparkling': 'is_sparkling'
    }
    payload.pop('postType', None)

    winemaker = payload.pop('wineWinemaker', None)
    image_name = get_image_name(payload)

    comment = payload.pop('wineComment', None)
    post_id = payload.pop('postId', None)
    if post:
        assert post_id == post_id
        assert comment == post.team_comments
        assert wine == post.wine
        assert wine.year == post.wine_year
        assert_image(image_name, post, post_image)

    assert winemaker == wine.winemaker.name
    assert_image(image_name, wine, wine_image)

    if payload.get('isSparkling', None):
        payload['isSparkling'] = True

    for key, value in payload.items():
        assert value == getattr(wine, wine_keys[key])
