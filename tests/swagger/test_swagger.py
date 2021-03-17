import copy

from unittest import TestCase
from mock import Mock
from parameterized import parameterized, param

from samtranslator.swagger.swagger import SwaggerEditor
from samtranslator.model.exceptions import InvalidDocumentException
from tests.translator.test_translator import deep_sort_lists

_X_INTEGRATION = "x-amazon-apigateway-integration"
_X_ANY_METHOD = "x-amazon-apigateway-any-method"
_X_POLICY = "x-amazon-apigateway-policy"
_ALLOW_CREDENTALS_TRUE = "'true'"


class TestSwaggerEditor_init(TestCase):
    def test_must_raise_on_invalid_swagger(self):

        invalid_swagger = {"paths": {}}  # Missing "Swagger" keyword
        with self.assertRaises(ValueError):
            SwaggerEditor(invalid_swagger)

    def test_must_succeed_on_valid_swagger(self):
        valid_swagger = {"swagger": "2.0", "paths": {"/foo": {}, "/bar": {}}}

        editor = SwaggerEditor(valid_swagger)
        self.assertIsNotNone(editor)

        self.assertEqual(editor.paths, {"/foo": {}, "/bar": {}})

    def test_must_fail_on_invalid_openapi_version(self):
        invalid_swagger = {"openapi": "2.3.0", "paths": {"/foo": {}, "/bar": {}}}

        with self.assertRaises(ValueError):
            SwaggerEditor(invalid_swagger)

    def test_must_fail_on_invalid_openapi_version_2(self):
        invalid_swagger = {"openapi": "3.1.1.1", "paths": {"/foo": {}, "/bar": {}}}

        with self.assertRaises(ValueError):
            SwaggerEditor(invalid_swagger)

    def test_must_succeed_on_valid_openapi3(self):
        valid_swagger = {"openapi": "3.0.1", "paths": {"/foo": {}, "/bar": {}}}

        editor = SwaggerEditor(valid_swagger)
        self.assertIsNotNone(editor)

        self.assertEqual(editor.paths, {"/foo": {}, "/bar": {}})


class TestSwaggerEditor_has_path(TestCase):
    def setUp(self):
        self.swagger = {
            "swagger": "2.0",
            "paths": {
                "/foo": {"get": {}, "somemethod": {}},
                "/bar": {"post": {}, _X_ANY_METHOD: {}},
                "badpath": "string value",
            },
        }

        self.editor = SwaggerEditor(self.swagger)

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


class TestSwaggerEditor_has_integration(TestCase):
    def setUp(self):
        self.swagger = {
            "swagger": "2.0",
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

        self.editor = SwaggerEditor(self.swagger)

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


class TestSwaggerEditor_add_path(TestCase):
    def setUp(self):

        self.original_swagger = {
            "swagger": "2.0",
            "paths": {"/foo": {"get": {"a": "b"}}, "/bar": {}, "/badpath": "string value"},
        }

        self.editor = SwaggerEditor(self.original_swagger)

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
        self.assertEqual(self.editor.swagger["paths"][path][method], {})

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
        original_value = copy.deepcopy(self.original_swagger["paths"][path][method])

        self.editor.add_path(path, method)
        modified_swagger = self.editor.swagger
        self.assertEqual(original_value, modified_swagger["paths"][path][method])


class TestSwaggerEditor_add_lambda_integration(TestCase):
    def setUp(self):

        self.original_swagger = {
            "swagger": "2.0",
            "paths": {
                "/foo": {"post": {"a": [1, 2, "b"], "responses": {"something": "is already here"}}},
                "/bar": {"get": {_X_INTEGRATION: {"a": "b"}}},
            },
        }

        self.editor = SwaggerEditor(self.original_swagger)

    def test_must_add_new_integration_to_new_path(self):
        path = "/newpath"
        method = "get"
        integration_uri = "something"
        expected = {
            "responses": {},
            _X_INTEGRATION: {"type": "aws_proxy", "httpMethod": "POST", "uri": integration_uri},
        }

        self.editor.add_lambda_integration(path, method, integration_uri)

        self.assertTrue(self.editor.has_path(path, method))
        actual = self.editor.swagger["paths"][path][method]
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
                        "uri": {"Fn::If": ["condition", integration_uri, {"Ref": "AWS::NoValue"}]},
                    },
                },
                {"Ref": "AWS::NoValue"},
            ]
        }

        self.editor.add_lambda_integration(path, method, integration_uri, condition=condition)

        self.assertTrue(self.editor.has_path(path, method))
        actual = self.editor.swagger["paths"][path][method]
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
            _X_INTEGRATION: {"type": "aws_proxy", "httpMethod": "POST", "uri": integration_uri},
        }

        # Just make sure test is working on an existing path
        self.assertTrue(self.editor.has_path(path, method))

        self.editor.add_lambda_integration(path, method, integration_uri)

        actual = self.editor.swagger["paths"][path][method]
        self.assertEqual(expected, actual)

    def test_must_raise_on_existing_integration(self):

        with self.assertRaises(ValueError):
            self.editor.add_lambda_integration("/bar", "get", "integrationUri")

    def test_must_add_credentials_to_the_integration(self):
        path = "/newpath"
        method = "get"
        integration_uri = "something"
        expected = "arn:aws:iam::*:user/*"
        api_auth_config = {"DefaultAuthorizer": "AWS_IAM", "InvokeRole": "CALLER_CREDENTIALS"}

        self.editor.add_lambda_integration(path, method, integration_uri, None, api_auth_config)
        actual = self.editor.swagger["paths"][path][method][_X_INTEGRATION]["credentials"]
        self.assertEqual(expected, actual)

    def test_must_add_credentials_to_the_integration_overrides(self):
        path = "/newpath"
        method = "get"
        integration_uri = "something"
        expected = "arn:aws:iam::*:role/xxxxxx"
        api_auth_config = {"DefaultAuthorizer": "MyAuth"}
        method_auth_config = {"Authorizer": "AWS_IAM", "InvokeRole": "arn:aws:iam::*:role/xxxxxx"}

        self.editor.add_lambda_integration(path, method, integration_uri, method_auth_config, api_auth_config)
        actual = self.editor.swagger["paths"][path][method][_X_INTEGRATION]["credentials"]
        self.assertEqual(expected, actual)


