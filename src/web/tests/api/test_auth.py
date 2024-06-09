import pytest
import time

from django.urls import reverse

from web.tests.api.utils import assert_and_load_response_data, dump_request_data


@pytest.mark.django_db
class TestRegistration:
    def setup(self):
        self.url = reverse('create_user_api')

    def test_successful_registration(self, client):
        payload = {'email': 'raisinapitesting@test.com', 'username': 'raisinapitesting', 'password': 'raisinapitesting'}

        response = client.post(self.url, data=dump_request_data(payload), content_type='application/json')
        response_data = assert_and_load_response_data(response)

    def test_empty_data_registration(self, client):
        response = client.post(self.url, content_type='application/json')
        response_data = assert_and_load_response_data(response, 400, 101)

    def test_same_username_registration(self, client, logged_api_user):
        payload = {'email': 'raisinapitesting@test.com', 'username': f'{logged_api_user.username}', 'password': 'raisinapitesting'}

        response = client.post(self.url, data=dump_request_data(payload), content_type='application/json')
        response_data = assert_and_load_response_data(response, 400, 115)

    def test_same_email_registration(self, client, logged_api_user):
        payload = {'email': f'{logged_api_user.email}', 'username': 'raisinapitesting', 'password': 'raisinapitesting'}

        response = client.post(self.url, data=dump_request_data(payload), content_type='application/json')
        response_data = assert_and_load_response_data(response, 400, 116)


@pytest.mark.django_db
class TestTokenRefresh:
    def setup(self):
        self.url = reverse('refresh_refreshtoken_api')

    def test_successful_token_refresh(self, client, logged_api_user):
        payload = {'refresh_token': f'{logged_api_user.REFRESH_TOKEN}'}

        time.sleep(1)
        response = client.post(
            self.url, data=dump_request_data(payload), content_type='application/json'
        )
        response_data = assert_and_load_response_data(response)
        assert response_data['token'] != logged_api_user.TOKEN
        assert response_data['exp'] > logged_api_user.TOKEN_EXPIRES

    def test_empty_data_token_refresh(self, client):
        response = client.post(self.url, content_type='application/json')
        response_data = assert_and_load_response_data(response, 400, 101)

    def test_wrong_token_refresh(self, client):
        url = reverse('refresh_refreshtoken_api')
        payload = {'refresh_token': 'testtoken'}

        response = client.post(
            self.url, data=dump_request_data(payload), content_type='application/json'
        )
        response_data = assert_and_load_response_data(response, 400, 111)


@pytest.mark.django_db
class TestResetPassword:
    def setup(self):
        self.url = reverse('reset_password_api')

    def test_reset_password_using_email(self, client, logged_api_user):
        payload = {'username': f'{logged_api_user.email}'}

        response = client.post(self.url, data=dump_request_data(payload), content_type='application/json')
        response_data = assert_and_load_response_data(response)

    def test_reset_password_using_username(self, client, logged_api_user):
        payload = {'username': f'{logged_api_user.username}'}

        response = client.post(self.url, data=dump_request_data(payload), content_type='application/json')
        response_data = assert_and_load_response_data(response)

    def test_empty_data_reset_password(self, client):
        response = client.post(self.url, content_type='application/json')
        response_data = assert_and_load_response_data(response, 400, 101)

    def test_reset_password_wrong_username(self, client):
        payload = {'username': f'randomuser'}
        response = client.post(self.url, data=dump_request_data(payload), content_type='application/json')
        response_data = assert_and_load_response_data(response, 400, 101)

    def test_reset_password_wrong_email(self, client):
        payload = {'username': f'randomuser@randomuser.com'}
        response = client.post(self.url, data=dump_request_data(payload), content_type='application/json')
        response_data = assert_and_load_response_data(response, 400, 101)


@pytest.mark.django_db
class TestLogout:
    def setup(self):
        self.url = reverse('delete_refreshtoken_api')

    def test_logout(self, client, logged_api_user):
        payload = {'refresh_token': f'{logged_api_user.REFRESH_TOKEN}'}
        response = client.post(self.url, data=dump_request_data(payload), content_type='application/json')
        response_data = assert_and_load_response_data(response)

    def test_empty_data_logout(self, client):
        response = client.post(self.url, content_type='application/json')
        response_data = assert_and_load_response_data(response, 400, 101)

    def test_wrong_token_logout(self, client):
        payload = {'refresh_token': 'randomtoken'}
        response = client.post(self.url, data=dump_request_data(payload), content_type='application/json')
        response_data = assert_and_load_response_data(response, 400, 111)




