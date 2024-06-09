from rest_framework.filters import SearchFilter


class AutocompleteSearchFilter(SearchFilter):
    search_param = 'query'
    min_letters = 3
    lookup_prefixes = {
        '^': 'unaccent__istartswith',
        '=': 'unaccent__iexact',
        '@': 'unaccent__search',
        '$': 'unaccent__iregex',
        '*': 'unaccent__icontains'
    }

    def filter_queryset(self, request, queryset, view):
        params = request.query_params.get(self.search_param, '')
        params = params.replace('\x00', '')  # strip null characters
        if not params or len(params) < self.min_letters:
            return queryset.none()
        qs = super().filter_queryset(request, queryset, view)

        if 'winemaker' in request.query_params and request.query_params.get('winemaker', None):
            winemaker = request.query_params.get('winemaker')
            qs1 = qs.filter(winemaker_id=winemaker)
            qs2 = qs.exclude(winemaker_id=winemaker)
            qs = qs1.union(qs2, all=True)
        return qs
