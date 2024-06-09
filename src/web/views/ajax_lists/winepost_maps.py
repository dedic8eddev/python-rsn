def winepost_items_col_map_with_vuforia():
    return {
        0: 'id',
        1: 'status',
        2: 'title',                     # img
        3: None,  # label
        4: None,

        5: 'wine__winemaker__name',
        6: 'wine__domain',
        7: 'wine__designation',
        8: 'wine__grape_variety',
        9: 'wine__winemaker__region',

        10: 'wine_year',
        11: 'wine__color',
        12: 'wine__is_sparkling',
        13: 'description',
        14: 'modified_time',

        15: 'author__username',         # author img
        16: 'expert__username',         # expert img
        17: 'place__name',              # geolocation
        18: 'comment_number',
        19: 'price',
    }


def winepost_items_col_map_for_winemaker():
    return {
        0: 'wp.id',
        1: None,  # img
        2: None,  # vuforia img
        3: 'modified_time',
        4: 'author__username',  # author img

        5: 'title',
        6: 'status',

        7: 'wine__winemaker__region',  # designation
        8: 'wine__grape_variety',
        9: 'wine_year',
        10: 'wine__color',
        11: 'wine__is_sparkling',

        12: 'comment_number',
        13: 'likevote_number',
        14: 'drank_it_too_number',
    }


def winepost_items_col_map_for_winepost():
    return {
        0: 'id',
        1: 'author__username',  # author img
        2: None,  # img

        3: 'title',
        4: 'description',
        5: 'status',

        6: 'wine__winemaker__name',
        7: 'wine__winemaker__domain',
        8: 'wine__winemaker__region',

        9: 'wine__grape_variety',
        10: 'wine__winemaker__region',
        11: 'wine_year',

        12: 'wine__color',
        13: 'wine__is_sparkling',
        14: None,  # geolocation

        15: 'comment_number',
        16: 'likevote_number',
        17: 'drank_it_too_number',
    }


def winepost_items_col_map_referees():
    return {
        0: 'id',
        1: None,  # img
        2: 'modified_time',
        3: 'author__username',  # author img

        4: 'title',
        5: 'description',
        6: 'status',

        7: 'wine__winemaker__name',
        8: 'wine__winemaker__domain',
        9: 'wine__winemaker__region',

        10: 'wine__grape_variety',
        11: 'wine__winemaker__region',
        12: 'wine_year',

        13: 'wine__color',
        14: 'wine__is_sparkling',
        15: None,  # geolocation

        16: 'comment_number',
        17: 'likevote_number',
        18: 'drank_it_too_number',
    }


def winepost_items_col_map_for_user():
    return {
        0: 'id',
        1: None,  # img
        2: 'modified_time',

        3: 'title',
        4: 'description',
        5: 'status',

        6: 'wine__winemaker__region',
        7: 'wine__grape_variety',
        8: 'wine__winemaker__name',

        9: 'wine_year',
        10: 'wine__color',
        11: 'wine__is_sparkling',

        12: 'comment_number',
        13: 'likevote_number',
        14: 'drank_it_too_number',
    }
