from unittest import TestCase

from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.preferences.deployment_preference import DeploymentPreference


class TestDeploymentPreference(TestCase):
    def setUp(self):
        self.deployment_type = "AllAtOnce"
        self.pre_traffic_hook = "pre_traffic_function_ref"
        self.post_traffic_hook = "post_traffic_function_ref"
        self.alarms = ["alarm1ref", "alarm2ref"]
        self.role = {"Ref": "MyRole"}
        self.trigger_configurations = {
            "TriggerEvents": ["DeploymentSuccess", "DeploymentFailure"],
            "TriggerTargetArn": {"Ref": "MySNSTopic"},
            "TriggerName": "TestTrigger",
        }
        self.expected_deployment_preference = DeploymentPreference(
            self.deployment_type,
            self.pre_traffic_hook,
            self.post_traffic_hook,
            self.alarms,
            True,
            self.role,
            self.trigger_configurations,
        )

    def test_from_dict_with_intrinsic_function_type(self):

        type = {"Ref": "SomeType"}
        expected_deployment_preference = DeploymentPreference(
            type,
            self.pre_traffic_hook,
            self.post_traffic_hook,
            self.alarms,
            True,
            self.role,
            self.trigger_configurations,
        )

        deployment_preference_yaml_dict = dict()
        deployment_preference_yaml_dict["Type"] = type
        deployment_preference_yaml_dict["Hooks"] = {
            "PreTraffic": self.pre_traffic_hook,
            "PostTraffic": self.post_traffic_hook,
        }
        deployment_preference_yaml_dict["Alarms"] = self.alarms
        deployment_preference_yaml_dict["Role"] = self.role
        deployment_preference_yaml_dict["TriggerConfigurations"] = self.trigger_configurations
        deployment_preference_from_yaml_dict = DeploymentPreference.from_dict(
            "logical_id", deployment_preference_yaml_dict
        )

        self.assertEqual(expected_deployment_preference, deployment_preference_from_yaml_dict)

    def test_from_dict(self):
        deployment_preference_yaml_dict = dict()
        deployment_preference_yaml_dict["Type"] = self.deployment_type
        deployment_preference_yaml_dict["Hooks"] = {
            "PreTraffic": self.pre_traffic_hook,
            "PostTraffic": self.post_traffic_hook,
        }
        deployment_preference_yaml_dict["Alarms"] = self.alarms
        deployment_preference_yaml_dict["Role"] = self.role
        deployment_preference_yaml_dict["TriggerConfigurations"] = self.trigger_configurations
        deployment_preference_from_yaml_dict = DeploymentPreference.from_dict(
            "logical_id", deployment_preference_yaml_dict
        )

        self.assertEqual(self.expected_deployment_preference, deployment_preference_from_yaml_dict)

    def test_from_dict_with_disabled_preference_does_not_require_other_parameters(self):
        expected_deployment_preference = DeploymentPreference(None, None, None, None, False, None, None)

        deployment_preference_yaml_dict = dict()
        deployment_preference_yaml_dict["Enabled"] = False
        deployment_preference_from_yaml_dict = DeploymentPreference.from_dict(
            "logical_id", deployment_preference_yaml_dict
        )

        self.assertEqual(expected_deployment_preference, deployment_preference_from_yaml_dict)

    def test_from_dict_with_string_disabled_preference_does_not_require_other_parameters(self):
        expected_deployment_preference = DeploymentPreference(None, None, None, None, False, None, None)

        deployment_preference_yaml_dict = dict()
        deployment_preference_yaml_dict["Enabled"] = "False"
        deployment_preference_from_yaml_dict = DeploymentPreference.from_dict(
            "logical_id", deployment_preference_yaml_dict
        )

        self.assertEqual(expected_deployment_preference, deployment_preference_from_yaml_dict)

    def test_from_dict_with_lowercase_string_disabled_preference_does_not_require_other_parameters(self):
        expected_deployment_preference = DeploymentPreference(None, None, None, None, False, None, None)

        deployment_preference_yaml_dict = dict()
        deployment_preference_yaml_dict["Enabled"] = "false"
        deployment_preference_from_yaml_dict = DeploymentPreference.from_dict(
            "logical_id", deployment_preference_yaml_dict
        )

        self.assertEqual(expected_deployment_preference, deployment_preference_from_yaml_dict)

    def test_from_dict_with_non_dict_hooks_raises_invalid_resource_exception(self):
        with self.assertRaises(InvalidResourceException):
            DeploymentPreference.from_dict("logical_id", {"Type": "Canary", "Hooks": "badhook"})

    def test_from_dict_with_missing_type_raises_invalid_resource_exception(self):
        with self.assertRaises(InvalidResourceException):
            DeploymentPreference.from_dict("logical_id", dict())
