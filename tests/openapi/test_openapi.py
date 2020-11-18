import copy

from unittest import TestCase
from parameterized import parameterized, param

from samtranslator.open_api.open_api import OpenApiEditor
from samtranslator.model.exceptions import InvalidDocumentException

_X_INTEGRATION = "x-amazon-apigateway-integration"
_X_ANY_METHOD = "x-amazon-apigateway-any-method"


# TODO: add a case for swagger and make sure it fails
class TestOpenApiEditor_init(TestCase):

    # OAS3 doesn't support swagger
    def test_must_raise_on_valid_swagger(self):

        valid_swagger = {
            "swagger": "2.0",  # "openapi": "2.1.0"
            "paths": {"/foo": {}, "/bar": {}},
        }  # missing openapi key word
        with self.assertRaises(ValueError):
            OpenApiEditor(valid_swagger)

    def test_must_raise_on_invalid_openapi(self):

        invalid_openapi = {"paths": {}}  # Missing "openapi" keyword
        with self.assertRaises(ValueError):
            OpenApiEditor(invalid_openapi)

    def test_must_succeed_on_valid_openapi(self):
        valid_openapi = {"openapi": "3.0.1", "paths": {"/foo": {}, "/bar": {}}}

        editor = OpenApiEditor(valid_openapi)
        self.assertIsNotNone(editor)

        self.assertEqual(editor.paths, {"/foo": {}, "/bar": {}})

    def test_must_fail_on_invalid_openapi_version(self):
        invalid_openapi = {"openapi": "2.3.0", "paths": {"/foo": {}, "/bar": {}}}

        with self.assertRaises(ValueError):
            OpenApiEditor(invalid_openapi)

    def test_must_fail_on_invalid_openapi_version_2(self):
        invalid_openapi = {"openapi": "3.1.1.1", "paths": {"/foo": {}, "/bar": {}}}

        with self.assertRaises(ValueError):
            OpenApiEditor(invalid_openapi)

    def test_must_succeed_on_valid_openapi3(self):
        valid_openapi = {"openapi": "3.0.1", "paths": {"/foo": {}, "/bar": {}}}

        editor = OpenApiEditor(valid_openapi)
        self.assertIsNotNone(editor)

        self.assertEqual(editor.paths, {"/foo": {}, "/bar": {}})


class TestOpenApiEditor_has_path(TestCase):
    def setUp(self):
        self.openapi = {
            "openapi": "3.0.1",
            "paths": {
                "/foo": {"get": {}, "somemethod": {}},
                "/bar": {"post": {}, _X_ANY_METHOD: {}},
                "badpath": "string value",
            },
        }

        self.editor = OpenApiEditor(self.openapi)

    def test_must_find_path_and_method(self):
        self.assertTrue(self.editor.has_path("/foo"))
        self.assertTrue(self.editor.has_path("/foo", "get"))
        self.assertTrue(self.editor.has_path("/foo", "somemethod"))
        self.assertTrue(self.editor.has_path("/bar"))
        self.assertTrue(self.editor.has_path("/bar", "post"))

    def test_must_find_with_method_case_insensitive(self):
        self.assertTrue(self.editor.has_path("/foo", "GeT"))
        self.assertTrue(self.editor.has_path("/bar", "POST"))

        # Only Method is case insensitive. Path is case sensitive
        self.assertFalse(self.editor.has_path("/FOO"))

    def test_must_work_with_any_method(self):
        """
        Method name "ANY" is special. It must be converted to the x-amazon style value before search
        """
        self.assertTrue(self.editor.has_path("/bar", "any"))
        self.assertTrue(self.editor.has_path("/bar", "AnY"))  # Case insensitive
        self.assertTrue(self.editor.has_path("/bar", _X_ANY_METHOD))
        self.assertFalse(self.editor.has_path("/foo", "any"))

    def test_must_not_find_path(self):
        self.assertFalse(self.editor.has_path("/foo/other"))
        self.assertFalse(self.editor.has_path("/bar/xyz"))
        self.assertFalse(self.editor.has_path("/abc"))

    def test_must_not_find_path_and_method(self):
        self.assertFalse(self.editor.has_path("/foo", "post"))
        self.assertFalse(self.editor.has_path("/foo", "abc"))
        self.assertFalse(self.editor.has_path("/bar", "get"))
        self.assertFalse(self.editor.has_path("/bar", "xyz"))

    def test_must_not_fail_on_bad_path(self):

        self.assertTrue(self.editor.has_path("badpath"))
        self.assertFalse(self.editor.has_path("badpath", "somemethod"))


