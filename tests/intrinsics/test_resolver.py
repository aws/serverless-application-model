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

    def test_evaluate_condition_scenarios(self):
        resolver = IntrinsicsResolver({})
        conditions = {"Condition1": True, "Condition2": False, "NestedCondition": "Condition1"}

        # Test direct boolean values
        self.assertTrue(resolver.evaluate_condition(True, conditions))
        self.assertFalse(resolver.evaluate_condition(False, conditions))

        # Test string literals
        self.assertTrue(resolver.evaluate_condition("true", conditions))
        self.assertFalse(resolver.evaluate_condition("false", conditions))

        # Test condition lookups
        self.assertTrue(resolver.evaluate_condition("Condition1", conditions))
        self.assertFalse(resolver.evaluate_condition("Condition2", conditions))
        self.assertTrue(resolver.evaluate_condition("NestedCondition", conditions))

    def test_evaluate_condition_intrinsic_functions(self):
        resolver = IntrinsicsResolver({})
        conditions = {"Condition1": True, "Condition2": False}

        # Test Fn::Equals
        self.assertTrue(resolver.evaluate_condition({"Fn::Equals": ["value1", "value1"]}, conditions))

        # Test Fn::And
        self.assertFalse(resolver.evaluate_condition({"Fn::And": ["Condition1", "Condition2"]}, conditions))

        # Test Fn::Or
        self.assertTrue(resolver.evaluate_condition({"Fn::Or": ["Condition1", "Condition2"]}, conditions))

        # Test Fn::Not
        self.assertFalse(resolver.evaluate_condition({"Fn::Not": ["Condition1"]}, conditions))

    def test_evaluate_condition_error_cases(self):
        resolver = IntrinsicsResolver({})
        conditions = {}

        # Test invalid condition name
        with self.assertRaises(InvalidDocumentException):
            resolver.evaluate_condition("NonExistentCondition", conditions)

        # Test invalid function
        with self.assertRaises(InvalidDocumentException):
            resolver.evaluate_condition({"InvalidFunction": []}, conditions)

        # Test invalid condition structure
        with self.assertRaises(InvalidDocumentException):
            resolver.evaluate_condition({"key1": "value1", "key2": "value2"}, conditions)


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

    def test_resolve_ref_value(self):
        # Test with non-intrinsic input
        non_intrinsic = {"key": "value"}
        self.assertEqual(non_intrinsic, self.resolver.resolve_ref_value(non_intrinsic))

        # Test with non-Ref intrinsic
        non_ref = {"Fn::Sub": "value"}
        self.assertEqual(non_ref, self.resolver.resolve_ref_value(non_ref))

        # Test with AWS::NoValue
        ref_input = {"Ref": "AWS::NoValue"}
        self.assertEqual(None, self.resolver.resolve_ref_value(ref_input))


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
