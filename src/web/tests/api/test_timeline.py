import pytest
from rest_framework import status as http_status
from django.urls import reverse
from .utils import assert_and_load_response_all_json, dump_request_data
from web.constants import UserTypeE, get_post_status_for_wine_status
from web.models import TimeLineItem


@pytest.mark.usefixtures("timeline_items")
@pytest.mark.django_db(transaction=True)
class TestTimeLine:
    def setup(self):
        pass

    def test_timeline_items(self, api_client_authenticated):
        response = api_client_authenticated.post(reverse('get_timeline_items_api'))
        data_json = assert_and_load_response_all_json(response)
        assert len(data_json['data']['items']) > 0
        for item in data_json['data']['items']:
            assert item['author']['type'] == UserTypeE.USER
            post_status_expected = get_post_status_for_wine_status(item['cached_item']['wine_data']['status'])
            post_kind_expected = get_post_status_for_wine_status(item['cached_item']['wine_data']['wine_kind'])
            assert item['cached_item']['status'] == post_status_expected
            assert item['cached_item']['post_kind'] == post_kind_expected

    def test_newest_timeline_item(self, api_client_authenticated):
        tl_items_db = TimeLineItem.active.all().order_by('-id')
        tl_id = tl_items_db.first().id

        response = api_client_authenticated.post(
            reverse('get_newest_timeline_item_api'),
            data=dump_request_data({"tl_id": tl_id}),
            content_type="application/json"
        )
        assert response.status_code == http_status.HTTP_200_OK
        data_json = assert_and_load_response_all_json(response)
        assert data_json['data']['item']['id'] == tl_id