class TestSwaggerEditor_iter_on_path(TestCase):
    def setUp(self):

        self.original_swagger = {"swagger": "2.0", "paths": {"/foo": {}, "/bar": {}, "/baz": "some value"}}

        self.editor = SwaggerEditor(self.original_swagger)

    def test_must_iterate_on_paths(self):

        expected = {"/foo", "/bar", "/baz"}
        actual = set(list(self.editor.iter_on_path()))

        self.assertEqual(expected, actual)


class TestSwaggerEditor_add_cors(TestCase):
    def setUp(self):

        self.original_swagger = {
            "swagger": "2.0",
            "paths": {"/foo": {}, "/withoptions": {"options": {"some": "value"}}, "/bad": "some value"},
        }

        self.editor = SwaggerEditor(self.original_swagger)

    def test_must_add_options_to_new_path(self):
        allowed_origins = "origins"
        allowed_headers = ["headers", "2"]
        allowed_methods = {"key": "methods"}
        max_age = 60
        allow_credentials = True
        options_method_response_allow_credentials = True
        path = "/foo"
        expected = {"some cors": "return value"}

        self.editor._options_method_response_for_cors = Mock()
        self.editor._options_method_response_for_cors.return_value = expected

        self.editor.add_cors(path, allowed_origins, allowed_headers, allowed_methods, max_age, allow_credentials)
        self.assertEqual(expected, self.editor.swagger["paths"][path]["options"])
        self.editor._options_method_response_for_cors.assert_called_with(
            allowed_origins, allowed_headers, allowed_methods, max_age, options_method_response_allow_credentials
        )

    def test_must_skip_existing_path(self):
        path = "/withoptions"
        expected = copy.deepcopy(self.original_swagger["paths"][path]["options"])

        self.editor.add_cors(path, "origins", "headers", "methods")
        self.assertEqual(expected, self.editor.swagger["paths"][path]["options"])

    def test_must_fail_with_bad_values_for_path(self):
        path = "/bad"

        with self.assertRaises(InvalidDocumentException):
            self.editor.add_cors(path, "origins", "headers", "methods")

    def test_must_fail_for_invalid_allowed_origin(self):

        path = "/foo"
        with self.assertRaises(ValueError):
            self.editor.add_cors(path, None, "headers", "methods")

    def test_must_work_for_optional_allowed_headers(self):

        allowed_origins = "origins"
        allowed_headers = None  # No Value
        allowed_methods = "methods"
        max_age = 60
        allow_credentials = True
        options_method_response_allow_credentials = True

        expected = {"some cors": "return value"}
        path = "/foo"

        self.editor._options_method_response_for_cors = Mock()
        self.editor._options_method_response_for_cors.return_value = expected

        self.editor.add_cors(path, allowed_origins, allowed_headers, allowed_methods, max_age, allow_credentials)

        self.assertEqual(expected, self.editor.swagger["paths"][path]["options"])

        self.editor._options_method_response_for_cors.assert_called_with(
            allowed_origins, allowed_headers, allowed_methods, max_age, options_method_response_allow_credentials
        )

    def test_must_make_default_value_with_optional_allowed_methods(self):

        allowed_origins = "origins"
        allowed_headers = "headers"
        allowed_methods = None  # No Value
        max_age = 60
        allow_credentials = True
        options_method_response_allow_credentials = True

        default_allow_methods_value = "some default value"
        default_allow_methods_value_with_quotes = "'{}'".format(default_allow_methods_value)
        expected = {"some cors": "return value"}
        path = "/foo"

        self.editor._make_cors_allowed_methods_for_path = Mock()
        self.editor._make_cors_allowed_methods_for_path.return_value = default_allow_methods_value

        self.editor._options_method_response_for_cors = Mock()
        self.editor._options_method_response_for_cors.return_value = expected

        self.editor.add_cors(path, allowed_origins, allowed_headers, allowed_methods, max_age, allow_credentials)

        self.assertEqual(expected, self.editor.swagger["paths"][path]["options"])

        self.editor._options_method_response_for_cors.assert_called_with(
            allowed_origins,
            allowed_headers,
            # Must be called with default value.
            # And value must be quoted
            default_allow_methods_value_with_quotes,
            max_age,
            options_method_response_allow_credentials,
        )

    def test_must_accept_none_allow_credentials(self):
        allowed_origins = "origins"
        allowed_headers = ["headers", "2"]
        allowed_methods = {"key": "methods"}
        max_age = 60
        allow_credentials = None
        options_method_response_allow_credentials = False
        path = "/foo"
        expected = {"some cors": "return value"}

        self.editor._options_method_response_for_cors = Mock()
        self.editor._options_method_response_for_cors.return_value = expected

        self.editor.add_cors(path, allowed_origins, allowed_headers, allowed_methods, max_age, allow_credentials)
        self.assertEqual(expected, self.editor.swagger["paths"][path]["options"])
        self.editor._options_method_response_for_cors.assert_called_with(
            allowed_origins, allowed_headers, allowed_methods, max_age, options_method_response_allow_credentials
        )


