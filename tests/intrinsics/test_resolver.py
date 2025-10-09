from unittest import TestCase
from unittest.mock import Mock, patch

from samtranslator.intrinsics.actions import Action
from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.model.exceptions import InvalidDocumentException


class TestParameterReferenceResolution(TestCase):
    def setUp(self):
        self.parameter_values = {"param1": "value1", "param2": "value2", "param3": "value3"}

        self.resolver = IntrinsicsResolver(self.parameter_values)

    def test_must_resolve_top_level_direct_refs(self):
        input = {"key1": {"Ref": "param1"}, "key2": {"Ref": "param2"}, "key3": {"a": "b"}}

        expected = {
            "key1": self.parameter_values["param1"],
            "key2": self.parameter_values["param2"],
            "key3": {"a": "b"},
        }

        output = self.resolver.resolve_parameter_refs(input)
        self.assertEqual(output, expected)

    def test_must_resolve_nested_refs(self):
        input = {"key1": {"sub1": {"sub2": {"sub3": {"Ref": "param1"}, "list": [1, "b", {"Ref": "param2"}]}}}}

        expected = {
            "key1": {
                "sub1": {
                    "sub2": {"sub3": self.parameter_values["param1"], "list": [1, "b", self.parameter_values["param2"]]}
                }
            }
        }

        output = self.resolver.resolve_parameter_refs(input)
        self.assertEqual(output, expected)

    def test_must_resolve_direct_refs(self):
        input = {"Ref": "param1"}
        expected = self.parameter_values["param1"]

        output = self.resolver.resolve_parameter_refs(input)
        self.assertEqual(output, expected)

    def test_must_resolve_array_refs(self):
        input = ["foo", 1, 2, {"Ref": "param1"}]
        expected = ["foo", 1, 2, self.parameter_values["param1"]]

        output = self.resolver.resolve_parameter_refs(input)
        self.assertEqual(output, expected)

    def test_must_skip_unknown_refs(self):
        input = {"key1": {"Ref": "someresource"}, "key2": {"Ref": "param1"}}

        expected = {"key1": {"Ref": "someresource"}, "key2": self.parameter_values["param1"]}

        output = self.resolver.resolve_parameter_refs(input)
        self.assertEqual(output, expected)

    def test_must_resolve_inside_sub_strings(self):
        input = {"Fn::Sub": "prefix ${param1} ${param2} ${param3} ${param1} suffix"}

        expected = {"Fn::Sub": "prefix value1 value2 value3 value1 suffix"}

        output = self.resolver.resolve_parameter_refs(input)
        self.assertEqual(output, expected)

    def test_must_skip_over_sub_literals(self):
        input = {"Fn::Sub": "prefix ${!MustNotBeReplaced} suffix"}

        expected = {"Fn::Sub": "prefix ${!MustNotBeReplaced} suffix"}

        output = self.resolver.resolve_parameter_refs(input)
        self.assertEqual(output, expected)

    def test_must_resolve_refs_inside_other_intrinsics(self):
        input = {"key1": {"Fn::Join": ["-", [{"Ref": "param1"}, "some other value"]]}}

        expected = {"key1": {"Fn::Join": ["-", [self.parameter_values["param1"], "some other value"]]}}

        output = self.resolver.resolve_parameter_refs(input)
        self.assertEqual(output, expected)

    def test_skip_invalid_values_for_ref(self):
        input = {"Ref": ["ref cannot have list value"]}

        expected = {"Ref": ["ref cannot have list value"]}
        output = self.resolver.resolve_parameter_refs(input)
        self.assertEqual(output, expected)

    def test_skip_invalid_values_for_sub(self):
        input = {
            # Invalid Sub resource, must never be parsed, and must not error out
            "Fn::Sub": [{"a": "b"}]
        }

        expected = {"Fn::Sub": [{"a": "b"}]}

        output = self.resolver.resolve_parameter_refs(input)
        self.assertEqual(output, expected)

    def test_throw_on_empty_parameters(self):
        with self.assertRaises(InvalidDocumentException):
            IntrinsicsResolver(None).resolve_parameter_refs({})

    def test_throw_on_non_dict_parameters(self):
        with self.assertRaises(InvalidDocumentException):
            IntrinsicsResolver([1, 2, 3]).resolve_parameter_refs({})

    def test_short_circuit_on_empty_parameters(self):
        resolver = IntrinsicsResolver({})
        resolver._try_resolve_parameter_refs = Mock()  # Mock other methods to detect any actual calls
        input = {"Ref": "foo"}
        expected = {"Ref": "foo"}

        self.assertEqual(resolver.resolve_parameter_refs(input), expected)
        resolver._try_resolve_parameter_refs.assert_not_called()

    def test_cloudformation_internal_placeholder_not_resolved(self):
        """Test that CloudFormation internal placeholders are not resolved"""
        parameter_values = {
            "UserPoolArn": "{{IntrinsicFunction:debugging-cloudformation-issues4/Cognito.Outputs.UserPoolArn/Fn::GetAtt}}",
            "NormalParam": "normal-value",
        }
        resolver = IntrinsicsResolver(parameter_values)

        # CloudFormation placeholder should not be resolved
        input1 = {"Ref": "UserPoolArn"}
        expected1 = {"Ref": "UserPoolArn"}
        output1 = resolver.resolve_parameter_refs(input1)
        self.assertEqual(output1, expected1)

        # Normal parameter should still be resolved
        input2 = {"Ref": "NormalParam"}
        expected2 = "normal-value"
        output2 = resolver.resolve_parameter_refs(input2)
        self.assertEqual(output2, expected2)

    def test_cloudformation_placeholders_in_nested_structure(self):
        """Test CloudFormation placeholders in nested structures"""
        parameter_values = {
            "Placeholder1": "{{IntrinsicFunction:stack/Output1/Fn::GetAtt}}",
            "Placeholder2": "{{IntrinsicFunction:stack/Output2/Fn::GetAtt}}",
            "NormalParam": "value",
        }
        resolver = IntrinsicsResolver(parameter_values)

        input = {
            "Resources": {
                "Resource1": {
                    "Properties": {
                        "Prop1": {"Ref": "Placeholder1"},
                        "Prop2": {"Ref": "NormalParam"},
                        "Prop3": {"Ref": "Placeholder2"},
                    }
                }
            }
        }

        expected = {
            "Resources": {
                "Resource1": {
                    "Properties": {
                        "Prop1": {"Ref": "Placeholder1"},  # Not resolved
                        "Prop2": "value",  # Resolved
                        "Prop3": {"Ref": "Placeholder2"},  # Not resolved
                    }
                }
            }
        }

        output = resolver.resolve_parameter_refs(input)
        self.assertEqual(output, expected)

    def test_cloudformation_placeholders_in_lists(self):
        """Test CloudFormation placeholders in list structures"""
        parameter_values = {
            "VpceId": "{{IntrinsicFunction:stack/VpcEndpoint.Outputs.Id/Fn::GetAtt}}",
            "Region": "us-east-1",
        }
        resolver = IntrinsicsResolver(parameter_values)

        input = [{"Ref": "VpceId"}, {"Ref": "Region"}, "static-value", {"Ref": "VpceId"}]

        expected = [
            {"Ref": "VpceId"},  # Not resolved
            "us-east-1",  # Resolved
            "static-value",
            {"Ref": "VpceId"},  # Not resolved
        ]

        output = resolver.resolve_parameter_refs(input)
        self.assertEqual(output, expected)

    def test_cloudformation_placeholders_with_sub(self):
        """Test that CloudFormation placeholders inside Fn::Sub are not substituted

        Similar to Ref, Fn::Sub should not substitute CloudFormation internal placeholders.
        This prevents the placeholders from being embedded in strings where they can't be
        properly handled by CloudFormation.
        """
        parameter_values = {
            "Placeholder": "{{IntrinsicFunction:stack/Output/Fn::GetAtt}}",
            "NormalParam": "normal-value",
        }
        resolver = IntrinsicsResolver(parameter_values)

        # Sub should not substitute CloudFormation placeholders, but should substitute normal params
        input = {"Fn::Sub": "Value is ${Placeholder} and ${NormalParam}"}
        expected = {"Fn::Sub": "Value is ${Placeholder} and normal-value"}

        output = resolver.resolve_parameter_refs(input)
        self.assertEqual(output, expected)

    def test_various_cloudformation_placeholder_formats(self):
        """Test various CloudFormation placeholder formats"""
        parameter_values = {
            "Valid1": "{{IntrinsicFunction:stack/Resource.Outputs.Value/Fn::GetAtt}}",
            "Valid2": "{{IntrinsicFunction:name-with-dashes/Out/Fn::GetAtt}}",
            "Valid3": "{{IntrinsicFunction:stack123/Resource.Out/Fn::GetAtt}}",
            "NotPlaceholder1": "{{SomethingElse}}",
            "NotPlaceholder2": "{{intrinsicfunction:lowercase}}",
            "NotPlaceholder3": "normal-string",
        }
        resolver = IntrinsicsResolver(parameter_values)

        # Valid placeholders should not be resolved
        for param in ["Valid1", "Valid2", "Valid3"]:
            input = {"Ref": param}
            expected = {"Ref": param}
            output = resolver.resolve_parameter_refs(input)
            self.assertEqual(output, expected, f"Failed for {param}")

        # Non-placeholders should be resolved
        test_cases = [
            ("NotPlaceholder1", "{{SomethingElse}}"),
            ("NotPlaceholder2", "{{intrinsicfunction:lowercase}}"),
            ("NotPlaceholder3", "normal-string"),
        ]

        for param, expected_value in test_cases:
            input = {"Ref": param}
            output = resolver.resolve_parameter_refs(input)
            self.assertEqual(output, expected_value, f"Failed for {param}")


