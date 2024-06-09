import logging
import os

import textract
from django.conf import settings
from google.cloud import vision as gc_vision

from web.utils.filenames import (create_dir_if_not_exists, get_extension,
                                 get_local_file_contents)
from web.utils.temp_images import listdir
from web.utils.upload_tools import download_to_local

log = logging.getLogger(__name__)
MAX_IMAGES_IN_PDF = 100
MAX_FILESIZE_BYTES = 9999000


def get_text_rows_from_ocr(file, wf_id=None, wl_id=None):
    google_vision_image_formats = [
        'jpeg', 'jpg', 'gif', 'bmp', 'png', 'raw', 'ico', 'webp'
    ]

    ext = get_extension(file.name).strip('.')
    path = os.path.join(settings.PROJECT_ROOT, 'media', file.name)

    text_rows = []
    if ext in google_vision_image_formats:
        log.info(
            "Using GOOGLE API VISION FOR FILEPATH {}".format(str(file.name))
        )
        download_to_local(file, path)
        text_rows = read_text_rows_from_pic_google_vision(path)
        os.remove(path)

        return text_rows

    try:
        log.info("Using TEXTRACT FOR FILEPATH {}".format(str(file.name)))
        download_to_local(file, path)
        text_rows = read_text_rows_from_pic_textract(path)
        os.remove(path)
    except textract.exceptions.ExtensionNotSupported:
        log.debug(
            "FILE with path {} has UNSUPPORTED EXTENSION - SKIPPING.".format(
                str(file.name))
            )
        archive_related(file)
        text_rows = ["ERROR - FILE has unsupported extension - can't parse."]
    except Exception as e:
        log.debug(
            "EXCEPTION OCCURED DURING OCR-ING THE FILE with path {} - "
            "SKIPPING. Exception string: {}" .format(file.name, str(e))
        )
        archive_related(file)
        text_rows = ["ERROR - BROKEN FILE - can't parse."]

    return text_rows


def archive_related(file):
    # TODO only if really file
    file.instance.is_archived = True
    file.instance.winelist.is_archived = True
    file.instance.save()
    file.instance.winelist.save()


# https://stackoverflow.com/questions/36728347/cloud-vision-api-pdf-ocr
def read_text_rows_from_pic_google_vision(pic_path):
    rows_out = []
    client = gc_vision.ImageAnnotatorClient()

    if not check_file_size_for_google_vision(pic_path):
        return []

    try:
        content = get_local_file_contents(pic_path, 'rb')
        image = gc_vision.types.Image(content=content)
        response = client.document_text_detection(image=image)
        document = response.full_text_annotation
        old_s_x0 = 0
        old_s_y0 = 0
        old_w_x0 = 0
        old_w_y0 = 0
        old_w_x1 = 0
        old_w_y1 = 0

        for page in document.pages:
            old_block_x1 = None
            old_block_y0 = None
            old_block_y1 = None
            block_x0 = None
            block_y0 = None
            row_out_arr = []
            buf_text_arr = []
            blocks_rows = []

            # ========================= experiment ==========================
            for block in page.blocks:
                vrt = block.bounding_box.vertices
                b_x0 = vrt[0].x
                b_y0 = vrt[0].y
                b_x1 = vrt[2].x
                b_y1 = vrt[2].y
                i_found = -1
                row_i_found = -1
                s_txt = ""
                for par in block.paragraphs:
                    for w in par.words:
                        for s in w.symbols:
                            s_txt += s.text
                        s_txt += " "
                br_out = {
                    'b_x0': b_x0,
                    'b_y0': b_y0,
                    'b_x1': b_x1,
                    'b_y1': b_y1,
                    'block': block,
                    'txt': s_txt,
                }

                if blocks_rows:
                    for row_i, row in enumerate(blocks_rows):
                        for i in range(len(row)-1, -1, -1):
                            br = row[i]
                            if (
                                br['b_y0'] <= b_y0 <= br['b_y1'] or
                                b_y0 <= br['b_y0'] <= b_y1
                            ):
                                i_found = i
                                row_i_found = row_i
                                break

                if row_i_found >= 0:
                    row_upd = blocks_rows[row_i_found]
                    if i_found >= 0:
                        row_upd.insert(i_found + 1, br_out)
                    else:
                        row_upd.append([br_out])
                    blocks_rows[row_i_found] = row_upd
                else:
                    row_upd = [br_out]
                    blocks_rows.append(row_upd)

            for br_row in blocks_rows:
                for br in br_row:
                    block = br['block']
                    new_row = False
                    block_x0 = block.bounding_box.vertices[0].x
                    block_y0 = block.bounding_box.vertices[0].y
                    block_words = []
                    old_par_x0 = None
                    old_par_y0 = None

                    for paragraph in block.paragraphs:
                        for w in paragraph.words:
                            w_x0 = w.bounding_box.vertices[0].x
                            w_y0 = w.bounding_box.vertices[0].y
                            w_x1 = w.bounding_box.vertices[2].x
                            w_y1 = w.bounding_box.vertices[2].y
                            if w_y0 > old_w_y1:
                                buf_text_arr.append("<NL>")
                            for s in w.symbols:
                                buf_text_arr.append(s.text)
                            buf_text_arr.append(" ")
                            old_w_x0 = w_x0
                            old_w_y0 = w_y0
                            old_w_x1 = w_x1
                            old_w_y1 = w_y1

            row_out_txt = ""
            for c in buf_text_arr:
                if c == '<NL>':
                    rows_out.append(row_out_txt)
                    row_out_txt = ""
                else:
                    row_out_txt += c

            rows_out.append(row_out_txt)

        return rows_out
    except Exception as e:
        msg = "OCR: FILE {} parsing in Google Vision API FAILED - message {}"
        log.debug(msg.format(pic_path, str(e)))
        return []


