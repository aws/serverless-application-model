from parameterized import parameterized

from unittest import TestCase
from mock import patch, Mock

from samtranslator.plugins.globals.globals import GlobalProperties, Globals, InvalidGlobalsSectionException


class GlobalPropertiesTestCases(object):

    dict_with_single_level_should_be_merged = {
        "global": {"a": 1, "b": 2},
        "local": {"a": "foo", "c": 3, "d": 4},
        "expected_output": {"a": "foo", "b": 2, "c": 3, "d": 4},
    }

    dict_keys_are_case_sensitive = {
        "global": {"banana": "is tasty"},
        "local": {"BaNaNa": "is not tasty"},
        "expected_output": {"banana": "is tasty", "BaNaNa": "is not tasty"},
    }

    dict_properties_with_different_types_must_be_overridden_str_and_dict = {
        "global": {"key": "foo"},
        "local": {"key": {"a": "b"}},
        "expected_output": {"key": {"a": "b"}},
    }

    dict_properties_with_different_types_must_be_overridden_boolean_and_int = {
        "global": {"key": True},
        "local": {"key": 1},
        "expected_output": {"key": 1},
    }

    dict_properties_with_different_types_must_be_overridden_dict_and_array = {
        "global": {"key": {"a": "b"}},
        "local": {"key": ["a"]},
        "expected_output": {"key": ["a"]},
    }

    dict_with_empty_local_must_merge = {"global": {"a": "b"}, "local": {}, "expected_output": {"a": "b"}}

    nested_dict_keys_should_be_merged = {
        "global": {"key1": {"key2": {"key3": {"key4": "value"}}}},
        "local": {"key1": {"key2": {"key3": {"key4": "local value"}}}},
        "expected_output": {"key1": {"key2": {"key3": {"key4": "local value"}}}},
    }

    nested_dict_with_different_levels_should_be_merged = {
        "global": {"key1": {"key2": {"key3": "value3"}, "globalOnlyKey": "global value"}},
        "local": {"key1": {"key2": "foo", "localOnlyKey": "local value"}},
        "expected_output": {
            "key1": {
                # Key2 does not recurse any further
                "key2": "foo",
                "globalOnlyKey": "global value",
                "localOnlyKey": "local value",
            }
        },
    }

    nested_dicts_with_non_overridden_keys_should_be_copied = {
        "global": {"key1": {"key2": {"key3": {"key4": "value"}}, "globalOnly": {"globalOnlyKey": "globalOnlyValue"}}},
        "local": {
            "key1": {
                "key2": {"key3": {"localkey4": "other value 4"}, "localkey3": "other value 3"},
                "localkey2": "other value 2",
            }
        },
        "expected_output": {
            "key1": {
                "key2": {"key3": {"key4": "value", "localkey4": "other value 4"}, "localkey3": "other value 3"},
                "localkey2": "other value 2",
                "globalOnly": {"globalOnlyKey": "globalOnlyValue"},
            }
        },
    }

    arrays_with_mutually_exclusive_elements_must_be_concatenated = {
        "global": [1, 2, 3],
        "local": [11, 12, 13],
        "expected_output": [1, 2, 3, 11, 12, 13],
    }

    arrays_with_duplicate_elements_must_be_concatenated = {
        "global": ["a", "b", "c", "z"],
        "local": ["a", "b", "x", "y", "z"],
        "expected_output": ["a", "b", "c", "z", "a", "b", "x", "y", "z"],
    }

    arrays_with_nested_dict_must_be_concatenated = {
        "global": [{"a": 1}, {"b": 2}],
        "local": [{"x": 1}, {"y": 2}],
        "expected_output": [{"a": 1}, {"b": 2}, {"x": 1}, {"y": 2}],
    }

    arrays_with_mixed_element_types_must_be_concatenated = {
        "global": [1, 2, "foo", True, {"x": "y"}, ["nested", "array"]],
        "local": [False, 9, 8, "bar"],
        "expected_output": [1, 2, "foo", True, {"x": "y"}, ["nested", "array"], False, 9, 8, "bar"],
    }

    arrays_with_exactly_same_values_must_be_concatenated = {
        "global": [{"a": 1}, {"b": 2}, "foo", 1, 2, True, False],
        "local": [{"a": 1}, {"b": 2}, "foo", 1, 2, True, False],
        "expected_output": [{"a": 1}, {"b": 2}, "foo", 1, 2, True, False, {"a": 1}, {"b": 2}, "foo", 1, 2, True, False],
    }

    # Arrays are concatenated. Other keys in dictionary are merged
    nested_dict_with_array_values_must_be_merged_and_concatenated = {
        "global": {"key": "global value", "nested": {"array_key": [1, 2, 3]}, "globalOnlyKey": "global value"},
        "local": {"key": "local value", "nested": {"array_key": [8, 9, 10]}, "localOnlyKey": "local value"},
        "expected_output": {
            "key": "local value",
            "nested": {"array_key": [1, 2, 3, 8, 9, 10]},
            "globalOnlyKey": "global value",
            "localOnlyKey": "local value",
        },
    }

    intrinsic_function_must_be_overridden = {
        "global": {"Ref": "foo"},
        "local": {"Fn::Spooky": "bar"},
        "expected_output": {"Fn::Spooky": "bar"},
    }

    intrinsic_function_in_global_must_override_dict_value_in_local = {
        "global": {"Ref": "foo"},
        "local": {"a": "b"},
        "expected_output": {"a": "b"},
    }

    intrinsic_function_in_local_must_override_dict_value_in_global = {
        "global": {"a": "b"},
        "local": {"Fn::Something": "value"},
        "expected_output": {"Fn::Something": "value"},
    }

    intrinsic_function_in_nested_dict_must_be_overridden = {
        "global": {"key1": {"key2": {"key3": {"Ref": "foo"}, "globalOnlyKey": "global value"}}},
        "local": {"key1": {"key2": {"key3": {"Fn::Something": "New value"}}}},
        "expected_output": {
            "key1": {"key2": {"key3": {"Fn::Something": "New value"}, "globalOnlyKey": "global value"}}
        },
    }

    invalid_intrinsic_function_dict_must_be_merged = {
        "global": {
            # This is not an intrinsic function because the dict contains two keys
            "Ref": "foo",
            "key": "global value",
        },
        "local": {"Fn::Something": "bar", "other": "local value"},
        "expected_output": {"Ref": "foo", "key": "global value", "Fn::Something": "bar", "other": "local value"},
    }

    intrinsic_function_in_local_must_override_invalid_intrinsic_in_global = {
        "global": {
            # This is not an intrinsic function because the dict contains two keys
            "Ref": "foo",
            "key": "global value",
        },
        "local": {
            # This is an intrinsic function which essentially resolves to a primitive type.
            # So local is primitive type whereas global is a dictionary. Prefer local
            "Fn::Something": "bar"
        },
        "expected_output": {"Fn::Something": "bar"},
    }

    primitive_type_inputs_must_be_handled = {"global": "input string", "local": 123, "expected_output": 123}

    mixed_type_inputs_must_be_handled = {"global": {"a": "b"}, "local": [1, 2, 3], "expected_output": [1, 2, 3]}


