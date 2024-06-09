from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10


class DataTablesJSPagination(LimitOffsetPagination):
    limit_query_param = 'length'
    offset_query_param = 'start'

    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'recordsTotal': self.count,
            'recordsFiltered': self.count,
            'results': data
        })