def read_text_rows_from_pic_textract(path):
    ext = get_extension(path).strip('.')
    if ext == 'pdf':
        log.debug("TEXTRACT - PDF - PATH %s " % path)
        # read textual part of the PDF (text encoded in the PDF) if present
        text_bytes = textract.process(path, layout=True)
        if text_bytes:
            text_str = text_bytes.decode('UTF-8')
            log.debug(
                "TEXTRACT - PDF - TEXT BYTES AVAILABLE. TEXT STR {}".format(
                    text_str
                )
            )
            rows_out = text_str.split("\n")
            rows_out = [
                ro.replace('\u0000', ' ') for ro in rows_out
                if ro.lower().find('newrelic') == -1
                and ro.lower().find('current python') == -1
            ]
        else:
            log.debug("TEXTRACT - PDF - TEXT BYTES NOT AVAILABLE")
            rows_out = []

        # read and OCR the graphical part of the PDF
        # (images contained in the PDF) if present
        file = os.path.basename(path)
        dir_path = os.path.dirname(path)
        dir_images_root = os.path.join(dir_path, "{}-images".format(file))
        img_temp_dir = create_dir_if_not_exists(dir_images_root)
        img_temp_path = os.path.join(img_temp_dir, "img")
        cmd = "pdfimages -j %s %s" % (path, img_temp_path)
        res = os.system(cmd)
        if res == 0:
            dirs, files = listdir(img_temp_dir)
            img_paths = [os.path.join(img_temp_dir, f) for f in files]
            if len(img_paths) > MAX_IMAGES_IN_PDF:
                err_rows_out = [
                    "! ALERT ! Graphical part of this PDF contains more than "
                    "{} images. We can't parse so many images. You "
                    "get a result based only on the text part of this PDF "
                    ".\n".format(MAX_IMAGES_IN_PDF)  # noqa
                ]
                err_rows_out.extend(rows_out)
                rows_out = err_rows_out
            else:
                if img_paths:
                    for img_path in img_paths:
                        img_rows_out = read_text_rows_from_pic_google_vision(
                            img_path
                        )
                        os.unlink(img_path)
                        if img_rows_out:
                            rows_out.extend(img_rows_out)
                    os.rmdir(img_temp_dir)
        return rows_out

    # Not PDF
    text_bytes = textract.process(path)
    log.debug("TEXTRACT - NOT PDF - PATH %s " % path)
    if text_bytes:
        text_str = text_bytes.decode('UTF-8')
        log.debug("TEXTRACT - TEXT BYTES AVAILABLE. TEXT STR %s", text_str)
        rows_out = text_str.split("\n")
        rows_out = [
            ro.replace('\u0000', ' ') for ro in rows_out
            if ro.lower().find('newrelic') == -1
            and ro.lower().find('current python') == -1
        ]

        return rows_out
    else:
        log.debug("TEXTRACT - TEXT BYTES NOT AVAILABLE. ")

        return []


def check_file_size_for_google_vision(pic_path):
    exc_message = 'BG-OCR: FILE {} DOES NOT EXIST OR IS BROKEN - '.format(
        pic_path
    )

    try:
        size = os.path.getsize(pic_path)
    except OSError as e:
        log.debug(exc_message + "OSError message {}".format(str(e)))

        return False
    except FileNotFoundError as e:
        log.debug(exc_message + "FileNotFoundError message {}".format(str(e)))

        return False
    except Exception as e:
        log.debug(exc_message + "Exception message {}".format(str(e)))

        return False

    if size <= MAX_FILESIZE_BYTES:
        return True

    msg = "BG-OCR: FILE {} EXCEEDS MAX_FILESIZE_BYTES {} - could not be sent to Google Vision API"  # noqa
    log.debug(msg.format(pic_path, MAX_FILESIZE_BYTES))

    return False
