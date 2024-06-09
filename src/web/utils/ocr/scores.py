# import datetime
import re

from django.urls import reverse

from web.constants import WinemakerStatusE, PostStatusE
from web.utils.ocr.db import clean_row, deabbr_row, unify_spelling_row
from web.models.models import NWLAExcludedWord


def search_matches(escape, value, flags=re.IGNORECASE):
    if escape in value:
        return re.search(r'\b%s\b' % re.escape(escape), value, flags=flags)
    return False


def sort_highlight_zones(e):
    return e[0][0]


def get_highlight_borders(all_found_bounds):
    # print(all_found_bounds)
    overlapped_status = 0
    if len(all_found_bounds) > 1:  # then check for intersections
        relaunch_whole_loop = True  # because of the list modification
        break_j_loop = False
        while relaunch_whole_loop:
            b_counter = 0
            for b in all_found_bounds:
                j_counter = 0
                for j in all_found_bounds:
                    # cutting the number of cycles & check intersections
                    if j_counter > b_counter and set(b[0]) & set(j[0]):
                        # check statuses (highlighting colors)
                        if b[1] == j[1]:
                            all_found_bounds[b_counter][0] = list(range(
                                min(b[0][0], j[0][0]),
                                max(b[0][len(b[0]) - 1],
                                    j[0][len(j[0]) - 1]) + 1))
                            all_found_bounds.remove(j)
                            break_j_loop = True
                            break
                        else:
                            outer_left_border = min(b[0][0], j[0][0])
                            inner_left_border = max(b[0][0], j[0][0])
                            inner_right_border = min(b[0][len(b[0]) - 1],
                                                     j[0][len(j[0]) - 1])
                            outer_right_border = max(b[0][len(b[0]) - 1],
                                                     j[0][len(j[0]) - 1])

                            if outer_left_border == inner_left_border and \
                                    outer_right_border == \
                                    inner_right_border:
                                all_found_bounds[b_counter][0] = \
                                    list(range(
                                        outer_left_border,
                                        outer_right_border + 1))
                                all_found_bounds[b_counter][1] = \
                                    overlapped_status
                                all_found_bounds.remove(j)
                            elif outer_left_border == inner_left_border:
                                all_found_bounds[b_counter][0] = \
                                    list(range(outer_left_border,
                                               inner_right_border + 1))
                                all_found_bounds[j_counter][0] = \
                                    list(range(
                                        inner_right_border + 1,  # +1 to
                                        # not overlap the previous border
                                        outer_right_border + 1))
                                if outer_right_border == \
                                        j[0][len(j[0]) - 1]:
                                    all_found_bounds[j_counter][1] = j[1]
                                else:
                                    all_found_bounds[j_counter][1] = b[1]

                                all_found_bounds[b_counter][1] = \
                                    overlapped_status
                            elif outer_right_border == inner_right_border:
                                all_found_bounds[b_counter][0] = list(
                                    range(
                                        outer_left_border,
                                        inner_left_border  # without +1
                                        # to not overlap the next border
                                    ))
                                all_found_bounds[j_counter][0] = list(
                                    range(
                                        inner_left_border,
                                        outer_right_border + 1
                                    ))
                                if outer_left_border == b[0][0]:
                                    all_found_bounds[b_counter][1] = b[1]
                                else:
                                    all_found_bounds[b_counter][1] = j[1]

                                all_found_bounds[j_counter][1] = \
                                    overlapped_status
                            else:
                                # left_part
                                all_found_bounds[b_counter][0] = list(
                                    range(
                                        outer_left_border,
                                        inner_left_border  # without +1
                                        # to not overlap middle part
                                    )
                                )
                                # middle_part
                                all_found_bounds.append([list(range(
                                    inner_left_border,
                                    inner_right_border + 1)),
                                    overlapped_status]
                                )
                                # right_part
                                all_found_bounds[j_counter][0] = list(
                                    range(
                                        inner_right_border + 1,  # +1 to
                                        # not overlap middle part
                                        outer_right_border + 1
                                    )
                                )

                                if outer_left_border == b[0][0]:
                                    all_found_bounds[b_counter][1] = b[1]
                                else:
                                    all_found_bounds[b_counter][1] = j[1]

                                if outer_right_border == j[
                                        0][len(j[0]) - 1]:
                                    all_found_bounds[j_counter][1] = j[1]
                                else:
                                    all_found_bounds[j_counter][1] = b[1]
                        break_j_loop = True
                        break
                    else:
                        j_counter += 1
                if break_j_loop:
                    break_j_loop = False
                    relaunch_whole_loop = True
                    break  # break_b_loop
                else:
                    relaunch_whole_loop = False
                    b_counter += 1
    return all_found_bounds