class TestSwaggerEditor_options_method_response_for_cors(TestCase):
    def test_correct_value_is_returned(self):
        self.maxDiff = None
        headers = "foo"
        methods = {"a": "b"}
        origins = [1, 2, 3]
        max_age = 60
        allow_credentials = True

        expected = {
            "summary": "CORS support",
            "consumes": ["application/json"],
            "produces": ["application/json"],
            _X_INTEGRATION: {
                "type": "mock",
                "requestTemplates": {"application/json": '{\n  "statusCode" : 200\n}\n'},
                "responses": {
                    "default": {
                        "statusCode": "200",
                        "responseParameters": {
                            "method.response.header.Access-Control-Allow-Credentials": _ALLOW_CREDENTALS_TRUE,
                            "method.response.header.Access-Control-Allow-Headers": headers,
                            "method.response.header.Access-Control-Allow-Methods": methods,
                            "method.response.header.Access-Control-Allow-Origin": origins,
                            "method.response.header.Access-Control-Max-Age": max_age,
                        },
                        "responseTemplates": {"application/json": "{}\n"},
                    }
                },
            },
            "responses": {
                "200": {
                    "description": "Default response for CORS method",
                    "headers": {
                        "Access-Control-Allow-Credentials": {"type": "string"},
                        "Access-Control-Allow-Headers": {"type": "string"},
                        "Access-Control-Allow-Methods": {"type": "string"},
                        "Access-Control-Allow-Origin": {"type": "string"},
                        "Access-Control-Max-Age": {"type": "integer"},
                    },
                }
            },
        }

        actual = SwaggerEditor(SwaggerEditor.gen_skeleton())._options_method_response_for_cors(
            origins, headers, methods, max_age, allow_credentials
        )
        self.assertEqual(expected, actual)

    def test_allow_headers_is_skipped_with_no_value(self):
        headers = None  # No value
        methods = "methods"
        origins = "origins"
        allow_credentials = True

        expected = {
            "method.response.header.Access-Control-Allow-Credentials": _ALLOW_CREDENTALS_TRUE,
            "method.response.header.Access-Control-Allow-Methods": methods,
            "method.response.header.Access-Control-Allow-Origin": origins,
        }

        expected_headers = {
            "Access-Control-Allow-Credentials": {"type": "string"},
            "Access-Control-Allow-Methods": {"type": "string"},
            "Access-Control-Allow-Origin": {"type": "string"},
        }

        options_config = SwaggerEditor(SwaggerEditor.gen_skeleton())._options_method_response_for_cors(
            origins, headers, methods, allow_credentials=allow_credentials
        )

        actual = options_config[_X_INTEGRATION]["responses"]["default"]["responseParameters"]
        self.assertEqual(expected, actual)
        self.assertEqual(expected_headers, options_config["responses"]["200"]["headers"])

    def test_allow_methods_is_skipped_with_no_value(self):
        headers = "headers"
        methods = None  # No value
        origins = "origins"
        allow_credentials = True

        expected = {
            "method.response.header.Access-Control-Allow-Credentials": _ALLOW_CREDENTALS_TRUE,
            "method.response.header.Access-Control-Allow-Headers": headers,
            "method.response.header.Access-Control-Allow-Origin": origins,
        }

        options_config = SwaggerEditor(SwaggerEditor.gen_skeleton())._options_method_response_for_cors(
            origins, headers, methods, allow_credentials=allow_credentials
        )

        actual = options_config[_X_INTEGRATION]["responses"]["default"]["responseParameters"]
        self.assertEqual(expected, actual)

    def test_allow_origins_is_not_skipped_with_no_value(self):
        headers = None
        methods = None
        origins = None
        allow_credentials = False

        expected = {
            # We will ALWAYS set AllowOrigin. This is a minimum requirement for CORS
            "method.response.header.Access-Control-Allow-Origin": origins
        }

        options_config = SwaggerEditor(SwaggerEditor.gen_skeleton())._options_method_response_for_cors(
            origins, headers, methods, allow_credentials=allow_credentials
        )

        actual = options_config[_X_INTEGRATION]["responses"]["default"]["responseParameters"]
        self.assertEqual(expected, actual)

    def test_max_age_can_be_set_to_zero(self):
        headers = None
        methods = "methods"
        origins = "origins"
        max_age = 0
        allow_credentials = True

        expected = {
            "method.response.header.Access-Control-Allow-Credentials": _ALLOW_CREDENTALS_TRUE,
            "method.response.header.Access-Control-Allow-Methods": methods,
            "method.response.header.Access-Control-Allow-Origin": origins,
            "method.response.header.Access-Control-Max-Age": max_age,
        }

        options_config = SwaggerEditor(SwaggerEditor.gen_skeleton())._options_method_response_for_cors(
            origins, headers, methods, max_age, allow_credentials
        )

        actual = options_config[_X_INTEGRATION]["responses"]["default"]["responseParameters"]
        self.assertEqual(expected, actual)

    def test_allow_credentials_is_skipped_with_false_value(self):
        headers = "headers"
        methods = "methods"
        origins = "origins"
        allow_credentials = False

        expected = {
            "method.response.header.Access-Control-Allow-Headers": headers,
            "method.response.header.Access-Control-Allow-Methods": methods,
            "method.response.header.Access-Control-Allow-Origin": origins,
        }

        options_config = SwaggerEditor(SwaggerEditor.gen_skeleton())._options_method_response_for_cors(
            origins, headers, methods, allow_credentials=allow_credentials
        )

        actual = options_config[_X_INTEGRATION]["responses"]["default"]["responseParameters"]
        self.assertEqual(expected, actual)


class TestSwaggerEditor_make_cors_allowed_methods_for_path(TestCase):
    def setUp(self):
        self.editor = SwaggerEditor(
            {
                "swagger": "2.0",
                "paths": {
                    "/foo": {"get": {}, "POST": {}, "DeLeTe": {}},
                    "/withany": {"head": {}, _X_ANY_METHOD: {}},
                    "/nothing": {},
                },
            }
        )

    def test_must_return_all_defined_methods(self):
        path = "/foo"
        expected = "DELETE,GET,OPTIONS,POST"  # Result should be sorted alphabetically

        actual = self.editor._make_cors_allowed_methods_for_path(path)
        self.assertEqual(expected, actual)

    def test_must_work_for_any_method(self):
        path = "/withany"
        expected = "DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT"  # Result should be sorted alphabetically

        actual = self.editor._make_cors_allowed_methods_for_path(path)
        self.assertEqual(expected, actual)

    def test_must_work_with_no_methods(self):
        path = "/nothing"
        expected = "OPTIONS"

        actual = self.editor._make_cors_allowed_methods_for_path(path)
        self.assertEqual(expected, actual)

    def test_must_skip_non_existent_path(self):
        path = "/no-path"
        expected = ""

        actual = self.editor._make_cors_allowed_methods_for_path(path)
        self.assertEqual(expected, actual)


class TestSwaggerEditor_normalize_method_name(TestCase):
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
        self.assertEqual(expected, SwaggerEditor._normalize_method_name(input), msg)


