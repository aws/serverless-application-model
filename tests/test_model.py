from typing import Any, List, Optional
from unittest import TestCase
from unittest.mock import Mock

import pytest
from parameterized import parameterized
from samtranslator.internal.schema_source.common import BaseModel
from samtranslator.intrinsics.resource_refs import SupportedResourceReferences
from samtranslator.model import PropertyType, Resource, ResourceTypeResolver, SamResourceMacro
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.types import IS_BOOL, IS_DICT, IS_INT, IS_STR
from samtranslator.plugins import LifeCycleEvents
from samtranslator.validator.property_rule import PropertyRules


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
            ), f"resource did not have expected property attribute {name} with value {value}"

        actual_to_dict = resource.to_dict()
        expected_to_dict = {"id": resource_dict}
        assert (
            actual_to_dict == expected_to_dict
        ), f"to_dict() returned different values from what was passed to from_dict(); expected {expected_to_dict}, got {actual_to_dict}"
    else:
        with pytest.raises(expected_exception):
            resource = DummyResource.from_dict(logical_id, resource_dict)


class TestResourceAttributes(TestCase):
    class MyResource(Resource):
        resource_type = "foo"
        property_types = {}

    def test_to_dict(self):
        """Tests if resource attributes are correctly set and converted to dictionary"""

        empty_resource_dict = {"id": {"Type": "foo", "Properties": {}}}
        dict_with_attributes = {
            "id": {"Type": "foo", "Properties": {}, "UpdatePolicy": "update", "DeletionPolicy": {"foo": "bar"}}
        }
        dict_with_attributes2 = {
            "id": {
                "Type": "foo",
                "Properties": {},
                "UpdateReplacePolicy": "update",
                "Metadata": {"foo": "bar"},
                "Condition": "con",
            }
        }

        r = self.MyResource("id")
        self.assertEqual(r.to_dict(), empty_resource_dict)

        r = self.MyResource("id", attributes={"UpdatePolicy": "update", "DeletionPolicy": {"foo": "bar"}})
        self.assertEqual(r.to_dict(), dict_with_attributes)

        r = self.MyResource(
            "id", attributes={"UpdateReplacePolicy": "update", "Metadata": {"foo": "bar"}, "Condition": "con"}
        )
        self.assertEqual(r.to_dict(), dict_with_attributes2)

    def test_invalid_attr(self):
        with pytest.raises(KeyError):
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
            "UpdateReplacePolicy": "update",
            "Metadata": {"foo": "bar"},
            "Condition": "con",
        }

        r = self.MyResource.from_dict("id", resource_dict=no_attribute)
        self.assertEqual(r.logical_id, "id")  # Just making sure the resource got created

        r = self.MyResource.from_dict("id", resource_dict=all_supported_attributes)
        self.assertEqual(r.get_resource_attribute("DeletionPolicy"), [1, 2, 3])
        self.assertEqual(r.get_resource_attribute("UpdatePolicy"), "update")
        self.assertEqual(r.get_resource_attribute("UpdateReplacePolicy"), "update")
        self.assertEqual(r.get_resource_attribute("Metadata"), {"foo": "bar"})
        self.assertEqual(r.get_resource_attribute("Condition"), "con")