class TestGlobalPropertiesMerge(TestCase):

    # Get all attributes of the test case object which is not a built-in method like __str__
    @parameterized.expand([d for d in dir(GlobalPropertiesTestCases) if not d.startswith("__")])
    def test_global_properties_merge(self, testcase):

        configuration = getattr(GlobalPropertiesTestCases, testcase)
        if not configuration:
            raise Exception("Invalid configuration for test case " + testcase)

        global_properties = GlobalProperties(configuration["global"])
        actual = global_properties.merge(configuration["local"])

        self.assertEqual(actual, configuration["expected_output"])


class TestGlobalsPropertiesEdgeCases(TestCase):
    @patch.object(GlobalProperties, "_token_of")
    def test_merge_with_objects_of_unsupported_token_type(self, token_of_mock):

        token_of_mock.return_value = "some random type"
        properties = GlobalProperties("global value")

        with self.assertRaises(TypeError):
            # Raise type error because token type is invalid
            properties.merge("local value")


class TestGlobalsObject(TestCase):
    def setUp(self):
        self._originals = {
            "resource_prefix": Globals._RESOURCE_PREFIX,
            "supported_properties": Globals.supported_properties,
        }
        Globals._RESOURCE_PREFIX = "prefix_"
        Globals.supported_properties = {
            "prefix_type1": ["prop1", "prop2"],
            "prefix_type2": ["otherprop1", "otherprop2"],
        }

        self.template = {
            "Globals": {
                "type1": {"prop1": "value1", "prop2": "value2"},
                "type2": {"otherprop1": "value1", "otherprop2": "value2"},
            }
        }

    def tearDown(self):
        Globals._RESOURCE_PREFIX = self._originals["resource_prefix"]
        Globals.supported_properties = self._originals["supported_properties"]

    def test_parse_should_parse_all_known_resource_types(self):
        globals = Globals(self.template)

        parsed_globals = globals._parse(self.template["Globals"])

        self.assertTrue("prefix_type1" in parsed_globals)
        self.assertEqual(self.template["Globals"]["type1"], parsed_globals["prefix_type1"].global_properties)
        self.assertTrue("prefix_type2" in parsed_globals)
        self.assertEqual(self.template["Globals"]["type2"], parsed_globals["prefix_type2"].global_properties)

    def test_parse_should_error_if_globals_is_not_dict(self):

        template = {"Globals": "hello"}

        with self.assertRaises(InvalidGlobalsSectionException):
            Globals(template)

    def test_parse_should_error_if_globals_contains_unknown_types(self):

        template = {"Globals": {"random_type": {"key": "value"}, "type1": {"key": "value"}}}

        with self.assertRaises(InvalidGlobalsSectionException):
            Globals(template)

    def test_parse_should_error_if_globals_contains_unknown_properties_of_known_type(self):

        template = {"Globals": {"type1": {"unknown_property": "value"}}}

        with self.assertRaises(InvalidGlobalsSectionException):
            Globals(template)

    def test_parse_should_error_if_value_is_not_dictionary(self):

        template = {"Globals": {"type1": "string value"}}

        with self.assertRaises(InvalidGlobalsSectionException):
            Globals(template)

    def test_parse_should_not_error_if_value_is_empty(self):

        template = {"Globals": {"type1": {}}}  # empty value

        globals = Globals(template)
        parsed = globals._parse(template["Globals"])

        self.assertTrue("prefix_type1" in parsed)
        self.assertEqual({}, parsed["prefix_type1"].global_properties)

    def test_init_without_globals_section_in_template(self):

        template = {"a": "b"}

        global_obj = Globals(template)
        self.assertEqual({}, global_obj.template_globals)

    def test_del_section_with_globals_section_in_template(self):
        template = self.template
        expected = {}

        Globals.del_section(template)
        self.assertEqual(expected, template)

    def test_del_section_with_no_globals_section_in_template(self):
        template = {"a": "b"}

        expected = {"a": "b"}

        Globals.del_section(template)
        self.assertEqual(expected, template)

    @patch.object(Globals, "_parse")
    def test_merge_must_actually_do_merge(self, parse_mock):

        type1_mock = Mock()
        type2_mock = Mock()
        parse_mock.return_value = {"type1": type1_mock, "type2": type2_mock}

        local_properties = {"a": "b"}
        expected = "some merged value"
        type1_mock.merge.return_value = expected

        # Try to merge for type1
        globals = Globals(self.template)
        result = globals.merge("type1", local_properties)

        self.assertEqual(expected, result)
        type1_mock.merge.assert_called_with(local_properties)
        type2_mock.merge.assert_not_called()

    @patch.object(Globals, "_parse")
    def test_merge_must_skip_unsupported_types(self, parse_mock):

        type1_mock = Mock()
        parse_mock.return_value = {"type1": type1_mock}

        local_properties = {"a": "b"}
        expected = {"a": "b"}

        globals = Globals(self.template)

        # Since type is not available in the globals, nothing should happen
        result = globals.merge("some random type", local_properties)

        self.assertEqual(expected, result)
        type1_mock.merge.assert_not_called()

    @patch.object(Globals, "_parse")
    def test_merge_must_skip_with_no_types(self, parse_mock):

        parse_mock.return_value = {}

        local_properties = {"a": "b"}
        expected = {"a": "b"}

        globals = Globals(self.template)

        # Since type is not available in the globals, nothing should happen
        result = globals.merge("some random type", local_properties)

        self.assertEqual(expected, result)

    def test_merge_end_to_end_on_known_type1(self):

        type = "prefix_type1"
        properties = {"prop1": "overridden value", "a": "b", "key": [1, 2, 3]}

        expected = {"prop1": "overridden value", "prop2": "value2", "a": "b", "key": [1, 2, 3]}  # inherited from global

        globals = Globals(self.template)
        result = globals.merge(type, properties)

        self.assertEqual(expected, result)

    def test_merge_end_to_end_on_known_type2(self):

        type = "prefix_type2"
        properties = {"a": "b", "key": [1, 2, 3]}

        expected = {
            "otherprop1": "value1",  # inherited from global
            "otherprop2": "value2",  # inherited from global
            "a": "b",
            "key": [1, 2, 3],
        }

        globals = Globals(self.template)
        result = globals.merge(type, properties)

        self.assertEqual(expected, result)

    def test_merge_end_to_end_unknown_type(self):

        type = "some unknown type"
        properties = {"a": "b", "key": [1, 2, 3]}

        # Output equals input
        expected = {"a": "b", "key": [1, 2, 3]}

        globals = Globals(self.template)
        result = globals.merge(type, properties)

        self.assertEqual(expected, result)


