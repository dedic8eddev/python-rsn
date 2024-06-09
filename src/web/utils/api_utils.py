def boolean(value):
    """
    Convert value to boolean representation to use it as flag
    """

    # non string value
    if value == 0 or value is False or value is None:
        return False

    if value == 1 or value is True:
        return True

    if isinstance(value, str):
        if value.lower() in ('0', 'no', 'false'):
            return False

        if value.lower() in ('1', 'yes', 'true'):
            return True

    raise KeyError(f"Can not convert '{value}' to boolean")