class TestSwaggerEditor_swagger_property(TestCase):
    def test_must_return_copy_of_swagger(self):

        input = {"swagger": "2.0", "paths": {}}

        editor = SwaggerEditor(input)
        self.assertEqual(input, editor.swagger)  # They are equal in content
        input["swagger"] = "3"
        self.assertEqual("2.0", editor.swagger["swagger"])  # Editor works on a diff copy of input

        editor.add_path("/foo", "get")
        self.assertEqual({"/foo": {"get": {}}}, editor.swagger["paths"])
        self.assertEqual({}, input["paths"])  # Editor works on a diff copy of input


class TestSwaggerEditor_is_valid(TestCase):
    @parameterized.expand(
        [
            param(SwaggerEditor.gen_skeleton()),
            # Dict can contain any other unrecognized properties
            param({"swagger": "anyvalue", "paths": {}, "foo": "bar", "baz": "bar"}),
        ]
    )
    def test_must_work_on_valid_values(self, swagger):
        self.assertTrue(SwaggerEditor.is_valid(swagger))

    @parameterized.expand(
        [
            ({}, "empty dictionary"),
            ([1, 2, 3], "array data type"),
            ({"paths": {}}, "missing swagger property"),
            ({"swagger": "hello"}, "missing paths property"),
            ({"swagger": "hello", "paths": [1, 2, 3]}, "array value for paths property"),
        ]
    )
    def test_must_fail_for_invalid_values(self, data, case):
        self.assertFalse(SwaggerEditor.is_valid(data), "Swagger dictionary with {} must not be valid".format(case))


class TestSwaggerEditor_add_models(TestCase):
    def setUp(self):

        self.original_swagger = {"swagger": "2.0", "paths": {"/foo": {}}}

        self.editor = SwaggerEditor(self.original_swagger)

    def test_must_add_definitions(self):

        models = {"User": {"type": "object", "properties": {"username": {"type": "string"}}}}

        self.editor.add_models(models)

        expected = {"user": {"type": "object", "properties": {"username": {"type": "string"}}}}

        self.assertEqual(expected, self.editor.swagger["definitions"])

    def test_must_fail_without_type_in_model(self):

        models = {"User": {"properties": {"username": {"type": "string"}}}}

        with self.assertRaises(InvalidDocumentException):
            self.editor.add_models(models)

    def test_must_fail_without_properties_in_model(self):
        models = {"User": {"type": "object"}}

        with self.assertRaises(InvalidDocumentException):
            self.editor.add_models(models)


