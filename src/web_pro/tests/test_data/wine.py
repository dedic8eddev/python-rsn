from web_pro.tests.test_data.utils import get_image


class WineTestData:
    wine_template = {
        'imageFile': '',
        'wineName': 'TestWine',
        'wineWinemaker': 'TestWine',
        'wineDomain': 'TestWine',
        'wineYear': '1992',
        'wineColor': 30,
        'wineGrapeVariety': 'TestWine',
        'wineComment': 'TestWine',
        'postType': ''
        }

    def get_add_wine_payload(self, color: int, is_sparkling=False):
        payload = self.wine_template.copy()

        if is_sparkling:
            payload['isSparkling'] = 'on'
        payload['postType'] = 'add'
        payload['wineColor'] = color
        payload['imageFile'] = get_image()
        return payload

    def get_add_existing_wine_payload(self, winepost):
        wine = winepost.wine
        payload = {
            'imageFile': wine.main_image,
            'wineName': wine.name,
            'wineWinemaker': wine.winemaker.name,
            'wineDomain': wine.domain,
            'wineYear': wine.year,
            'wineColor': wine.color,
            'wineGrapeVariety': wine.grape_variety,
            'postId': wine.grape_variety,
            'wineComment': '',
            'postType': 'add'
        }

        if wine.is_sparkling:
            payload['isSparkling'] = 'on'

        return payload

    def get_edit_wine_payload(self, winepost, color=None, is_sparkling=None, winemaker=None):
        payload = self.wine_template.copy()
        payload['postId'] = winepost.id
        payload['postType'] = 'edit'
        payload['wineColor'] = color if color else payload['wineColor']
        payload['wineWinemaker'] = winemaker.name if winemaker else ''
        if is_sparkling:
            payload['isSparkling'] = True
        return payload

    def get_delete_wine_payload(self, winepost):
        payload = self.wine_template.copy()
        payload['postId'] = winepost.id
        payload['postType'] = 'delete'
        return payload

    def get_wine_template(self, post_type):
        payload = self.wine_template.copy()
        payload['postType'] = post_type
        return payload
