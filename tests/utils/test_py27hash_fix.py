import copy
from unittest import TestCase
from unittest.mock import patch

from samtranslator.model.exceptions import InvalidDocumentException
from samtranslator.utils.py27hash_fix import (
    Py27Dict,
    Py27Keys,
    Py27LongInt,
    Py27UniStr,
    _convert_to_py27_type,
    to_py27_compatible_template,
)


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
        self.assertIsInstance(added2, ("".__class__, bytes))
        self.assertNotIsInstance(added2, Py27UniStr)
        self.assertEqual(added2, "barfoo")

    def test_repr(self):
        py27str = Py27UniStr("some string")
        self.assertEqual(repr(py27str), "u'some string'")

    def test_repr_with_unicode_literals(self):
        py27str = Py27UniStr("\xdf\u9054")
        self.assertEqual(repr(py27str), "u'\\xdf\\u9054'")

    def test_serialized_dict_with_unicode_literal_values(self):
        d = {"key": Py27UniStr("\xdf")}
        self.assertEqual(str(d), "{'key': u'\\xdf'}")

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

    def test_py27_hash(self):
        a = Py27UniStr("abcdef")
        self.assertEqual(a._get_py27_hash(), 484452592760221083)
        # do it twice since _get_py27_hash caches the hash
        self.assertEqual(a._get_py27_hash(), 484452592760221083)

    def test_deepcopy(self):
        a = Py27UniStr("abcdef")
        self.assertTrue(a is copy.deepcopy(a))  # deepcopy should give back the same object


