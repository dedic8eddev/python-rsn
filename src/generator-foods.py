import csv
from django import *
from web import *
from web.models import *
import os
# posts = Post.active.filter(status=20)
# venues = Place.active.filter(is_venue=True)
# p_g_i = 0
# for venue in venues:
#     for i in range(0, 12):
#         if p_g_i >= len(posts):
#             exit()
#         post = posts[p_g_i]
#         post.venue = venue
#         post.save()
#         post.refresh_from_db()
#         p_g_i += 1

filepath = os.path.join(settings.MEDIA_ROOT, 'data', 'export-all-foods.csv')
user_admin = UserProfile.active.get(username='admin')

DELIMITER = ';'
QUOTING = csv.QUOTE_MINIMAL
LINE_TERMINATOR = '\r\n'
ENCLOSURE = '"'


csv.register_dialect(
    'mydialect',
    delimiter=DELIMITER,
    quotechar=ENCLOSURE,
    doublequote=True,
    skipinitialspace=True,
    lineterminator=LINE_TERMINATOR,
    quoting=QUOTING)
with open(filepath, newline='') as csvfile:
    csv_reader = csv.reader(csvfile, dialect='mydialect')
    row_mapping = [
        'id',
        'created_time',
        'modified_time',
        'status',
        'type',
        'is_archived',
        'is_parent_post',
        'is_star_review',
        'title',
        'description',
        'latitude',
        'longitude',
        'comment_number',
        'drank_it_too_number',
        'likevote_number',
        'star_review_number',
        'author_id',
        'parent_post_id',
        'place_id',
        'wine_id',
        'main_image_id',
        'last_modifier_id',
        'wine_year',
        'foursquare_place_name',
        'foursquare_place_url',
        'user_mentions',
        'expert_id',
        'in_doubt',
        'validated_at',
        'validated_by_id',
        'team_comments',
        'free_so2',
        'total_so2',
        'wine_trade',
        'yearly_data',
        'grape_variety',
        'ref_image_id',
        'vuf_match_post_id',
        'vuf_match_wine_id',
        'is_scanned',
        'is_star_discovery',
        'certified_by',
        'is_organic',
        'is_biodynamic',
    ]
    item_objs = {}
    rows_dict = []
    row_i = 1
    venues = Place.active.filter(is_venue=True)
    for row in csv_reader:
        if row_i < 2:
            row_i += 1
            continue
        else:
            row_i += 1
        len_row = len(row)
        row_dict = {}
        for index, field in enumerate(row_mapping):
            if index < len_row:
                row_dict[field] = row[index]
            else:
                row_dict[field] = None

        main_image = AbstractImage.active.get(id=row_dict['main_image_id'])
        item_data = {
            'author': user_admin,
            'created_time': row_dict['created_time'],
            'modified_time': row_dict['modified_time'],
            'status': row_dict['status'],
            'type': row_dict['type'],
            'is_archived': row_dict['is_archived'],
            'is_parent_post': row_dict['is_parent_post'],
            'is_star_review': row_dict['is_star_review'],
            'title': row_dict['title'],
            'description': row_dict['description'],
            'latitude': row_dict['latitude'],
            'longitude': row_dict['longitude'],
            'comment_number': row_dict['comment_number'],
            'drank_it_too_number': row_dict['drank_it_too_number'],
            'likevote_number': row_dict['likevote_number'],
            'star_review_number': row_dict['star_review_number'],
            'main_image': row_dict['main_image'],
            'wine_year': row_dict['wine_year'],
            'foursquare_place_name': row_dict['foursquare_place_name'],
            'foursquare_place_url': row_dict['foursquare_place_url'],
            'user_mentions': row_dict['user_mentions'],
            'in_doubt': row_dict['in_doubt'],
            'team_comments': row_dict['team_comments'],
            'free_so2': row_dict['free_so2'],
            'total_so2': row_dict['total_so2'],
            'wine_trade': row_dict['wine_trade'],
            'yearly_data': row_dict['yearly_data'],
            'grape_variety': row_dict['grape_variety'],
            'is_scanned': row_dict['is_scanned'],
            'is_star_discovery': row_dict['is_star_discovery'],
            'certified_by': row_dict['certified_by'],
            'is_organic': row_dict['is_organic'],
            'is_biodynamic': row_dict['is_biodynamic'],
            # 'validated_at' :          row_dict['validated_at'],
            # 'validated_by_id' :       row_dict['validated_by_id'],
            # 'ref_image_id' :          row_dict['ref_image_id'],
            # 'vuf_match_post_id' :     row_dict['vuf_match_post_id'],
            # 'vuf_match_wine_id' :     row_dict['vuf_match_wine_id'],
            # 'wine_id' :               row_dict['wine_id'],
            # 'last_modifier_id' :      row_dict['last_modifier_id'],
            # 'expert_id' :             row_dict['expert_id'],
            # 'parent_post_id' :        row_dict['parent_post_id'],
            # 'place_id' :              row_dict['place_id'],
        }
        for venue in venues:
            new_post = Post(**item_data)
            new_post.venue = venue
            new_post.save()
