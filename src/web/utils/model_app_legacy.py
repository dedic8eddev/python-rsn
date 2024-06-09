from web.constants import PlaceStatusE, PostStatusE, WineStatusE


# APPLICATION LEGACY
def api_status_winepost(obj):
    result = {}
    status = obj.status
    is_archived = obj.is_archived

    api_status = PostStatusE.DRAFT if status in [
        PostStatusE.IN_DOUBT, PostStatusE.DELETED, PostStatusE.BIO_ORGANIC
    ] else status

    if status == PostStatusE.IN_DOUBT:
        result['in_doubt'] = True

    result['post_status'] = api_status
    result['status'] = api_status
    result['wine_kind'] = PostStatusE.DELETED if is_archived else status

    return result


# APPLICATION LEGACY FOR TIMELINE
# post status must be used instead of wine status here for wine_kind
def api_status_winepost_tl(obj):
    result = {}
    status = obj.status
    is_archived = obj.is_archived

    if status == PostStatusE.IN_DOUBT:
        result['in_doubt'] = True

    api_status = PostStatusE.DRAFT if status in [
        PostStatusE.IN_DOUBT, PostStatusE.DELETED, PostStatusE.BIO_ORGANIC
    ] else status

    result['post_status'] = api_status
    result['status'] = api_status
    result['post_kind'] = PostStatusE.DELETED if is_archived else status

    return result


# APPLICATION LEGACY
def api_status_wine(obj):
    result = {}
    status = obj.status
    is_archived = obj.is_archived

    if status == WineStatusE.IN_DOUBT:  # APPLICATION LEGACY
        api_status = WineStatusE.ON_HOLD
        result['in_doubt'] = True
    elif status == WineStatusE.DELETED:  # APPLICATION LEGACY
        api_status = WineStatusE.ON_HOLD
        result['is_archived'] = True
    elif status == WineStatusE.BIO_ORGANIC:  # APPLICATION LEGACY
        api_status = WineStatusE.ON_HOLD
    else:
        api_status = status

    result['status'] = api_status
    result['wine_kind'] = PostStatusE.DELETED if is_archived else status

    return result


# APPLICATION LEGACY
def api_status_place(obj):
    if obj.status == PlaceStatusE.IN_DOUBT:  # APPLICATION LEGACY
        return {
            'status': PlaceStatusE.DRAFT,
            'in_doubt': True
        }

    return {
        'status': obj.status,
        'in_doubt': False
    }


# APPLICATION LEGACY
def api_status_winemaker(obj):
    if obj.status == PostStatusE.IN_DOUBT:  # APPLICATION LEGACY
        return {
            'status': PostStatusE.DRAFT,
            'in_doubt': True,
            'is_archived': False
        }

    if obj.status == PostStatusE.DELETED:  # APPLICATION LEGACY
        return {
            'status': PostStatusE.DRAFT,
            'in_doubt': False,
            'is_archived': True
        }

    if obj.status == PostStatusE.BIO_ORGANIC:  # APPLICATION LEGACY
        api_status = PostStatusE.DRAFT
    else:
        api_status = obj.status

    return {
        'status': api_status,
        'in_doubt': True,
        'is_archived': False
    }
