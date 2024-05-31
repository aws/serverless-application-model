"""
"""

import copy
import ctypes
import json
import logging
from typing import Any, Dict, Iterator, List, Optional, cast

from samtranslator.parser.parser import Parser
from samtranslator.third_party.py27hash.hash import Hash

LOG = logging.getLogger(__name__)
# Constants based on Python2.7 dictionary
# See: https://github.com/python/cpython/blob/v2.7.18/Objects/dictobject.c
MINSIZE = 8
PERTURB_SHIFT = 5

unicode_string_type = str  # TODO: remove it, python 2 legacy code
long_int_type = int  # TODO: remove it, python 2 legacy code


def to_py27_compatible_template(  # noqa: PLR0912
    template: Dict[str, Any], parameter_values: Optional[Dict[str, Any]] = None
) -> None:
    """
    Convert an input template to a py27hash-compatible template. This function has to be run before any
    manipulation occurs for sake of keeping the same initial state. This function modifies the input template,
    rather than return a copied template. We choose not to return a copy because copying the template might
    change its internal state in Py2.7.
    We only convert necessary parts in the template which could affect the hash generation for Serverless Api
    template is modified
    Also update parameter_values to py27hash-compatible if it is provided.

    Parameters
    ----------
    template: dict
        input template
    """
    # Passing to parser for a simple validation. Validation is normally done within translator.translate(...).
    # However, becuase this conversion is done before translate and also requires the template to be valid, we
    # perform a simple validation here to just make sure the template is minimally safe for conversion.
    Parser.validate_datatypes(template)  # type: ignore[no-untyped-call]

    if not _template_has_api_resource(template) and not _template_has_httpapi_resource_with_default_authorizer(  # type: ignore[no-untyped-call, no-untyped-call]
        template
    ):
        # no need to convert when all of the following conditions are true:
        # 1. template does not contain any API resource
        # 2. template does not contain any HttpApi resource with DefaultAuthorizer (TODO: remove after py3 migration and fix of security issue)
        return

    if "Globals" in template and isinstance(template["Globals"], dict) and "Api" in template["Globals"]:
        # "Api" section under "Globals" could affect swagger generation for AWS::Serverless::Api resources
        template["Globals"]["Api"] = _convert_to_py27_type(template["Globals"]["Api"])  # type: ignore[no-untyped-call]

    if "Parameters" in template and isinstance(template["Parameters"], dict):
        new_parameters_dict = Py27Dict()
        for logical_id, param_dict in template["Parameters"].items():
            if isinstance(param_dict, dict) and "Default" in param_dict:
                param_dict["Default"] = _convert_to_py27_type(param_dict["Default"])  # type: ignore[no-untyped-call]

            # dict keys have to be Py27UniStr for correct serialization
            new_parameters_dict[Py27UniStr(logical_id)] = param_dict
        template["Parameters"] = new_parameters_dict

    if "Resources" in template and isinstance(template["Resources"], dict):
        new_resources_dict = Py27Dict()
        for logical_id, resource_dict in template["Resources"].items():
            if isinstance(resource_dict, dict):
                resource_type = resource_dict.get("Type")
                resource_properties = resource_dict.get("Properties")
                if resource_properties is not None:
                    # We only convert for AWS::Serverless::Api resource
                    if resource_type in [
                        "AWS::Serverless::Api",
                        "AWS::Serverless::HttpApi",
                    ]:
                        resource_dict["Properties"] = _convert_to_py27_type(resource_properties)  # type: ignore[no-untyped-call]
                    elif resource_type in ["AWS::Serverless::Function", "AWS::Serverless::StateMachine"]:
                        # properties below could affect swagger generation
                        if "Condition" in resource_dict:
                            resource_dict["Condition"] = _convert_to_py27_type(resource_dict["Condition"])  # type: ignore[no-untyped-call]
                        if "FunctionName" in resource_properties:
                            resource_properties["FunctionName"] = _convert_to_py27_type(  # type: ignore[no-untyped-call]
                                resource_properties["FunctionName"]
                            )
                        if "Events" in resource_properties:
                            resource_properties["Events"] = _convert_to_py27_type(resource_properties["Events"])  # type: ignore[no-untyped-call]

            new_resources_dict[Py27UniStr(logical_id)] = resource_dict
        template["Resources"] = new_resources_dict

    if parameter_values:
        for key, val in parameter_values.items():
            parameter_values[key] = _convert_to_py27_type(val)  # type: ignore[no-untyped-call]