class TestSwaggerEditor_add_request_model_to_method(TestCase):
    def setUp(self):

        self.original_swagger = {
            "swagger": "2.0",
            "paths": {"/foo": {"get": {"x-amazon-apigateway-integration": {"test": "must have integration"}}}},
        }

        self.editor = SwaggerEditor(self.original_swagger)

    def test_must_add_body_parameter_to_method_with_required_true(self):

        model = {"Model": "User", "Required": True}

        self.editor.add_request_model_to_method("/foo", "get", model)

        expected = [{"in": "body", "required": True, "name": "user", "schema": {"$ref": "#/definitions/user"}}]

        self.assertEqual(expected, self.editor.swagger["paths"]["/foo"]["get"]["parameters"])

    def test_must_add_body_parameter_to_method_with_required_false(self):

        model = {"Model": "User", "Required": False}

        self.editor.add_request_model_to_method("/foo", "get", model)

        expected = [{"in": "body", "required": False, "name": "user", "schema": {"$ref": "#/definitions/user"}}]

        self.assertEqual(expected, self.editor.swagger["paths"]["/foo"]["get"]["parameters"])

    def test_must_add_body_parameter_to_existing_method_parameters(self):

        original_swagger = {
            "swagger": "2.0",
            "paths": {
                "/foo": {
                    "get": {
                        "x-amazon-apigateway-integration": {"test": "must have integration"},
                        "parameters": [{"test": "existing parameter"}],
                    }
                }
            },
        }

        editor = SwaggerEditor(original_swagger)

        model = {"Model": "User", "Required": True}

        editor.add_request_model_to_method("/foo", "get", model)

        expected = [
            {"test": "existing parameter"},
            {"in": "body", "required": True, "name": "user", "schema": {"$ref": "#/definitions/user"}},
        ]

        self.assertEqual(expected, editor.swagger["paths"]["/foo"]["get"]["parameters"])

    def test_must_not_add_body_parameter_to_method_without_integration(self):

        original_swagger = {"swagger": "2.0", "paths": {"/foo": {"get": {}}}}

        editor = SwaggerEditor(original_swagger)

        model = {"Model": "User", "Required": True}

        editor.add_request_model_to_method("/foo", "get", model)

        expected = {}

        self.assertEqual(expected, editor.swagger["paths"]["/foo"]["get"])

    def test_must_add_body_parameter_to_method_without_required(self):

        model = {"Model": "User"}

        self.editor.add_request_model_to_method("/foo", "get", model)

        expected = [{"in": "body", "name": "user", "schema": {"$ref": "#/definitions/user"}}]

        self.assertEqual(expected, self.editor.swagger["paths"]["/foo"]["get"]["parameters"])

    def test_must_add_body_parameter_to_method_openapi_without_required(self):

        original_openapi = {
            "openapi": "3.0.1",
            "paths": {"/foo": {"get": {"x-amazon-apigateway-integration": {"test": "must have integration"}}}},
        }

        editor = SwaggerEditor(original_openapi)

        model = {"Model": "User", "Required": True}

        editor.add_request_model_to_method("/foo", "get", model)

        expected = {
            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/user"}}},
            "required": True,
        }

        self.assertEqual(expected, editor.swagger["paths"]["/foo"]["get"]["requestBody"])

    def test_must_add_body_parameter_to_method_openapi_required_true(self):

        original_openapi = {
            "openapi": "3.0.1",
            "paths": {"/foo": {"get": {"x-amazon-apigateway-integration": {"test": "must have integration"}}}},
        }

        editor = SwaggerEditor(original_openapi)

        model = {"Model": "User"}

        editor.add_request_model_to_method("/foo", "get", model)

        expected = {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/user"}}}}

        self.assertEqual(expected, editor.swagger["paths"]["/foo"]["get"]["requestBody"])


class TestSwaggerEditor_add_auth(TestCase):
    def setUp(self):

        self.original_swagger = {
            "swagger": "2.0",
            "paths": {
                "/foo": {"get": {_X_INTEGRATION: {"a": "b"}}, "post": {_X_INTEGRATION: {"a": "b"}}},
                "/bar": {"get": {_X_INTEGRATION: {"a": "b"}}},
            },
        }

        self.editor = SwaggerEditor(self.original_swagger)

    def test_add_apikey_security_definition_is_added(self):
        expected = {"type": "apiKey", "name": "x-api-key", "in": "header"}

        self.editor.add_apikey_security_definition()
        self.assertIn("securityDefinitions", self.editor.swagger)
        self.assertIn("api_key", self.editor.swagger["securityDefinitions"])
        self.assertEqual(expected, self.editor.swagger["securityDefinitions"]["api_key"])

    def test_must_add_default_apikey_to_all_paths(self):
        expected = [{"api_key": []}]
        path = "/foo"

        self.editor.set_path_default_apikey_required(path)
        methods = self.editor.swagger["paths"][path]
        for method in methods:
            self.assertEqual(expected, methods[method]["security"])

    def test_add_default_apikey_to_all_paths_correctly_handles_method_level_settings(self):
        self.original_swagger = {
            "swagger": "2.0",
            "paths": {
                "/foo": {
                    "apikeyfalse": {_X_INTEGRATION: {"a": "b"}, "security": [{"api_key_false": []}]},
                    "apikeytrue": {_X_INTEGRATION: {"a": "b"}, "security": [{"api_key": []}]},
                    "apikeydefault": {_X_INTEGRATION: {"a": "b"}},
                }
            },
        }

        self.editor = SwaggerEditor(self.original_swagger)
        api_key_exists = [{"api_key": []}]
        path = "/foo"

        self.editor.set_path_default_apikey_required(path)
        self.assertEqual([], self.editor.swagger["paths"][path]["apikeyfalse"]["security"])
        self.assertEqual(api_key_exists, self.editor.swagger["paths"][path]["apikeytrue"]["security"])
        self.assertEqual(api_key_exists, self.editor.swagger["paths"][path]["apikeydefault"]["security"])

    def test_set_method_apikey_handling_apikeyrequired_false(self):
        expected = [{"api_key_false": []}]
        path = "/bar"
        method = "get"

        self.editor._set_method_apikey_handling(path, method, False)
        self.assertEqual(expected, self.editor.swagger["paths"][path][method]["security"])

    def test_set_method_apikey_handling_apikeyrequired_true(self):
        expected = [{"api_key": []}]
        path = "/bar"
        method = "get"

        self.editor._set_method_apikey_handling(path, method, True)
        self.assertEqual(expected, self.editor.swagger["paths"][path][method]["security"])


class TestSwaggerEditor_add_request_parameter_to_method(TestCase):
    def setUp(self):
        self.original_swagger = {
            "swagger": "2.0",
            "paths": {"/foo": {"get": {"x-amazon-apigateway-integration": {"test": "must have integration"}}}},
        }

        self.editor = SwaggerEditor(self.original_swagger)

    def test_must_add_parameter_to_method_with_required_and_caching_true(self):

        parameters = [{"Name": "method.request.header.Authorization", "Required": True, "Caching": True}]

        self.editor.add_request_parameters_to_method("/foo", "get", parameters)

        expected_parameters = [{"in": "header", "required": True, "name": "Authorization", "type": "string"}]

        method_swagger = self.editor.swagger["paths"]["/foo"]["get"]

        self.assertEqual(expected_parameters, method_swagger["parameters"])
        self.assertEqual(["method.request.header.Authorization"], method_swagger[_X_INTEGRATION]["cacheKeyParameters"])

    def test_must_add_parameter_to_method_with_required_and_caching_false(self):

        parameters = [{"Name": "method.request.header.Authorization", "Required": False, "Caching": False}]

        self.editor.add_request_parameters_to_method("/foo", "get", parameters)

        expected_parameters = [{"in": "header", "required": False, "name": "Authorization", "type": "string"}]

        method_swagger = self.editor.swagger["paths"]["/foo"]["get"]

        self.assertEqual(expected_parameters, method_swagger["parameters"])
        self.assertNotIn("cacheKeyParameters", method_swagger[_X_INTEGRATION].keys())

    def test_must_add_parameter_to_method_with_existing_parameters(self):

        original_swagger = {
            "swagger": "2.0",
            "paths": {
                "/foo": {
                    "get": {
                        "x-amazon-apigateway-integration": {"test": "must have integration"},
                        "parameters": [{"test": "existing parameter"}],
                    }
                }
            },
        }

        editor = SwaggerEditor(original_swagger)

        parameters = [{"Name": "method.request.header.Authorization", "Required": False, "Caching": False}]

        editor.add_request_parameters_to_method("/foo", "get", parameters)

        expected_parameters = [
            {"test": "existing parameter"},
            {"in": "header", "required": False, "name": "Authorization", "type": "string"},
        ]

        method_swagger = editor.swagger["paths"]["/foo"]["get"]

        self.assertEqual(expected_parameters, method_swagger["parameters"])
        self.assertNotIn("cacheKeyParameters", method_swagger[_X_INTEGRATION].keys())

    def test_must_not_add_parameter_to_method_without_integration(self):
        original_swagger = {"swagger": "2.0", "paths": {"/foo": {"get": {}}}}

        editor = SwaggerEditor(original_swagger)

        parameters = [{"Name": "method.request.header.Authorization", "Required": True, "Caching": True}]

        editor.add_request_parameters_to_method("/foo", "get", parameters)

        expected = {}

        self.assertEqual(expected, editor.swagger["paths"]["/foo"]["get"])


class TestSwaggerEditor_add_resource_policy(TestCase):
    def setUp(self):

        self.original_swagger = {"swagger": "2.0", "paths": {"/foo": {"get": {}, "put": {}}}}

        self.editor = SwaggerEditor(self.original_swagger)

    def test_must_add_custom_statements(self):

        resourcePolicy = {
            "CustomStatements": [
                {"Action": "execute-api:Invoke", "Resource": ["execute-api:/*/*/*"]},
                {"Action": "execute-api:blah", "Resource": ["execute-api:/*/*/*"]},
            ]
        }

        self.editor.add_custom_statements(resourcePolicy.get("CustomStatements"))

        expected = {
            "Version": "2012-10-17",
            "Statement": [
                {"Action": "execute-api:Invoke", "Resource": ["execute-api:/*/*/*"]},
                {"Action": "execute-api:blah", "Resource": ["execute-api:/*/*/*"]},
            ],
        }

        self.assertEqual(deep_sort_lists(expected), deep_sort_lists(self.editor.swagger[_X_POLICY]))

    def test_must_add_fn_if_custom_statements(self):

        resourcePolicy = {
            "CustomStatements": {
                "Fn::If": [
                    "condition",
                    {"Action": "execute-api:Invoke", "Resource": ["execute-api:/*/*/*"]},
                    {"Action": "execute-api:blah", "Resource": ["execute-api:/*/*/*"]},
                ]
            }
        }

        self.editor.add_custom_statements(resourcePolicy.get("CustomStatements"))

        expected = {
            "Version": "2012-10-17",
            "Statement": {
                "Fn::If": [
                    "condition",
                    {"Action": "execute-api:Invoke", "Resource": ["execute-api:/*/*/*"]},
                    {"Action": "execute-api:blah", "Resource": ["execute-api:/*/*/*"]},
                ]
            },
        }

        self.assertEqual(deep_sort_lists(expected), deep_sort_lists(self.editor.swagger[_X_POLICY]))

    def test_must_add_iam_allow(self):
        ## fails
        resourcePolicy = {"AwsAccountWhitelist": ["123456"]}

        self.editor.add_resource_policy(resourcePolicy, "/foo", "123", "prod")

        expected = {
            "Version": "2012-10-17",
            "Statement": {
                "Action": "execute-api:Invoke",
                "Resource": [
                    {"Fn::Sub": ["execute-api:/${__Stage__}/PUT/foo", {"__Stage__": "prod"}]},
                    {"Fn::Sub": ["execute-api:/${__Stage__}/GET/foo", {"__Stage__": "prod"}]},
                ],
                "Effect": "Allow",
                "Principal": {"AWS": ["123456"]},
            },
        }

        self.assertEqual(deep_sort_lists(expected), deep_sort_lists(self.editor.swagger[_X_POLICY]))

    def test_must_add_iam_deny(self):

        resourcePolicy = {"AwsAccountBlacklist": ["123456"]}

        self.editor.add_resource_policy(resourcePolicy, "/foo", "123", "prod")

        expected = {
            "Version": "2012-10-17",
            "Statement": {
                "Action": "execute-api:Invoke",
                "Resource": [
                    {"Fn::Sub": ["execute-api:/${__Stage__}/PUT/foo", {"__Stage__": "prod"}]},
                    {"Fn::Sub": ["execute-api:/${__Stage__}/GET/foo", {"__Stage__": "prod"}]},
                ],
                "Effect": "Deny",
                "Principal": {"AWS": ["123456"]},
            },
        }

        self.assertEqual(deep_sort_lists(expected), deep_sort_lists(self.editor.swagger[_X_POLICY]))

    def test_must_add_ip_allow(self):

        resourcePolicy = {"IpRangeWhitelist": ["1.2.3.4"]}

        self.editor.add_resource_policy(resourcePolicy, "/foo", "123", "prod")

        expected = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Resource": [
                        {"Fn::Sub": ["execute-api:/${__Stage__}/PUT/foo", {"__Stage__": "prod"}]},
                        {"Fn::Sub": ["execute-api:/${__Stage__}/GET/foo", {"__Stage__": "prod"}]},
                    ],
                    "Effect": "Allow",
                    "Principal": "*",
                },
                {
                    "Action": "execute-api:Invoke",
                    "Resource": [
                        {"Fn::Sub": ["execute-api:/${__Stage__}/PUT/foo", {"__Stage__": "prod"}]},
                        {"Fn::Sub": ["execute-api:/${__Stage__}/GET/foo", {"__Stage__": "prod"}]},
                    ],
                    "Effect": "Deny",
                    "Condition": {"NotIpAddress": {"aws:SourceIp": ["1.2.3.4"]}},
                    "Principal": "*",
                },
            ],
        }

        self.assertEqual(deep_sort_lists(expected), deep_sort_lists(self.editor.swagger[_X_POLICY]))

    def test_must_add_ip_deny(self):

        resourcePolicy = {"IpRangeBlacklist": ["1.2.3.4"]}

        self.editor.add_resource_policy(resourcePolicy, "/foo", "123", "prod")

        expected = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Resource": [
                        {"Fn::Sub": ["execute-api:/${__Stage__}/PUT/foo", {"__Stage__": "prod"}]},
                        {"Fn::Sub": ["execute-api:/${__Stage__}/GET/foo", {"__Stage__": "prod"}]},
                    ],
                    "Effect": "Allow",
                    "Principal": "*",
                },
                {
                    "Action": "execute-api:Invoke",
                    "Resource": [
                        {"Fn::Sub": ["execute-api:/${__Stage__}/PUT/foo", {"__Stage__": "prod"}]},
                        {"Fn::Sub": ["execute-api:/${__Stage__}/GET/foo", {"__Stage__": "prod"}]},
                    ],
                    "Effect": "Deny",
                    "Condition": {"IpAddress": {"aws:SourceIp": ["1.2.3.4"]}},
                    "Principal": "*",
                },
            ],
        }

        self.assertEqual(deep_sort_lists(expected), deep_sort_lists(self.editor.swagger[_X_POLICY]))

    def test_must_add_vpc_allow_string_only(self):

        resourcePolicy = {
            "SourceVpcWhitelist": ["vpc-123", "vpce-345"],
        }

        self.editor.add_resource_policy(resourcePolicy, "/foo", "123", "prod")

        expected = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Resource": [
                        {"Fn::Sub": ["execute-api:/${__Stage__}/PUT/foo", {"__Stage__": "prod"}]},
                        {"Fn::Sub": ["execute-api:/${__Stage__}/GET/foo", {"__Stage__": "prod"}]},
                    ],
                    "Effect": "Allow",
                    "Principal": "*",
                },
                {
                    "Action": "execute-api:Invoke",
                    "Resource": [
                        {"Fn::Sub": ["execute-api:/${__Stage__}/PUT/foo", {"__Stage__": "prod"}]},
                        {"Fn::Sub": ["execute-api:/${__Stage__}/GET/foo", {"__Stage__": "prod"}]},
                    ],
                    "Effect": "Deny",
                    "Condition": {
                        "StringNotEquals": {
                            "aws:SourceVpc": ["vpc-123"],
                            "aws:SourceVpce": ["vpce-345"],
                        }
                    },
                    "Principal": "*",
                },
            ],
        }

        self.assertEqual(deep_sort_lists(expected), deep_sort_lists(self.editor.swagger[_X_POLICY]))

    def test_must_add_vpc_deny_string_only(self):

        resourcePolicy = {
            "SourceVpcBlacklist": ["vpc-123"],
        }

        self.editor.add_resource_policy(resourcePolicy, "/foo", "123", "prod")

        expected = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Resource": [
                        {"Fn::Sub": ["execute-api:/${__Stage__}/PUT/foo", {"__Stage__": "prod"}]},
                        {"Fn::Sub": ["execute-api:/${__Stage__}/GET/foo", {"__Stage__": "prod"}]},
                    ],
                    "Effect": "Allow",
                    "Principal": "*",
                },
                {
                    "Action": "execute-api:Invoke",
                    "Resource": [
                        {"Fn::Sub": ["execute-api:/${__Stage__}/PUT/foo", {"__Stage__": "prod"}]},
                        {"Fn::Sub": ["execute-api:/${__Stage__}/GET/foo", {"__Stage__": "prod"}]},
                    ],
                    "Effect": "Deny",
                    "Condition": {"StringEquals": {"aws:SourceVpc": ["vpc-123"]}},
                    "Principal": "*",
                },
            ],
        }

        self.assertEqual(deep_sort_lists(expected), deep_sort_lists(self.editor.swagger[_X_POLICY]))

    def test_must_add_vpc_allow_string_and_instrinic(self):

        resourcePolicy = {
            "SourceVpcWhitelist": ["vpc-123", "vpce-345", "vpc-678"],
            "IntrinsicVpcWhitelist": ["Mock-Allowlist-A", "Mock-Allowlist-B"],
            "IntrinsicVpceWhitelist": ["Mock-Allowlist-C"],
        }

        self.editor.add_resource_policy(resourcePolicy, "/foo", "123", "prod")

        expected = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Resource": [
                        {"Fn::Sub": ["execute-api:/${__Stage__}/PUT/foo", {"__Stage__": "prod"}]},
                        {"Fn::Sub": ["execute-api:/${__Stage__}/GET/foo", {"__Stage__": "prod"}]},
                    ],
                    "Effect": "Allow",
                    "Principal": "*",
                },
                {
                    "Action": "execute-api:Invoke",
                    "Resource": [
                        {"Fn::Sub": ["execute-api:/${__Stage__}/PUT/foo", {"__Stage__": "prod"}]},
                        {"Fn::Sub": ["execute-api:/${__Stage__}/GET/foo", {"__Stage__": "prod"}]},
                    ],
                    "Effect": "Deny",
                    "Condition": {
                        "StringNotEquals": {
                            "aws:SourceVpc": ["vpc-123", "vpc-678", "Mock-Allowlist-A", "Mock-Allowlist-B"],
                            "aws:SourceVpce": ["vpce-345", "Mock-Allowlist-C"],
                        }
                    },
                    "Principal": "*",
                },
            ],
        }

        self.assertEqual(deep_sort_lists(expected), deep_sort_lists(self.editor.swagger[_X_POLICY]))

    def test_must_add_vpc_deny_string_and_intrinsic(self):
        resourcePolicy = {
            "SourceVpcBlacklist": ["vpc-123", "vpce-789", "vpce-abc"],
            "IntrinsicVpceBlacklist": ["Mock-Denylist-A", "Mock-List-1"],
        }

        self.editor.add_resource_policy(resourcePolicy, "/foo", "123", "prod")

        expected = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Resource": [
                        {"Fn::Sub": ["execute-api:/${__Stage__}/PUT/foo", {"__Stage__": "prod"}]},
                        {"Fn::Sub": ["execute-api:/${__Stage__}/GET/foo", {"__Stage__": "prod"}]},
                    ],
                    "Effect": "Allow",
                    "Principal": "*",
                },
                {
                    "Action": "execute-api:Invoke",
                    "Resource": [
                        {"Fn::Sub": ["execute-api:/${__Stage__}/PUT/foo", {"__Stage__": "prod"}]},
                        {"Fn::Sub": ["execute-api:/${__Stage__}/GET/foo", {"__Stage__": "prod"}]},
                    ],
                    "Effect": "Deny",
                    "Condition": {
                        "StringEquals": {
                            "aws:SourceVpc": ["vpc-123"],
                            "aws:SourceVpce": ["vpce-789", "vpce-abc", "Mock-Denylist-A", "Mock-List-1"],
                        }
                    },
                    "Principal": "*",
                },
            ],
        }

        self.assertEqual(deep_sort_lists(expected), deep_sort_lists(self.editor.swagger[_X_POLICY]))

    def test_must_not_add_non_valid_string_list(self):

        resourcePolicy = {
            "SourceVpcBlacklist": ["non-valid-endpoint-name-a", "non-valid-endpoint-name-b"],
            "SourceVpcWhitelist": ["non-valid-endpoint-name-1", "non-valid-endpoint-name-2"],
        }

        self.editor.add_resource_policy(resourcePolicy, "/foo", "123", "prod")

        expected = {}
        self.assertEqual(deep_sort_lists(expected), deep_sort_lists(self.editor.swagger[_X_POLICY]))

    def test_must_add_vpc_mixed_lists(self):

        resourcePolicy = {
            "SourceVpcWhitelist": ["vpc-123", "vpc-abc", "vpce-123", "vpce-ghi"],
            "IntrinsicVpcWhitelist": ["Mock-Allowlist-A", "Mock-Allowlist-B"],
            "IntrinsicVpceWhitelist": ["Mock-Allowlist-C"],
            "SourceVpcBlacklist": ["vpc-456", "vpc-def", "vpce-789", "vpce-abc"],
            "IntrinsicVpcBlacklist": ["Mock-List-1"],
            "IntrinsicVpceBlacklist": ["Mock-Denylist-A", "Mock-List-1"],
        }

        self.editor.add_resource_policy(resourcePolicy, "/foo", "123", "prod")

        expected = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Resource": [
                        {"Fn::Sub": ["execute-api:/${__Stage__}/PUT/foo", {"__Stage__": "prod"}]},
                        {"Fn::Sub": ["execute-api:/${__Stage__}/GET/foo", {"__Stage__": "prod"}]},
                    ],
                    "Effect": "Allow",
                    "Principal": "*",
                },
                {
                    "Action": "execute-api:Invoke",
                    "Resource": [
                        {"Fn::Sub": ["execute-api:/${__Stage__}/PUT/foo", {"__Stage__": "prod"}]},
                        {"Fn::Sub": ["execute-api:/${__Stage__}/GET/foo", {"__Stage__": "prod"}]},
                    ],
                    "Effect": "Deny",
                    "Condition": {
                        "StringEquals": {
                            "aws:SourceVpc": ["vpc-456", "vpc-def", "Mock-List-1"],
                            "aws:SourceVpce": ["vpce-789", "vpce-abc", "Mock-Denylist-A", "Mock-List-1"],
                        },
                    },
                    "Principal": "*",
                },
                {
                    "Action": "execute-api:Invoke",
                    "Resource": [
                        {"Fn::Sub": ["execute-api:/${__Stage__}/PUT/foo", {"__Stage__": "prod"}]},
                        {"Fn::Sub": ["execute-api:/${__Stage__}/GET/foo", {"__Stage__": "prod"}]},
                    ],
                    "Effect": "Deny",
                    "Condition": {
                        "StringNotEquals": {
                            "aws:SourceVpc": ["vpc-123", "vpc-abc", "Mock-Allowlist-A", "Mock-Allowlist-B"],
                            "aws:SourceVpce": ["vpce-123", "vpce-ghi", "Mock-Allowlist-C"],
                        }
                    },
                    "Principal": "*",
                },
            ],
        }
        self.assertEqual(deep_sort_lists(expected), deep_sort_lists(self.editor.swagger[_X_POLICY]))

    def test_must_add_iam_allow_and_custom(self):
        resourcePolicy = {
            "AwsAccountWhitelist": ["123456"],
            "CustomStatements": [
                {"Action": "execute-api:Invoke", "Resource": ["execute-api:/*/*/*"]},
                {"Action": "execute-api:blah", "Resource": ["execute-api:/*/*/*"]},
            ],
        }

        self.editor.add_resource_policy(resourcePolicy, "/foo", "123", "prod")
        self.editor.add_custom_statements(resourcePolicy.get("CustomStatements"))

        expected = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Resource": [
                        {"Fn::Sub": ["execute-api:/${__Stage__}/PUT/foo", {"__Stage__": "prod"}]},
                        {"Fn::Sub": ["execute-api:/${__Stage__}/GET/foo", {"__Stage__": "prod"}]},
                    ],
                    "Effect": "Allow",
                    "Principal": {"AWS": ["123456"]},
                },
                {"Action": "execute-api:Invoke", "Resource": ["execute-api:/*/*/*"]},
                {"Action": "execute-api:blah", "Resource": ["execute-api:/*/*/*"]},
            ],
        }

        self.assertEqual(deep_sort_lists(expected), deep_sort_lists(self.editor.swagger[_X_POLICY]))


