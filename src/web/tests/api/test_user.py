import pytest
from rest_framework import status as http_status
from django.urls import reverse
from .utils import assert_and_load_response_all_json, dump_request_data
from web.constants import ApiResultStatusE

# There's lack of likes/ comments etc. factories, tests should be made after factories creation
@pytest.mark.django_db
class TestUserProfile:
    def setup(self):
        self.url = reverse('reset_password_api')

    # TODO: add some fixtures for wineposts, general posts, likes etc
    def test_own_profile(self, logged_api_user, api_client_authenticated):
        response = api_client_authenticated.post(reverse('get_user_own_api'))
        data_json = assert_and_load_response_all_json(response)
        assert data_json['data']['user']['id'] == logged_api_user.id

    def test_any_profile(self, another_user, api_client_authenticated):
        response = api_client_authenticated.post(
            reverse('get_user_any_api'),
            data=dump_request_data({'user_id': another_user.id}),
            content_type='application/json')

        data_json = assert_and_load_response_all_json(response)
        assert data_json['data']['user']['id'] == another_user.id

    def test_delete_own_profile(self, api_client_authenticated):
        response = api_client_authenticated.post(reverse('delete_user_own_api'))
        assert_and_load_response_all_json(response)

    def test_update_own_profile(self, api_client_authenticated):
        updated_user_data = {"full_name": "Krzysztof Testowy"}
        """
        NOT a JSON call - we use typical application/octet stream with JSON stored in the "data"  field
        The same is true for ALL requests which provide images: adding/updating a place, winepost, general post, 
        winemaker etc.
        """
        response = api_client_authenticated.post(
            reverse('update_user_api'),
            data={"data": dump_request_data(updated_user_data)}
        )

        data_json = assert_and_load_response_all_json(response)
        assert data_json['data']['full_name'] == updated_user_data['full_name']

    # TODO: fixtures for some items
    def test_notifications_list(self, logged_api_user, api_client):
        api_client.credentials(HTTP_AUTHORIZATION=logged_api_user.TOKEN)
        response = api_client.post(reverse('get_notifications_list_api'))
        assert_and_load_response_all_json(response, expected_api_statuses=[ApiResultStatusE.STATUS_OK,
                                                                           ApiResultStatusE.RESULT_EMPTY])

    def test_update_lang_data(self, api_client_authenticated):
        response = api_client_authenticated.post(
            reverse('update_lang_data_api'),
            data=dump_request_data({'lang': 'FR'}),
            content_type='application/json')
        data_json = assert_and_load_response_all_json(response)
        assert data_json['data']['lang'] == 'FR'

        response = api_client_authenticated.post(
            reverse('update_lang_data_api'),
            data=dump_request_data({'lang': 'en'}),
            content_type='application/json')
        data_json = assert_and_load_response_all_json(response)
        assert data_json['data']['lang'] == 'EN'

    def test_update_push_data(self, api_client_authenticated):
        push_data_1 = {
            'push_user_id': "123456",
            'push_user_token': "ABCDEFGHI",
        }
        push_data_2 = {
            'push_user_id': "654321",
            'push_user_token': "IHGFEDBCA",
        }

        response = api_client_authenticated.post(
            reverse('update_push_data_api'),
            data=dump_request_data(push_data_1),
            content_type='application/json')
        data_json = assert_and_load_response_all_json(response)
        assert data_json['data']['push_user_id'] == push_data_1['push_user_id']
        assert data_json['data']['push_user_token'] == push_data_1['push_user_token']

        response = api_client_authenticated.post(
            reverse('update_push_data_api'),
            data=dump_request_data(push_data_2),
            content_type='application/json')
        data_json = assert_and_load_response_all_json(response)
        assert data_json['data']['push_user_id'] == push_data_2['push_user_id']
        assert data_json['data']['push_user_token'] == push_data_2['push_user_token']


