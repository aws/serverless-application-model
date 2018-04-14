from mock import Mock, patch
from unittest import TestCase

from samtranslator.model.function_policies import FunctionPolicies, PolicyTypes, PolicyEntry

class TestFunctionPolicies(TestCase):

    def setUp(self):
        self.policy_template_processor_mock = Mock()
        self.is_policy_template_mock = Mock()

        self.function_policies = FunctionPolicies({}, self.policy_template_processor_mock)
        self.function_policies._is_policy_template = self.is_policy_template_mock


    @patch.object(FunctionPolicies, "_get_policies")
    def test_initialization_must_ingest_policies_from_resource_properties(self, get_policies_mock):
        resource_properties = {}
        dummy_policy_results = ["some", "policy", "statements"]
        expected_length = 3

        get_policies_mock.return_value = dummy_policy_results
        function_policies = FunctionPolicies(resource_properties, self.policy_template_processor_mock)

        get_policies_mock.assert_called_once_with(resource_properties)
        self.assertEquals(expected_length, len(function_policies))


    @patch.object(FunctionPolicies, "_get_policies")
    def test_get_must_yield_results_on_every_call(self, get_policies_mock):
        resource_properties = {} # Just some input
        dummy_policy_results = ["some", "policy", "statements"]
        expected_results = ["some", "policy", "statements"]

        # Setup _get_policies to return these dummy values for testing
        get_policies_mock.return_value = dummy_policy_results
        function_policies = FunctionPolicies(resource_properties, self.policy_template_processor_mock)

        # `list()` will implicitly call the `get()` repeatedly because it is a generator
        self.assertEquals(list(function_policies.get()), expected_results)


    @patch.object(FunctionPolicies, "_get_policies")
    def test_get_must_yield_no_results_with_no_policies(self, get_policies_mock):
        resource_properties = {} # Just some input
        dummy_policy_results = []
        expected_result = []

        # Setup _get_policies to return these dummy values for testing
        get_policies_mock.return_value = dummy_policy_results
        function_policies = FunctionPolicies(resource_properties, self.policy_template_processor_mock)

        # `list()` will implicitly call the `get()` repeatedly because it is a generator
        self.assertEquals(list(function_policies.get()), expected_result)

    def test_contains_policies_must_work_for_valid_input(self):
        resource_properties = {
            "Policies": "some managed policy"
        }

        self.assertTrue(self.function_policies._contains_policies(resource_properties))

    def test_contains_policies_must_ignore_resources_without_policies(self):
        resource_properties = {
            "some key": "value"
        }

        self.assertFalse(self.function_policies._contains_policies(resource_properties))

    def test_contains_policies_must_ignore_non_dict_resources(self):
        resource_properties = "some value"

        self.assertFalse(self.function_policies._contains_policies(resource_properties))

    def test_contains_policies_must_ignore_none_resources(self):
        resource_properties = None

        self.assertFalse(self.function_policies._contains_policies(resource_properties))

    def test_contains_policies_must_ignore_lowercase_property_name(self):
        # Property names are case sensitive
        resource_properties = {
            "policies": "some managed policy"
        }

        self.assertFalse(self.function_policies._contains_policies(resource_properties))

    def test_get_type_must_work_for_managed_policy(self):
        policy = "managed policy is a string"
        expected = PolicyTypes.MANAGED_POLICY

        result = self.function_policies._get_type(policy)
        self.assertEquals(result, expected)

    @patch("samtranslator.model.function_policies.is_instrinsic")
    def test_get_type_must_work_for_managed_policy_with_intrinsics(self, is_intrinsic_mock):
        policy = {
            "Ref": "somevalue"
        }
        expected = PolicyTypes.MANAGED_POLICY
        is_intrinsic_mock.return_value = True

        result = self.function_policies._get_type(policy)
        self.assertEquals(result, expected)

    def test_get_type_must_work_for_policy_statements(self):
        policy = {
            "Statement": "policy statements have a 'Statement' key"
        }
        expected = PolicyTypes.POLICY_STATEMENT

        result = self.function_policies._get_type(policy)
        self.assertEquals(result, expected)

    def test_get_type_must_work_for_policy_templates(self):
        policy = {
            "PolicyTemplate": "some template"
        }
        self.is_policy_template_mock.return_value = True
        expected = PolicyTypes.POLICY_TEMPLATE

        result = self.function_policies._get_type(policy)
        self.assertEquals(result, expected)

    def test_get_type_must_ignore_invalid_policy(self):
        policy = {
            "not-sure-what-this-is": "value"
        }
        # This is also not a policy template
        self.is_policy_template_mock.return_value = False
        expected = PolicyTypes.UNKNOWN

        result = self.function_policies._get_type(policy)
        self.assertEquals(result, expected)

    def test_get_type_must_ignore_invalid_policy_value_list(self):
        policy = ["invalid", "policy"]
        expected = PolicyTypes.UNKNOWN

        self.is_policy_template_mock.return_value = False

        result = self.function_policies._get_type(policy)
        self.assertEquals(result, expected)
        self.is_policy_template_mock.assert_called_once_with(policy)

    def test_get_policies_must_return_all_policies(self):
        policies = [
            "managed policy 1",
            {"Ref": "some managed policy"},
            {"Statement": "policy statement"},
            {"PolicyTemplate": "some value"},
            ["unknown", "policy"]
        ]
        resource_properties = {
            "Policies": policies
        }
        self.is_policy_template_mock.side_effect = [True, False] # Return True for policy template, False for the list

        expected = [
            PolicyEntry(data="managed policy 1", type=PolicyTypes.MANAGED_POLICY),
            PolicyEntry(data={"Ref": "some managed policy"}, type=PolicyTypes.MANAGED_POLICY),
            PolicyEntry(data={"Statement": "policy statement"}, type=PolicyTypes.POLICY_STATEMENT),
            PolicyEntry(data={"PolicyTemplate": "some value"}, type=PolicyTypes.POLICY_TEMPLATE),
            PolicyEntry(data=["unknown", "policy"], type=PolicyTypes.UNKNOWN),
        ]

        result = self.function_policies._get_policies(resource_properties)
        self.assertEquals(result, expected)

    def test_get_policies_must_ignore_if_resource_does_not_contain_policy(self):
        resource_properties = {
        }
        expected = []

        result = self.function_policies._get_policies(resource_properties)
        self.assertEquals(result, expected)

    def test_get_policies_must_ignore_if_policies_is_empty(self):
        resource_properties = {
            "Policies": []
        }
        expected = []

        result = self.function_policies._get_policies(resource_properties)
        self.assertEquals(result, expected)

    def test_get_policies_must_work_for_single_policy_string(self):
        resource_properties = {
            "Policies": "single managed policy"
        }
        expected = [
            PolicyEntry(data="single managed policy", type=PolicyTypes.MANAGED_POLICY)
        ]

        result = self.function_policies._get_policies(resource_properties)
        self.assertEquals(result, expected)

    def test_get_policies_must_work_for_single_dict_with_managed_policy_intrinsic(self):
        resource_properties = {
            "Policies": {
                "Ref": "some managed policy"
            }
        }
        expected = [
            PolicyEntry(data={"Ref": "some managed policy"}, type=PolicyTypes.MANAGED_POLICY)
        ]

        result = self.function_policies._get_policies(resource_properties)
        self.assertEquals(result, expected)

    def test_get_policies_must_work_for_single_dict_with_policy_statement(self):
        resource_properties = {
            "Policies": {
                "Statement": "some policy statement"
            }
        }
        expected = [
            PolicyEntry(data={"Statement": "some policy statement"}, type=PolicyTypes.POLICY_STATEMENT)
        ]

        result = self.function_policies._get_policies(resource_properties)
        self.assertEquals(result, expected)

    def test_get_policies_must_work_for_single_dict_of_policy_template(self):
        resource_properties = {
            "Policies": {
                "PolicyTemplate": "some template"
            }
        }
        self.is_policy_template_mock.return_value = True
        expected = [
            PolicyEntry(data={"PolicyTemplate": "some template"}, type=PolicyTypes.POLICY_TEMPLATE)
        ]

        result = self.function_policies._get_policies(resource_properties)
        self.assertEquals(result, expected)
        self.is_policy_template_mock.assert_called_once_with(resource_properties["Policies"])

    def test_get_policies_must_work_for_single_dict_of_invalid_policy_template(self):
        resource_properties = {
            "Policies": {
                "InvalidPolicyTemplate": "some template"
            }
        }
        self.is_policy_template_mock.return_value = False # Invalid policy template
        expected = [
            PolicyEntry(data={"InvalidPolicyTemplate": "some template"}, type=PolicyTypes.UNKNOWN)
        ]

        result = self.function_policies._get_policies(resource_properties)
        self.assertEquals(result, expected)
        self.is_policy_template_mock.assert_called_once_with({"InvalidPolicyTemplate": "some template"})

    def test_get_policies_must_work_for_unknown_policy_types(self):
        resource_properties = {
            "Policies": [
                1, 2, 3
            ]
        }
        expected = [
            PolicyEntry(data=1, type=PolicyTypes.UNKNOWN),
            PolicyEntry(data=2, type=PolicyTypes.UNKNOWN),
            PolicyEntry(data=3, type=PolicyTypes.UNKNOWN),
        ]

        self.is_policy_template_mock.return_value = False

        result = self.function_policies._get_policies(resource_properties)
        self.assertEquals(result, expected)

    def test_is_policy_template_must_detect_valid_policy_templates(self):
        template_name = "template_name"
        policy = {
            template_name: {
                "Param1": "foo"
            }
        }

        self.policy_template_processor_mock.has.return_value = True
        function_policies = FunctionPolicies({}, self.policy_template_processor_mock)

        self.assertTrue(function_policies._is_policy_template(policy))

        self.policy_template_processor_mock.has.assert_called_once_with(template_name)

    def test_is_policy_template_must_ignore_non_dict_policies(self):
        policy = [1,2,3]

        self.policy_template_processor_mock.has.return_value = True
        function_policies = FunctionPolicies({}, self.policy_template_processor_mock)

        self.assertFalse(function_policies._is_policy_template(policy))

        self.policy_template_processor_mock.has.assert_not_called()

    def test_is_policy_template_must_ignore_none_policies(self):
        policy = None

        function_policies = FunctionPolicies({}, self.policy_template_processor_mock)
        self.assertFalse(function_policies._is_policy_template(policy))

    def test_is_policy_template_must_ignore_dict_with_two_keys(self):
        template_name = "template_name"
        policy = {
            template_name: {"param1": "foo"},
            "A": "B"
        }

        self.policy_template_processor_mock.has.return_value = True

        function_policies = FunctionPolicies({}, self.policy_template_processor_mock)
        self.assertFalse(function_policies._is_policy_template(policy))

    def test_is_policy_template_must_ignore_non_policy_templates(self):
        template_name = "template_name"
        policy = {
            template_name: {"param1": "foo"}
        }

        self.policy_template_processor_mock.has.return_value = False

        function_policies = FunctionPolicies({}, self.policy_template_processor_mock)
        self.assertFalse(function_policies._is_policy_template(policy))

        self.policy_template_processor_mock.has.assert_called_once_with(template_name)

    def test_is_policy_template_must_return_false_without_the_processor(self):
        policy = {
            "template_name": {"param1": "foo"}
        }

        function_policies_obj = FunctionPolicies({}, None) # No policy template processor

        self.assertFalse(function_policies_obj._is_policy_template(policy))
        self.policy_template_processor_mock.has.assert_not_called()