class TestResourceRuntimeAttributes(TestCase):
    def test_resource_must_override_runtime_attributes(self):
        class NewResource(Resource):
            resource_type = "foo"
            property_types = {}

            mock_attr1 = Mock()
            mock_attr2 = Mock()
            mock_attr1.return_value = "value1"
            mock_attr2.return_value = "value2"

            runtime_attrs = {"attr1": mock_attr1, "attr2": mock_attr2}

        logical_id = "SomeId"
        resource = NewResource(logical_id)
        self.assertEqual("value1", resource.get_runtime_attr("attr1"))
        self.assertEqual("value2", resource.get_runtime_attr("attr2"))

        with self.assertRaises(KeyError):
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

            def to_cloudformation(self, **kwargs: Any) -> List[Any]:
                return []

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

            def to_cloudformation(self, **kwargs: Any) -> List[Any]:
                return []

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

            def to_cloudformation(self, **kwargs: Any) -> List[Any]:
                return []

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

            def to_cloudformation(self, **kwargs: Any) -> List[Any]:
                return []

        sam_resource = NewSamResource("SamLogicalId")

        cfn_resources = [self.ResourceType1("logicalId1"), self.ResourceType2("logicalId2")]

        self.supported_resource_refs = sam_resource.get_resource_references(cfn_resources, self.supported_resource_refs)

        self.assertEqual(0, len(self.supported_resource_refs))

    def test_must_skip_if_no_resources(self):
        class NewSamResource(SamResourceMacro):
            resource_type = "foo"
            property_types = {}
            referable_properties = {"prop1": "resource_type1"}

            def to_cloudformation(self, **kwargs: Any) -> List[Any]:
                return []

        sam_resource = NewSamResource("SamLogicalId")

        cfn_resources = []

        self.supported_resource_refs = sam_resource.get_resource_references(cfn_resources, self.supported_resource_refs)

        self.assertEqual(0, len(self.supported_resource_refs))

    def test_must_raise_if_input_is_absent(self):
        class NewSamResource(SamResourceMacro):
            resource_type = "foo"
            property_types = {}
            referable_properties = {"prop1": "resource_type1"}

            def to_cloudformation(self, **kwargs: Any) -> List[Any]:
                return []

        sam_resource = NewSamResource("SamLogicalId")

        cfn_resources = [self.ResourceType1("logicalId1")]

        with self.assertRaises(ValueError):
            sam_resource.get_resource_references(cfn_resources, None)


class TestResourceTypeResolver(TestCase):
    def test_can_resolve_must_handle_null_resource_dict(self):
        resolver = ResourceTypeResolver()

        self.assertFalse(resolver.can_resolve(None))  # type: ignore[arg-type]

    def test_can_resolve_must_handle_non_dict(self):
        resolver = ResourceTypeResolver()

        self.assertFalse(resolver.can_resolve("some string value"))  # type: ignore[arg-type]

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


# Restructured test classes for better organization
class SamResourceMacroTestBase:
    """Shared test fixtures for SamResourceMacro tests"""

    @classmethod
    def setup_test_fixtures(cls):
        """Set up common test fixtures"""

        class TestSettingProperties(BaseModel):
            NestedVar1: Optional[str] = None
            NestedVar2: Optional[str] = None

        class TestProperties(BaseModel):
            ConditionalVar1: Optional[int] = None
            ConditionalVar2: Optional[int] = None
            ConditionalVar3: Optional[int] = None
            ExclusiveVar1: Optional[str] = None
            ExclusiveVar2: Optional[str] = None
            ExclusiveVar3: Optional[str] = None
            InclusiveVar1: Optional[bool] = None
            InclusiveVar2: Optional[bool] = None
            InclusiveVar3: Optional[bool] = None
            NestedSetting1: Optional[TestSettingProperties] = None
            NestedSetting2: Optional[TestSettingProperties] = None
            NestedSetting3: Optional[TestSettingProperties] = None

        class TestResource(SamResourceMacro):
            resource_type = "Test::Resource"
            property_types = {
                "ConditionalVar1": PropertyType(False, IS_INT),
                "ConditionalVar2": PropertyType(False, IS_INT),
                "ConditionalVar3": PropertyType(False, IS_INT),
                "ExclusiveVar1": PropertyType(False, IS_STR),
                "ExclusiveVar2": PropertyType(False, IS_STR),
                "ExclusiveVar3": PropertyType(False, IS_STR),
                "InclusiveVar1": PropertyType(False, IS_BOOL),
                "InclusiveVar2": PropertyType(False, IS_BOOL),
                "InclusiveVar3": PropertyType(False, IS_BOOL),
                "NestedSetting1": PropertyType(False, IS_DICT),
                "NestedSetting2": PropertyType(False, IS_DICT),
                "NestedSetting3": PropertyType(False, IS_DICT),
            }

            def to_cloudformation(self, **kwargs):
                return []

        return TestProperties, TestSettingProperties, TestResource


