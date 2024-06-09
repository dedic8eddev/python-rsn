class PlaceTestData:
    GET = (
        'get_place_api',
        {
            'place_id': '0',
        }
    )
    # api/places/place
    @staticmethod
    def get_reverse():
        return (
            'get_place_api',
            {
                'place_id': 0,
            }
        )

    # api/places/place/add
    @staticmethod
    def add_reverse():
        return (
            'add_place_api',
            {"name": "Degustatornia",
             "type": "20",
             "description": "Very nice bar located nearby Motlawa river in the center of Gdansk (Old Town)",
             "street_address": "ul. Grodzka 16 (za hotelem Hilton)",
             "house_number": "16",
             "zip_code": "80841",
             "city": "Gdansk",
             "country": "Poland",
             "country_iso_code": "PL",
             "phone_number": "+48 888 728 272",
             "website_url": "degustatornia.eu",
             "email": "degu@degustatornia.eu",
             "latitude": "54.35409",
             "longitude": "18.6574003",
             "social_facebook_url": "https://web.facebook.com/DEGUSTATORNIA/",
             "social_twitter_url": "",
             "social_instagram_url": ""}
        )
