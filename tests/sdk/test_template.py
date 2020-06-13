from unittest import TestCase
from six import assertCountEqual

from samtranslator.sdk.template import SamTemplate
from samtranslator.sdk.resource import SamResource


class TestSamTemplate(TestCase):
    def setUp(self):

        self.template_dict = {
            "Properties": {"c": "d"},
            "Metadata": {"a": "b"},
            "Resources": {
                "Function1": {"Type": "AWS::Serverless::Function", "DependsOn": "SomeOtherResource"},
                "Function2": {"Type": "AWS::Serverless::Function", "a": "b"},
                "Api": {"Type": "AWS::Serverless::Api"},
                "Layer": {"Type": "AWS::Serverless::LayerVersion"},
                "NonSam": {"Type": "AWS::Lambda::Function"},
            },
        }

    def test_iterate_must_yield_sam_resources_only(self):
        template = SamTemplate(self.template_dict)

        expected = [
            ("Function1", {"Type": "AWS::Serverless::Function", "DependsOn": "SomeOtherResource", "Properties": {}}),
            ("Function2", {"Type": "AWS::Serverless::Function", "a": "b", "Properties": {}}),
            ("Api", {"Type": "AWS::Serverless::Api", "Properties": {}}),
            ("Layer", {"Type": "AWS::Serverless::LayerVersion", "Properties": {}}),
        ]

        actual = [(id, resource.to_dict()) for id, resource in template.iterate()]
        assertCountEqual(self, expected, actual)

    def test_iterate_must_filter_by_resource_type(self):

        template = SamTemplate(self.template_dict)

        type = "AWS::Serverless::Function"
        expected = [
            ("Function1", {"Type": "AWS::Serverless::Function", "DependsOn": "SomeOtherResource", "Properties": {}}),
            ("Function2", {"Type": "AWS::Serverless::Function", "a": "b", "Properties": {}}),
        ]

        actual = [(id, resource.to_dict()) for id, resource in template.iterate({type})]
        self.assertEqual(expected, actual)

    def test_iterate_must_filter_by_layers_resource_type(self):
        template = SamTemplate(self.template_dict)

        type = "AWS::Serverless::LayerVersion"
        expected = [("Layer", {"Type": "AWS::Serverless::LayerVersion", "Properties": {}})]

        actual = [(id, resource.to_dict()) for id, resource in template.iterate({type})]
        self.assertEqual(expected, actual)

    def test_iterate_must_not_return_non_sam_resources_with_filter(self):
        template = SamTemplate(self.template_dict)

        type = "AWS::Lambda::Function"
        expected = []

        actual = [(id, resource.to_dict()) for id, resource in template.iterate({type})]
        self.assertEqual(expected, actual)

    def test_iterate_must_filter_with_resource_not_found(self):
        template = SamTemplate(self.template_dict)

        type = "AWS::Serverless::SimpleTable"
        expected = []

        actual = [(id, resource.to_dict()) for id, resource in template.iterate({type})]
        self.assertEqual(expected, actual)

    def test_set_must_add_to_template(self):
        template = SamTemplate(self.template_dict)
        template.set("NewResource", {"Type": "something"})

        # Set would modify the original template dictionary
        self.assertEqual(self.template_dict["Resources"].get("NewResource"), {"Type": "something"})

    def test_set_must_work_with_sam_resource_input(self):
        template = SamTemplate(self.template_dict)
        template.set("NewResource", SamResource({"Type": "something"}))

        # Set would modify the original template dictionary
        self.assertEqual(self.template_dict["Resources"].get("NewResource"), {"Type": "something"})

    def test_get_must_return_resource(self):
        expected = {"Type": "AWS::Serverless::Function", "DependsOn": "SomeOtherResource", "Properties": {}}

        template = SamTemplate(self.template_dict)

        actual = template.get("Function1")
        self.assertIsNotNone(actual)
        self.assertTrue(isinstance(actual, SamResource))
        self.assertEqual(actual.to_dict(), expected)

    def test_get_must_return_none_for_unknown_resource(self):
        template = SamTemplate(self.template_dict)

        actual = template.get("Something")
        self.assertIsNone(actual)

    def test_delete_must_delete_resource(self):
        id = "Function1"
        template = SamTemplate(self.template_dict)

        # Check if it exists
        self.assertIsNotNone(template.get(id))
        # Delete
        template.delete(id)
        # Check that it does not exist
        self.assertIsNone(template.get(id))

    def test_delete_must_skip_resource_not_present(self):
        id = "SomeResource"
        template = SamTemplate(self.template_dict)

        self.assertIsNone(template.get(id))
        template.delete(id)
        self.assertIsNone(template.get(id))

    def test_to_dict_must_not_modify_non_resource_properties(self):
        template = SamTemplate(self.template_dict)

        # Verify that actual references match - Input should be untouched
        self.assertTrue(template.to_dict()["Properties"] is self.template_dict["Properties"])
        self.assertTrue(template.to_dict()["Metadata"] is self.template_dict["Metadata"])