class TestGlobalsOpenApi(TestCase):
    template = {"Globals": {"Api": {"OpenApiVersion": "3.0"}}}

    table_driven = [
        {
            "name": "happy case",
            "input": {
                "Resources": {
                    "MyApi": {
                        "Type": "AWS::Serverless::Api",
                        "Properties": {
                            "__MANAGE_SWAGGER": True,
                            "OpenApiVersion": "3.0",
                            "DefinitionBody": {"swagger": "2.0"},
                        },
                    }
                }
            },
            "expected": {
                "Resources": {
                    "MyApi": {
                        "Type": "AWS::Serverless::Api",
                        "Properties": {
                            "__MANAGE_SWAGGER": True,
                            "OpenApiVersion": "3.0",
                            "DefinitionBody": {"openapi": "3.0"},
                        },
                    }
                }
            },
        },
        {
            "name": "no openapi",
            "input": {
                "Resources": {
                    "MyApi": {"Type": "AWS::Serverless::Api", "Properties": {"DefinitionBody": {"swagger": "2.0"}}}
                }
            },
            "expected": {
                "Resources": {
                    "MyApi": {"Type": "AWS::Serverless::Api", "Properties": {"DefinitionBody": {"swagger": "2.0"}}}
                }
            },
        },
        {
            "name": "Openapi set to 2.0",
            "input": {
                "Resources": {
                    "MyApi": {
                        "Type": "AWS::Serverless::Api",
                        "Properties": {
                            "__MANAGE_SWAGGER": True,
                            "OpenApiVersion": "2.0",
                            "DefinitionBody": {"swagger": "2.0"},
                        },
                    }
                }
            },
            "expected": {
                "Resources": {
                    "MyApi": {
                        "Type": "AWS::Serverless::Api",
                        "Properties": {
                            "__MANAGE_SWAGGER": True,
                            "OpenApiVersion": "2.0",
                            "DefinitionBody": {"swagger": "2.0"},
                        },
                    }
                }
            },
        },
        {
            "name": "No definition body",
            "input": {
                "Resources": {
                    "MyApi": {
                        "Type": "AWS::Serverless::Api",
                        "Properties": {"__MANAGE_SWAGGER": True, "OpenApiVersion": "3.0"},
                    }
                }
            },
            "expected": {
                "Resources": {
                    "MyApi": {
                        "Type": "AWS::Serverless::Api",
                        "Properties": {"__MANAGE_SWAGGER": True, "OpenApiVersion": "3.0"},
                    }
                }
            },
        },
        {
            "name": "ignore customer defined swagger",
            "input": {
                "Resources": {
                    "MyApi": {
                        "Type": "AWS::Serverless::Api",
                        "Properties": {"OpenApiVersion": "3.0", "DefinitionBody": {"swagger": "2.0"}},
                    }
                }
            },
            "expected": {
                "Resources": {
                    "MyApi": {
                        "Type": "AWS::Serverless::Api",
                        "Properties": {"OpenApiVersion": "3.0", "DefinitionBody": {"swagger": "2.0"}},
                    }
                }
            },
        },
        {
            "name": "No Resources",
            "input": {"some": "other", "swagger": "donottouch"},
            "expected": {"some": "other", "swagger": "donottouch"},
        },
    ]

    def test_openapi_postprocess(self):
        for test in self.table_driven:
            global_obj = Globals(self.template)
            global_obj.fix_openapi_definitions(test["input"])
            self.assertEqual(test["input"], test["expected"], test["name"])
