from .vuforia import fetch_vuforia_images_all, fetch_vuforia_images_by_ids
from ..services.vuforia import VuforiaService


def discover_target_ids_by_names(image_id):
    # fetch whether the target_id has been updated (set) for the image in the meantime, during discovery
    # of some other image (all images' target_ids are discovered at the same time)
    res_target_id = None
    images = fetch_vuforia_images_by_ids([image_id])
    if not images:
        return None
    if images[0]['target_id']:
        return images[0]['target_id']

    # get ALL targets stored in vuforia database - sadly it's the only way,
    # there's no direct searching by name
    status_code, r = VuforiaService().get_all_targets()
    if status_code != VuforiaService().STATUS_CODE_OK or 'results' not in r \
            or not r['results']:
        return None

    target_ids_vuforia = r['results']
    all_images_in_db = fetch_vuforia_images_all()
    target_ids_db = [item['target_id'] for item in all_images_in_db if item['target_id']]
    images_by_name = {item['name']: item for item in all_images_in_db}
    target_ids_not_db = list(set(target_ids_vuforia) - set(target_ids_db)) \
        if target_ids_db else target_ids_vuforia

    # not all target_ids from Vuforia are in DB, updating
    if target_ids_not_db:
        # for each target_id not in DB, fetch the target details (including target_id
        # and name) from Vuforia and attempt to match each result row by "name" field
        # with images_by_name
        for target_id in target_ids_not_db:
            sc, r = VuforiaService().get_target_by_id(target_id)
            if sc == VuforiaService.STATUS_CODE_OK \
                    and 'target_record' in r \
                    and r['target_record']:
                target_name = r['target_record']['name']
                # image with this name (without target_id) exists in DB,: update the
                # target_id for it
                if target_name in images_by_name and images_by_name[target_name]:
                    img = images_by_name[target_name]
                    if img['id'] == image_id:
                        res_target_id = target_id
    return res_target_id
