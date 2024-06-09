from web.constants import AutocompleteQueryType
from web.forms.common import AutocompleteQueryForm
from web.serializers.nested import PlaceSerializer
from web.serializers.posts import WineSerializer
from web.serializers.users import UserSerializer
from web.serializers.winemakers import WinemakerSerializer


# common function used by all autocomplete AJAX endpoints
def autocomplete_common_ajax(
    request, EntityClass, entity_field, FormClass=AutocompleteQueryForm,
    extra_filter_criteria=None
):
    if request.method == 'POST':
        form = FormClass(request.POST)

    # noqa eg. http://localhost:8000/ajax/autocomplete/winemaker/?min_letters=2&query=Bre
    elif request.method == 'GET':
        form = FormClass(request.GET)

    if form.is_valid():
        cd = form.cleaned_data

        query = cd['query']
        filter_criteria = {}

        if extra_filter_criteria:
            for filter_field, filter_cond in extra_filter_criteria.items():
                filter_criteria[filter_field] = filter_cond

        if cd['min_letters']:
            if len(query) < cd['min_letters']:
                return {
                    "items": [],
                    "query": query
                }

        if cd['query_type'] and cd['query_type'] == AutocompleteQueryType.STARTS:  # noqa
            filter_criteria[entity_field+'__unaccent__istartswith'] = query
        if cd['query_type'] and cd['query_type'] == AutocompleteQueryType.ENDS:
            filter_criteria[entity_field+'__unaccent__iendswith'] = query
        else:  # CONTAINS - default value
            filter_criteria[entity_field+'__unaccent__icontains'] = query

        items = EntityClass.active.filter(
            **filter_criteria
        ).distinct(entity_field)

        if EntityClass.__name__ == 'Wine':
            items = WineSerializer(
                items, many=True, context={
                    'request': request, 'include_winemaker_data': True
                }
            ).data
        elif EntityClass.__name__ == 'Winemaker':
            items = WinemakerSerializer(
                items, many=True, context={'request': request}
            ).data
        elif EntityClass.__name__ == 'UserProfile':
            items = UserSerializer(
                items, many=True, context={'request': request}
            ).data
        elif EntityClass.__name__ == 'Place':
            items = PlaceSerializer(
                items, many=True, context={'request': request}
            ).data
        else:
            return {}

        return {'items': items, 'query': query}

    return {
        'items': [],
        'query': None,
    }