class TestPy27LongInt(TestCase):
    def test_long_int(self):
        i = Py27LongInt(9223372036854775810)
        self.assertEqual(repr(i), "9223372036854775810L")

    def test_normal_int(self):
        i = Py27LongInt(100)
        self.assertEqual(repr(i), "100")

    def test_serialized_dict_with_long_int(self):
        i = Py27LongInt(9223372036854775810)
        d = {"num": i}
        self.assertEqual(str(d), "{'num': 9223372036854775810L}")

    def test_serialized_dict_with_normal_int(self):
        i = Py27LongInt(100)
        d = {"num": i}
        self.assertEqual(str(d), "{'num': 100}")

    def test_deepcopy(self):
        a = Py27LongInt(10)
        self.assertTrue(a is copy.deepcopy(a))  # deepcopy should give back the same object


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
            ("/users", "get"),
            ("/users", "post"),
            ("/any/lambdatokennone", "any"),
            ("/any/cognitomultiple", "any"),
            ("/any/lambdatoken", "any"),
            ("/any/default", "any"),
            ("/any/lambdarequest", "any"),
            ("/users", "patch"),
            ("/users", "delete"),
            ("/users", "put"),
            ("/", "get"),
            ("/any/noauth", "any"),
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
        expected_copied_orders = [[0, 1, 2, 3, 4, 5, 6, 7]]

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
        expected_order = [
            "MyCognitoAuth",
            "MyLambdaTokenAuthNoneFunctionInvokeRole",
            "MyCognitoAuthMultipleUserPools",
            "MyLambdaTokenAuth",
            "MyLambdaRequestAuth",
        ]
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
            "api_key",
        ]
        expected_order = [
            "MyLambdaTokenAuthNoneFunctionInvokeRole",
            "api_key",
            "MyLambdaRequestAuth",
            "MyCognitoAuth",
            "MyLambdaTokenAuth",
            "MyCognitoAuthMultipleUserPools",
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
            "api_key",
        ]
        expected_order = [
            "MyLambdaTokenAuthNoneFunctionInvokeRole",
            "api_key",
            "MyLambdaRequestAuth",
            "MyCognitoAuth",
            "MyLambdaTokenAuth",
            "MyCognitoAuthMultipleUserPools",
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
            "api_key",
        ]
        expected_order = [
            "MyLambdaTokenAuthNoneFunctionInvokeRole",
            "api_key",
            "MyLambdaTokenAuth",
            "MyLambdaRequestAuth",
            "MyCognitoAuth",
            "MyCognitoAuthMultipleUserPools",
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
        """"""
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
            key_idx_order = [expected_order.index(i) for i in py27_dict]
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


class TestConvertToPy27Dict(TestCase):
    def test_with_string_input(self):
        original = "aaa"
        converted = _convert_to_py27_type(original)
        self.assertIsInstance(converted, Py27UniStr)
        self.assertEqual(converted, "aaa")

    def test_with_simple_dict(self):
        original = {"a": "b"}
        converted = _convert_to_py27_type(original)
        self.assertIsInstance(converted, Py27Dict)
        self.assertEqual(converted, {"a": "b"})
        self.assertEqual(str(converted), "{u'a': u'b'}")

        for key, val in converted.items():
            if isinstance(key, str):
                self.assertIsInstance(key, Py27UniStr)
            if isinstance(val, str):
                self.assertIsInstance(val, Py27UniStr)

    def test_with_nested_dict(self):
        original = {"a": {"b": "c"}}
        converted = _convert_to_py27_type(original)
        self.assertIsInstance(converted, Py27Dict)
        self.assertIsInstance(converted["a"], Py27Dict)

    def test_with_list(self):
        original = [{"a": "b"}, {"c": "d"}]
        converted = _convert_to_py27_type(original)
        self.assertIsInstance(converted, list)
        for item in converted:
            self.assertIsInstance(item, Py27Dict)

    def test_with_other_type(self):
        original = [("a", "b"), set(["a", "b"]), 123, 123.123]
        converted = _convert_to_py27_type(original)
        self.assertIsInstance(converted[0], tuple)
        self.assertIsInstance(converted[1], set)
        self.assertIsInstance(converted[2], int)
        self.assertIsInstance(converted[3], float)
        self.assertEqual(original, converted)

    def test_with_long_int_input(self):
        original = 9223372036854775810
        converted = _convert_to_py27_type(original)
        self.assertIsInstance(converted, Py27LongInt)
        self.assertEqual(converted, original)

    def test_with_normal_int_input(self):
        original = 99
        converted = _convert_to_py27_type(original)
        self.assertNotIsInstance(converted, Py27LongInt)
        self.assertIsInstance(converted, int)
        self.assertEqual(converted, original)


class TestToPy27CompatibleTemplate(TestCase):
    def test_all(self):
        input_template = {
            "Globals": {"Api": {}},
            "Parameters": {"Param1": {"Default": "Value"}, "Param2": {"Default": {}}},
            "Resources": {
                "Api": {"Type": "AWS::Serverless::Api", "Properties": {}},
                "Function": {"Type": "AWS::Serverless::Function", "Properties": {}},
                "StateMachine": {"Type": "AWS::Serverless::StateMachine", "Properties": {}},
                "Other": {"Type": "AWS::S3::Bucket", "Properties": {}},
            },
        }
        param_values = {"paramA": "valueA", "paramB": ["valueB1", "valueB2", "valueB3"]}
        to_py27_compatible_template(input_template, param_values)
        self.assertEqual(str(input_template["Globals"]), "{'Api': {}}")
        self.assertEqual(
            str(input_template["Parameters"]), "{u'Param2': {'Default': {}}, u'Param1': {'Default': u'Value'}}"
        )
        self.assertEqual(
            str(input_template["Resources"]),
            "{u'Function': {'Type': 'AWS::Serverless::Function', 'Properties': {}}, u'Api': {'Type': '"
            "AWS::Serverless::Api', 'Properties': {}}, u'Other': {'Type': 'AWS::S3::Bucket', 'Properti"
            "es': {}}, u'StateMachine': {'Type': 'AWS::Serverless::StateMachine', 'Properties': {}}}",
        )
        self.assertEqual(str(param_values), "{'paramA': u'valueA', 'paramB': [u'valueB1', u'valueB2', u'valueB3']}")

    def test_empty_dict_fails_validation(self):
        input_template = {}
        with self.assertRaises(InvalidDocumentException):
            to_py27_compatible_template(input_template)

    def test_only_globals_fails_validation(self):
        input_template = {
            "Globals": {
                "Api": {"Name": "123"},
                "Function": {"Handler": "handler.handler"},
            }
        }
        with self.assertRaises(InvalidDocumentException):
            to_py27_compatible_template(input_template)

    def test_only_parameters_fails_validation(self):
        template = {
            "Parameters": {
                "Param1": {"Description": "description", "Default": "default value"},
                "Param2": {"Description": "description"},
            }
        }
        with self.assertRaises(InvalidDocumentException):
            to_py27_compatible_template(template)

    def test_resources_api(self):
        template = {
            "Resources": {
                "Api": {"Type": "AWS::Serverless::Api", "Properties": {"Name": "MyApi"}},
                "HttpApi": {"Type": "AWS::Serverless::HttpApi"},
                "Function": {
                    "Type": "AWS::Serverless::Function",
                    "Properties": {
                        "FunctionName": {"Ref": "MyFunctionName"},
                        "Events": {
                            "ApiEvent": {"Type": "Api", "Properties": {"Path": "/user", "Method": "GET"}},
                            "SecondApiEvent": {"Type": "Api", "Properties": {"Path": "/admin", "Method": "GET"}},
                        },
                    },
                },
                "StateMachine": {
                    "Type": "AWS::Serverless::StateMachine",
                    "Condition": "ShouldAddStateMachine",
                    "Properties": {
                        "Event": {
                            "ApiEvent": {"Type": "Api", "Properties": {"Path": "/state-machine", "Method": "GET"}}
                        }
                    },
                },
            }
        }
        to_py27_compatible_template(template)
        self.assertIsInstance(template["Resources"], Py27Dict)
        self.assertNotIsInstance(template["Resources"]["Api"], Py27Dict)
        self.assertIsInstance(template["Resources"]["Api"]["Properties"], Py27Dict)
        self.assertIsInstance(template["Resources"]["Api"]["Properties"]["Name"], Py27UniStr)

    def test_comprehensive_resources(self):
        template = {
            "Resources": {
                "Api": {"Type": "AWS::Serverless::Api", "Properties": {"Name": "MyApi"}},
                "HttpApi": {"Type": "AWS::Serverless::HttpApi"},
                "Function": {
                    "Type": "AWS::Serverless::Function",
                    "Properties": {
                        "FunctionName": {"Ref": "MyFunctionName"},
                        "Events": {
                            "ApiEvent": {"Type": "Api", "Properties": {"Path": "/user", "Method": "GET"}},
                            "SecondApiEvent": {"Type": "Api", "Properties": {"Path": "/admin", "Method": "GET"}},
                        },
                    },
                },
                "StateMachine": {
                    "Type": "AWS::Serverless::StateMachine",
                    "Condition": "ShouldAddStateMachine",
                    "Properties": {
                        "Name": "statemachine",
                        "Events": {
                            "ApiEvent": {"Type": "Api", "Properties": {"Path": "/state-machine", "Method": "GET"}}
                        },
                    },
                },
            }
        }
        to_py27_compatible_template(template)

        self.assertNotIsInstance(template, Py27Dict)
        self.assertIsInstance(template["Resources"], Py27Dict)

        self.assertNotIsInstance(template["Resources"]["Api"], Py27Dict)
        self.assertIsInstance(template["Resources"]["Api"]["Properties"], Py27Dict)
        self.assertIsInstance(template["Resources"]["Api"]["Properties"]["Name"], Py27UniStr)

        self.assertNotIsInstance(template["Resources"]["HttpApi"], Py27Dict)

        self.assertNotIsInstance(template["Resources"]["Function"], Py27Dict)
        self.assertNotIsInstance(template["Resources"]["Function"]["Properties"], Py27Dict)
        self.assertIsInstance(template["Resources"]["Function"]["Properties"]["FunctionName"], Py27Dict)
        self.assertIsInstance(template["Resources"]["Function"]["Properties"]["Events"], Py27Dict)

        self.assertNotIsInstance(template["Resources"]["StateMachine"], Py27Dict)
        self.assertNotIsInstance(template["Resources"]["StateMachine"]["Properties"], Py27Dict)
        self.assertIsInstance(template["Resources"]["StateMachine"]["Condition"], Py27UniStr)
        self.assertNotIsInstance(template["Resources"]["StateMachine"]["Properties"]["Name"], Py27UniStr)
        self.assertIsInstance(template["Resources"]["StateMachine"]["Properties"]["Events"], Py27Dict)

    @patch("samtranslator.utils.py27hash_fix._convert_to_py27_type")
    def test_no_conversion_happens(self, _convert_to_py27_type_mock):
        template = {"Resources": {"S3Bucket": {"Type": "AWS::S3::Bucket", "Properties": {}}}}
        to_py27_compatible_template(template)

        _convert_to_py27_type_mock.assert_not_called()

    @patch("samtranslator.utils.py27hash_fix._convert_to_py27_type")
    def test_explicit_api(self, _convert_to_py27_type_mock):
        template = {
            "Resources": {
                "Api": {"Type": "AWS::Serverless::Api", "Properties": {"Name": "MyApi"}},
            }
        }
        to_py27_compatible_template(template)

        _convert_to_py27_type_mock.assert_called_once_with({"Name": "MyApi"})

    @patch("samtranslator.utils.py27hash_fix._convert_to_py27_type")
    def test_implicit_api(self, _convert_to_py27_type_mock):
        template = {
            "Resources": {
                "Function": {
                    "Type": "AWS::Serverless::Function",
                    "Properties": {
                        "FunctionName": {"Ref": "MyFunctionName"},
                        "Events": {
                            "ApiEvent": {"Type": "Api", "Properties": {"Path": "/user", "Method": "GET"}},
                            "SecondApiEvent": {"Type": "Api", "Properties": {"Path": "/admin", "Method": "GET"}},
                        },
                    },
                },
            }
        }
        to_py27_compatible_template(template)
        self.assertEqual(_convert_to_py27_type_mock.call_count, 2)

    @patch("samtranslator.utils.py27hash_fix._convert_to_py27_type")
    def test_invalid_function_events(self, _convert_to_py27_type_mock):
        template = {
            "Resources": {
                "Function": {
                    "Type": "AWS::Serverless::Function",
                    "Properties": {
                        "FunctionName": {"Ref": "MyFunctionName"},
                        "Events": {"Fn::If": ["Condition", {}, {}]},
                    },
                },
            }
        }
        to_py27_compatible_template(template)
        _convert_to_py27_type_mock.assert_not_called()

    @patch("samtranslator.utils.py27hash_fix._convert_to_py27_type")
    def test_explit_httpapi_with_default_authorizer(self, _convert_to_py27_type_mock):
        template = {
            "Resources": {
                "Api": {
                    "Type": "AWS::Serverless::HttpApi",
                    "Properties": {
                        "Stage": "myStage",
                        "Auth": {"Authorizers": {"Authorizer1": {}}, "DefaultAuthorizer": "Authorizer1"},
                    },
                },
            }
        }
        to_py27_compatible_template(template)

        _convert_to_py27_type_mock.assert_called_once_with(
            {"Stage": "myStage", "Auth": {"Authorizers": {"Authorizer1": {}}, "DefaultAuthorizer": "Authorizer1"}}
        )

    @patch("samtranslator.utils.py27hash_fix._convert_to_py27_type")
    def test_explit_httpapi_with_global_default_authorizer(self, _convert_to_py27_type_mock):
        template = {
            "Globals": {"HttpApi": {"Auth": {"Authorizers": {"Authorizer1": {}}, "DefaultAuthorizer": "Authorizer1"}}},
            "Resources": {
                "Api": {
                    "Type": "AWS::Serverless::HttpApi",
                    "Properties": {
                        "Stage": "myStage",
                    },
                },
            },
        }
        to_py27_compatible_template(template)

        _convert_to_py27_type_mock.assert_called_once_with(
            {
                "Stage": "myStage",
            }
        )

    @patch("samtranslator.utils.py27hash_fix._convert_to_py27_type")
    def test_explit_httpapi_with_no_default_authorizer(self, _convert_to_py27_type_mock):
        template = {
            "Resources": {
                "Api": {
                    "Type": "AWS::Serverless::HttpApi",
                    "Properties": {
                        "Stage": "myStage",
                    },
                },
            }
        }
        to_py27_compatible_template(template)

        _convert_to_py27_type_mock.assert_not_called()

    @patch("samtranslator.utils.py27hash_fix._convert_to_py27_type")
    def test_explicit_httpapi_with_httpapi_event(self, _convert_to_py27_type_mock):
        template = {
            "Resources": {
                "Api": {
                    "Type": "AWS::Serverless::HttpApi",
                    "Properties": {
                        "Stage": "myStage",
                        "Auth": {"Authorizers": {"Authorizer1": {}}, "DefaultAuthorizer": "Authorizer1"},
                    },
                },
                "Function": {
                    "Type": "AWS::Serverless::Function",
                    "Properties": {
                        "FunctionName": "MyFunctionName",
                        "Events": {
                            "ApiEvent": {"Type": "HttpApi", "Properties": {"Path": "/user", "Method": "GET"}},
                            "ApiEvent2": {"Type": "HttpApi", "Properties": {"Path": "/user", "Method": "POST"}},
                        },
                    },
                },
            }
        }
        to_py27_compatible_template(template)

        _convert_to_py27_type_mock.assert_any_call(
            {"Stage": "myStage", "Auth": {"Authorizers": {"Authorizer1": {}}, "DefaultAuthorizer": "Authorizer1"}}
        )
        _convert_to_py27_type_mock.assert_any_call("MyFunctionName")
        _convert_to_py27_type_mock.assert_any_call(
            {
                "ApiEvent": {"Type": "HttpApi", "Properties": {"Path": "/user", "Method": "GET"}},
                "ApiEvent2": {"Type": "HttpApi", "Properties": {"Path": "/user", "Method": "POST"}},
            }
        )

    @patch("samtranslator.utils.py27hash_fix._convert_to_py27_type")
    def test_implicit_httpapi(self, _convert_to_py27_type_mock):
        template = {
            "Globals": {"HttpApi": {"Auth": {"Authorizers": {"Authorizer1": {}}, "DefaultAuthorizer": "Authorizer1"}}},
            "Resources": {
                "Function1": {
                    "Type": "AWS::S3::Bucket",
                },
                "Function2": {
                    "Type": "AWS::Serverless::Function",
                    "Properties": {
                        "FunctionName": "MyFunctionName2",
                    },
                },
                "Function3": {
                    "Type": "AWS::Serverless::Function",
                    "Properties": {
                        "FunctionName": "MyFunctionName3",
                        "Events": {
                            "ApiEvent3": {"Type": "HttpApi", "Properties": {"Path": "/user", "Method": "GET"}},
                        },
                    },
                },
            },
        }
        to_py27_compatible_template(template)

        _convert_to_py27_type_mock.assert_any_call("MyFunctionName2")
        _convert_to_py27_type_mock.assert_any_call("MyFunctionName3")
        _convert_to_py27_type_mock.assert_any_call(
            {
                "ApiEvent3": {"Type": "HttpApi", "Properties": {"Path": "/user", "Method": "GET"}},
            }
        )

    @patch("samtranslator.utils.py27hash_fix._convert_to_py27_type")
    def test_implicit_httpapi_with_no_globals(self, _convert_to_py27_type_mock):
        template = {
            "Resources": {
                "Function": {
                    "Type": "AWS::Serverless::Function",
                    "Properties": {
                        "FunctionName": "MyFunctionName",
                        "Events": {
                            "ApiEvent": {"Type": "HttpApi", "Properties": {"Path": "/user", "Method": "GET"}},
                        },
                    },
                },
            }
        }

        to_py27_compatible_template(template)
        _convert_to_py27_type_mock.assert_not_called()
