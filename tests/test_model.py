import pytest

from unittest import TestCase
from mock import Mock, call, ANY
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model import PropertyType, Resource, SamResourceMacro, ResourceTypeResolver
from samtranslator.intrinsics.resource_refs import SupportedResourceReferences
from samtranslator.plugins import LifeCycleEvents


def valid_if_true(value, should_raise=True):
    """Validator that passes if the input is True."""
    if value is True:
        return True

    if should_raise:
        raise TypeError
    return False


class DummyResource(Resource):
    resource_type = "AWS::Dummy::Resource"
    property_types = {
        "RequiredProperty": PropertyType(True, valid_if_true),
        "OptionalProperty": PropertyType(False, valid_if_true),
    }


@pytest.mark.parametrize(
    "logical_id,resource_dict,expected_exception",
    [
        # Valid required property
        ("id", {"Type": "AWS::Dummy::Resource", "Properties": {"RequiredProperty": True}}, None),
        # Valid required property and valid optional property
        (
            "id",
            {"Type": "AWS::Dummy::Resource", "Properties": {"RequiredProperty": True, "OptionalProperty": True}},
            None,
        ),
        # Required property not provided
        ("id", {"Type": "AWS::Dummy::Resource", "Properties": {"OptionalProperty": True}}, InvalidResourceException),
        # Required property provided, but invalid
        ("id", {"Type": "AWS::Dummy::Resource", "Properties": {"RequiredProperty": False}}, InvalidResourceException),
        # Property with invalid name provided
        (
            "id",
            {"Type": "AWS::Dummy::Resource", "Properties": {"RequiredProperty": True, "InvalidProperty": True}},
            InvalidResourceException,
        ),
        # Missing Properties
        ("id", {"Type": "AWS::Other::Other"}, InvalidResourceException),
        # Missing Type
        ("id", {"Properties": {"RequiredProperty": True, "OptionalProperty": True}}, InvalidResourceException),
        # Valid Type with invalid Properties
        ("id", {"Type": "AWS::Dummy::Resource", "Properties": "Invalid"}, InvalidResourceException),
        # Valid Properties with invalid Type
        (
            "id",
            {"Type": "AWS::Invalid::Invalid", "Properties": {"RequiredProperty": True, "OptionalProperty": True}},
            InvalidResourceException,
        ),
        # Invalid logical_id
        (
            "invalid_id",
            {"Type": "AWS::Dummy::Resource", "Properties": {"RequiredProperty": True, "OptionalProperty": True}},
            InvalidResourceException,
        ),
        # intrinsic function
        (
            "id",
            {"Type": "AWS::Dummy::Resource", "Properties": {"RequiredProperty": {"Fn::Any": ["logicalid", "Arn"]}}},
            None,
        ),
    ],
)
def test_resource_type_validation(logical_id, resource_dict, expected_exception):
    if not expected_exception:
        resource = DummyResource.from_dict(logical_id, resource_dict)
        for name, value in resource_dict["Properties"].items():
            assert (
                getattr(resource, name) == value
            ), "resource did not have expected property attribute {property_name} with value {property_value}".format(
                property_name=name, property_value=value
            )

        actual_to_dict = resource.to_dict()
        expected_to_dict = {"id": resource_dict}
        assert (
            actual_to_dict == expected_to_dict
        ), "to_dict() returned different values from what was passed to from_dict(); expected {expected}, got {actual}".format(
            expected=expected_to_dict, actual=actual_to_dict
        )
    else:
        with pytest.raises(expected_exception):
            resource = DummyResource.from_dict(logical_id, resource_dict)


