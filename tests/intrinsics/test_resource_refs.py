from unittest import TestCase
from samtranslator.intrinsics.resource_refs import SupportedResourceReferences


class TestSupportedResourceReferences(TestCase):
    def test_add_multiple_properties_to_one_logicalId(self):

        resource_refs = SupportedResourceReferences()

        resource_refs.add("logicalId", "property1", "value1")
        resource_refs.add("logicalId", "property2", "value2")
        resource_refs.add("logicalId", "property3", "value3")

        expected = {"property1": "value1", "property2": "value2", "property3": "value3"}

        self.assertEqual(expected, resource_refs.get_all("logicalId"))

    def test_add_multiple_logical_ids(self):
        resource_refs = SupportedResourceReferences()

        resource_refs.add("logicalId1", "property1", "value1")
        resource_refs.add("logicalId2", "property2", "value2")
        resource_refs.add("logicalId3", "property3", "value3")

        self.assertEqual({"property1": "value1"}, resource_refs.get_all("logicalId1"))
        self.assertEqual({"property2": "value2"}, resource_refs.get_all("logicalId2"))
        self.assertEqual({"property3": "value3"}, resource_refs.get_all("logicalId3"))

    def test_add_must_error_on_duplicate_value(self):

        resource_refs = SupportedResourceReferences()

        resource_refs.add("logicalId", "property", "value1")

        with self.assertRaises(ValueError):
            resource_refs.add("logicalId", "property", "value2")

    def test_add_must_error_if_value_is_empty(self):
        resource_refs = SupportedResourceReferences()
        with self.assertRaises(ValueError):
            resource_refs.add("logicalId", "property", "")

    def test_add_must_error_if_value_is_not_string(self):
        resource_refs = SupportedResourceReferences()
        with self.assertRaises(ValueError):
            resource_refs.add("logicalId", "property", {"a": "b"})

    def test_add_must_error_when_logicalId_is_absent(self):
        resource_refs = SupportedResourceReferences()
        with self.assertRaises(ValueError):
            resource_refs.add("", "property", "value1")

    def test_add_must_error_when_property_is_absent(self):
        resource_refs = SupportedResourceReferences()
        with self.assertRaises(ValueError):
            resource_refs.add("logicalId", "", "value1")

    def test_get_all_on_non_existent_logical_id(self):
        resource_refs = SupportedResourceReferences()

        resource_refs.add("logicalId", "property", "value1")

        self.assertEqual(None, resource_refs.get_all("some logical id"))

    def test_get_must_return_correct_value(self):
        resource_refs = SupportedResourceReferences()

        resource_refs.add("logicalId1", "property1", "value1")
        resource_refs.add("logicalId1", "property2", "value2")
        resource_refs.add("newLogicalId", "newProperty", "newValue")

        self.assertEqual("value1", resource_refs.get("logicalId1", "property1"))
        self.assertEqual("value2", resource_refs.get("logicalId1", "property2"))
        self.assertEqual("newValue", resource_refs.get("newLogicalId", "newProperty"))

    def test_get_on_non_existent_property(self):
        resource_refs = SupportedResourceReferences()

        resource_refs.add("logicalId1", "property1", "value1")
        self.assertEqual(None, resource_refs.get("logicalId1", "SomeProperty"))
        self.assertEqual(None, resource_refs.get("SomeLogicalId", "property1"))

    def test_len_single_resource(self):
        resource_refs = SupportedResourceReferences()

        resource_refs.add("logicalId1", "property1", "value1")
        resource_refs.add("logicalId1", "property2", "value2")
        self.assertEqual(1, len(resource_refs))  # Each unique logicalId adds one to the len

    def test_len_multiple_resources(self):
        resource_refs = SupportedResourceReferences()

        resource_refs.add("logicalId1", "property1", "value1")
        resource_refs.add("logicalId2", "property2", "value2")
        self.assertEqual(2, len(resource_refs))
