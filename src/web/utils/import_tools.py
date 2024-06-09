import json
import urllib
import urllib.request


class PlaceImporter:
    def import_places(self, token="1f4828aa9821ebbd9ba9eb037eb335b192cdc39377ce0fbada9da078ca3b449c",
                      skip=0, limit=1, as_json=True):

        url = "https://cdn.contentful.com/spaces/hoitsb2r705z/entries?access_token=%s&skip=%d&limit=%d"

        response = urllib.request.urlopen(url % (token, skip, limit))
        data = response.read()

        if as_json:
            data_out = json.loads(data.decode())

            if data_out:
                return data_out
            else:
                return {}
            # data = json.loads(response.read().decode(response.info().get_param('charset') or 'utf-8'))
        else:
            return data