class TestOpenApiEditor_has_integration(TestCase):
    def setUp(self):
        self.openapi = {
            "openapi": "3.0.1",
            "paths": {
                "/foo": {
                    "get": {_X_INTEGRATION: {"a": "b"}},
                    "post": {"Fn::If": ["Condition", {_X_INTEGRATION: {"a": "b"}}, {"Ref": "AWS::NoValue"}]},
                    "delete": {"Fn::If": ["Condition", {"Ref": "AWS::NoValue"}, {_X_INTEGRATION: {"a": "b"}}]},
                    "somemethod": {"foo": "value"},
                    "emptyintegration": {_X_INTEGRATION: {}},
                    "badmethod": "string value",
                }
            },
        }

        self.editor = OpenApiEditor(self.openapi)

    def test_must_find_integration(self):
        self.assertTrue(self.editor.has_integration("/foo", "get"))

    def test_must_find_integration_with_condition(self):
        self.assertTrue(self.editor.has_integration("/foo", "post"))

    def test_must_find_integration_with_condition2(self):
        self.assertTrue(self.editor.has_integration("/foo", "delete"))

    def test_must_not_find_integration(self):
        self.assertFalse(self.editor.has_integration("/foo", "somemethod"))

    def test_must_not_find_empty_integration(self):
        self.assertFalse(self.editor.has_integration("/foo", "emptyintegration"))

    def test_must_handle_bad_value_for_method(self):
        self.assertFalse(self.editor.has_integration("/foo", "badmethod"))


class TestOpenApiEditor_add_path(TestCase):
    def setUp(self):

        self.original_openapi = {
            "openapi": "3.0.1",
            "paths": {"/foo": {"get": {"a": "b"}}, "/bar": {}, "/badpath": "string value"},
        }

        self.editor = OpenApiEditor(self.original_openapi)

    @parameterized.expand(
        [
            param("/new", "get", "new path, new method"),
            param("/foo", "new method", "existing path, new method"),
            param("/bar", "get", "existing path, new method"),
        ]
    )
    def test_must_add_new_path_and_method(self, path, method, case):

        self.assertFalse(self.editor.has_path(path, method))
        self.editor.add_path(path, method)
        self.assertTrue(self.editor.has_path(path, method), "must add for " + case)
        self.assertEqual(self.editor.openapi["paths"][path][method], {})

    def test_must_raise_non_dict_path_values(self):

        path = "/badpath"
        method = "get"

        with self.assertRaises(InvalidDocumentException):
            self.editor.add_path(path, method)

    def test_must_skip_existing_path(self):
        """
        Given an existing path/method, this must
        :return:
        """

        path = "/foo"
        method = "get"
        original_value = copy.deepcopy(self.original_openapi["paths"][path][method])

        self.editor.add_path(path, method)
        modified_openapi = self.editor.openapi
        self.assertEqual(original_value, modified_openapi["paths"][path][method])


class TestOpenApiEditor_add_lambda_integration(TestCase):
    def setUp(self):

        self.original_openapi = {
            "openapi": "3.0.1",
            "paths": {
                "/foo": {"post": {"a": [1, 2, "b"], "responses": {"something": "is already here"}}},
                "/bar": {"get": {_X_INTEGRATION: {"a": "b"}}},
            },
        }

        self.editor = OpenApiEditor(self.original_openapi)

    def test_must_add_new_integration_to_new_path(self):
        path = "/newpath"
        method = "get"
        integration_uri = "something"
        expected = {
            "responses": {},
            _X_INTEGRATION: {
                "type": "aws_proxy",
                "httpMethod": "POST",
                "payloadFormatVersion": "2.0",
                "uri": integration_uri,
            },
        }

        self.editor.add_lambda_integration(path, method, integration_uri)

        self.assertTrue(self.editor.has_path(path, method))
        actual = self.editor.openapi["paths"][path][method]
        self.assertEqual(expected, actual)

    def test_must_add_new_integration_with_conditions_to_new_path(self):
        path = "/newpath"
        method = "get"
        integration_uri = "something"
        condition = "condition"
        expected = {
            "Fn::If": [
                "condition",
                {
                    "responses": {},
                    _X_INTEGRATION: {
                        "type": "aws_proxy",
                        "httpMethod": "POST",
                        "payloadFormatVersion": "2.0",
                        "uri": {"Fn::If": ["condition", integration_uri, {"Ref": "AWS::NoValue"}]},
                    },
                },
                {"Ref": "AWS::NoValue"},
            ]
        }

        self.editor.add_lambda_integration(path, method, integration_uri, condition=condition)

        self.assertTrue(self.editor.has_path(path, method))
        actual = self.editor.openapi["paths"][path][method]
        self.assertEqual(expected, actual)

    def test_must_add_new_integration_to_existing_path(self):
        path = "/foo"
        method = "post"
        integration_uri = "something"
        expected = {
            # Current values present in the dictionary *MUST* be preserved
            "a": [1, 2, "b"],
            # Responses key must be untouched
            "responses": {"something": "is already here"},
            # New values must be added
            _X_INTEGRATION: {
                "type": "aws_proxy",
                "httpMethod": "POST",
                "payloadFormatVersion": "2.0",
                "uri": integration_uri,
            },
        }

        # Just make sure test is working on an existing path
        self.assertTrue(self.editor.has_path(path, method))

        self.editor.add_lambda_integration(path, method, integration_uri)

        actual = self.editor.openapi["paths"][path][method]
        self.assertEqual(expected, actual)


