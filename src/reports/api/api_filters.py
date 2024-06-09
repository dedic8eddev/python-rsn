from rest_framework import filters


class DataTablesJSOrderingFilter(filters.OrderingFilter):
    ordering_param = 'order'

    def get_ordering(self, request, queryset, view):
        order_column = request.query_params.get("order[0][column]")
        fields = []
        if order_column:
            field = request.query_params.get(f"columns[{order_column}][name]")
            print(field)
            if field:
                order_type = request.query_params.get("order[0][dir]")
                if order_type == 'asc':
                    fields = [field]
                elif order_type == 'desc':
                    fields = [f'-{field}']
        ordering = self.remove_invalid_fields(queryset, fields, view, request)
        if ordering:
            return ordering

        # print(view)
        return super().get_ordering(request, queryset, view)


class DataTablesJSSearchFilter(filters.SearchFilter):
    search_param = 'search_value'
