import os

from django.db import connection

from .fetches import fetchalldict


def vuf_set_images_to_delete_for_wine(wine_id, winepost_id):
    sql = "UPDATE vuforia_image SET delete_from_vuforia = true " \
          "    WHERE wine_id = %(wine_id)s " \
          "          AND vuforia_deleted != true " \
          "          AND delete_from_vuforia != true"
    params = {"wine_id": wine_id}
    if winepost_id:
        sql += "  AND post_id != %(post_id)s "
        params['post_id'] = winepost_id
    with connection.cursor() as cursor:
        cursor.execute(sql, params)


def decorate_images_with_name(items):
    if items:
        for i, item in enumerate(items):
            items[i]['name'] = os.path.basename(item['image_file'])


def fetch_vuforia_images_all():
    sql = "SELECT ai.id, ai.image_file, ai.width, ai.height, ai.created_time, ai.modified_time, " \
          "    vi.post_id, vi.wine_id, vi.rating_reco, vi.rating_tracking, " \
          "    vi.target_id, vi.is_dirty" \
          "    FROM vuforia_image vi " \
          "    INNER JOIN web_abstractimage ai ON ai.id=vi.abstractimage_ptr_id " \
          "    WHERE vi.vuforia_deleted != true AND delete_from_vuforia != true"
    params = []
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        items = fetchalldict(cursor)
        decorate_images_with_name(items)
        return items


def fetch_vuforia_images_by_ids(ids):
    ids_str = ','.join(["'%s'" % iid for iid in ids])
    sql = "SELECT ai.id, ai.image_file, ai.width, ai.height, ai.created_time, ai.modified_time, " \
          "    vi.post_id, vi.wine_id, vi.rating_reco, vi.rating_tracking, " \
          "    vi.target_id, vi.is_dirty" \
          "    FROM vuforia_image vi " \
          "    INNER JOIN web_abstractimage ai ON ai.id=vi.abstractimage_ptr_id " \
          "    WHERE vi.abstractimage_ptr_id IN (%s)" % ids_str
    params = []
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        items = fetchalldict(cursor)
        decorate_images_with_name(items)
        return items