class TestSamResourceMacroValidation(TestCase):
    """Test validate_before_transform functionality with restructured approach"""

    def setUp(self):
        self.TestProperties, self.TestSettingProperties, self.TestResource = (
            SamResourceMacroTestBase.setup_test_fixtures()
        )

    def test_validate_before_transform_simple_rules_pass(self):
        """Test successful validation with simple rules"""

        class Resource(self.TestResource):
            def get_property_validation_rules(self):
                return (
                    PropertyRules()
                    .addConditionalInclusive("ConditionalVar1", ["ConditionalVar2"])
                    .addMutuallyExclusive("ExclusiveVar1", "ExclusiveVar2")
                    .addMutuallyInclusive("InclusiveVar1", "InclusiveVar2")
                )

        resource = Resource("TestId")
        resource.ConditionalVar1 = 1
        resource.ConditionalVar2 = 2
        resource.ExclusiveVar1 = "value1"
        resource.InclusiveVar1 = True
        resource.InclusiveVar2 = True

        # Should not raise exception
        resource.validate_before_transform(self.TestProperties)

    def test_validate_before_transform_complex_rules_pass(self):
        """Test successful validation when all rules are satisfied"""

        class Resource(self.TestResource):
            def get_property_validation_rules(self):
                return (
                    PropertyRules()
                    .addConditionalInclusive("ConditionalVar1", ["ConditionalVar2"])
                    .addConditionalInclusive("ConditionalVar2", ["ConditionalVar3"])
                    .addConditionalInclusive("NestedSetting1.NestedVar1", ["NestedSetting2.NestedVar2"])
                    .addMutuallyExclusive("ExclusiveVar1", "ExclusiveVar2")
                    .addMutuallyExclusive("ExclusiveVar2", "ExclusiveVar3")
                    .addMutuallyExclusive("NestedSetting1.NestedVar1", "NestedSetting2.NestedVar1")
                    .addMutuallyExclusive("NestedSetting1.NestedVar2", "ExclusiveVar3")
                    .addMutuallyInclusive("InclusiveVar1", "ExclusiveVar1")
                    .addMutuallyInclusive("NestedSetting1.NestedVar1", "NestedSetting2.NestedVar2")
                    .addMutuallyInclusive("NestedSetting2.NestedVar2", "NestedSetting3.NestedVar2")
                )

        resource = Resource("TestId")

        # Happy case: All rules satisfied
        resource.ConditionalVar1 = 1
        resource.ConditionalVar2 = 2
        resource.ConditionalVar3 = 3
        resource.ExclusiveVar1 = "ONLY_EXCLUSIVE_VAL"
        resource.InclusiveVar1 = True
        resource.InclusiveVar2 = False
        resource.NestedSetting2 = {"NestedVar2": "NestedVar2"}
        resource.NestedSetting1 = {"NestedVar1": "NestedVar1"}
        resource.NestedSetting3 = {"NestedVar2": "NestedVar2"}

        # Should not raise any exception
        resource.validate_before_transform(self.TestProperties)

    def test_validate_before_transform_conditional_inclusive(self):
        """Test CONDITIONAL_INCLUSIVE validation rule"""

        class Resource(self.TestResource):
            def get_property_validation_rules(self):
                return (
                    PropertyRules()
                    .addConditionalInclusive("ConditionalVar1=1", ["ConditionalVar2", "ConditionalVar3"])
                    .addConditionalInclusive(
                        "NestedSetting1.NestedVar1=test", ["NestedSetting2.NestedVar2=22", "NestedSetting2.NestedVar1"]
                    )
                )

        resource = Resource("TestId")

        # Test 1: When ConditionalVar1=1, ConditionalVar2 and ConditionalVar3 should be present
        resource.ConditionalVar1 = 1
        resource.NestedSetting1 = {"NestedVar1": "test"}
        with self.assertRaises(InvalidResourceException) as error_1:
            resource.validate_before_transform(self.TestProperties)
        self.assertEqual(
            "Resource with id [TestId] is invalid. 'ConditionalVar1=1' requires all of: 'ConditionalVar2', 'ConditionalVar3'.\n'NestedSetting1.NestedVar1=test' requires all of: 'NestedSetting2.NestedVar2=22', 'NestedSetting2.NestedVar1'.",
            error_1.exception.message,
        )

        # Test 2: Add ConditionalVar2, should still fail for ConditionalVar3
        resource.ConditionalVar2 = 2
        with self.assertRaises(InvalidResourceException) as error_2:
            resource.validate_before_transform(self.TestProperties)
        self.assertEqual(
            "Resource with id [TestId] is invalid. 'ConditionalVar1=1' requires all of: 'ConditionalVar3'.\n'NestedSetting1.NestedVar1=test' requires all of: 'NestedSetting2.NestedVar2=22', 'NestedSetting2.NestedVar1'.",
            error_2.exception.message,
        )

        # Test 3: Add ConditionalVar3, should still fail for NestedSetting2.NestedVar2
        resource.ConditionalVar3 = 3
        with self.assertRaises(InvalidResourceException) as error_3:
            resource.validate_before_transform(self.TestProperties)
        self.assertEqual(
            "Resource with id [TestId] is invalid. 'NestedSetting1.NestedVar1=test' requires all of: 'NestedSetting2.NestedVar2=22', 'NestedSetting2.NestedVar1'.",
            error_3.exception.message,
        )

        # Test 4: Add NestedSetting2.NestedVar2=22, should still fail for NestedSetting2.NestedVar1=12
        resource.NestedSetting2 = {"NestedVar2": 22}
        with self.assertRaises(InvalidResourceException) as error_4:
            resource.validate_before_transform(self.TestProperties)
        self.assertEqual(
            "Resource with id [TestId] is invalid. 'NestedSetting1.NestedVar1=test' requires all of: 'NestedSetting2.NestedVar1'.",
            error_4.exception.message,
        )

        # Test 5: Set NestedSetting2.NestedVar1, should pass
        resource.NestedSetting2 = {"NestedVar2": 22, "NestedVar1": 12}
        resource.validate_before_transform(self.TestProperties)

        # Test 6: When ConditionalVar1 is None/unset, conditional rules should not apply
        resource.ConditionalVar1 = None
        resource.ConditionalVar2 = None
        resource.ConditionalVar3 = None
        resource.NestedSetting1 = None
        resource.NestedSetting2 = None
        resource.validate_before_transform(self.TestProperties)  # Should pass

        # Test 7: When ConditionalVar1 != 1, rules should not apply (value-specific behavior)
        resource.ConditionalVar1 = 2  # Different value than 1
        resource.ConditionalVar2 = None  # Missing target properties
        resource.ConditionalVar3 = None
        resource.validate_before_transform(self.TestProperties)  # Should pass

        # Test 8: When NestedSetting1.NestedVar1 != "test", nested rule should not apply
        resource.ConditionalVar1 = 1
        resource.ConditionalVar2 = 2
        resource.ConditionalVar3 = 3
        resource.NestedSetting1 = {"NestedVar1": "different"}  # Different value than "test"
        resource.NestedSetting2 = None  # Missing target property
        resource.validate_before_transform(self.TestProperties)  # Should pass

        # Test 9: All conditions are met - should pass
        resource.ConditionalVar1 = 1
        resource.ConditionalVar2 = 2
        resource.ConditionalVar3 = 3
        resource.NestedSetting1 = {"NestedVar1": "test"}
        resource.NestedSetting2 = {"NestedVar2": 22, "NestedVar1": 12}
        resource.validate_before_transform(self.TestProperties)  # Should pass

    def test_validate_before_transform_conditional_exclusive(self):
        """Test CONDITIONAL_EXCLUSIVE validation rule"""

        class Resource(self.TestResource):
            def get_property_validation_rules(self):
                return (
                    PropertyRules()
                    .addConditionalExclusive("ConditionalVar1=1", ["ConditionalVar2", "ConditionalVar3"])
                    .addConditionalExclusive(
                        "NestedSetting1.NestedVar1=test", ["NestedSetting2.NestedVar2=22", "NestedSetting2.NestedVar1"]
                    )
                )

        resource = Resource("TestId")

        # Test 1: When ConditionalVar1=1, ConditionalVar2 and ConditionalVar3 should NOT be present
        resource.ConditionalVar1 = 1
        resource.ConditionalVar2 = 2
        resource.ConditionalVar3 = 3
        with self.assertRaises(InvalidResourceException) as error_1:
            resource.validate_before_transform(self.TestProperties)
        self.assertIn(
            "'ConditionalVar1=1' cannot be used with 'ConditionalVar2', 'ConditionalVar3'", error_1.exception.message
        )

        # Test 2: Remove conflicting properties, should pass
        resource.ConditionalVar2 = None
        resource.ConditionalVar3 = None
        resource.validate_before_transform(self.TestProperties)

        # Test 3: When NestedSetting1.NestedVar1="test", NestedSetting2.NestedVar2 should NOT be present
        resource.NestedSetting1 = {"NestedVar1": "test"}
        resource.NestedSetting2 = {"NestedVar2": "value2"}
        with self.assertRaises(InvalidResourceException) as error_3:
            resource.validate_before_transform(self.TestProperties)
        self.assertIn(
            "'NestedSetting1.NestedVar1=test' cannot be used with 'NestedSetting2.NestedVar2'",
            error_3.exception.message,
        )

        # Test 4: Remove NestedSetting2.NestedVar2, should pass
        resource.NestedSetting2 = None
        resource.validate_before_transform(self.TestProperties)

        # Test 5: When ConditionalVar1 is None/unset, conditional rules should not apply
        resource.ConditionalVar1 = None
        resource.ConditionalVar2 = 2
        resource.ConditionalVar3 = 3
        resource.NestedSetting1 = None
        resource.NestedSetting2 = {"NestedVar2": "value2"}
        resource.validate_before_transform(self.TestProperties)  # Should pass

        # Test 6: When ConditionalVar1 != 1, rules should not apply (value-specific behavior)
        resource.ConditionalVar1 = 2  # Different value than 1
        resource.ConditionalVar2 = 2  # Conflicting properties present
        resource.ConditionalVar3 = 3
        resource.validate_before_transform(self.TestProperties)  # Should pass

        # Test 7: When NestedSetting1.NestedVar1 != "test", nested rule should not apply
        resource.ConditionalVar1 = 1
        resource.ConditionalVar2 = None
        resource.ConditionalVar3 = None
        resource.NestedSetting1 = {"NestedVar1": "different"}  # Different value than "test"
        resource.NestedSetting2 = {"NestedVar2": "value2"}  # Conflicting property present
        resource.validate_before_transform(self.TestProperties)  # Should pass

    def test_validate_before_transform_mutually_inclusive(self):
        """Test MUTUALLY_INCLUSIVE validation rule"""

        class Resource(self.TestResource):
            def get_property_validation_rules(self):
                return (
                    PropertyRules()
                    .addMutuallyInclusive("InclusiveVar1", "InclusiveVar2")
                    .addMutuallyInclusive("InclusiveVar1", "InclusiveVar3")
                    .addMutuallyInclusive("NestedSetting1.NestedVar1", "NestedSetting2.NestedVar2")
                )

        resource = Resource("TestId")

        # Test 1: When InclusiveVar1 is specified, InclusiveVar2 and InclusiveVar3 should be present
        resource.InclusiveVar1 = True
        with self.assertRaises(InvalidResourceException) as error_1:
            resource.validate_before_transform(self.TestProperties)
        expected_errors = [
            "When using 'InclusiveVar1', you must also specify 'InclusiveVar2'",
            "When using 'InclusiveVar1', you must also specify 'InclusiveVar3'",
        ]
        for expected_error in expected_errors:
            self.assertIn(expected_error, error_1.exception.message)

        # Test 2: Add InclusiveVar2, should still fail for InclusiveVar3
        resource.InclusiveVar2 = True
        with self.assertRaises(InvalidResourceException) as error_2:
            resource.validate_before_transform(self.TestProperties)
        self.assertIn("When using 'InclusiveVar1', you must also specify 'InclusiveVar3'", error_2.exception.message)

        # Test 3: Add InclusiveVar3, should pass for inclusive vars
        resource.InclusiveVar3 = True
        resource.validate_before_transform(self.TestProperties)

        # Test 4: When NestedSetting1.NestedVar1 is specified, NestedSetting2.NestedVar2 should be present
        resource.NestedSetting1 = {"NestedVar1": "AUTO"}
        with self.assertRaises(InvalidResourceException) as error_4:
            resource.validate_before_transform(self.TestProperties)
        self.assertIn(
            "When using 'NestedSetting1.NestedVar1', you must also specify 'NestedSetting2.NestedVar2'",
            error_4.exception.message,
        )

        # Test 5: Add NestedSetting2.NestedVar2, should pass
        resource.NestedSetting2 = {"NestedVar2": "REQUIRED"}
        resource.validate_before_transform(self.TestProperties)

    def test_validate_before_transform_mutually_exclusive(self):
        """Test MUTUALLY_EXCLUSIVE validation rule"""

        class Resource(self.TestResource):
            def get_property_validation_rules(self):
                return (
                    PropertyRules()
                    .addMutuallyExclusive("ExclusiveVar1", "ExclusiveVar2")
                    .addMutuallyExclusive("ExclusiveVar2", "ExclusiveVar3")
                    .addMutuallyExclusive("NestedSetting1.NestedVar1", "NestedSetting2.NestedVar1")
                    .addMutuallyExclusive("NestedSetting1.NestedVar2", "ExclusiveVar3")
                )

        resource = Resource("TestId")

        # Test 1: Cannot have both ExclusiveVar1 and ExclusiveVar2
        resource.ExclusiveVar1 = "value1"
        resource.ExclusiveVar2 = "value2"
        with self.assertRaises(InvalidResourceException) as error_1:
            resource.validate_before_transform(self.TestProperties)
        self.assertEqual(
            "Resource with id [TestId] is invalid. Cannot specify 'ExclusiveVar1' and 'ExclusiveVar2' together.",
            error_1.exception.message,
        )

        # Test 2: Remove ExclusiveVar1, should pass
        resource.ExclusiveVar1 = None
        resource.ExclusiveVar2 = "value2"
        resource.validate_before_transform(self.TestProperties)

        # Test 3: Cannot have both ExclusiveVar2 and ExclusiveVar3
        resource.ExclusiveVar2 = "value2"
        resource.ExclusiveVar3 = "value3"
        with self.assertRaises(InvalidResourceException) as error_3:
            resource.validate_before_transform(self.TestProperties)
        self.assertEqual(
            "Resource with id [TestId] is invalid. Cannot specify 'ExclusiveVar2' and 'ExclusiveVar3' together.",
            error_3.exception.message,
        )

        # Test 4: Test multiple conflicts
        resource.ExclusiveVar1 = "value1"
        resource.ExclusiveVar2 = "value2"
        resource.ExclusiveVar3 = "value3"
        with self.assertRaises(InvalidResourceException) as error_4:
            resource.validate_before_transform(self.TestProperties)
        expected_errors = [
            "Cannot specify 'ExclusiveVar1' and 'ExclusiveVar2' together",
            "Cannot specify 'ExclusiveVar2' and 'ExclusiveVar3' together",
        ]
        for expected_error in expected_errors:
            self.assertIn(expected_error, error_4.exception.message)

        # Test 5: Test nested property exclusions
        resource.ExclusiveVar1 = None
        resource.ExclusiveVar2 = None
        resource.ExclusiveVar3 = None
        resource.NestedSetting1 = {"NestedVar1": "nested_value1"}
        resource.NestedSetting2 = {"NestedVar1": "nested_value2"}
        with self.assertRaises(InvalidResourceException) as error_5:
            resource.validate_before_transform(self.TestProperties)
        self.assertEqual(
            "Resource with id [TestId] is invalid. Cannot specify 'NestedSetting1.NestedVar1' and 'NestedSetting2.NestedVar1' together.",
            error_5.exception.message,
        )

        # Test 6: Test nested vs top-level exclusion
        resource.NestedSetting2 = {"NestedVar1": None}
        resource.NestedSetting1 = {"NestedVar2": "nested_value1"}
        resource.ExclusiveVar3 = "value3"
        with self.assertRaises(InvalidResourceException) as error_6:
            resource.validate_before_transform(self.TestProperties)
        self.assertEqual(
            "Resource with id [TestId] is invalid. Cannot specify 'NestedSetting1.NestedVar2' and 'ExclusiveVar3' together.",
            error_6.exception.message,
        )

        # Test 7: Clean state should pass
        resource.ExclusiveVar1 = None
        resource.ExclusiveVar2 = None
        resource.ExclusiveVar3 = None
        resource.NestedSetting1 = {"NestedVar1": "nested_value1"}
        resource.NestedSetting2 = {"NestedVar2": "nested_value2"}
        resource.validate_before_transform(self.TestProperties)

    @parameterized.expand(
        [
            # Single type error
            (
                [{"loc": ("ConditionalVar1",), "msg": "not a valid int", "type": "type_error.integer"}],
                1,
                ["Property 'ConditionalVar1' value must be integer."],
            ),
            # Union type consolidation
            (
                [
                    {"loc": ("ExclusiveVar1",), "msg": "not a valid str", "type": "type_error.str"},
                    {"loc": ("ExclusiveVar1",), "msg": "not a valid int", "type": "type_error.integer"},
                ],
                1,
                ["Property 'ExclusiveVar1' value must be string or integer."],
            ),
            # Missing property error
            (
                [{"loc": ("RequiredProperty",), "msg": "field required", "type": "value_error.missing"}],
                1,
                ["Property 'RequiredProperty' is required."],
            ),
            # Invalid property error
            (
                [{"loc": ("InvalidProperty",), "msg": "extra fields not permitted", "type": "value_error.extra"}],
                1,
                ["Property 'InvalidProperty' is an invalid property."],
            ),
            # Nested property error
            (
                [{"loc": ("NestedSetting1", "NestedVar1"), "msg": "not a valid str", "type": "type_error.str"}],
                1,
                ["Property 'NestedSetting1.NestedVar1' value must be string."],
            ),
            # Multiple properties with errors
            (
                [
                    {"loc": ("ConditionalVar1",), "msg": "not a valid int", "type": "type_error.integer"},
                    {"loc": ("ExclusiveVar1",), "msg": "field required", "type": "value_error.missing"},
                    {"loc": ("NestedSetting1", "NestedVar1"), "msg": "not a valid str", "type": "type_error.str"},
                ],
                3,
                [
                    "Property 'ConditionalVar1' value must be integer.",
                    "Property 'ExclusiveVar1' is required.",
                    "Property 'NestedSetting1.NestedVar1' value must be string.",
                ],
            ),
            # Fallback error formatting
            (
                [{"loc": ("SomeProperty",), "msg": "Some Custom Error Message", "type": "custom_error"}],
                1,
                ["Property 'SomeProperty' some custom error message."],
            ),
        ],
    )
    def test_format_all_errors(self, mock_errors, expected_count, expected_messages):
        """Test formatting various types of validation errors"""
        resource = self.TestResource("TestId")

        formatted_errors = resource._format_all_errors(mock_errors)
        self.assertEqual(len(formatted_errors), expected_count)

        for expected_message in expected_messages:
            self.assertIn(expected_message, formatted_errors)