class TestResourceAttributes(TestCase):
    class MyResource(Resource):
        resource_type = "foo"
        property_types = {}

    def test_to_dict(self):
        """Tests if resource attributes are correctly set and converted to dictionary
        """

        empty_resource_dict = {"id": {"Type": "foo", "Properties": {}}}
        dict_with_attributes = {
            "id": {"Type": "foo", "Properties": {}, "UpdatePolicy": "update", "DeletionPolicy": {"foo": "bar"}}
        }

        r = self.MyResource("id")
        self.assertEqual(r.to_dict(), empty_resource_dict)

        r = self.MyResource("id", attributes={"UpdatePolicy": "update", "DeletionPolicy": {"foo": "bar"}})
        self.assertEqual(r.to_dict(), dict_with_attributes)

    def test_invalid_attr(self):

        with pytest.raises(KeyError) as ex:
            # Unsupported attributes cannot be added to the resource
            self.MyResource("id", attributes={"foo": "bar"})

        # But unsupported properties will silently be ignored when deserialization from dictionary
        with_unsupported_attributes = {
            "Type": "foo",
            "Properties": {},
            "DeletionPolicy": "foo",
            "UnsupportedPolicy": "bar",
        }
        r = self.MyResource.from_dict("id", resource_dict=with_unsupported_attributes)
        self.assertEqual(r.get_resource_attribute("DeletionPolicy"), "foo")

        with pytest.raises(KeyError):
            r.get_resource_attribute("UnsupportedPolicy")

    def test_from_dict(self):
        no_attribute = {"Type": "foo", "Properties": {}}
        all_supported_attributes = {
            "Type": "foo",
            "Properties": {},
            "UpdatePolicy": "update",
            "DeletionPolicy": [1, 2, 3],
        }

        r = self.MyResource.from_dict("id", resource_dict=no_attribute)
        self.assertEqual(r.logical_id, "id")  # Just making sure the resource got created

        r = self.MyResource.from_dict("id", resource_dict=all_supported_attributes)
        self.assertEqual(r.get_resource_attribute("DeletionPolicy"), [1, 2, 3])
        self.assertEqual(r.get_resource_attribute("UpdatePolicy"), "update")


class TestResourceRuntimeAttributes(TestCase):
    def test_resource_must_override_runtime_attributes(self):
        class NewResource(Resource):
            resource_type = "foo"
            property_types = {}
            runtime_attrs = {"attr1": Mock(), "attr2": Mock()}

            runtime_attrs["attr1"].return_value = "value1"
            runtime_attrs["attr2"].return_value = "value2"

        logical_id = "SomeId"
        resource = NewResource(logical_id)
        self.assertEqual("value1", resource.get_runtime_attr("attr1"))
        self.assertEqual("value2", resource.get_runtime_attr("attr2"))

        with self.assertRaises(NotImplementedError):
            resource.get_runtime_attr("invalid_attribute")

    def test_resource_default_runtime_attributes(self):
        # There are no attributes by default
        class NewResource(Resource):
            resource_type = "foo"
            property_types = {}

        resource = NewResource("SomeId")
        self.assertEqual(0, len(resource.runtime_attrs))


class TestSamResourceReferableProperties(TestCase):
    class ResourceType1(Resource):
        resource_type = "resource_type1"
        property_types = {}

    class ResourceType2(Resource):
        resource_type = "resource_type2"
        property_types = {}

    class ResourceType3(Resource):
        resource_type = "resource_type3"
        property_types = {}

    def setUp(self):
        self.supported_resource_refs = SupportedResourceReferences()

    def test_must_get_property_for_available_resources(self):
        class NewSamResource(SamResourceMacro):
            resource_type = "foo"
            property_types = {}
            referable_properties = {"prop1": "resource_type1", "prop2": "resource_type2", "prop3": "resource_type3"}

        sam_resource = NewSamResource("SamLogicalId")

        cfn_resources = [self.ResourceType1("logicalId1"), self.ResourceType2("logicalId2")]

        self.supported_resource_refs = sam_resource.get_resource_references(cfn_resources, self.supported_resource_refs)

        self.assertEqual("logicalId1", self.supported_resource_refs.get("SamLogicalId", "prop1"))
        self.assertEqual("logicalId2", self.supported_resource_refs.get("SamLogicalId", "prop2"))

        # there is no cfn resource of for "prop3" in the cfn_resources list
        self.assertEqual(None, self.supported_resource_refs.get("SamLogicalId", "prop3"))

        # Must add only for the given SAM resource
        self.assertEqual(1, len(self.supported_resource_refs))

    def test_must_work_with_two_resources_of_same_type(self):
        class NewSamResource(SamResourceMacro):
            resource_type = "foo"
            property_types = {}
            referable_properties = {"prop1": "resource_type1", "prop2": "resource_type2", "prop3": "resource_type3"}

        sam_resource1 = NewSamResource("SamLogicalId1")
        sam_resource2 = NewSamResource("SamLogicalId2")

        cfn_resources = [self.ResourceType1("logicalId1"), self.ResourceType2("logicalId2")]

        self.supported_resource_refs = sam_resource1.get_resource_references(
            cfn_resources, self.supported_resource_refs
        )

        self.supported_resource_refs = sam_resource2.get_resource_references(
            cfn_resources, self.supported_resource_refs
        )

        self.assertEqual("logicalId1", self.supported_resource_refs.get("SamLogicalId1", "prop1"))
        self.assertEqual("logicalId2", self.supported_resource_refs.get("SamLogicalId1", "prop2"))
        self.assertEqual("logicalId1", self.supported_resource_refs.get("SamLogicalId2", "prop1"))
        self.assertEqual("logicalId2", self.supported_resource_refs.get("SamLogicalId2", "prop2"))

        self.assertEqual(2, len(self.supported_resource_refs))

    def test_must_skip_unknown_resource_types(self):
        class NewSamResource(SamResourceMacro):
            resource_type = "foo"
            property_types = {}
            referable_properties = {"prop1": "foo", "prop2": "bar"}

        sam_resource = NewSamResource("SamLogicalId")

        # None of the CFN resource types are in the referable list
        cfn_resources = [self.ResourceType1("logicalId1"), self.ResourceType2("logicalId2")]

        self.supported_resource_refs = sam_resource.get_resource_references(cfn_resources, self.supported_resource_refs)

        self.assertEqual(0, len(self.supported_resource_refs))

    def test_must_skip_if_no_supported_properties(self):
        class NewSamResource(SamResourceMacro):
            resource_type = "foo"
            property_types = {}
            referable_properties = {}

        sam_resource = NewSamResource("SamLogicalId")

        cfn_resources = [self.ResourceType1("logicalId1"), self.ResourceType2("logicalId2")]

        self.supported_resource_refs = sam_resource.get_resource_references(cfn_resources, self.supported_resource_refs)

        self.assertEqual(0, len(self.supported_resource_refs))

    def test_must_skip_if_no_resources(self):
        class NewSamResource(SamResourceMacro):
            resource_type = "foo"
            property_types = {}
            referable_properties = {"prop1": "resource_type1"}

        sam_resource = NewSamResource("SamLogicalId")

        cfn_resources = []

        self.supported_resource_refs = sam_resource.get_resource_references(cfn_resources, self.supported_resource_refs)

        self.assertEqual(0, len(self.supported_resource_refs))

    def test_must_raise_if_input_is_absent(self):
        class NewSamResource(SamResourceMacro):
            resource_type = "foo"
            property_types = {}
            referable_properties = {"prop1": "resource_type1"}

        sam_resource = NewSamResource("SamLogicalId")

        cfn_resources = [self.ResourceType1("logicalId1")]

        with self.assertRaises(ValueError):
            sam_resource.get_resource_references(cfn_resources, None)


