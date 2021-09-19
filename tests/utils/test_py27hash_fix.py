import copy

from unittest import TestCase
from samtranslator.utils.py27hash_fix import Py27Dict, Py27Keys, Py27UniStr
from six import python_2_unicode_compatible, string_types


class TestPy27UniStr(TestCase):
    def test_equality(self):
        original_str = "Hello, World!"
        py27_str = Py27UniStr(original_str)
        self.assertEqual(original_str, py27_str)

    def test_add_both_py27unistr(self):
        part1 = Py27UniStr("foo")
        part2 = Py27UniStr("bar")
        added = part1 + part2
        self.assertIsInstance(added, Py27UniStr)
        self.assertEqual(added, "foobar")

    def test_add_py27unistr_and_normal_str(self):
        part1 = Py27UniStr("foo")
        part2 = "bar"
        added1 = part1 + part2
        self.assertIsInstance(added1, Py27UniStr)
        self.assertEqual(added1, "foobar")

        added2 = part2 + part1
        self.assertIsInstance(added2, string_types)
        self.assertNotIsInstance(added2, Py27UniStr)
        self.assertEqual(added2, "barfoo")

    def test_repr(self):
        py27str = Py27UniStr("some string")
        self.assertEqual(repr(py27str), "u'some string'")

    def test_upper(self):
        py27str = Py27UniStr("upper")
        upper = py27str.upper()
        self.assertIsInstance(upper, Py27UniStr)
        self.assertEqual(upper, "UPPER")

    def test_lower(self):
        py27str = Py27UniStr("LOWER")
        lower = py27str.lower()
        self.assertIsInstance(lower, Py27UniStr)
        self.assertEqual(lower, "lower")

    def test_replace_wihtout_count(self):
        py27str = Py27UniStr("aaa_bbb_aaa")
        replaced = py27str.replace("b", "a")
        self.assertIsInstance(replaced, Py27UniStr)
        self.assertEqual(replaced, "aaa_aaa_aaa")

    def test_replace_with_count(self):
        py27str = Py27UniStr("a_bb_a")
        replaced = py27str.replace("b", "c", 1)
        self.assertIsInstance(replaced, Py27UniStr)
        self.assertEqual(replaced, "a_cb_a")

    def test_split_without_maxsplit(self):
        before = Py27UniStr("a,b,c")
        after = before.split(",")
        self.assertIsInstance(after, list)
        self.assertEqual(after, ["a", "b", "c"])
        for c in after:
            self.assertIsInstance(c, Py27UniStr)

    def test_split_with_maxsplit(self):
        before = Py27UniStr("a,b,c")
        after = before.split(",", 1)
        self.assertIsInstance(after, list)
        self.assertEqual(after, ["a", "b,c"])
        for c in after:
            self.assertIsInstance(c, Py27UniStr)


class TestPy27Keys(TestCase):
    def test_merge(self):
        input_keys_1 = ["a", "b", "c", "d"]
        input_keys_2 = ["d", "e", "f", "g"]
        py27_keys = Py27Keys()
        for key in input_keys_1:
            py27_keys.add(key)
        self.assertEqual(py27_keys.keys(), ["a", "c", "b", "d"])
        py27_keys.merge(input_keys_2)
        self.assertEqual(py27_keys.keys(), ["a", "c", "b", "e", "d", "g", "f"])

    def test_copy(self):
        input_keys = ["a", "b", "c", "d"]
        py27_keys = Py27Keys()
        for key in input_keys:
            py27_keys.add(key)

        copied = py27_keys.copy()
        self.assertEqual(copied.keys(), ["a", "c", "b", "d"])

    def test_pop(self):
        input_keys = ["a", "b", "c", "d"]
        py27_keys = Py27Keys()
        for key in input_keys:
            py27_keys.add(key)

        self.assertEqual(py27_keys.pop(), "a")


