from web.models import get_parent_post_for_winepost


def update_yearly_data_with_parent_post(
    winepost, cur_year, data_cur_year,
    compare_fields=['free_so2', 'total_so2', 'grape_variety'],
    create_new_wine_if_needed=True
):
    # we ALWAYS save those parameters, regardless if the wp is a parent post
    # or not; also each winepost HAS yearly_data defined, even if
    # it's a child post and has its own data only
    winepost.wine_year = cur_year
    winepost.free_so2 = data_cur_year['free_so2'] if data_cur_year['free_so2'] else None  # noqa
    winepost.total_so2 = data_cur_year['total_so2'] if data_cur_year['total_so2'] else None  # noqa
    winepost.grape_variety = data_cur_year['grape_variety']
    winepost.save()
    winepost.refresh_from_db()

    action = 'OK'
    if not winepost.yearly_data:
        winepost.yearly_data = {}

    pp = get_parent_post_for_winepost(winepost)
    # year has not been set in the "cur_year" field:
    if not cur_year:
        return action

    # parent post - just update the yearly_data for cur_year
    if winepost.is_parent_post:
        winepost.yearly_data[cur_year] = data_cur_year
        winepost.save()
        winepost.refresh_from_db()
    # winepost is not a not parent post, but a parent post for it exists and
    # the year has not been defined yet in pp yearly_data - add yearly data to
    # the parent post
    elif pp:
        if not pp.yearly_data:
            pp.yearly_data = {}
        if (
            cur_year not in pp.yearly_data or
            empty_fields_in_yearly_data(
                pp.yearly_data[cur_year], compare_fields
            )
        ):
            pp.yearly_data[cur_year] = data_cur_year
            pp.save()
            pp.refresh_from_db()
        elif (
            cur_year in pp.yearly_data and
            not _is_yearly_data_exact_for_year(
                pp.yearly_data[cur_year],
                data_cur_year,
                compare_fields
            )
        ):
            if create_new_wine_if_needed:  # used in ADMINpanel for redirection
                new_wine = winepost.wine.clone_as_new_draft()
                new_wine.grape_variety = data_cur_year['grape_variety']
                new_wine.year = cur_year
                new_wine.save()
                new_wine.refresh_from_db()
                winepost.wine = new_wine
                action = 'RELOAD_DRAFT'
            else:  # DO NOT CREATE NEW WINE, just update the yearly_data
                if not winepost.yearly_data:
                    winepost.yearly_data = {}
                winepost.yearly_data[cur_year] = data_cur_year
                winepost.save()
                winepost.refresh_from_db()

    return action


def delete_yearly_data_with_parent_post(winepost, year):
    if (
        winepost.is_parent_post and
        winepost.yearly_data and
        year in winepost.yearly_data
    ):
        del winepost.yearly_data[year]
        winepost.save()
        winepost.refresh_from_db()
    action = 'OK'
    return action


def empty_fields_in_yearly_data(yd, compare_fields):
    for field in compare_fields:
        if field not in yd or not yd[field]:
            return True
    return False


def _is_yearly_data_exact_for_year(
    data_pp_for_year, data_wp_for_year, compare_fields
):
    is_exact = True
    for field in compare_fields:
        if field not in data_pp_for_year:
            continue
        if (
            data_pp_for_year[field] and
            data_wp_for_year[field] != data_pp_for_year[field]
        ):
            is_exact = False
            break
    return is_exact


def get_yearly_data_for_winepost(winepost):
    if winepost.is_parent_post:
        return winepost.yearly_data if winepost.yearly_data else {}
    else:
        pp = get_parent_post_for_winepost(winepost)
        if pp:
            return pp.yearly_data if pp.yearly_data else {}
        else:
            return winepost.yearly_data if winepost.yearly_data else {}
