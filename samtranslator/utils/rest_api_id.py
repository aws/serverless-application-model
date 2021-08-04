def get_rest_api_id_string(rest_api_id):
    """
    rest_api_id can be either a string or a dictionary where the actual api id is the value at key "Ref".
    If rest_api_id is a dictionary, returns value at key "Ref". Otherwise, return rest_api_id.

    :param rest_api_id: a string or dictionary that contain the rest_api_id
    :return: string value of rest_api_id
    """
    return rest_api_id.get("Ref") if isinstance(rest_api_id, dict) else rest_api_id