class TestSwaggerEditor_add_authorization_scopes(TestCase):
    def setUp(self):
        self.api = api = {
            "Auth": {
                "Authorizers": {"MyOtherCognitoAuth": {}, "MyCognitoAuth": {}},
                "DefaultAuthorizer": "MyCognitoAuth",
            }
        }
        self.editor = SwaggerEditor(
            {
                "swagger": "2.0",
                "paths": {
                    "/cognito": {
                        "get": {
                            "x-amazon-apigateway-integration": {
                                "httpMethod": "POST",
                                "type": "aws_proxy",
                                "uri": {
                                    "Fn::Sub": "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${MyFn.Arn}/invocations"
                                },
                            },
                            "security": [],
                            "responses": {},
                        }
                    }
                },
            }
        )

    def test_should_include_auth_scopes_if_defined_with_authorizer(self):
        auth = {"AuthorizationScopes": ["ResourceName/method.scope"], "Authorizer": "MyOtherCognitoAuth"}
        self.editor.add_auth_to_method("/cognito", "get", auth, self.api)
        self.assertEqual(
            [{"MyOtherCognitoAuth": ["ResourceName/method.scope"]}],
            self.editor.swagger["paths"]["/cognito"]["get"]["security"],
        )

    def test_should_include_auth_scopes_with_default_authorizer(self):
        auth = {"AuthorizationScopes": ["ResourceName/method.scope"], "Authorizer": "MyCognitoAuth"}
        self.editor.add_auth_to_method("/cognito", "get", auth, self.api)
        self.assertEqual(
            [{"MyCognitoAuth": ["ResourceName/method.scope"]}],
            self.editor.swagger["paths"]["/cognito"]["get"]["security"],
        )

    def test_should_include_only_specified_authorizer_auth_if_no_scopes_defined(self):
        auth = {"Authorizer": "MyOtherCognitoAuth"}
        self.editor.add_auth_to_method("/cognito", "get", auth, self.api)
        self.assertEqual([{"MyOtherCognitoAuth": []}], self.editor.swagger["paths"]["/cognito"]["get"]["security"])

    def test_should_include_none_if_default_is_overwritte(self):
        auth = {"Authorizer": "NONE"}

        self.editor.add_auth_to_method("/cognito", "get", auth, self.api)
        self.assertEqual([{"NONE": []}], self.editor.swagger["paths"]["/cognito"]["get"]["security"])
