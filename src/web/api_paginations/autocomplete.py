from rest_framework.pagination import BasePagination
from rest_framework.response import Response
from collections import OrderedDict


DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10


class AutocompletePagination(BasePagination):
    query = None

    def paginate_queryset(self, queryset, request, view=None):
        self.query = request.query_params.get('query', None)
        return queryset

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('data', {
                'items': data,
                'query': self.query
            })
        ]))

    def get_paginated_response_schema(self, schema):
        return {
            'type': 'object',
            'properties': {
                'data': {
                    'items': schema,
                    'query': {
                        'type': 'string',
                        'nullable': False,
                    }
                },
            },
        }
