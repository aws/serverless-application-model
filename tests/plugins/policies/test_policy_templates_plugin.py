from unittest import TestCase
from mock import Mock, MagicMock, patch, call

from samtranslator.plugins import BasePlugin
from samtranslator.model.resource_policies import PolicyTypes, PolicyEntry
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.plugins.policies.policy_templates_plugin import PolicyTemplatesForResourcePlugin
from samtranslator.policy_template_processor.exceptions import InsufficientParameterValues, InvalidParameterValues


class TestPolicyTemplatesForResourcePlugin(TestCase):
    def setUp(self):
        self._policy_template_processor_mock = Mock()
        self.plugin = PolicyTemplatesForResourcePlugin(self._policy_template_processor_mock)

    def test_plugin_must_setup_correct_name(self):
        # Name is the class name
        expected_name = "PolicyTemplatesForResourcePlugin"

        self.assertEqual(self.plugin.name, expected_name)

    def test_plugin_must_be_instance_of_base_plugin_class(self):
        self.assertTrue(isinstance(self.plugin, BasePlugin))

    def test_must_only_support_function_resource(self):
        function_type = "AWS::Serverless::Function"
        self.assertTrue(self.plugin._is_supported(function_type))

    def test_must_not_support_non_function_resources(self):
        resource_type = "AWS::Serverless::Api"
        self.assertFalse(self.plugin._is_supported(resource_type))

    @patch("samtranslator.plugins.policies.policy_templates_plugin.ResourcePolicies")
    def test_on_before_transform_resource_must_work_on_every_policy_template(self, function_policies_class_mock):
        is_supported_mock = Mock()
        self.plugin._is_supported = is_supported_mock
        is_supported_mock.return_value = True

        function_policies_obj_mock = MagicMock()
        function_policies_class_mock.return_value = function_policies_obj_mock
        function_policies_class_mock.POLICIES_PROPERTY_NAME = "Policies"

        template1 = {"MyTemplate1": {"Param1": "value1"}}
        template2 = {"MyTemplate2": {"Param2": "value2"}}
        resource_properties = {"Policies": [template1, template2]}

        policies = [
            PolicyEntry(data=template1, type=PolicyTypes.POLICY_TEMPLATE),
            PolicyEntry(data=template2, type=PolicyTypes.POLICY_TEMPLATE),
        ]

        # Setup to return all the policies
        function_policies_obj_mock.__len__.return_value = 2
        function_policies_obj_mock.get.return_value = iter(policies)

        # These are the values returned on every call to `convert` method
        self._policy_template_processor_mock.convert.side_effect = [
            {"Statement1": {"key1": "value1"}},
            {"Statement2": {"key2": "value2"}},
        ]

        expected = [{"Statement1": {"key1": "value1"}}, {"Statement2": {"key2": "value2"}}]
        self.plugin.on_before_transform_resource("logicalId", "resource_type", resource_properties)

        # This will overwrite the resource_properties input array
        self.assertEqual(expected, resource_properties["Policies"])
        function_policies_obj_mock.get.assert_called_once_with()
        self._policy_template_processor_mock.convert.assert_has_calls(
            [call("MyTemplate1", {"Param1": "value1"}), call("MyTemplate2", {"Param2": "value2"})]
        )

    @patch("samtranslator.plugins.policies.policy_templates_plugin.ResourcePolicies")
    def test_on_before_transform_resource_must_skip_non_policy_templates(self, function_policies_class_mock):
        is_supported_mock = Mock()
        self.plugin._is_supported = is_supported_mock
        is_supported_mock.return_value = True

        function_policies_obj_mock = MagicMock()
        function_policies_class_mock.return_value = function_policies_obj_mock
        function_policies_class_mock.POLICIES_PROPERTY_NAME = "Policies"

        template1 = {"MyTemplate1": {"Param1": "value1"}}
        template2 = {"MyTemplate2": {"Param2": "value2"}}
        regular_policy = {"regular policy": "something"}
        resource_properties = {"Policies": [template1, regular_policy, template2]}

        policies = [
            PolicyEntry(data=template1, type=PolicyTypes.POLICY_TEMPLATE),
            PolicyEntry(data=regular_policy, type=PolicyTypes.MANAGED_POLICY),
            PolicyEntry(data=template2, type=PolicyTypes.POLICY_TEMPLATE),
        ]

        # Setup to return all the policies
        function_policies_obj_mock.__len__.return_value = 3
        function_policies_obj_mock.get.return_value = iter(policies)

        # These are the values returned on every call to `convert` method
        self._policy_template_processor_mock.convert.side_effect = [
            {"Statement1": {"key1": "value1"}},
            {"Statement2": {"key2": "value2"}},
        ]

        expected = [
            {"Statement1": {"key1": "value1"}},
            {"regular policy": "something"},
            {"Statement2": {"key2": "value2"}},
        ]
        self.plugin.on_before_transform_resource("logicalId", "resource_type", resource_properties)

        # This will overwrite the resource_properties input array
        self.assertEqual(expected, resource_properties["Policies"])
        function_policies_obj_mock.get.assert_called_once_with()
        self._policy_template_processor_mock.convert.assert_has_calls(
            [call("MyTemplate1", {"Param1": "value1"}), call("MyTemplate2", {"Param2": "value2"})]
        )

    @patch("samtranslator.plugins.policies.policy_templates_plugin.ResourcePolicies")
    def test_on_before_transform_must_raise_on_insufficient_parameter_values(self, function_policies_class_mock):
        is_supported_mock = Mock()
        self.plugin._is_supported = is_supported_mock
        is_supported_mock.return_value = True

        function_policies_obj_mock = MagicMock()
        function_policies_class_mock.return_value = function_policies_obj_mock

        template1 = {"MyTemplate1": {"Param1": "value1"}}
        resource_properties = {"Policies": template1}

        policies = [PolicyEntry(data=template1, type=PolicyTypes.POLICY_TEMPLATE)]

        # Setup to return all the policies
        function_policies_obj_mock.__len__.return_value = 1
        function_policies_obj_mock.get.return_value = iter(policies)

        # These are the values returned on every call to `convert` method
        self._policy_template_processor_mock.convert.side_effect = InsufficientParameterValues("message")

        with self.assertRaises(InvalidResourceException):
            self.plugin.on_before_transform_resource("logicalId", "resource_type", resource_properties)

        # Make sure the input was not changed
        self.assertEqual(resource_properties, {"Policies": {"MyTemplate1": {"Param1": "value1"}}})

    @patch("samtranslator.plugins.policies.policy_templates_plugin.ResourcePolicies")
    def test_on_before_transform_must_raise_on_invalid_parameter_values(self, function_policies_class_mock):
        is_supported_mock = Mock()
        self.plugin._is_supported = is_supported_mock
        is_supported_mock.return_value = True

        function_policies_obj_mock = MagicMock()
        function_policies_class_mock.return_value = function_policies_obj_mock

        template1 = {"MyTemplate1": {"Param1": "value1"}}
        resource_properties = {"Policies": template1}

        policies = [PolicyEntry(data=template1, type=PolicyTypes.POLICY_TEMPLATE)]

        # Setup to return all the policies
        function_policies_obj_mock.__len__.return_value = 1
        function_policies_obj_mock.get.return_value = iter(policies)

        self._policy_template_processor_mock.convert.side_effect = InvalidParameterValues("message")

        with self.assertRaises(InvalidResourceException):
            self.plugin.on_before_transform_resource("logicalId", "resource_type", resource_properties)

        # Make sure the input was not changed
        self.assertEqual(resource_properties, {"Policies": {"MyTemplate1": {"Param1": "value1"}}})

    @patch("samtranslator.plugins.policies.policy_templates_plugin.ResourcePolicies")
    def test_on_before_transform_must_bubble_exception(self, function_policies_class_mock):
        is_supported_mock = Mock()
        self.plugin._is_supported = is_supported_mock
        is_supported_mock.return_value = True

        function_policies_obj_mock = MagicMock()
        function_policies_class_mock.return_value = function_policies_obj_mock

        template1 = {"MyTemplate1": {"Param1": "value1"}}
        resource_properties = {"Policies": template1}

        policies = [PolicyEntry(data=template1, type=PolicyTypes.POLICY_TEMPLATE)]

        # Setup to return all the policies
        function_policies_obj_mock.__len__.return_value = 1
        function_policies_obj_mock.get.return_value = iter(policies)

        self._policy_template_processor_mock.convert.side_effect = TypeError("message")

        with self.assertRaises(TypeError):
            self.plugin.on_before_transform_resource("logicalId", "resource_type", resource_properties)

        # Make sure the input was not changed
        self.assertEqual(resource_properties, {"Policies": {"MyTemplate1": {"Param1": "value1"}}})

    def test_on_before_transform_resource_must_skip_unsupported_resources(self):

        is_supported_mock = Mock()
        data_mock = Mock()

        self.plugin._is_supported = is_supported_mock
        is_supported_mock.return_value = False

        self.plugin.on_before_transform_resource(data_mock, data_mock, data_mock)

        # Make sure none of the data elements were accessed, because the method returned immediately
        self.assertEqual([], data_mock.method_calls)

    @patch("samtranslator.plugins.policies.policy_templates_plugin.ResourcePolicies")
    def test_on_before_transform_resource_must_skip_function_with_no_policies(self, function_policies_class_mock):
        is_supported_mock = Mock()
        self.plugin._is_supported = is_supported_mock
        is_supported_mock.return_value = True

        function_policies_obj_mock = MagicMock()
        function_policies_class_mock.return_value = function_policies_obj_mock

        # Setup to return NO policies
        function_policies_obj_mock.__len__.return_value = 0

        self.plugin.on_before_transform_resource("logicalId", "resource_type", {})

        # Since length was zero, get() should never be called
        function_policies_obj_mock.get.assert_not_called()
