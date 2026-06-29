from unittest import TestCase
from unittest.mock import MagicMock

from samtranslator.translator.verify_logical_id import do_not_verify, verify_unique_logical_id


def _make_resource(logical_id, resource_type):
    r = MagicMock()
    r.logical_id = logical_id
    r.resource_type = resource_type
    return r


class TestDoNotVerifyDict(TestCase):
    def test_all_values_are_lists(self):
        for key, value in do_not_verify.items():
            self.assertIsInstance(value, list, f"do_not_verify['{key}'] must be a list, got {type(value)}")

    def test_no_substring_bypass(self):
        # A crafted type that is a substring of a real allowed type must NOT match.
        # Before the fix, "AWS::Serverless::Fun" in "AWS::Serverless::Function" was True.
        resource = _make_resource("MyFunc", "AWS::Lambda::Function")
        existing = {"MyFunc": {"Type": "AWS::Serverless::Fun"}}  # substring, not exact

        result = verify_unique_logical_id(resource, existing)
        self.assertFalse(result, "Substring of an allowed type must not bypass the uniqueness check")

    def test_no_superstring_bypass(self):
        # A type that contains an allowed type as a substring must NOT match.
        resource = _make_resource("MyFunc", "AWS::Lambda::Function")
        existing = {"MyFunc": {"Type": "AWS::Serverless::FunctionExtra"}}

        result = verify_unique_logical_id(resource, existing)
        self.assertFalse(result, "Superstring of an allowed type must not bypass the uniqueness check")


class TestVerifyUniqueLogicalId(TestCase):
    def test_new_logical_id_is_unique(self):
        resource = _make_resource("NewFunc", "AWS::Lambda::Function")
        existing = {}
        self.assertTrue(verify_unique_logical_id(resource, existing))

    def test_none_logical_id_is_unique(self):
        resource = _make_resource(None, "AWS::Lambda::Function")
        self.assertTrue(verify_unique_logical_id(resource, {}))

    def test_allowed_transform_returns_true(self):
        resource = _make_resource("MyFunc", "AWS::Lambda::Function")
        existing = {"MyFunc": {"Type": "AWS::Serverless::Function"}}
        self.assertTrue(verify_unique_logical_id(resource, existing))

    def test_allowed_transform_multi_value_returns_true(self):
        resource = _make_resource("MyApi", "AWS::ApiGatewayV2::Api")
        existing = {"MyApi": {"Type": "AWS::Serverless::HttpApi"}}
        self.assertTrue(verify_unique_logical_id(resource, existing))

        existing2 = {"MyApi": {"Type": "AWS::Serverless::WebSocketApi"}}
        self.assertTrue(verify_unique_logical_id(resource, existing2))

    def test_disallowed_type_collision_returns_false(self):
        resource = _make_resource("MyBucket", "AWS::Lambda::Function")
        existing = {"MyBucket": {"Type": "AWS::S3::Bucket"}}
        self.assertFalse(verify_unique_logical_id(resource, existing))

    def test_unknown_resource_type_returns_false(self):
        resource = _make_resource("SomeId", "AWS::Custom::Unknown")
        existing = {"SomeId": {"Type": "AWS::Custom::Something"}}
        self.assertFalse(verify_unique_logical_id(resource, existing))
