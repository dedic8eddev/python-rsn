import json
import base64
from packaging import version
from rest_framework import status as http_status

from django.urls import reverse
from web.constants import ApiResultStatusE

HTTP_HEADER_ENCODING = 'iso-8859-1'
LOGIN_URL = 'create_refreshtoken_api'
PASSWORD = 'test'


def login(user, client):
    auth = prepare_credentials(user.username, PASSWORD)
    response = client.post(reverse(LOGIN_URL), data={}, HTTP_AUTHORIZATION=auth, content_type='application/json')
    response_data = assert_and_load_response_data(response)
    return 'Token ' + response_data['token'], response_data['refresh_token'], response_data['exp']


def login_userdata(user, client):
    auth = prepare_credentials(user.username, PASSWORD)
    response = client.post(reverse(LOGIN_URL), data={}, HTTP_AUTHORIZATION=auth, content_type='application/json')
    response_data = assert_and_load_response_data(response)
    return 'Token ' + response_data['token'], response_data['refresh_token'], response_data['exp'], \
           response_data['user']['id'], response_data['user']['email']


def prepare_credentials(username, password):
    credentials = f'{username}:{password}'
    base64_credentials = base64.b64encode(credentials.encode(HTTP_HEADER_ENCODING)).decode(HTTP_HEADER_ENCODING)

    return f'Basic {base64_credentials}'


def dump_request_data(request_data):
    return json.dumps(request_data)


def assert_and_load_response_data(response, status_code=200, error_status=400):
    assert response.status_code == status_code
    if status_code != http_status.HTTP_200_OK:
        response_data = json.loads(response.content)
        assert response_data['status'] == error_status
        return json.loads(response.content)
    return json.loads(response.content)['data']


def assert_and_load_response_all_json(response, expected_api_statuses=[ApiResultStatusE.STATUS_OK],
                                      status_code=http_status.HTTP_200_OK,
                                      error_status=http_status.HTTP_400_BAD_REQUEST):
    assert response.status_code == status_code
    if status_code != http_status.HTTP_200_OK:
        response_data = json.loads(response.content)
        assert response_data['status'] == error_status
        return json.loads(response.content)
    json_data = json.loads(response.content)
    assert json_data['status'] in expected_api_statuses
    return json_data


def assert_response_status_code(response, status_code):
    assert response.status_code == status_code
