import copy
import json

from samtranslator.utils.py27hash_fix import Py27Dict, Py27Keys, Py27UniStr

# Using UTF8 BOM as marker but
# this can be anything else
_PY2_MARKER = "\xef\xbb\xbf" 

# Dummy marker for Py27Keys.DUMMY
_KEYORDER_DUMMY_MARKER = _PY2_MARKER + "DUMMY"


def encode_py27(data):
    """Encode py27 objects into JSON serialization objects
    Strings will have PY2 Marker prefixed: u"abc" -> "{_PY2_MARKER}abc"
    Py27Dicts will have keylist saved in the value of dict[_PY2_MARKER]
    """
    if isinstance(data, Py27UniStr):
        return _PY2_MARKER + data
    if isinstance(data, Py27Dict):
        # Encode all keys and values as well
        result = {encode_py27(key): encode_py27(value) for key, value in data.items()}

        # Serialize Py27Keys
        keylist = data.keylist
        result[_PY2_MARKER] = {
            "keylist": {
                "debug": keylist.debug,
                "size": keylist.size,
                "fill": keylist.fill,
                "mask": keylist.mask,
                "keyorder": encode_keyorder(keylist.keyorder),
            }
        }
        return result

    if isinstance(data, list):
        return [encode_py27(item) for item in data]
    if isinstance(data, dict):
        return {encode_py27(key): encode_py27(value) for key, value in data.items()}
    return data


def encode_keyorder(keyorder):
    """Encode keyorder
    Turn dummy keys into dummy markers for serialization 
    """
    if keyorder is None:
        return None
    if keyorder == {}:
        return {}

    encoded_keyorder = dict()
    for i in keyorder:
        if keyorder[i] == Py27Keys.DUMMY:
            encoded_keyorder[i] = _KEYORDER_DUMMY_MARKER
        else:
            encoded_keyorder[i] = keyorder[i]
    return encoded_keyorder


def decode_keyorder(keyorder, keys):
    """Decode keyorder
    Turn dummy markers into Py27Keys.DUMMY for exact reference
    Update keys in keyorder to point to the exact reference in the new Py27Dict
    """
    if keyorder is None:
        return None
    if keyorder == {}:
        return {}

    decoded_keyorder = dict()
    for i in keyorder:
        if keyorder[i] == _KEYORDER_DUMMY_MARKER:
            decoded_keyorder[int(i)] = Py27Keys.DUMMY
        else:
            # Use the exact reference in the dict keys instead of serialized ones.
            # This will also fix u"abc" and "abc" keys
            decoded_keyorder[int(i)] = keys[keys.index(keyorder[i])]
    return decoded_keyorder


def decode_py27(data):
    if isinstance(data, str) and data.startswith(_PY2_MARKER):
        return Py27UniStr(data[3:])
    if isinstance(data, list):
        return [decode_py27(item) for item in data]
    if isinstance(data, dict):
        if _PY2_MARKER in data:
            py27Dict = Py27Dict(
                {decode_py27(key): decode_py27(value) for key, value in data.items() if key != _PY2_MARKER}
            )
            state = data[_PY2_MARKER]
            keylist_state = state["keylist"]
            del data[_PY2_MARKER]

            keylist = Py27Keys()
            keylist.debug = keylist_state["debug"]
            keylist.size = keylist_state["size"]
            keylist.fill = keylist_state["fill"]
            keylist.mask = keylist_state["mask"]
            keylist.keyorder = decode_keyorder(keylist_state["keyorder"], py27Dict.keys())
            keylist.__setstate__(keylist.__dict__)

            py27Dict.keylist = keylist

            return py27Dict
        return {decode_py27(key): decode_py27(value) for key, value in data.items()}
    return data


def fast_copy(data):
    encoded_string = json.dumps(encode_py27(data))
    data_copy = decode_py27(json.loads(encoded_string))
    return data_copy
