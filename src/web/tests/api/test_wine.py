import pytest
from django.urls import reverse
from .utils import assert_and_load_response_all_json, dump_request_data
from web.models import Wine


@pytest.mark.django_db
class TestWine:
    def setup(self):
        pass

    def test_wine_items(self, api_client_authenticated, timeline_items):
        response = api_client_authenticated.post(reverse('get_wine_items_api'))
        data_json = assert_and_load_response_all_json(response)
        assert len(data_json['data']['items']) > 0

    def test_wine_similiar_items(self, api_client_authenticated, timeline_items):
        response = api_client_authenticated.post(
            reverse('get_wine_similiar_items_api'),
            data=dump_request_data({"wine_name": "wine"}),
            content_type='application/json'
        )
        data_json = assert_and_load_response_all_json(response)
        assert len(data_json['data']['items']) > 0

    def test_wine_profile(self, api_client_authenticated, timeline_items):
        wines = Wine.active.all()
        wine = wines.first()
        response = api_client_authenticated.post(
            reverse('get_wine_profile_api'),
            data=dump_request_data({"wine_id": wine.id}),
            content_type='application/json'
        )

        data_json = assert_and_load_response_all_json(response)
        assert data_json['data']['wine']['id'] == wine.id
        assert len(data_json['data']['reviews']) > 0
