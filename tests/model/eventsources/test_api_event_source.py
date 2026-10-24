from unittest import TestCase
from unittest.mock import Mock, patch

from parameterized import parameterized
from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.model.eventsources.push import Api
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.lambda_ import LambdaFunction, LambdaPermission
from samtranslator.swagger.swagger import SwaggerEditor


class ApiEventSource(TestCase):
    def setUp(self):
        self.logical_id = "Api"

        self.api_event_source = Api(self.logical_id)
        self.api_event_source.Path = "/foo"
        self.api_event_source.Method = "GET"
        self.api_event_source.RestApiId = "abc123"

        self.permission = Mock()
        self.permission.logicial_id = "ApiPermission"

        self.func = LambdaFunction("func")

        self.stage = "Prod"
        self.suffix = "123"
        self.kwargs = {
            "function": self.func,
            "explicit_api": {},
            "api_id": "RestApi",
            "intrinsics_resolver": IntrinsicsResolver({}),
        }

    @patch("boto3.session.Session.region_name", "eu-west-2")
    def test_get_permission_without_trailing_slash(self):
        cfn = self.api_event_source.to_cloudformation(**self.kwargs)

        perm = cfn[0]
        self.assertIsInstance(perm, LambdaPermission)

        try:
            arn = self._extract_path_from_arn(f"{self.logical_id}PermissionProd", perm)
        except AttributeError:
            self.fail("Permission class isn't valid")

        self.assertEqual(arn, "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${__ApiId__}/${__Stage__}/GET/foo")

    @patch("boto3.session.Session.region_name", "eu-west-2")
    def test_get_permission_with_trailing_slash(self):
        self.api_event_source.Path = "/foo/"
        cfn = self.api_event_source.to_cloudformation(**self.kwargs)

        perm = cfn[0]
        self.assertIsInstance(perm, LambdaPermission)

        try:
            arn = self._extract_path_from_arn(f"{self.logical_id}PermissionProd", perm)
        except AttributeError:
            self.fail("Permission class isn't valid")

        self.assertEqual(arn, "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${__ApiId__}/${__Stage__}/GET/foo")

    @patch("boto3.session.Session.region_name", "eu-west-2")
    def test_get_permission_with_path_parameter_to_any_path(self):
        self.api_event_source.Path = "/foo/{userId+}"
        cfn = self.api_event_source.to_cloudformation(**self.kwargs)

        perm = cfn[0]
        self.assertIsInstance(perm, LambdaPermission)

        try:
            arn = self._extract_path_from_arn(f"{self.logical_id}PermissionProd", perm)
        except AttributeError:
            self.fail("Permission class isn't valid")

        self.assertEqual(
            arn, "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${__ApiId__}/${__Stage__}/GET/foo/*"
        )

    @patch("boto3.session.Session.region_name", "eu-west-2")
    def test_get_permission_with_path_parameter(self):
        self.api_event_source.Path = "/foo/{userId}/bar"
        cfn = self.api_event_source.to_cloudformation(**self.kwargs)

        perm = cfn[0]
        self.assertIsInstance(perm, LambdaPermission)

        try:
            arn = self._extract_path_from_arn(f"{self.logical_id}PermissionProd", perm)
        except AttributeError:
            self.fail("Permission class isn't valid")

        self.assertEqual(
            arn, "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${__ApiId__}/${__Stage__}/GET/foo/*/bar"
        )

    @patch("boto3.session.Session.region_name", "eu-west-2")
    def test_get_permission_with_proxy_resource(self):
        self.api_event_source.Path = "/foo/{proxy+}"
        cfn = self.api_event_source.to_cloudformation(**self.kwargs)

        perm = cfn[0]
        self.assertIsInstance(perm, LambdaPermission)

        try:
            arn = self._extract_path_from_arn(f"{self.logical_id}PermissionProd", perm)
        except AttributeError:
            self.fail("Permission class isn't valid")

        self.assertEqual(
            arn, "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${__ApiId__}/${__Stage__}/GET/foo/*"
        )

    @patch("boto3.session.Session.region_name", "eu-west-2")
    def test_get_permission_with_just_slash(self):
        self.api_event_source.Path = "/"
        cfn = self.api_event_source.to_cloudformation(**self.kwargs)

        perm = cfn[0]
        self.assertIsInstance(perm, LambdaPermission)

        try:
            arn = self._extract_path_from_arn(f"{self.logical_id}PermissionProd", perm)
        except AttributeError:
            self.fail("Permission class isn't valid")

        self.assertEqual(arn, "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${__ApiId__}/${__Stage__}/GET/")

    @parameterized.expand(
        [(method, paths) for method in ("get", "any") for paths in ({}, {"paths": None}, {"paths": {}})]
    )
    def test_merge_definitions_keeps_generated_path(self, method, paths):
        self.api_event_source.Method = method
        editor = SwaggerEditor(SwaggerEditor.gen_skeleton())
        editor.add_lambda_integration("/foo", method, "lambda-uri", {}, {})

        merged = self.api_event_source._get_merged_definitions("RestApi", {"swagger": "2.0", **paths}, editor)

        self.assertEqual(merged["paths"], editor.swagger["paths"])

    @parameterized.expand([("get", "get"), ("any", "x-amazon-apigateway-any-method")])
    def test_merge_definitions_preserves_inline_method_fields(self, method, method_key):
        self.api_event_source.Method = method
        editor = SwaggerEditor(SwaggerEditor.gen_skeleton())
        editor.add_lambda_integration("/foo", method, "lambda-uri", {}, {})
        source = {
            "swagger": "2.0",
            "paths": {
                "/foo": {
                    method_key: {
                        "summary": "Inline operation",
                        "x-amazon-apigateway-integration": {"type": "http_proxy", "uri": "https://example.com"},
                    },
                    "post": {"summary": "Other method"},
                },
                "/other": {"get": {"summary": "Other path"}},
            },
        }

        merged = self.api_event_source._get_merged_definitions("RestApi", source, editor)

        self.assertEqual(set(merged["paths"]["/foo"]), {method_key, "post"})
        self.assertEqual(
            merged["paths"]["/foo"][method_key],
            {"summary": "Inline operation", **editor.swagger["paths"]["/foo"][method_key]},
        )
        self.assertEqual(merged["paths"]["/foo"]["post"], {"summary": "Other method"})
        self.assertEqual(merged["paths"]["/other"], {"get": {"summary": "Other path"}})

    def test_merge_definitions_rejects_invalid_inline_any_method(self):
        self.api_event_source.Method = "any"
        editor = SwaggerEditor(SwaggerEditor.gen_skeleton())
        editor.add_lambda_integration("/foo", "any", "lambda-uri", {}, {})
        source = {"swagger": "2.0", "paths": {"/foo": {"x-amazon-apigateway-any-method": "invalid"}}}

        with self.assertRaisesRegex(
            InvalidResourceException, r"DefinitionBody.paths./foo.x-amazon-apigateway-any-method"
        ):
            self.api_event_source._get_merged_definitions("RestApi", source, editor)

    def _extract_path_from_arn(self, logical_id, perm):
        arn = perm.to_dict().get(logical_id, {}).get("Properties", {}).get("SourceArn", {}).get("Fn::Sub", [])[0]

        if arn is None:
            raise AttributeError("Arn not found")

        return arn