def undo_mark_unicode_str_in_template(template_dict: Dict[str, Any]) -> Dict[str, Any]:
    return cast(Dict[str, Any], json.loads(json.dumps(template_dict)))


class Py27UniStr(unicode_string_type):
    """
    A string subclass to allow string be recognized as Python2 unicode string
    To preserve the instance type in string operations, we need to override certain methods
    """

    def __add__(self, other):  # type: ignore[no-untyped-def]
        return Py27UniStr(super().__add__(other))

    def __repr__(self) -> str:
        return "u" + super().encode("unicode_escape").decode("ascii").__repr__().replace("\\\\", "\\")

    def upper(self) -> "Py27UniStr":
        return Py27UniStr(super().upper())

    def lower(self) -> "Py27UniStr":
        return Py27UniStr(super().lower())

    def replace(self, __old, __new, __count=None):  # type: ignore[no-untyped-def]
        if __count:
            return Py27UniStr(super().replace(__old, __new, __count))
        return Py27UniStr(super().replace(__old, __new))

    def split(self, sep=None, maxsplit=-1):  # type: ignore[no-untyped-def]
        return [Py27UniStr(s) for s in super().split(sep, maxsplit)]

    def __deepcopy__(self, memo):  # type: ignore[no-untyped-def]
        return self  # strings are immutable

    def _get_py27_hash(self) -> int:
        h: Optional[int] = getattr(self, "_py27_hash", None)
        if h is None:
            self._py27_hash = h = ctypes.c_size_t(Hash.hash(self)).value
        return h


class Py27LongInt(long_int_type):
    """
    An int subclass to allow int be recognized as Python2 long int
    Overriding __repr__ only
    """

    PY2_MAX_INT = 9223372036854775807  # sys.maxint from Python2.7 Lambda runtime

    def __repr__(self) -> str:
        if self > Py27LongInt.PY2_MAX_INT:
            return super().__repr__() + "L"
        return super().__repr__()

    def __deepcopy__(self, memo):  # type: ignore[no-untyped-def]
        return self  # primitive types (ints) are immutable