def get_by_row_score(winemakers_by_status, wines, wines_by_wm, text_rows,
                     moderated_indexes, new_exclusion_word_row):
    natural = 20
    no_data = 2
    exclude = 0
    not_natural_and_others = [exclude, no_data, 10, 15, 25, 30, 45]
    excluded_from_total_score = [exclude]
    moderated = [natural, 25, 30]

    exceptions = list(NWLAExcludedWord.objects.values_list('word', flat=True))
    unac_exceptions = [clean_row(item) for item in exceptions]
    unispelled_exceptions = [unify_spelling_row(item) for item in unac_exceptions]
    deabbr_exceptions = [deabbr_row(item) for item in unispelled_exceptions]

    data_out = {
        'num_rows_total': 0,
        'num_rows_yes': 0,
        'num_rows_no': 0,
        'score_percent': 0.0,
        'rows_out': [],
        'rows_orig': text_rows,
        'file': None,
    }

    i = 0
    for raw_row in text_rows:
        if raw_row == "broken file - contains more than 100 images." \
                      " can't parse":
            break
        row = raw_row.strip(' ,.:;-')
        row_cmp = clean_row(row)
        row_unispelled = unify_spelling_row(row_cmp)
        row_deabbr = deabbr_row(row_unispelled)

        if len(row) < 1:
            continue

        found_where = []

        all_matches = []

        result_ready = False
        # Search in predefined sequence: Naturals -> Bio-Organics ->
        # Not-Naturals -> To-Investigates -> In-Doubts -> Others
        for winemakers in winemakers_by_status:
            if not result_ready:
                for wm in winemakers:
                    another_match = {
                        'pt': 0,
                        'status_pt': 0,
                        'wm_obj': None,
                        'wine_obj': None,
                        'found': False,
                        'found_what': [],
                        'status': no_data
                    }

                    matched_wm_name = False
                    matched_wm_domain = False
                    short_wm_name_to_exclude = False
                    short_domain_to_exclude = False
                    found_wine_obj = None
                    found_what = []
                    wine_inside_wm_found = False

                    if (  # Winemaker name
                        wm.get('deabbr_name') and
                        not wm['deabbr_name'].isdigit() and
                        search_matches(escape=wm['deabbr_name'],
                                       value=row_deabbr)
                    ):
                        if wm.get('status') == WinemakerStatusE.VALIDATED or (
                                # excluded words check
                                # is only for not 'NATURAL's
                                wm.get('status') != WinemakerStatusE.VALIDATED
                                and not wm['deabbr_name'] in deabbr_exceptions
                        ):
                            matched_wm_name = True
                            found_url = reverse('edit_winemaker',
                                                args=[wm['id']])
                            found_what.append((wm['name'], wm['deabbr_name'],
                                               'winemaker', found_url, False))
                    if (  # Winemaker name short
                        wm.get('deabbr_name_short') and
                        not wm['deabbr_name_short'].isdigit() and
                        search_matches(escape=wm['deabbr_name_short'],
                                       value=row_deabbr)
                    ):
                        if wm.get('status') == WinemakerStatusE.VALIDATED or (
                                # excluded words check
                                # is only for not 'NATURAL's
                                wm.get('status') != WinemakerStatusE.VALIDATED
                                and not wm['deabbr_name_short'] in
                                deabbr_exceptions
                        ):
                            found_url = reverse('edit_winemaker',
                                                args=[wm['id']])
                            if (  # exclude the matched short version from
                                  # WHAT? column in presence of
                                  # the matched full version
                                matched_wm_name
                            ):
                                short_wm_name_to_exclude = True
                            matched_wm_name = True
                            found_what.append((wm['name_short'],
                                               wm['deabbr_name_short'],
                                               'winemaker_short', found_url,
                                               short_wm_name_to_exclude))
                    if (  # Domain
                        wm.get('deabbr_domain') and
                        wm['deabbr_domain'] in row_deabbr and
                        not wm['deabbr_domain'].isdigit() and
                        search_matches(escape=wm['deabbr_domain'],
                                       value=row_deabbr)
                    ):
                        if wm.get('status') == WinemakerStatusE.VALIDATED or (
                                # excluded words
                                # check is only for not 'NATURAL's
                                wm.get('status') != WinemakerStatusE.VALIDATED
                                and not wm['deabbr_domain'] in
                                deabbr_exceptions
                        ):
                            matched_wm_domain = True
                            found_url = reverse('edit_winemaker',
                                                args=[wm['id']])
                            found_what.append((wm['domain'],
                                               wm['deabbr_domain'],
                                               'domain', found_url, False))
                    if (  # Domain short
                        wm.get('deabbr_domain_short') and
                        wm['deabbr_domain_short'] in row_deabbr and
                        not wm['deabbr_domain_short'].isdigit() and
                        search_matches(escape=wm['deabbr_domain_short'],
                                       value=row_deabbr)
                    ):
                        if wm.get('status') == WinemakerStatusE.VALIDATED or (
                                # excluded words check
                                # is only for not 'NATURAL's
                                wm.get('status') != WinemakerStatusE.VALIDATED
                                and not wm['deabbr_domain_short'] in
                                deabbr_exceptions
                        ):
                            found_url = reverse('edit_winemaker',
                                                args=[wm['id']])
                            if (  # exclude the matched short version from
                                  # WHAT? column in presence of
                                  # the matched full version
                                matched_wm_domain
                            ):
                                short_domain_to_exclude = True
                            matched_wm_domain = True
                            found_what.append((wm['domain_short'],
                                               wm['deabbr_domain_short'],
                                               'domain_short', found_url,
                                               short_domain_to_exclude))
                    if matched_wm_name or matched_wm_domain:
                        matched_wm_status = wm.get('status')
                        if matched_wm_status == WinemakerStatusE.VALIDATED:
                            wines_by_wm_status = wines_by_wm[0]
                        elif matched_wm_status == WinemakerStatusE.BIO_ORGANIC:
                            wines_by_wm_status = wines_by_wm[1]
                        elif matched_wm_status == WinemakerStatusE.REFUSED:
                            wines_by_wm_status = wines_by_wm[2]
                        elif matched_wm_status == WinemakerStatusE.TO_INVESTIGATE:
                            wines_by_wm_status = wines_by_wm[3]
                        elif matched_wm_status == WinemakerStatusE.IN_DOUBT:
                            wines_by_wm_status = wines_by_wm[4]
                        else:
                            wines_by_wm_status = wines_by_wm[5]

                        wines_for_wm = wines_by_wm_status[wm.get('id')] if wm.get(
                            'id') in wines_by_wm_status else None
                        if wines_for_wm:
                            for wine in wines_for_wm:
                                another_match = {
                                    'pt': 0,
                                    'status_pt': 0,
                                    'wm_obj': wm,
                                    'wine_obj': None,
                                    'found': True,
                                    'found_what': found_what,
                                    'status': no_data
                                }

                                found_what_wine = []
                                found_wine_obj = None
                                matched_wine = False
                                short_wine_name_to_exclude = False

                                if (  # Wine name
                                    wine.get('deabbr_name') and
                                    wine['deabbr_name'] in row_deabbr and
                                    not wine['deabbr_name'].isdigit() and
                                    search_matches(escape=wine['deabbr_name'],
                                                   value=row_deabbr)
                                ):
                                    if wine.get('wp_status') == \
                                            PostStatusE.PUBLISHED or (
                                            # excluded words check
                                            # is only for not 'NATURAL's
                                            wine.get('wp_status') !=
                                            PostStatusE.PUBLISHED and
                                            not wine['deabbr_name'] in
                                            deabbr_exceptions
                                    ):
                                        found_wine_obj = wine
                                        matched_wine = True
                                        if 'wp_id' in wine and wine['wp_id']:
                                            found_url = reverse(
                                                'edit_winepost',
                                                args=[wine['wp_id']])
                                        else:
                                            found_url = "#"

                                        found_what_wine.append(
                                            (wine['wine_name'],
                                             wine['deabbr_name'],
                                             'wine_name', found_url, False))
                                if (  # Wine name short
                                        wine.get('deabbr_name_short') and
                                        wine['deabbr_name_short'] in row_deabbr and
                                        not wine['deabbr_name_short'].isdigit() and
                                        search_matches(escape=wine[
                                            'deabbr_name_short'
                                        ], value=row_deabbr)
                                ):
                                    if wine.get('wp_status') == \
                                            PostStatusE.PUBLISHED or (
                                            # excluded words check
                                            # is only for not 'NATURAL's
                                            wine.get('wp_status') !=
                                            PostStatusE.PUBLISHED and
                                            not wine['deabbr_name_short'] in
                                            deabbr_exceptions
                                    ):
                                        if 'wp_id' in wine and wine['wp_id']:
                                            found_url = reverse(
                                                'edit_winepost',
                                                args=[wine['wp_id']]
                                            )
                                        else:
                                            found_url = "#"

                                        # exclude the matched short version
                                        # from WHAT? column in presence of
                                        # the matched full version
                                        if matched_wine:
                                            short_wine_name_to_exclude = True
                                        found_wine_obj = wine
                                        matched_wine = True
                                        found_what_wine.append(
                                            (wine['wine_name_short'],
                                             wine['deabbr_name_short'],
                                             'wine_name_short',
                                             found_url,
                                             short_wine_name_to_exclude))
                                if found_wine_obj:
                                    wine_inside_wm_found = True
                                    # break  # we want to search for max. 1 wine
                                    pt = matched_wm_name + matched_wm_domain + matched_wine
                                    item_status = found_wine_obj['wp_status']

                                    if item_status == natural:
                                        status_pt = 2
                                    elif item_status in moderated:
                                        status_pt = 1
                                    else:
                                        status_pt = 0

                                    another_match['pt'] = pt
                                    another_match['status_pt'] = status_pt
                                    another_match['wm_obj'] = wm
                                    another_match['wine_obj'] = found_wine_obj
                                    another_match['status'] = item_status
                                    another_match['found'] = True
                                    another_match['found_what'] = \
                                        found_what + found_what_wine
                                    all_matches.append(another_match)
                        if wine_inside_wm_found:
                            result_ready = True
                            break  # stop the search among winemakers if
                            # winemaker + wine has been found.
                        else:
                            pt = matched_wm_name + matched_wm_domain

                            # print('WINE_INSIDE_not_found. PT=', pt)
                            item_status = wm['status']
                            if item_status == natural:
                                status_pt = 2
                            elif item_status in moderated:
                                status_pt = 1
                            else:
                                status_pt = 0

                            # match priority rules for item_status,
                            # if pt > another_match['pt'] or (
                            #     item_status and
                            #     another_match['status'] and
                            #     item_status in moderated and
                            #     another_match['status'] not in moderated
                            # ):
                            if pt >= 2 or status_pt == 2:
                                another_match['pt'] = pt
                                another_match['status_pt'] = status_pt
                                another_match['wm_obj'] = wm
                                another_match['wine_obj'] = found_wine_obj
                                another_match['status'] = item_status
                                another_match['found'] = True
                                another_match['found_what'] = found_what
                                all_matches.append(another_match)
                                result_ready = True
                                break  # any 2 matching fields is enough
                                # to credit a result
            else:
                break  # the cycle for winemakers_by_status

        # if not another_match['found']:
        if not all_matches:
            # search through all wines by wine_name + wine_name_short
            # print('PRE_ALL_WINES: ', all_matches)
            for wine in wines:
                another_match = {
                    'pt': 0,
                    'status_pt': 0,
                    'wm_obj': None,
                    'wine_obj': None,
                    'found': False,
                    'found_what': [],
                    'status': no_data,
                    'wine_only_match': True
                }
                pt = 0
                status_pt = 0
                matched_wm_name = False
                matched_wm_domain = False
                matched_wine = False
                found_wine_obj = None
                short_wine_all_name_to_exclude = False
                found_what = []
                item_status = None
                if (  # Wine name
                        wine.get('deabbr_name') and
                        wine['deabbr_name'] in row_deabbr and
                        search_matches(escape=wine['deabbr_name'],
                                       value=row_deabbr) and
                        not wine['deabbr_name'] in deabbr_exceptions and
                        not wine['deabbr_name'].isdigit()
                ):
                    found_wine_obj = wine
                    if 'wp_id' in wine and wine['wp_id']:
                        found_url = reverse('edit_winepost',
                                            args=[wine['wp_id']])
                        found_wm_url = reverse(
                            'edit_winemaker', args=[wine['winemaker_id']])
                    else:
                        found_url = "#"
                        found_wm_url = "#"

                    found_what.append((wine['wine_name'], wine['deabbr_name'],
                                       'wine_name', found_url, False))
                if (  # Wine name short
                        wine.get('deabbr_name_short') and
                        wine['deabbr_name_short'] in row_deabbr and
                        search_matches(
                            escape=wine['deabbr_name_short'],
                            value=row_deabbr) and
                        not wine['deabbr_name_short'] in deabbr_exceptions and
                        not wine['deabbr_name_short'].isdigit()
                ):
                    if 'wp_id' in wine and wine['wp_id']:
                        found_url = reverse('edit_winepost',
                                            args=[wine['wp_id']])
                        found_wm_url = reverse(
                            'edit_winemaker', args=[wine['winemaker_id']])
                    else:
                        found_url = "#"
                        found_wm_url = "#"

                    # exclude the matched short version from WHAT? column
                    # in presence of the matched full version
                    if found_wine_obj:
                        short_wine_all_name_to_exclude = True
                    found_wine_obj = wine
                    found_what.append((wine['wine_name_short'],
                                       wine['deabbr_name_short'],
                                       'wine_name_short', found_url,
                                       short_wine_all_name_to_exclude))
                if found_wine_obj:
                    if wine['wm_name']:
                        found_what.append((wine['wm_name'],
                                           wine['deabbr_wm_name'],
                                           'winemaker', found_wm_url, False))
                    elif wine['wm_name_short']:
                        found_what.append((wine['wm_name_short'],
                                           wine['deabbr_wm_name_short'],
                                           'winemaker_short', found_wm_url,
                                           False))
                    else:
                        pass

                # if found_wine_obj:
                #     break  # we want to search for max. 1 wine

                if found_wine_obj:
                    # check if it is already in the list under any found
                    # winemaker
                    if all_matches:
                        exising_wp_ids_list = []
                        for m in all_matches:
                            if m['wm_obj']:
                                exising_wp_ids_list.append(m['wm_obj']['id'])
                        if found_wine_obj['winemaker_id'] in exising_wp_ids_list:
                            continue

                    if found_wine_obj['wp_status'] == natural:
                        status_pt = 2
                    elif found_wine_obj['wp_status'] in moderated:
                        status_pt = 1
                    else:
                        status_pt = 0

                    another_match['pt'] = 1
                    another_match['status_pt'] = status_pt
                    another_match['wine_obj'] = found_wine_obj
                    another_match['found'] = True
                    another_match['found_what'] = found_what
                    another_match['status'] = found_wine_obj['wp_status']
                    all_matches.append(another_match)

        # if another_match['found']:
        if all_matches:
            # print('PRE_HIGHLIGHTING: ', all_matches)
            # highlight matches in current row
            all_found_bounds = []
            for another_match in all_matches:
                for f_i in another_match['found_what']:
                    iter_result = re.finditer(
                        pattern=r'\b%s\b' % re.escape(f_i[1]),
                        string=row_deabbr
                    )
                    for m in iter_result:
                        all_found_bounds.append([
                            list(range(m.start(), m.end() + 1)),
                            another_match['status']
                        ])

            # print('PRE highlighting')
            all_found_bounds = get_highlight_borders(all_found_bounds)
            all_found_bounds.sort(key=sort_highlight_zones, reverse=True)
            # print('POST highlighting')

            # formatting highlighting boundaries into HTML
            for x_hl in all_found_bounds:
                if x_hl:
                    if x_hl[1] == 10:  # DRAFT
                        color = '#1CBDDC'
                    elif x_hl[1] == 15:  # IN_DOUBT
                        color = '#00008B'
                    elif x_hl[1] == 20:  # NATURAL
                        color = '#66B266'
                    elif x_hl[1] == 25:  # NOT_NATURAL
                        color = '#FF5D5D'
                    elif x_hl[1] == 30:  # BIO_ORGANIC
                        color = '#FFA500'
                    elif x_hl[1] == 45:  # TO_INVESTIGATE
                        color = '#A066B2'
                    elif x_hl[1] == 0:  # OVERLAPPED
                        color = '#000000'
                    else:  # COLOR TO SPOT A WRONG BEHAVIOUR
                        color = '#808080'

                    x0 = x_hl[0][0]
                    x1 = x_hl[0][len(x_hl[0]) - 1]

                    row_tmp = f'{row_deabbr[0:x0]}' \
                              f'<span style="color: {color}"><b>' \
                              f'{row_deabbr[x0:x1]}</b></span>' \
                              f'{row_deabbr[x1:]}'
                    row_deabbr = row_tmp

            # print('PRE found what/where assembly')
            found_what_urls = []
            colors = {10: '#1CBDDC',
                      15: '#00008B',
                      20: '#66B266',
                      25: '#FF5D5D',
                      30: '#FFA500',
                      45: '#A066B2',
                      0: '#000000'}
            for another_match in all_matches:
                found_what_urls.append('<div class="outerDiv">')  # section for formatting
                found_where.append('<div class="outerDiv">')  # section for formatting
                for it in another_match['found_what']:
                    if not it[4]:  # if short name value here is in presence
                        # of the full name value
                        # then it should not be displayed in WHAT? column
                        found_what_urls.append(f'<span><a style="color:{colors[another_match["status"]]};" href={it[3]} target="_blank">{it[0]}</a> <i class="fa fa-times-circle add_excluded_keyword" data-keyword="{it[0]}" data-link="{it[3]}"></i></span>')  # noqa
                        found_what_urls.append('- ')  # divider

                    found_where.append(f'<span style="color:{colors[another_match["status"]]};">{it[2]}</span>')  # noqa
                    found_where.append('- ')  # divider

                found_where.pop(-1)  # remove last divider
                found_where.append('</div>')

                found_what_urls.pop(-1)  # remove last divider
                found_what_urls.append('</div>')
            # print('POST found what/where assembly')
        else:
            found_what_urls = []
            found_where = []

        # set wine only matches statuses to in_doubt
        if all_matches:
            for match_item in all_matches:
                if match_item.get('wine_only_match'):
                    match_item['status'] = PostStatusE.IN_DOUBT

        # choose the best match to set status for row
        # print('PRE_BESTMATCHING: ', all_matches)
        best_match = {
            'pt': 0,
            'status_pt': 0,
            'wm_obj': None,
            'wine_obj': None,
            'found': False,
            'found_what': [],
            'status': no_data
        }
        # Check whether 'already moderated' status is present and whether it
        # should persist for current row.
        if (
            moderated_indexes and
            isinstance(moderated_indexes.get(i), int) and
            not new_exclusion_word_row == i
        ):
            best_match['status'] = moderated_indexes.get(i)
            was_manually_moderated = True  # to preserve status
            # manually chosen by moderator in case of re-evaluation
        else:
            was_manually_moderated = False
            if len(all_matches) > 1:
                max_pt = 0
                max_status_pt = 0

                for match in all_matches:
                    if match['pt'] > max_pt:
                        max_pt = match['pt']
                        max_status_pt = match['status_pt']
                    elif match['pt'] == max_pt:
                        if match['status_pt'] > max_status_pt:
                            max_status_pt = match['status_pt']

                for match in all_matches:
                    if match['pt'] == max_pt and \
                            match['status_pt'] == max_status_pt:
                        best_match = match
            elif len(all_matches) == 1:
                best_match = all_matches[0]
            else:
                found_what_urls = []
                found_where = []

        if best_match['status'] == natural:
            item_res = 'yes'
            data_out['num_rows_yes'] += 1
            inc = True
            data_out['num_rows_total'] += 1
        elif best_match['status'] in not_natural_and_others and \
                best_match['status'] not in excluded_from_total_score:
            item_res = 'no'
            data_out['num_rows_no'] += 1
            inc = True
            data_out['num_rows_total'] += 1
        elif best_match['status'] in excluded_from_total_score:
            item_res = 'no'
            inc = False
        else:
            raise ValueError('the wrong status has been received')

        item_out = {
            'ind': i,  # index
            'row': row_deabbr,
            'res': item_res,  # 'is natural?' column. 'res' is row_yes.
            'inc': inc,  # include checkbox is True for all by default
            'status': best_match['status'],
            'moderated': was_manually_moderated,
            'found_where': " ".join(found_where) if found_where else "",
            'found_what': " ".join(found_what_urls) if found_what_urls else "",
        }

        data_out['rows_out'].append(item_out)
        i += 1

    if data_out['num_rows_total'] and data_out['num_rows_yes']:
        data_out['score_percent'] = round(data_out['num_rows_yes'] /
                                          data_out['num_rows_total'] * 100, 2)
    else:
        data_out['score_percent'] = 0.0
    # print('-----------------------', datetime.datetime.now() - a)
    print('return')
    return data_out