class TestResourceTypeResolver(TestCase):
    def test_can_resolve_must_handle_null_resource_dict(self):
        resolver = ResourceTypeResolver()

        self.assertFalse(resolver.can_resolve(None))

    def test_can_resolve_must_handle_non_dict(self):
        resolver = ResourceTypeResolver()

        self.assertFalse(resolver.can_resolve("some string value"))

    def test_can_resolve_must_handle_dict_without_type(self):
        resolver = ResourceTypeResolver()

        self.assertFalse(resolver.can_resolve({"a": "b"}))

    def test_can_resolve_must_handle_known_types(self):
        resolver = ResourceTypeResolver()
        resolver.resource_types = {"type1": DummyResource("id")}

        self.assertTrue(resolver.can_resolve({"Type": "type1"}))

    def test_can_resolve_must_handle_unknown_types(self):
        resolver = ResourceTypeResolver()
        resolver.resource_types = {"type1": DummyResource("id")}

        self.assertFalse(resolver.can_resolve({"Type": "AWS::Lambda::Function"}))


class TestSamPluginsInResource(TestCase):
    def test_must_act_on_plugins_before_resource_creation(self):
        resource_type = "AWS::Dummy::Resource"
        resource_dict = {"Type": resource_type, "Properties": {"RequiredProperty": True}}
        expected_properties = {"RequiredProperty": True}

        mock_sam_plugins = Mock()
        DummyResource.from_dict("logicalId", resource_dict, sam_plugins=mock_sam_plugins)

        mock_sam_plugins.act.assert_called_once_with(
            LifeCycleEvents.before_transform_resource, "logicalId", resource_type, expected_properties
        )

    def test_must_act_on_plugins_for_resource_having_no_properties(self):
        resource_type = "MyResourceType"

        class MyResource(Resource):
            property_types = {}
            resource_type = "MyResourceType"

        # No Properties for this resource
        resource_dict = {"Type": resource_type}
        expected_properties = {}

        mock_sam_plugins = Mock()
        MyResource.from_dict("logicalId", resource_dict, sam_plugins=mock_sam_plugins)

        mock_sam_plugins.act.assert_called_once_with(
            LifeCycleEvents.before_transform_resource, "logicalId", resource_type, expected_properties
        )
