import json

from samtranslator.utils.py27hash_fix import Py27Dict, Py27UniStr

_PY2_MARKER = "\xef\xbb\xbf"


def encode_py2string(data):
    if isinstance(data, Py27UniStr):
        return _PY2_MARKER + data
    if isinstance(data, Py27Dict):
        result = {encode_py2string(key): encode_py2string(value) for key, value in data.items()}
        result[_PY2_MARKER] = True
        return result

    if isinstance(data, list):
        return [encode_py2string(item) for item in data]
    if isinstance(data, dict):
        return {encode_py2string(key): encode_py2string(value) for key, value in data.items()}
    return data


def decode_py2string(data):
    if isinstance(data, str) and data.startswith(_PY2_MARKER):
        return Py27UniStr(data[3:])
    if isinstance(data, list):
        return [decode_py2string(item) for item in data]
    if isinstance(data, dict):
        if _PY2_MARKER in data:
            del data[_PY2_MARKER]
            return Py27Dict({decode_py2string(key): decode_py2string(value) for key, value in data.items()})
        return {decode_py2string(key): decode_py2string(value) for key, value in data.items()}
    return data


def fast_copy(data):
    encoded_string = json.dumps(encode_py2string(data))
    return decode_py2string(json.loads(encoded_string))