def recalc_by_row_score(by_row_score, incs):
    if not by_row_score:
        return None

    if incs:
        for i, inc in enumerate(incs):
            incs[i] = int(inc)

    num_rows_included = 0
    num_rows_yes = 0
    num_rows_no = 0

    natural = 20
    exclude = 0
    no_data = 2
    not_natural_and_others = [exclude, no_data, 10, 15, 25, 30, 45]
    excluded_from_total_score = [exclude]

    for i, row_data in enumerate(by_row_score['rows_out']):
        # set status selected by moderator
        row_data['status'] = incs[i]

        if row_data['status'] == natural:
            by_row_score['rows_out'][i]['inc'] = True
            num_rows_included += 1
            row_data['res'] = 'yes'
            num_rows_yes += 1
        elif row_data['status'] in not_natural_and_others and \
                row_data['status'] not in excluded_from_total_score:
            by_row_score['rows_out'][i]['inc'] = True
            num_rows_included += 1
            row_data['res'] = 'no'
            num_rows_no += 1
        elif row_data['status'] in excluded_from_total_score:
            by_row_score['rows_out'][i]['inc'] = False
            row_data['res'] = 'no'
        else:
            raise ValueError('the wrong status has been received')

    by_row_score['num_rows_total'] = num_rows_included
    by_row_score['num_rows_yes'] = num_rows_yes
    by_row_score['num_rows_no'] = num_rows_no

    if num_rows_included and by_row_score['num_rows_yes'] and by_row_score['num_rows_total']:
        by_row_score['score_percent'] = round(by_row_score['num_rows_yes'] / by_row_score['num_rows_total'] * 100, 2)
    else:
        by_row_score['score_percent'] = 0.0

    return by_row_score
