import pytest
import json
from django.urls import reverse

from web.factories import PlaceFactory
from web.models import Place
from web.tests.api.utils import assert_response_status_code
from web_pro.tests.test_data.food import FoodPostData


@pytest.mark.django_db
class TestEstablishment:
    def setup(self):
        self.url = reverse('pro_establishment_data')

    def test_get_establishment_data(self, client, logged_user):
        establishment = PlaceFactory(author=logged_user)
        response = client.get(self.url)
        assert_response_status_code(response, 200)
        content = load_response(response)
        ref_image_id = parse_establishment_content(content)

        for key in content.keys():
            assert content[key] == getattr(establishment, key)


class TestUpdateEstablishment:
    def test_update_presentation(self):
        pass

    def test_update_info(self):
        pass

    def test_update_map(self):
        pass

    def test_update_opening_hours(self):
        pass

    def test_update_holidays(self):
        pass


def load_response(response):
    return json.loads(response.content)


def parse_establishment_content(content):
    types = content.pop('types')
    content.update(types)
    return content.pop('ref_image_id')
