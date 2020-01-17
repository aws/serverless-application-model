from mock import patch
from unittest import TestCase

from samtranslator.model.codedeploy import CodeDeployApplication
from samtranslator.model.codedeploy import CodeDeployDeploymentGroup
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.iam import IAMRole
from samtranslator.model.preferences.deployment_preference import DeploymentPreference
from samtranslator.model.preferences.deployment_preference_collection import CODEDEPLOY_APPLICATION_LOGICAL_ID
from samtranslator.model.preferences.deployment_preference_collection import CODE_DEPLOY_SERVICE_ROLE_LOGICAL_ID
from samtranslator.model.preferences.deployment_preference_collection import DeploymentPreferenceCollection


class TestDeploymentPreferenceCollection(TestCase):
    def setup_method(self, method):
        self.deployment_type_global = "AllAtOnce"
        self.alarms_global = [{"Ref": "alarm1"}, {"Ref": "alarm2"}]
        self.post_traffic_host_global = "post_traffic_function_ref"
        self.pre_traffic_hook_global = "pre_traffic_function_ref"
        self.function_logical_id = "FunctionLogicalId"

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_when_no_global_dict_each_local_deployment_preference_requires_parameters(self):
        with self.assertRaises(InvalidResourceException):
            DeploymentPreferenceCollection().add("", dict())

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_add_when_logical_id_previously_added_raises_value_error(self):
        with self.assertRaises(ValueError):
            deployment_preference_collection = DeploymentPreferenceCollection()
            deployment_preference_collection.add("1", {"Type": "Canary"})
            deployment_preference_collection.add("1", {"Type": "Linear"})

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_codedeploy_application(self):
        expected_codedeploy_application_resource = CodeDeployApplication(CODEDEPLOY_APPLICATION_LOGICAL_ID)
        expected_codedeploy_application_resource.ComputePlatform = "Lambda"

        self.assertEqual(
            DeploymentPreferenceCollection().codedeploy_application.to_dict(),
            expected_codedeploy_application_resource.to_dict(),
        )

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_codedeploy_iam_role(self):
        expected_codedeploy_iam_role = IAMRole("CodeDeployServiceRole")
        expected_codedeploy_iam_role.AssumeRolePolicyDocument = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": ["sts:AssumeRole"],
                    "Effect": "Allow",
                    "Principal": {"Service": ["codedeploy.amazonaws.com"]},
                }
            ],
        }
        expected_codedeploy_iam_role.ManagedPolicyArns = [
            "arn:aws:iam::aws:policy/service-role/AWSCodeDeployRoleForLambda"
        ]

        self.assertEqual(
            DeploymentPreferenceCollection().codedeploy_iam_role.to_dict(), expected_codedeploy_iam_role.to_dict()
        )

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_deployment_group_with_minimal_parameters(self):
        expected_deployment_group = CodeDeployDeploymentGroup(self.function_logical_id + "DeploymentGroup")
        expected_deployment_group.ApplicationName = {"Ref": CODEDEPLOY_APPLICATION_LOGICAL_ID}
        expected_deployment_group.AutoRollbackConfiguration = {
            "Enabled": True,
            "Events": ["DEPLOYMENT_FAILURE", "DEPLOYMENT_STOP_ON_ALARM", "DEPLOYMENT_STOP_ON_REQUEST"],
        }
        expected_deployment_group.DeploymentConfigName = {
            "Fn::Sub": ["CodeDeployDefault.Lambda${ConfigName}", {"ConfigName": self.deployment_type_global}]
        }
        expected_deployment_group.DeploymentStyle = {
            "DeploymentType": "BLUE_GREEN",
            "DeploymentOption": "WITH_TRAFFIC_CONTROL",
        }
        expected_deployment_group.ServiceRoleArn = {"Fn::GetAtt": [CODE_DEPLOY_SERVICE_ROLE_LOGICAL_ID, "Arn"]}

        deployment_preference_collection = DeploymentPreferenceCollection()
        deployment_preference_collection.add(self.function_logical_id, {"Type": self.deployment_type_global})
        deployment_group = deployment_preference_collection.deployment_group(self.function_logical_id)

        self.assertEqual(deployment_group.to_dict(), expected_deployment_group.to_dict())

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_deployment_preference_with_codedeploy_custom_configuration(self):
        deployment_type = "TestDeploymentConfiguration"
        deployment_preference_collection = DeploymentPreferenceCollection()
        deployment_preference_collection.add(self.function_logical_id, {"Type": deployment_type})
        deployment_group = deployment_preference_collection.deployment_group(self.function_logical_id)

        self.assertEqual(deployment_type, deployment_group.DeploymentConfigName)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_deployment_preference_with_codedeploy_predifined_configuration(self):
        deployment_type = "Canary10Percent5Minutes"
        expected_deployment_config_name = {
            "Fn::Sub": ["CodeDeployDefault.Lambda${ConfigName}", {"ConfigName": deployment_type}]
        }
        deployment_preference_collection = DeploymentPreferenceCollection()
        deployment_preference_collection.add(self.function_logical_id, {"Type": deployment_type})
        deployment_group = deployment_preference_collection.deployment_group(self.function_logical_id)

        print(deployment_group.DeploymentConfigName)
        self.assertEqual(expected_deployment_config_name, deployment_group.DeploymentConfigName)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_deployment_preference_with_conditional_custom_configuration(self):
        deployment_type = {
            "Fn::If": [
                "IsDevEnv",
                {"Fn::If": ["IsDevEnv1", "AllAtOnce", "TestDeploymentConfiguration"]},
                "Canary10Percent15Minutes",
            ]
        }

        expected_deployment_config_name = {
            "Fn::If": [
                "IsDevEnv",
                {
                    "Fn::If": [
                        "IsDevEnv1",
                        {"Fn::Sub": ["CodeDeployDefault.Lambda${ConfigName}", {"ConfigName": "AllAtOnce"}]},
                        "TestDeploymentConfiguration",
                    ]
                },
                {"Fn::Sub": ["CodeDeployDefault.Lambda${ConfigName}", {"ConfigName": "Canary10Percent15Minutes"}]},
            ]
        }
        deployment_preference_collection = DeploymentPreferenceCollection()
        deployment_preference_collection.add(self.function_logical_id, {"Type": deployment_type})
        deployment_group = deployment_preference_collection.deployment_group(self.function_logical_id)
        print(deployment_group.DeploymentConfigName)
        self.assertEqual(expected_deployment_config_name, deployment_group.DeploymentConfigName)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_deployment_group_with_all_parameters(self):
        expected_deployment_group = CodeDeployDeploymentGroup(self.function_logical_id + "DeploymentGroup")
        expected_deployment_group.AlarmConfiguration = {
            "Enabled": True,
            "Alarms": [{"Name": {"Ref": "alarm1"}}, {"Name": {"Ref": "alarm2"}}],
        }
        expected_deployment_group.ApplicationName = {"Ref": CODEDEPLOY_APPLICATION_LOGICAL_ID}
        expected_deployment_group.AutoRollbackConfiguration = {
            "Enabled": True,
            "Events": ["DEPLOYMENT_FAILURE", "DEPLOYMENT_STOP_ON_ALARM", "DEPLOYMENT_STOP_ON_REQUEST"],
        }
        expected_deployment_group.DeploymentConfigName = {
            "Fn::Sub": ["CodeDeployDefault.Lambda${ConfigName}", {"ConfigName": self.deployment_type_global}]
        }
        expected_deployment_group.DeploymentStyle = {
            "DeploymentType": "BLUE_GREEN",
            "DeploymentOption": "WITH_TRAFFIC_CONTROL",
        }
        expected_deployment_group.ServiceRoleArn = {"Fn::GetAtt": [CODE_DEPLOY_SERVICE_ROLE_LOGICAL_ID, "Arn"]}

        deployment_preference_collection = DeploymentPreferenceCollection()
        deployment_preference_collection.add(self.function_logical_id, self.global_deployment_preference_yaml_dict())
        deployment_group = deployment_preference_collection.deployment_group(self.function_logical_id)

        self.assertEqual(deployment_group.to_dict(), expected_deployment_group.to_dict())

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_update_policy_with_minimal_parameters(self):
        expected_update_policy = {
            "CodeDeployLambdaAliasUpdate": {
                "ApplicationName": {"Ref": CODEDEPLOY_APPLICATION_LOGICAL_ID},
                "DeploymentGroupName": {"Ref": self.function_logical_id + "DeploymentGroup"},
            }
        }

        deployment_preference_collection = DeploymentPreferenceCollection()
        deployment_preference_collection.add(self.function_logical_id, {"Type": "CANARY"})
        update_policy = deployment_preference_collection.update_policy(self.function_logical_id)

        self.assertEqual(expected_update_policy, update_policy.to_dict())

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_update_policy_with_all_parameters(self):
        expected_update_polcy = {
            "CodeDeployLambdaAliasUpdate": {
                "ApplicationName": {"Ref": CODEDEPLOY_APPLICATION_LOGICAL_ID},
                "DeploymentGroupName": {"Ref": self.function_logical_id + "DeploymentGroup"},
                "BeforeAllowTrafficHook": self.pre_traffic_hook_global,
                "AfterAllowTrafficHook": self.post_traffic_host_global,
            }
        }

        deployment_preference_collection = DeploymentPreferenceCollection()
        deployment_preference_collection.add(self.function_logical_id, self.global_deployment_preference_yaml_dict())
        update_policy = deployment_preference_collection.update_policy(self.function_logical_id)

        self.assertEqual(expected_update_polcy, update_policy.to_dict())

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_any_enabled_true_if_one_of_three_enabled(self):
        deployment_preference_collection = DeploymentPreferenceCollection()
        deployment_preference_collection.add("1", {"Type": "LINEAR"})
        deployment_preference_collection.add("2", {"Type": "LINEAR", "Enabled": False})
        deployment_preference_collection.add("3", {"Type": "CANARY", "Enabled": False})

        self.assertTrue(deployment_preference_collection.any_enabled())

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_any_enabled_true_if_all_of_three_enabled(self):
        deployment_preference_collection = DeploymentPreferenceCollection()
        deployment_preference_collection.add("1", {"Type": "LINEAR"})
        deployment_preference_collection.add("2", {"Type": "LINEAR", "Enabled": True})
        deployment_preference_collection.add("3", {"Type": "CANARY", "Enabled": True})

        self.assertTrue(deployment_preference_collection.any_enabled())

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_any_enabled_false_if_all_of_three_disabled(self):
        deployment_preference_collection = DeploymentPreferenceCollection()
        deployment_preference_collection.add("1", {"Type": "Linear", "Enabled": False})
        deployment_preference_collection.add("2", {"Type": "LINEAR", "Enabled": False})
        deployment_preference_collection.add("3", {"Type": "CANARY", "Enabled": False})

        self.assertFalse(deployment_preference_collection.any_enabled())

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_enabled_logical_ids_returns_one_if_one_of_three_enabled(self):
        deployment_preference_collection = DeploymentPreferenceCollection()
        enabled_logical_id = "1"
        deployment_preference_collection.add(enabled_logical_id, {"Type": "LINEAR"})
        deployment_preference_collection.add("2", {"Type": "LINEAR", "Enabled": False})
        deployment_preference_collection.add("3", {"Type": "CANARY", "Enabled": False})

        enabled_logical_ids = deployment_preference_collection.enabled_logical_ids()
        self.assertEqual(1, len(enabled_logical_ids))
        self.assertEqual(enabled_logical_id, enabled_logical_ids[0])

    def global_deployment_preference_yaml_dict(self):
        deployment_preference_yaml_dict = dict()
        deployment_preference_yaml_dict["Type"] = self.deployment_type_global
        deployment_preference_yaml_dict["Hooks"] = {
            "PreTraffic": self.pre_traffic_hook_global,
            "PostTraffic": self.post_traffic_host_global,
        }
        deployment_preference_yaml_dict["Alarms"] = self.alarms_global
        return deployment_preference_yaml_dict

    def global_deployment_preference(self):
        expected_deployment_preference = DeploymentPreference(
            self.deployment_type_global,
            self.pre_traffic_hook_global,
            self.post_traffic_host_global,
            self.alarms_global,
            True,
        )
        return expected_deployment_preference