class Py27Keys:
    """
    A class for tracking keys based on based on Python 2.7 order.
    Based on https://github.com/python/cpython/blob/v2.7.18/Objects/dictobject.c.

    The order of keys in Python 2.7 is path dependent -- the order of inserts and deletes matters
    in determining the iteration order.
    """

    # marker for deleted keys
    # we use DUMMY for a dummy key, force it to be treated as a str to avoid mypy unhappy
    DUMMY: str = cast(str, ["dummy"])
    _LARGE_DICT_SIZE_THRESHOLD = 50000

    def __init__(self) -> None:
        super().__init__()
        self.debug = False
        self.keyorder: Dict[int, str] = {}
        self.size = 0  # current size of the keys, equivalent to ma_used in dictobject.c
        self.fill = 0  # increment count when a key is added, equivalent to ma_fill in dictobject.c
        self.mask = MINSIZE - 1  # Python2 default dict size

    def __deepcopy__(self, memo):  # type: ignore[no-untyped-def]
        # add keys in the py2 order -- we can't do a straigh-up deep copy of keyorder because
        # in py2 copy.deepcopy of a dict may result in reordering of the keys
        ret = Py27Keys()
        for k in self:
            if k is self.DUMMY:
                continue
            ret.add(copy.deepcopy(k, memo))  # type: ignore[no-untyped-call]
        return ret

    def _get_key_idx(self, k):  # type: ignore[no-untyped-def]
        """Gets insert location for k"""

        # Py27UniStr caches the hash to improve performance so use its method instead of always computing the hash
        h = k._get_py27_hash() if isinstance(k, Py27UniStr) else ctypes.c_size_t(Hash.hash(k)).value
        i = h & self.mask

        if i not in self.keyorder or self.keyorder[i] == k:
            # empty slot or keys match
            return i

        freeslot = None
        if i in self.keyorder and self.keyorder[i] is self.DUMMY:
            # dummy slot
            freeslot = i

        walker = i
        perturb = h
        while i in self.keyorder and self.keyorder[i] != k:
            walker = (walker << 2) + walker + perturb + 1
            i = walker & self.mask

            if i not in self.keyorder:
                return i if freeslot is None else freeslot
            if self.keyorder[i] == k:
                return i
            if freeslot is None and self.keyorder[i] is self.DUMMY:
                freeslot = i
            perturb >>= PERTURB_SHIFT
        return i

    def _resize(self, request):  # type: ignore[no-untyped-def]
        """
        Resizes allocated size based
        """
        newsize = MINSIZE
        while newsize <= request:
            newsize <<= 1

        self.mask = newsize - 1

        # Reset key list to simulate the dict resize and copy operation
        oldkeyorder = copy.copy(self.keyorder)
        self.keyorder = {}
        self.fill = self.size = 0
        # reinsert all the keys using original order
        for idx in sorted(oldkeyorder.keys()):
            if oldkeyorder[idx] is not self.DUMMY:
                self.add(oldkeyorder[idx])  # type: ignore[no-untyped-call]

    def remove(self, key):  # type: ignore[no-untyped-def]
        """Removes key"""
        i = self._get_key_idx(key)  # type: ignore[no-untyped-call]
        if i in self.keyorder and self.keyorder[i] is not self.DUMMY:
            self.keyorder[i] = self.DUMMY
            self.size -= 1

    def add(self, key):  # type: ignore[no-untyped-def]
        """Adds key"""
        start_size = self.size
        i = self._get_key_idx(key)  # type: ignore[no-untyped-call]
        if i not in self.keyorder:
            # We are not replacing an existing key or a DUMMY key, increment fill
            self.size += 1
            self.fill += 1
            self.keyorder[i] = key
        else:
            if self.keyorder[i] is self.DUMMY:
                self.size += 1
            if self.keyorder[i] != key:
                self.keyorder[i] = key

        # Resize if 2/3 capacity
        if self.size > start_size and self.fill * 3 >= ((self.mask + 1) * 2):
            # Python2 dict increases size by a factor of 4 for small dict, and 2 for large dict
            self._resize(self.size * (2 if self.size > self._LARGE_DICT_SIZE_THRESHOLD else 4))  # type: ignore[no-untyped-call]

    def keys(self) -> List[str]:
        """Return keys in Python2 order"""
        return [self.keyorder[key] for key in sorted(self.keyorder.keys()) if self.keyorder[key] is not self.DUMMY]

    def __setstate__(self, state):  # type: ignore[no-untyped-def]
        """
        Overrides default pickling object to force re-adding all keys and match Python 2.7 deserialization logic.

        :param state: input state
        """
        self.__dict__ = state
        keys = self.keys()

        # Clear keys and re-add to match deserialization logic
        self.__init__()  # type: ignore[misc]

        for k in keys:
            if k == self.DUMMY:
                continue
            self.add(k)  # type: ignore[no-untyped-call]

    def __iter__(self) -> Iterator[str]:
        """
        Default iterator
        """
        return iter(self.keys())

    def __eq__(self, other):  # type: ignore[no-untyped-def]
        if isinstance(other, Py27Keys):
            return self.keys() == other.keys()
        if isinstance(other, list):
            return self.keys() == other
        return False

    def __len__(self) -> int:
        return len(self.keys())

    def merge(self, other):  # type: ignore[no-untyped-def]
        """
        Merge keys from an exisitng iterable into this key list.
        Equivalent to PyDict_Merge

        :param other: iterable
        """
        if len(other) == 0 or self is other:
            # nothing to do
            return

        # PyDict_Merge initial merge size is double the size of current + incoming dict
        if ((self.fill + len(other)) * 3) >= ((self.mask + 1) * 2):
            self._resize((self.size + len(other)) * 2)  # type: ignore[no-untyped-call]

        # Copy actual keys
        for k in other:
            self.add(k)  # type: ignore[no-untyped-call]

    def copy(self) -> "Py27Keys":
        """
        Makes a copy of self
        """
        # Copy creates a new object and merges keys in
        new = Py27Keys()
        new.merge(self.keys())  # type: ignore[no-untyped-call, no-untyped-call]
        return new

    def pop(self):  # type: ignore[no-untyped-def]
        """
        Pops the top element from the sorted keys if it exists. Returns None otherwise.
        """
        if self.keyorder:
            value = self.keys()[0]
            self.remove(value)  # type: ignore[no-untyped-call]
            return value
        return None


