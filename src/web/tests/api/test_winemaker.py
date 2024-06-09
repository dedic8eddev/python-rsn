import pytest
from django.urls import reverse
from .utils import assert_and_load_response_all_json, dump_request_data
from web.models import Winemaker


@pytest.mark.django_db
class TestWinemaker:
    def setup(self):
        pass

    def test_winemaker_items(self, api_client_authenticated, timeline_items):
        response = api_client_authenticated.post(reverse('get_winemaker_items_api'))
        data_json = assert_and_load_response_all_json(response)
        assert len(data_json['data']['items']) > 0
        assert data_json['data']['last_id'] is not None and int(data_json['data']['last_id']) > 0

    def test_winemaker_profile(self, api_client_authenticated, timeline_items):
        winemakers = Winemaker.active.all()
        winemaker = winemakers.first()
        response = api_client_authenticated.post(
            reverse('get_winemaker_profile_api'),
            data=dump_request_data({"winemaker_id": winemaker.id}),
            content_type='application/json'
        )

        data_json = assert_and_load_response_all_json(response)
        assert data_json['data']['winemaker']['id'] == winemaker.id
        assert len(data_json['data']['wines']) > 0
        assert data_json['data']['wine_last_id'] is not None and int(data_json['data']['wine_last_id']) > 0