class TestResourceReferenceResolution(TestCase):
    def setUp(self):
        self.resolver = IntrinsicsResolver({})

    @patch.object(IntrinsicsResolver, "_try_resolve_sam_resource_refs")
    @patch.object(IntrinsicsResolver, "_traverse")
    def test_resolve_sam_resource_refs(self, traverse_mock, try_resolve_mock):
        input = "foo"
        supported_refs = Mock()

        self.resolver.resolve_sam_resource_refs(input, supported_refs)
        traverse_mock.assert_called_once_with(input, supported_refs, try_resolve_mock)

    def test_resolve_sam_resource_refs_on_supported_intrinsic(self):
        action_mock = Mock()
        self.resolver.supported_intrinsics = {"foo": action_mock}
        input = {"foo": "bar"}
        supported_refs = Mock()

        self.resolver._try_resolve_sam_resource_refs(input, supported_refs)
        action_mock.resolve_resource_refs.assert_called_once_with(input, supported_refs)

    def test_resolve_sam_resource_refs_on_unknown_intrinsic(self):
        action_mock = Mock()
        self.resolver.supported_intrinsics = {"foo": action_mock}
        input = {"a": "b"}
        expected = {"a": "b"}
        supported_refs = Mock()

        result = self.resolver._try_resolve_sam_resource_refs(input, supported_refs)
        self.assertEqual(result, expected)
        action_mock.resolve_sam_resource_refs.assert_not_called()

    def test_short_circuit_on_empty_parameters(self):
        resolver = IntrinsicsResolver({})
        resolver._try_resolve_sam_resource_refs = Mock()  # Mock other methods to detect any actual calls
        input = {"Ref": "foo"}
        expected = {"Ref": "foo"}

        self.assertEqual(resolver.resolve_sam_resource_refs(input, {}), expected)
        resolver._try_resolve_sam_resource_refs.assert_not_called()


