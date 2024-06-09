from web.models import ApiUserStorage


class ApiUserStorageUtils:
    @classmethod
    def get_user_token_from_request(cls, request):
        token_data = request.META['HTTP_AUTHORIZATION']
        if not token_data or len(token_data) < 6:
            return None
        token = token_data[5:]
        return token

    @classmethod
    def _get_value_in_storage(cls, storage, setting_field):
        if storage.stored_data and setting_field in storage.stored_data:
            return storage.stored_data[setting_field]
        return None

    @classmethod
    def _set_value_in_storage(cls, storage, setting_field, setting_value):
        if not storage.stored_data:
            storage.stored_data = {}
        storage.stored_data[setting_field] = setting_value
        storage.save()
        storage.refresh_from_db()

    @classmethod
    def _clear_value_in_storage(cls, storage, setting_field):
        if storage.stored_data and setting_field in storage.stored_data:
            del storage.stored_data[setting_field]
        storage.save()
        storage.refresh_from_db()

    @classmethod
    def get_storage_by_token(cls, token, user_id):
        storage, created = ApiUserStorage.objects.get_or_create(token=token, user_id=user_id)
        return storage

    @classmethod
    def get_storage_by_request(cls, request):
        token = cls.get_user_token_from_request(request)
        storage = cls.get_storage_by_token(token, request.user.id)
        return storage

    @classmethod
    def get_value_by_token(cls, token, user_id, setting_field):
        storage = cls.get_storage_by_token(token, user_id)
        return cls._get_value_in_storage(storage, setting_field)

    @classmethod
    def get_value_by_request(cls, request, setting_field):
        storage = cls.get_storage_by_request(request)
        return cls._get_value_in_storage(storage, setting_field)

    @classmethod
    def set_value_by_token(cls, token, user_id, setting_field, setting_value):
        storage = cls.get_storage_by_token(token, user_id)
        cls._set_value_in_storage(storage, setting_field, setting_value)

    @classmethod
    def set_value_by_request(cls, request, setting_field, setting_value):
        storage = cls.get_storage_by_request(request)
        cls._set_value_in_storage(storage, setting_field, setting_value)

    @classmethod
    def clear_value_by_token(cls, token, user_id, setting_field):
        storage = cls.get_storage_by_token(token, user_id)
        cls._clear_value_in_storage(storage, setting_field)

    @classmethod
    def clear_value_by_request(cls, request, setting_field):
        storage = cls.get_storage_by_request(request)
        cls._clear_value_in_storage(storage, setting_field)
