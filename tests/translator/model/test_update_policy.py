from unittest import TestCase

from samtranslator.model.update_policy import UpdatePolicy


class TestUpdatePolicy(TestCase):
    def test_to_dict_only_application_and_deployment_group(self):
        expected_dict = {
            "CodeDeployLambdaAliasUpdate": {
                "ApplicationName": "application_name",
                "DeploymentGroupName": "deployment_group_name",
            }
        }
        update_policy_dict = UpdatePolicy("application_name", "deployment_group_name", None, None).to_dict()

        self.assertEqual(expected_dict, update_policy_dict)

    def test_to_dict_all_fields(self):
        expected_dict = {
            "CodeDeployLambdaAliasUpdate": {
                "ApplicationName": "application_name",
                "DeploymentGroupName": "deployment_group_name",
                "BeforeAllowTrafficHook": "before_allow_traffic_hook",
                "AfterAllowTrafficHook": "after_allow_traffic_hook",
            }
        }
        update_policy_dict = UpdatePolicy(
            "application_name", "deployment_group_name", "before_allow_traffic_hook", "after_allow_traffic_hook"
        ).to_dict()

        self.assertEqual(expected_dict, update_policy_dict)
