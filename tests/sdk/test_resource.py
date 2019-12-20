from unittest import TestCase

from samtranslator.sdk.resource import SamResource, SamResourceType


class TestSamResource(TestCase):
    def setUp(self):
        self.function_dict = {"Type": "AWS::Serverless::Function", "Properties": {"a": "b"}}

        self.api_dict = {"Type": "AWS::Serverless::Api", "Properties": {"a": "b"}}

        self.simple_table_dict = {"Type": "AWS::Serverless::SimpleTable", "Properties": {"a": "b"}}

    def test_init_must_extract_type_and_properties(self):
        resource_dict = {"Type": "foo", "Properties": {"a": "b"}}

        resource = SamResource(resource_dict)
        self.assertEqual(resource.type, "foo")
        self.assertEqual(resource.properties, {"a": "b"})

    def test_init_must_default_to_empty_properties_dict(self):
        resource_dict = {
            "Type": "foo"
            # Properties is missing
        }

        resource = SamResource(resource_dict)
        self.assertEqual(resource.properties, {})

    def test_valid_must_validate_sam_resources_only(self):
        self.assertTrue(SamResource({"Type": "AWS::Serverless::Api"}).valid())
        self.assertTrue(SamResource({"Type": "AWS::Serverless::Function"}).valid())
        self.assertTrue(SamResource({"Type": "AWS::Serverless::SimpleTable"}).valid())

        self.assertFalse(SamResource({"Type": "AWS::Lambda::Function"}).valid())

    def test_valid_must_not_work_with_resource_without_type(self):
        self.assertFalse(SamResource({"a": "b"}).valid())

    def test_to_dict_must_update_type_and_properties(self):
        resource_dict = {"Type": "AWS::Serverless::Function", "Properties": {"a": "b"}}

        resource = SamResource(resource_dict)
        resource.type = "AWS::Serverless::Api"
        resource.properties = {"c": "d"}

        self.assertEqual(resource.to_dict(), {"Type": "AWS::Serverless::Api", "Properties": {"c": "d"}})

        # Calling to_dict() has side effect of updating the original dictionary
        self.assertEqual(resource_dict, {"Type": "AWS::Serverless::Api", "Properties": {"c": "d"}})


class TestSamResourceTypeEnum(TestCase):
    def test_contains_sam_resources(self):
        self.assertEqual(SamResourceType.Function.value, "AWS::Serverless::Function")
        self.assertEqual(SamResourceType.Api.value, "AWS::Serverless::Api")
        self.assertEqual(SamResourceType.SimpleTable.value, "AWS::Serverless::SimpleTable")

    def test_has_value_must_work_for_sam_types(self):

        self.assertTrue(SamResourceType.has_value("AWS::Serverless::Function"))
        self.assertTrue(SamResourceType.has_value("AWS::Serverless::Api"))
        self.assertTrue(SamResourceType.has_value("AWS::Serverless::SimpleTable"))

        self.assertFalse(SamResourceType.has_value("AWS::Lambda::Function"))
