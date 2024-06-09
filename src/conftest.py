import pytest
from web.tests.api.utils import login
from web.factories import UserProfileFactory, TimeLineItemFactory, WineMakerFactory, WineFactory, WinePostFactory
from web.constants import UserTypeE, WineColorE, WineStatusE, get_post_status_for_wine_status


def create_user_of_type(user_type):
    user = UserProfileFactory(type=user_type)
    user.set_password('test')
    user.save()
    return user


@pytest.fixture
def user():
    user = create_user_of_type(UserTypeE.ADMINISTRATOR)
    return user


@pytest.fixture
def user_common():
    user = create_user_of_type(UserTypeE.USER)
    return user


@pytest.fixture
def user_owner():
    user = create_user_of_type(UserTypeE.OWNER)
    return user


@pytest.fixture
def another_user():
    user = UserProfileFactory()
    user.set_password('test')
    user.save()
    return user


@pytest.fixture
def token(client, user):
    login(user, client)


@pytest.fixture
def logged_api_user(user, client):
    user.TOKEN, user.REFRESH_TOKEN, user.TOKEN_EXPIRES = login(user, client)
    return user


@pytest.fixture
def logged_api_user_common(user_common, client):
    user_common.TOKEN, user_common.REFRESH_TOKEN, user_common.TOKEN_EXPIRES = login(user_common, client)
    return user_common


@pytest.fixture
def logged_api_user_owner(user_owner, client):
    user_owner.TOKEN, user_owner.REFRESH_TOKEN, user_owner.TOKEN_EXPIRES = login(user_owner, client)
    return user_owner


@pytest.fixture
def logged_user(user, client):
    client.login(username=user.username, password='test')
    return user


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def api_client_authenticated(logged_api_user):
    from rest_framework.test import APIClient
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION=logged_api_user.TOKEN)
    return api_client


@pytest.fixture
def api_client_authenticated_common(logged_api_user_common):
    from rest_framework.test import APIClient
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION=logged_api_user.TOKEN)
    return api_client


@pytest.fixture
def api_client_authenticated_owner(logged_api_user_owner):
    from rest_framework.test import APIClient
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION=logged_api_user.TOKEN)
    return api_client


@pytest.fixture
def timeline_items(django_db_blocker):
    authors = [create_user_of_type(UserTypeE.USER) for i in range(0, 2)]
    colors = [WineColorE.RED, WineColorE.WHITE, WineColorE.ORANGE]
    wine_statuses = [WineStatusE.VALIDATED, WineStatusE.ON_HOLD, WineStatusE.IN_DOUBT, WineStatusE.REFUSED,
                     WineStatusE.BIO_ORGANIC]
    items_out = []

    for author in authors:
        wm = WineMakerFactory(author=author)
        wm.save()
        for color in colors:
            for is_sparkling in [True, False]:
                for wine_status in wine_statuses:
                    post_status = get_post_status_for_wine_status(wine_status)
                    wine = WineFactory(author=author, winemaker=wm, color=color, is_sparkling=is_sparkling,
                                       status=wine_status)
                    wine.save()
                    for wp_i, year in enumerate([2001, 2002, 2003]):
                        wp = WinePostFactory(author=author,
                                             wine=wine,
                                             wine_year=str(year),
                                             status=post_status,
                                             is_parent_post=True if wp_i == 0 else False)
                        wp.save()
                        tl = TimeLineItemFactory(author=author, post_item=wp, cached_item=wp.to_dict())
                        tl.save()
                        items_out.append(tl)
    return items_out
