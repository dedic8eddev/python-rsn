from django.contrib import auth
from django.core.exceptions import PermissionDenied

from web.constants import UserStatusE, UserTypeE
from web.utils.exceptions import ResultErrorError


# --------------------- user-related tools -----------------------------
def get_current_user(request):
    if request.user:
        if request.user.type not in [
            UserTypeE.ADMINISTRATOR, UserTypeE.EDITOR
        ]:
            auth.logout(request)
            raise PermissionDenied(
                "this user is not allowed to access the administration panel"
            )

        prevent_using_non_active_account(request.user)

        return request.user
    else:
        return None


def prevent_using_non_active_account(user):
    if user.is_archived:
        raise ResultErrorError("account does not exist")
    elif user.status == UserStatusE.INACTIVE:
        raise ResultErrorError("unable to use the inactive account")
    elif user.status == UserStatusE.BANNED:
        raise ResultErrorError("unable to use the banned account")


def prevent_editing_not_own_item(user, item):
    if item.author != user:
        raise ResultErrorError(
            "The user can not edit item that is not his/her own"
        )


def is_privileged_account(user):
    if user.username in ('raisin', 'raisin-ja', 'raisin-en', 'admin'):
        return True
    else:
        return False


def list_control_parameters_by_form(cd, default_limit=10):
    limit = cd.get('limit', default_limit) or default_limit
    order_dir = cd.get('order', 'desc').lower() or 'desc'
    last_id = cd.get('last_id', None)
    order_by_field = cd.get('order_by', 'created_time') or 'created_time'
    order_by = order_by_field if order_dir == 'asc' else '-%s' % order_by_field

    result = (limit, order_dir, last_id, order_by)
    return result


def ajax_list_control_parameters_by_form(cd):
    limit = cd['limit'] if cd['limit'] else None
    order_dir = cd['order'].lower() if cd['order'] else 'desc'
    page = cd['page'] if cd['page'] else None
    order_by = 'id' if order_dir == 'asc' else '-modified_time'

    result = (page, limit, order_by, order_dir)
    return result


def list_last_id(items):
    return items[len(items) - 1].id if items else None


def get_search_value(request):
    search_value = None
    if "search[value]" in request.POST and request.POST["search[value]"] is not None:  # noqa
        search_value = request.POST["search[value]"]
    return search_value


def get_order_dir(request, default_order_dir):
    order_dir = default_order_dir
    if "order[0][dir]" in request.POST:
        if request.POST["order[0][dir]"] in ("asc", "desc"):
            order_dir = request.POST["order[0][dir]"]
    return order_dir


def get_sorting(request, col_map, default_order_by, default_order_dir):
    order_by = default_order_by
    order_dir = default_order_dir
    if "order[0][dir]" in request.POST:
        if request.POST["order[0][dir]"] in ("asc", "desc"):
            order_dir = request.POST["order[0][dir]"]

    if "order[0][column]" in request.POST:
        col = int(request.POST["order[0][column]"])
        if col in col_map and col_map[col]:
            order_by = col_map[col] if order_dir == 'asc' else "-" + col_map[col]  # noqa
    return order_by


def get_sorting_from_get_method(
        request, col_map, default_order_by, default_order_dir):
    order_by = default_order_by
    order_dir = default_order_dir
    if "order[0][dir]" in request.GET:
        if request.GET["order[0][dir]"] in ("asc", "desc"):
            order_dir = request.GET["order[0][dir]"]

    if "order[0][column]" in request.GET:
        col = int(request.GET["order[0][column]"])
        if col in col_map and col_map[col]:
            order_by = col_map[col] if order_dir == 'asc' else "-" + col_map[col]  # noqa
    return order_by
