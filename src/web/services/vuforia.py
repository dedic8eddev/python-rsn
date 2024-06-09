import base64
import copy
import hashlib
import hmac
import json
import time

import requests
from django.conf import settings


class VuforiaService:
    hex_digest = 'd41d8cd98f00b204e9800998ecf8427e'
    # < Response[200] > {"result_code":"TargetCreated",
    # "transaction_id":"72e6c2d622b84026a0f321df31570937","target_id":"9fba72e8042e48d192f3211ad8667f7f"}
    # < Response[400] > {"result_code": "Fail", "transaction_id": "0faa40f0ffc64814bd140dba8ad6d1f1"}
    # < Response[401] >{'result_code': 'AuthenticationFailure',
    #  'transaction_id': 'c46723a116924869803681d20fbde99a'}
    # < Response[403] > {"result_code": "TargetNameExist", "transaction_id": "58a2cfd1956a45f980ba28c1173e604c"}
    # {'transaction_id': 'b86f0dc7b6f14717bcc6359720dc5547', 'result_code': 'Fail'}
    STATUS_CODE_OK = 200
    STATUS_CODE_TARGET_CREATED = 201
    STATUS_CODE_FAIL = 400
    STATUS_CODE_AUTH_ERROR = 401
    STATUS_CODE_ALREADY_EXISTS = 403
    STATUS_CODE_NOT_FOUND = 404
    STATUS_CODE_BAD_IMAGE = 422

    def get_formatted_datetime(self):
        return time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())

    def get_tms_signature(self, req_method, req_date, req_body_in, req_content_type, req_path):
        if not req_content_type:
            req_content_type = ''
        req_body_in_copy = copy.deepcopy(req_body_in)
        if isinstance(req_body_in_copy, dict):
            req_body = json.dumps(req_body_in_copy)
        else:   # string
            req_body = req_body_in_copy

        if req_method in ['GET', 'DELETE']:
            hex_digest = self.hex_digest
        elif req_method in ['POST', 'PUT']:
            hex_digest = hashlib.md5(req_body.encode('utf-8')).hexdigest()
        else:
            raise ValueError("Invalid request method - only GET, DELETE, POST and PUT are allowed ")

        to_digest = "{req_method}\n{hex_digest}\n{req_content_type}\n{req_date}\n{req_path}".\
            format(
                req_method=req_method,
                hex_digest=hex_digest,
                req_content_type=req_content_type,
                req_date=req_date,
                req_path=req_path)

        sha_hashed = hmac.new(
            settings.VUFORIA_SECRET_KEY.encode('utf-8'),
            to_digest.encode('utf-8'),
            hashlib.sha1
        )
        sha_hashed_digest = sha_hashed.digest()
        # sha_hashed_hex_digest = sha_hashed.hexdigest()
        return base64.b64encode(sha_hashed_digest).decode('utf-8')

    def get_auth_string(self, req_method, req_date, req_body, req_content_type, req_path):
        tms_signature = self.get_tms_signature(req_method, req_date, req_body, req_content_type, req_path)
        res = "VWS %s:%s" % (settings.VUFORIA_ACCESS_KEY, tms_signature)
        return res

    def encode_image(self, image_data):
        return base64.b64encode(image_data).decode('utf-8')
        # im_in = Image.frombytes(image_data)
        # im_out = Image.new("RGB", im_in.size, (255,255,255))
        # im_out.paste(im_in, im_in)
        # im_out.tobytes(encoder_name='jpeg')
        # return base64.b64encode(im_out).decode('utf-8')

    def add_target(self, name, image_data, width, metadata, active_flag):
        if not image_data:
            return self.STATUS_CODE_FAIL, {"error": "No image data."}
        data = {
            'name': name,
            'width': width,
            'image': self.encode_image(image_data),
            'application_metadata': base64.b64encode(json.dumps(metadata).encode('utf-8')).decode('utf-8'),
            # 'active_flag': active_flag,
        }
        date = self.get_formatted_datetime()
        auth_string = self.get_auth_string('POST', date, data, 'application/json', '/targets')
        headers = {
            "Date": date,
            "Content-Type": "application/json",
            "Authorization": auth_string,
        }
        resp = requests.post("https://vws.vuforia.com/targets", data=json.dumps(data), headers=headers)
        return resp.status_code, resp.json()

    def update_target(self, target_id, name, image_data, width, metadata, active_flag):
        if not image_data:
            return self.STATUS_CODE_FAIL, {"error": "No image data."}
        url_rel = '/targets/%s' % target_id
        data = {
            # 'name': name,
            'width': width,
            'image': self.encode_image(image_data),
            'application_metadata': base64.b64encode(json.dumps(metadata).encode('utf-8')).decode('utf-8'),
            # 'active_flag': active_flag,
        }
        date = self.get_formatted_datetime()
        auth_string = self.get_auth_string('PUT', date, data, 'application/json', url_rel)
        headers = {
            "Date": date,
            "Content-Type": "application/json",
            "Authorization": auth_string,
        }
        url = "https://vws.vuforia.com%s" % url_rel
        resp = requests.put(url, data=json.dumps(data), headers=headers)
        return resp.status_code, resp.json()

    def get_all_targets(self):
        date = self.get_formatted_datetime()
        auth_string = self.get_auth_string('GET', date, None, None, '/targets')
        headers = {
            "Date": date,
            "Authorization": auth_string,
        }
        url = "https://vws.vuforia.com/targets"
        resp = requests.get(url, headers=headers)
        # {"result_code":"Success","transaction_id":"5efe83907f244c15b7688c365cef27cc",
        # "results":["64f8e780ca2b4018a16fe2b3447c6727","9fba72e8042e48d192f3211ad8667f7f"]}
        return resp.status_code, resp.json()

    def get_duplicates(self, target_id):
        url_rel = '/duplicates/%s' % target_id
        date = self.get_formatted_datetime()
        auth_string = self.get_auth_string('GET', date, None, None, url_rel)
        headers = {
            "Date": date,
            "Authorization": auth_string,
        }
        url = "https://vws.vuforia.com%s" % url_rel
        resp = requests.get(url, headers=headers)
        # {"result_code":"Success","transaction_id":"5efe83907f244c15b7688c365cef27cc",
        # "results":["64f8e780ca2b4018a16fe2b3447c6727","9fba72e8042e48d192f3211ad8667f7f"]}
        return resp.status_code, resp.json()

    def delete_target(self, target_id):
        url_rel = '/targets/{}'.format(target_id)
        date = self.get_formatted_datetime()
        auth_string = self.get_auth_string('DELETE', date, None, None, url_rel)
        headers = {
            "Date": date,
            "Authorization": auth_string,
        }

        url = "https://vws.vuforia.com%s" % url_rel
        resp = requests.delete(url, headers=headers)

        # sample response {"result_code":"Success","transaction_id":"5efe83907f244c15b7688c365cef27cc"
        return resp.status_code, resp.json()

    def get_target_by_id(self, target_id):
        date = self.get_formatted_datetime()
        url_rel = '/targets/{}'.format(target_id)
        auth_string = self.get_auth_string('GET', date, None, None, url_rel)
        headers = {
            "Date": date,
            "Authorization": auth_string,
        }
        url = "https://vws.vuforia.com{}".format(url_rel)
        resp = requests.get(url, headers=headers)
        # /targets/9fba72e8042e48d192f3211ad8667f7f{"result_code":"Success",
        # "transaction_id":"54fffa21b0e84dbc93423241aece9f73","target_record":
        #   {"target_id":"9fba72e8042e48d192f3211ad8667f7f","active_flag":true,"name":"553--568.jpgA",
        # "width":320,"tracking_rating":4,"reco_rating":""},"status":"success"}
        return resp.status_code, resp.json()