class TestOpenApiEditor_iter_on_path(TestCase):
    def setUp(self):

        self.original_openapi = {"openapi": "3.0.1", "paths": {"/foo": {}, "/bar": {}, "/baz": "some value"}}

        self.editor = OpenApiEditor(self.original_openapi)

    def test_must_iterate_on_paths(self):

        expected = {"/foo", "/bar", "/baz"}
        actual = set(list(self.editor.iter_on_path()))

        self.assertEqual(expected, actual)


class TestOpenApiEditor_normalize_method_name(TestCase):
    @parameterized.expand(
        [
            param("GET", "get", "must lowercase"),
            param("PoST", "post", "must lowercase"),
            param("ANY", _X_ANY_METHOD, "must convert any method"),
            param(None, None, "must skip empty values"),
            param({"a": "b"}, {"a": "b"}, "must skip non-string values"),
            param([1, 2], [1, 2], "must skip non-string values"),
        ]
    )
    def test_must_normalize(self, input, expected, msg):
        self.assertEqual(expected, OpenApiEditor._normalize_method_name(input), msg)


class TestOpenApiEditor_openapi_property(TestCase):
    def test_must_return_copy_of_openapi(self):

        input = {"openapi": "3.0.1", "paths": {}}

        editor = OpenApiEditor(input)
        self.assertEqual(input, editor.openapi)  # They are equal in content
        input["openapi"] = "3"
        self.assertEqual("3.0.1", editor.openapi["openapi"])  # Editor works on a diff copy of input

        editor.add_path("/foo", "get")
        self.assertEqual({"/foo": {"get": {}}}, editor.openapi["paths"])
        self.assertEqual({}, input["paths"])  # Editor works on a diff copy of input


class TestOpenApiEditor_is_valid(TestCase):
    @parameterized.expand(
        [
            param(OpenApiEditor.gen_skeleton()),
            # Dict can contain any other unrecognized properties
            param({"openapi": "3.1.1", "paths": {}, "foo": "bar", "baz": "bar"})
            # TODO check and update the regex accordingly
            # Fails for this: param({"openapi": "3.1.10", "paths": {}, "foo": "bar", "baz": "bar"})
        ]
    )
    def test_must_work_on_valid_values(self, openapi):
        self.assertTrue(OpenApiEditor.is_valid(openapi))

    @parameterized.expand(
        [
            ({}, "empty dictionary"),
            ([1, 2, 3], "array data type"),
            ({"paths": {}}, "missing openapi property"),
            ({"openapi": "hello"}, "missing paths property"),
            ({"openapi": "hello", "paths": [1, 2, 3]}, "array value for paths property"),
        ]
    )
    def test_must_fail_for_invalid_values(self, data, case):
        self.assertFalse(OpenApiEditor.is_valid(data), "openapi dictionary with {} must not be valid".format(case))


class TestOpenApiEditor_add_auth(TestCase):
    def setUp(self):

        self.original_openapi = {
            "openapi": "3.0.1",
            "paths": {
                "/foo": {"get": {_X_INTEGRATION: {"a": "b"}}, "post": {_X_INTEGRATION: {"a": "b"}}},
                "/bar": {"get": {_X_INTEGRATION: {"a": "b"}}},
            },
        }

        self.editor = OpenApiEditor(self.original_openapi)


class TestOpenApiEditor_get_integration_function(TestCase):
    def setUp(self):

        self.original_openapi = {
            "openapi": "3.0.1",
            "paths": {
                "$default": {
                    "x-amazon-apigateway-any-method": {
                        "Fn::If": [
                            "condition",
                            {
                                "security": [{"OpenIdAuth": ["scope1", "scope2"]}],
                                "isDefaultRoute": True,
                                "x-amazon-apigateway-integration": {
                                    "httpMethod": "POST",
                                    "type": "aws_proxy",
                                    "uri": {
                                        "Fn::If": [
                                            "condition",
                                            {
                                                "Fn::Sub": "arn:${AWS::Partition}:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${HttpApiFunction.Arn}/invocations"
                                            },
                                            {"Ref": "AWS::NoValue"},
                                        ]
                                    },
                                    "payloadFormatVersion": "1.0",
                                },
                                "responses": {},
                            },
                            {"Ref": "AWS::NoValue"},
                        ]
                    }
                },
                "/bar": {},
                "/badpath": "string value",
            },
        }

        self.editor = OpenApiEditor(self.original_openapi)

    def test_must_get_integration_function_if_exists(self):

        self.assertEqual(
            self.editor.get_integration_function_logical_id(OpenApiEditor._DEFAULT_PATH, OpenApiEditor._X_ANY_METHOD),
            "HttpApiFunction",
        )
        self.assertFalse(self.editor.get_integration_function_logical_id("/bar", "get"))
