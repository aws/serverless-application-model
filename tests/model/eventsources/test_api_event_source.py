from mock import Mock, patch
from unittest import TestCase

from samtranslator.model.eventsources.push import Api
from samtranslator.model.lambda_ import LambdaFunction, LambdaPermission


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

    @patch("boto3.session.Session.region_name", "eu-west-2")
    def test_get_permission_without_trailing_slash(self):
        cfn = self.api_event_source.to_cloudformation(function=self.func, explicit_api={})

        perm = cfn[0]
        self.assertIsInstance(perm, LambdaPermission)

        try:
            arn = self._extract_path_from_arn("{}PermissionProd".format(self.logical_id), perm)
        except AttributeError:
            self.fail("Permission class isn't valid")

        self.assertEqual(arn, "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${__ApiId__}/${__Stage__}/GET/foo")

    @patch("boto3.session.Session.region_name", "eu-west-2")
    def test_get_permission_with_trailing_slash(self):
        self.api_event_source.Path = "/foo/"
        cfn = self.api_event_source.to_cloudformation(function=self.func, explicit_api={})

        perm = cfn[0]
        self.assertIsInstance(perm, LambdaPermission)

        try:
            arn = self._extract_path_from_arn("{}PermissionProd".format(self.logical_id), perm)
        except AttributeError:
            self.fail("Permission class isn't valid")

        self.assertEqual(arn, "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${__ApiId__}/${__Stage__}/GET/foo")

    @patch("boto3.session.Session.region_name", "eu-west-2")
    def test_get_permission_with_path_parameter_to_any_path(self):
        self.api_event_source.Path = "/foo/{userId+}"
        cfn = self.api_event_source.to_cloudformation(function=self.func, explicit_api={})

        perm = cfn[0]
        self.assertIsInstance(perm, LambdaPermission)

        try:
            arn = self._extract_path_from_arn("{}PermissionProd".format(self.logical_id), perm)
        except AttributeError:
            self.fail("Permission class isn't valid")

        self.assertEqual(
            arn, "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${__ApiId__}/${__Stage__}/GET/foo/*"
        )

    @patch("boto3.session.Session.region_name", "eu-west-2")
    def test_get_permission_with_path_parameter(self):
        self.api_event_source.Path = "/foo/{userId}/bar"
        cfn = self.api_event_source.to_cloudformation(function=self.func, explicit_api={})

        perm = cfn[0]
        self.assertIsInstance(perm, LambdaPermission)

        try:
            arn = self._extract_path_from_arn("{}PermissionProd".format(self.logical_id), perm)
        except AttributeError:
            self.fail("Permission class isn't valid")

        self.assertEqual(
            arn, "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${__ApiId__}/${__Stage__}/GET/foo/*/bar"
        )

    @patch("boto3.session.Session.region_name", "eu-west-2")
    def test_get_permission_with_proxy_resource(self):
        self.api_event_source.Path = "/foo/{proxy+}"
        cfn = self.api_event_source.to_cloudformation(function=self.func, explicit_api={})

        perm = cfn[0]
        self.assertIsInstance(perm, LambdaPermission)

        try:
            arn = self._extract_path_from_arn("{}PermissionProd".format(self.logical_id), perm)
        except AttributeError:
            self.fail("Permission class isn't valid")

        self.assertEqual(
            arn, "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${__ApiId__}/${__Stage__}/GET/foo/*"
        )

    @patch("boto3.session.Session.region_name", "eu-west-2")
    def test_get_permission_with_just_slash(self):
        self.api_event_source.Path = "/"
        cfn = self.api_event_source.to_cloudformation(function=self.func, explicit_api={})

        perm = cfn[0]
        self.assertIsInstance(perm, LambdaPermission)

        try:
            arn = self._extract_path_from_arn("{}PermissionProd".format(self.logical_id), perm)
        except AttributeError:
            self.fail("Permission class isn't valid")

        self.assertEqual(arn, "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${__ApiId__}/${__Stage__}/GET/")

    def _extract_path_from_arn(self, logical_id, perm):
        arn = perm.to_dict().get(logical_id, {}).get("Properties", {}).get("SourceArn", {}).get("Fn::Sub", [])[0]

        if arn is None:
            raise AttributeError("Arn not found")

        return arn