class TestPy27Dict(TestCase):
    def test_py27_iteration_order_01(self):
        input_order = [
            ('/users', 'get'),
            ('/users', 'post'),
            ('/any/lambdatokennone', 'any'),
            ('/any/cognitomultiple', 'any'),
            ('/any/lambdatoken', 'any'),
            ('/any/default', 'any'),
            ('/any/lambdarequest', 'any'),
            ('/users', 'patch'),
            ('/users', 'delete'),
            ('/users', 'put'),
            ('/', 'get'),
            ('/any/noauth', 'any'),
        ]
        expected_orders = [
            "/any/cognitomultiple",
            "/any/lambdarequest",
            "/any/default",
            "/any/lambdatoken",
            "/any/lambdatokennone",
            "/",
            "/any/noauth",
            "/users",
        ]
        expected_copied_orders = [
            [0, 1, 2, 3, 4, 5, 6, 7]
        ]

        py27_dict = Py27Dict()
        for path, _ in input_order:
            py27_dict[path] = "" 

        self._validate_iteration_order(py27_dict, expected_orders, expected_copied_orders)

    def test_py27_iteration_order_02(self):
        input_order = [
            "MyCognitoAuth",
            "MyLambdaTokenAuthNoneFunctionInvokeRole",
            "MyCognitoAuthMultipleUserPools",
            "MyLambdaTokenAuth",
            "MyLambdaRequestAuth",
        ]
        expected_order = ["MyCognitoAuth", "MyLambdaTokenAuthNoneFunctionInvokeRole", "MyCognitoAuthMultipleUserPools", "MyLambdaTokenAuth", "MyLambdaRequestAuth"]
        expected_copied_orders = [
            [0, 1, 2, 3, 4],
        ]

        py27_dict = Py27Dict()
        for key in input_order:
            py27_dict[key] = ""

        self._validate_iteration_order(py27_dict, expected_order, expected_copied_orders)

    def test_py27_iteration_order_03(self):
        input_order = [
            "MyCognitoAuth",
            "MyLambdaTokenAuthNoneFunctionInvokeRole",
            "MyCognitoAuthMultipleUserPools",
            "MyLambdaTokenAuth",
            "MyLambdaRequestAuth",
            "api_key"
        ]
        expected_order = [
            "MyLambdaTokenAuthNoneFunctionInvokeRole",
            "api_key",
            "MyLambdaRequestAuth",
            "MyCognitoAuth",
            "MyLambdaTokenAuth",
            "MyCognitoAuthMultipleUserPools"
        ]
        expected_copied_orders = [
            [0, 5, 2, 3, 4, 1],
            [0, 1, 2, 3, 4, 5],
            [0, 5, 2, 3, 4, 1],
        ]

        py27_dict = Py27Dict()
        for key in input_order:
            py27_dict[key] = ""

        self._validate_iteration_order(py27_dict, expected_order, expected_copied_orders)

    def test_py27_iteration_order_04(self):
        """
        Variant of 03
        """
        input_order = [
            "MyCognitoAuth",
            "MyLambdaTokenAuthNoneFunctionInvokeRole",
            "MyCognitoAuthMultipleUserPools",
            "MyLambdaTokenAuth",
            "MyLambdaRequestAuth",
            "api_key"
        ]
        expected_order = [
            "MyLambdaTokenAuthNoneFunctionInvokeRole",
            "api_key",
            "MyLambdaRequestAuth",
            "MyCognitoAuth",
            "MyLambdaTokenAuth",
            "MyCognitoAuthMultipleUserPools"
        ]
        expected_copied_orders = [
            [0, 5, 2, 3, 4, 1],
            [0, 1, 2, 3, 4, 5],
            [0, 5, 2, 3, 4, 1],
        ]
        
        py27_dict = Py27Dict()
        for key in input_order[:-1]:
            py27_dict[key] = ""
            py27_dict = copy.deepcopy(py27_dict)
        self.assertNotIn("api_key", py27_dict)

        py27_dict["api_key"] = ""

        self._validate_iteration_order(py27_dict, expected_order, expected_copied_orders)

    def test_py27_iteration_order_05(self):
        """
        Variant of 04 - use .update() instead just setting the key
        """
        input_order = [
            "MyCognitoAuth",
            "MyLambdaTokenAuthNoneFunctionInvokeRole",
            "MyCognitoAuthMultipleUserPools",
            "MyLambdaTokenAuth",
            "MyLambdaRequestAuth",
            "api_key"
        ]
        expected_order = [
            "MyLambdaTokenAuthNoneFunctionInvokeRole",
            "api_key",
            "MyLambdaTokenAuth",
            "MyLambdaRequestAuth",
            "MyCognitoAuth",
            "MyCognitoAuthMultipleUserPools"
        ]
        expected_copied_orders = [
            [0, 5, 3, 4, 2, 1],
            [0, 1, 3, 4, 2, 5],
            [0, 5, 3, 4, 2, 1],
        ]
        
        py27_dict = Py27Dict()
        for key in input_order[:-1]:
            py27_dict[key] = ""
            py27_dict = copy.deepcopy(py27_dict)
        self.assertNotIn("api_key", py27_dict)

        py27_dict.update({"api_key": ""})

        self._validate_iteration_order(py27_dict, expected_order, expected_copied_orders)

    def test_py27_iteration_order_06(self):
        """
        A more complex test which simulate multiple dict operations
        """
        py27_dict = Py27Dict()
        py27_dict["info"] = ""
        py27_dict["paths"] = {}
        py27_dict["openapi"] = "3.1.1"
        self.assertEqual(py27_dict.keys(), ["info", "paths", "openapi"])

        py27_dict["securityDefinitions"] = {}
        self.assertEqual(py27_dict.keys(), ["info", "paths", "securityDefinitions", "openapi"])

        py27_dict = copy.deepcopy(py27_dict)
        self.assertEqual(py27_dict.keys(), ["info", "paths", "openapi", "securityDefinitions"])

        py27_dict["components"] = {}
        self.assertEqual(py27_dict.keys(), ["info", "paths", "openapi", "components", "securityDefinitions"])

        del py27_dict["securityDefinitions"]
        self.assertEqual(py27_dict.keys(), ["info", "paths", "openapi", "components"])

        py27_dict["securityDefinitions"] = {}
        self.assertEqual(py27_dict.keys(), ["info", "paths", "openapi", "components", "securityDefinitions"])

        del py27_dict["securityDefinitions"]
        self.assertEqual(py27_dict.keys(), ["info", "paths", "openapi", "components"])

        py27_dict = copy.deepcopy(py27_dict)
        self.assertEqual(py27_dict.keys(), ["info", "paths", "components", "openapi"])

    def test_py27_iteration_order_07(self):
        """

        """
        input_order = ["get", "post", "patch", "delete", "put"]
        expected_order = ["put", "delete", "post", "patch", "get"]
        expected_copied_orders = [
            [0, 2, 3, 4, 1],
            [0, 1, 2, 4, 3],
            [0, 3, 2, 4, 1],
            [0, 1, 2, 4, 3],
        ]
        py27_dict = Py27Dict()
        py27_dict_setdefault = Py27Dict()
        for key in input_order:
            py27_dict[key] = {}
            py27_dict_setdefault.setdefault(key, {})
        
        self.assertEqual(py27_dict, py27_dict_setdefault)
        self.assertEqual(py27_dict.keys(), py27_dict_setdefault.keys())

        self._validate_iteration_order(py27_dict, expected_order, expected_copied_orders)
        self._validate_iteration_order(py27_dict_setdefault, expected_order, expected_copied_orders)
        

    def _validate_iteration_order(self, py27_dict, expected_order, expected_copied_orders=[]):
        """
        Validates iteration order of a Py27Dict with given input_order
        If expected_copied_orders is supplied, validate also the iteration order after each deepcopy
        """
        self.assertEqual(py27_dict.keys(), expected_order)

        for expected_copied_order in expected_copied_orders:
            py27_dict = copy.deepcopy(py27_dict)
            key_idx_order = [expected_order.index(i) for i in py27_dict.keys()]
            self.assertEqual(key_idx_order, expected_copied_order)

    def test_dict_with_any_hashable_keys(self):
        py27_dict = Py27Dict()
        py27_dict["a"] = "b"
        py27_dict[1] = 2
        py27_dict[1.1] = 2.2
        py27_dict[("c", "d")] = ""
        self.assertEqual(py27_dict, {"a": "b", 1: 2, 1.1: 2.2, ("c", "d"): ""})

    def test_dict_create_fail_with_unhashable_key(self):
        with self.assertRaises(TypeError):
            py27_dict = Py27Dict()
            py27_dict[[1, 2]] = ""

    def test_dict_str_output(self):
        py27_dict = Py27Dict()
        py27_dict["a"] = "b"
        self.assertEqual(str(py27_dict), "{'a': 'b'}")
        self.assertEqual(py27_dict.__repr__(), "{'a': 'b'}")

    def test_dict_str_output_nested_dict(self):
        py27_dict = Py27Dict({"a": {"b": "c"}, 1: ""})
        self.assertEqual(str(py27_dict), "{'a': {'b': 'c'}, 1: ''}")
        self.assertEqual(py27_dict.__repr__(), "{'a': {'b': 'c'}, 1: ''}")

    def test_dict_py27unistr_output(self):
        py27_dict = Py27Dict()
        py27_dict[Py27UniStr("a")] = Py27UniStr("b")
        self.assertEqual(str(py27_dict), "{u'a': u'b'}")
        self.assertEqual(py27_dict.__repr__(), "{u'a': u'b'}")

    def test_dict_len(self):
        py27_dict = Py27Dict({"a": "", "b": "", "c": ""})
        self.assertEqual(len(py27_dict), 3)

    def test_update_dict_with_dict(self):
        py27_dict = Py27Dict({"a": ""})
        py27_dict.update({"b": ""})
        self.assertEqual(py27_dict, {"a": "", "b": ""})

        py27_dict.update({})
        self.assertEqual(py27_dict, {"a": "", "b": ""})

    def test_update_dict_with_tuple(self):
        py27_dict = Py27Dict({"a": ""})
        py27_dict.update([("b", "")])
        self.assertEqual(py27_dict, {"a": "", "b": ""})

    def test_update_dict_with_kwargs(self):
        py27_dict = Py27Dict({"a": ""})
        py27_dict.update(c="d", foo="bar")
        self.assertEqual(py27_dict, {"a": "", "c": "d", "foo": "bar"})

    def test_clear_dict(self):
        py27_dict = Py27Dict({"a": ""})
        py27_dict.clear()
        self.assertEqual(py27_dict, {})

    def test_copy_dict(self):
        py27_dict = Py27Dict({"a": ""})
        self.assertEqual(py27_dict.copy(), {"a": ""})

    def test_pop(self):
        py27_dict = Py27Dict({"a": "b"})
        self.assertEqual(py27_dict.pop("a"), "b")
        self.assertEqual(py27_dict.pop("c", "some_default_val"), "some_default_val")

    def test_popitem(self):
        py27_dict = Py27Dict({"a": "b"})
        self.assertEqual(py27_dict.popitem(), ("a", "b"))
        self.assertEqual(py27_dict.popitem(), None)

    def test_values(self):
        py27_dict = Py27Dict({"a": "b", "c": "d"})
        self.assertEqual(py27_dict.values(), ["b", "d"])

    def test_setdefault(self):
        py27_dict = Py27Dict({"a": "b"})
        # Existing key
        self.assertEqual(py27_dict.setdefault("a", "c"), "b")
        # Non-existent key
        self.assertEqual(py27_dict.setdefault("d", "c"), "c")
        self.assertEqual(py27_dict, {"a": "b", "d": "c"})