class TestSupportedIntrinsics(TestCase):
    def test_by_default_all_intrinsics_must_be_supported(self):
        # Just make sure we never remove support for some intrinsic
        resolver = IntrinsicsResolver({})

        # This needs to be updated when new intrinsics are added
        self.assertEqual(3, len(resolver.supported_intrinsics))
        self.assertTrue("Ref" in resolver.supported_intrinsics)
        self.assertTrue("Fn::Sub" in resolver.supported_intrinsics)
        self.assertTrue("Fn::GetAtt" in resolver.supported_intrinsics)

    def test_configure_supported_intrinsics(self):
        class SomeAction(Action):
            intrinsic_name = "IntrinsicName"

        action = SomeAction()
        supported_intrinsics = {"ThisCanBeAnyIntrinsicName": action}
        resolver = IntrinsicsResolver({}, supported_intrinsics)

        self.assertEqual(resolver.supported_intrinsics, {"ThisCanBeAnyIntrinsicName": action})

    def test_configure_supported_intrinsics_must_error_for_non_action_value(self):
        class SomeAction(Action):
            intrinsic_name = "Foo"

        # All intrinsics must have a value to be subclass of "Action"
        supported_intrinsics = {"A": "B", "Foo": SomeAction()}
        with self.assertRaises(TypeError):
            IntrinsicsResolver({}, supported_intrinsics)

    def test_configure_supported_intrinsics_must_error_for_non_dict_input(self):
        with self.assertRaises(TypeError):
            IntrinsicsResolver({}, [1, 2, 3])