class Py27Dict(dict):  # type: ignore[type-arg]
    """
    Compatibility class to support Python2.7 style iteration in Python3.x
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Overrides dict logic to always call set item. This allows Python2.7 style iteration
        """
        super().__init__()

        # Initialize iteration key list
        self.keylist = Py27Keys()

        # Initialize base arguments
        self.update(*args, **kwargs)  # type: ignore[no-untyped-call]

    def __deepcopy__(self, memo):  # type: ignore[no-untyped-def]
        cls = self.__class__
        result = cls.__new__(cls)
        for k, v in self.__dict__.items():
            setattr(result, k, copy.deepcopy(v, memo))

        for key, value in super().items():
            super(Py27Dict, result).__setitem__(copy.deepcopy(key, memo), copy.deepcopy(value, memo))

        return result

    def __reduce__(self):  # type: ignore[no-untyped-def]
        """
        Method necessary to fully pickle Python 3 subclassed dict objects with attribute fields.
        """
        return super().__reduce__()

    def __setitem__(self, key, value):  # type: ignore[no-untyped-def]
        """
        Override of __setitem__ to track keys and simulate Python2.7 dict

        Parameters
        ----------
        key: hashable
        value: Any
        """
        super().__setitem__(key, value)
        self.keylist.add(key)  # type: ignore[no-untyped-call]

    def __delitem__(self, key):  # type: ignore[no-untyped-def]
        """
        Override of __delitem__ to track kyes and simulate Python2.7 dict.

        Parameters
        ----------
        key: hashable
        """
        super().__delitem__(key)
        self.keylist.remove(key)  # type: ignore[no-untyped-call]

    def update(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        """
        Overrides dict logic to always call set item. This allows Python2.7 style iteration.

        Parameters
        ----------
        args: args
        kwargs: keyword args
        """
        for arg in args:
            # Cast to dict if applicable. Otherwise, assume it's an iterable of (key, value) pairs
            _arg = arg
            if isinstance(arg, dict):
                # Merge incoming keys into keylist
                self.keylist.merge(arg.keys())  # type: ignore[no-untyped-call]
                _arg = arg.items()

            for k, v in _arg:
                self[k] = v

        for k, v in dict(**kwargs).items():
            self[k] = v

    def clear(self) -> None:
        """
        Clears the dict along with its backing Python2.7 keylist.
        """
        super().clear()
        self.keylist = Py27Keys()

    def copy(self) -> "Py27Dict":
        """
        Copies the dict along with its backing Python2.7 keylist.

        Returns
        -------
        Py27Dict
            copy of self
        """
        new = Py27Dict()

        # First copy the keylist to the new object
        new.keylist = self.keylist.copy()

        # Copy keys into backing dict
        for k, v in self.items():  # type: ignore[no-untyped-call]
            new[k] = v

        return new

    def pop(self, key, default=None):  # type: ignore[no-untyped-def]
        """
        Pops the value at key from the dict if it exists, return default otherwise

        Parameters
        ----------
        key: hashable
            key to remove
        default: Any
            value to return if key is not found

        Returns
        -------
        Any
            value of key if found or default
        """
        value = super().pop(key, default)
        self.keylist.remove(key)  # type: ignore[no-untyped-call]
        return value

    def popitem(self):  # type: ignore[no-untyped-def]
        """
        Pops an element from the dict and returns the item.

        Returns
        -------
        tuple
            (key, value) pair of an element if found or None if dict is empty
        """
        if self:
            key = self.keylist.pop()  # type: ignore[no-untyped-call]
            value = self[key] if key else None

            del self[key]  # type: ignore[no-untyped-call]
            return key, value

        return None

    def __iter__(self) -> Iterator[str]:
        """
        Default iterator

        Returns
        -------
        iterator
        """
        return self.keylist.__iter__()

    def __str__(self) -> str:
        """
        Override to minic exact Python2.7 str(dict_obj)

        Returns
        -------
        str
        """
        string = "{"

        for i, key in enumerate(self):
            string += ", " if i > 0 else ""
            if isinstance(key, ("".__class__, bytes)):
                string += f"{key.__repr__()}: "
            else:
                string += f"{key}: "

            if isinstance(self[key], ("".__class__, bytes)):
                string += str(self[key].__repr__())
            else:
                string += str(self[key])

        string += "}"
        return string

    def __repr__(self) -> str:
        """
        Create a string version of this Dict

        Returns
        -------
        str
        """
        return self.__str__()

    def keys(self):  # type: ignore[no-untyped-def]
        """
        Returns keys ordered using Python2.7 iteration alogrithm

        Returns
        -------
        list
            list of keys
        """
        return self.keylist.keys()

    def values(self):  # type: ignore[no-untyped-def]
        """
        Returns values ordered using Python2.7 iteration algorithm

        Returns
        -------
        list
            list of values
        """
        return [self[k] for k in self]

    def items(self):  # type: ignore[no-untyped-def]
        """
        Returns items ordered using Python2.7 iteration algorithm

        Returns
        -------
        list
            list of items
        """
        return [(k, self[k]) for k in self]

    def setdefault(self, key, default):  # type: ignore[no-untyped-def]
        """
        Retruns the value of a key if the key exists. Otherwise inserts key with the default value

        Parameters
        ----------
        key: hashable
        default: Any

        Returns
        -------
        Any
        """
        if key not in self:
            self[key] = default
        return self[key]


def _convert_to_py27_type(original):  # type: ignore[no-untyped-def]
    if isinstance(original, ("".__class__, bytes)):
        # these are strings, return the Py27UniStr instance of the string
        return Py27UniStr(original)

    if isinstance(original, int) and original > Py27LongInt.PY2_MAX_INT:
        # only convert long int to Py27LongInt
        return Py27LongInt(original)

    if isinstance(original, list):
        return [_convert_to_py27_type(item) for item in original]  # type: ignore[no-untyped-call]

    if isinstance(original, dict):
        # Recursively convert dict items
        key_list = original.keys()
        new_dict = Py27Dict()
        for key in key_list:
            new_dict[Py27UniStr(key)] = _convert_to_py27_type(original[key])  # type: ignore[no-untyped-call]
        return new_dict

    # Anything else does not require conversion
    return original


def _template_has_api_resource(template):  # type: ignore[no-untyped-def]
    """
    Returns true if the template contains at lease one explicit or implicit AWS::Serverless::Api resource
    """
    for resource_dict in template.get("Resources", {}).values():
        if isinstance(resource_dict, dict) and resource_dict.get("Type") == "AWS::Serverless::Api":
            # i.e. an excplicit API is defined in the template
            return True

        if isinstance(resource_dict, dict) and resource_dict.get("Type") in [
            "AWS::Serverless::Function",
            "AWS::Serverless::StateMachine",
        ]:
            events = resource_dict.get("Properties", {}).get("Events", {})
            if isinstance(events, dict):
                for event_dict in events.values():
                    # An explicit or implicit API is referenced
                    if event_dict and isinstance(event_dict, dict) and event_dict.get("Type") == "Api":
                        return True

    return False


def _template_has_httpapi_resource_with_default_authorizer(template):  # type: ignore[no-untyped-def]
    """
    Returns true if the template contains at least one AWS::Serverless::HttpApi resource with DefaultAuthorizer configured
    """
    # Check whether DefaultAuthorizer is defined in Globals.HttpApi
    has_global_httpapi_default_authorizer = False
    if "Globals" in template and isinstance(template["Globals"], dict):
        globals_dict = template["Globals"]
        if "HttpApi" in globals_dict and isinstance(globals_dict["HttpApi"], dict):
            globals_httpapi_dict = globals_dict["HttpApi"]
            if "Auth" in globals_httpapi_dict and isinstance(globals_httpapi_dict["Auth"], dict):
                has_global_httpapi_default_authorizer = bool(globals_httpapi_dict["Auth"].get("DefaultAuthorizer"))

    # Check if there is explicit HttpApi resource
    for resource_dict in template.get("Resources", {}).values():
        if isinstance(resource_dict, dict) and resource_dict.get("Type") == "AWS::Serverless::HttpApi":
            auth = resource_dict.get("Properties", {}).get("Auth", {})
            if (
                auth and isinstance(auth, dict) and auth.get("DefaultAuthorizer")
            ) or has_global_httpapi_default_authorizer:
                return True

    # Check if there is any httpapi event for implicit api
    if has_global_httpapi_default_authorizer:
        for resource_dict in template.get("Resources", {}).values():
            if isinstance(resource_dict, dict) and resource_dict.get("Type") == "AWS::Serverless::Function":
                events = resource_dict.get("Properties", {}).get("Events", {})
                if isinstance(events, dict):
                    for event_dict in events.values():
                        if event_dict and isinstance(event_dict, dict) and event_dict.get("Type") == "HttpApi":
                            return True

    return False
