from unittest.case import skipIf

from integration.config.service_names import CODE_DEPLOY
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support, generate_suffix

CODEDEPLOY_APPLICATION_LOGICAL_ID = "ServerlessDeploymentApplication"
LAMBDA_FUNCTION_NAME = "MyLambdaFunction"
LAMBDA_ALIAS = "Live"


@skipIf(current_region_does_not_support([CODE_DEPLOY]), "CodeDeploy is not supported in this testing region")
class TestFunctionWithDeploymentPreference(BaseTest):
    def test_lambda_function_with_deployment_preference_uses_code_deploy(self):
        self.create_and_verify_stack("combination/function_with_deployment_basic")
        self._verify_no_deployment_then_update_and_verify_deployment()

    def test_lambda_function_with_custom_deployment_preference(self):
        custom_deployment_config_name = "CustomLambdaDeploymentConfiguration" + generate_suffix()
        parameters = [self.generate_parameter("DeployConfigName", custom_deployment_config_name)]

        self.create_and_verify_stack("combination/function_with_custom_code_deploy", parameters)
        self._verify_no_deployment_then_update_and_verify_deployment(parameters)

    def test_use_default_manage_policy(self):
        self.create_and_verify_stack("combination/function_with_deployment_default_role_managed_policy")
        self._verify_no_deployment_then_update_and_verify_deployment()

    def test_must_not_use_code_deploy(self):
        self.create_and_verify_stack(
            "combination/function_with_deployment_disabled", self.get_default_test_template_parameters()
        )
        # When disabled, there should be no CodeDeploy resources created. This was already verified above

    def test_flip_from_disable_to_enable(self):
        self.create_and_verify_stack(
            "combination/function_with_deployment_disabled", self.get_default_test_template_parameters()
        )

        pref = self.get_template_resource_property("MyLambdaFunction", "DeploymentPreference")
        pref["Enabled"] = "True"
        self.set_template_resource_property("MyLambdaFunction", "DeploymentPreference", pref)

        self.update_stack(self.get_default_test_template_parameters())

        self._verify_no_deployment_then_update_and_verify_deployment(self.get_default_test_template_parameters())

    def test_must_deploy_with_alarms_and_hooks(self):
        self.create_and_verify_stack("combination/function_with_deployment_alarms_and_hooks")
        self._verify_no_deployment_then_update_and_verify_deployment()

    def test_deployment_preference_in_globals(self):
        self.create_and_verify_stack("combination/function_with_deployment_globals")
        application_name = self.get_physical_id_by_type("AWS::CodeDeploy::Application")
        self.assertTrue(application_name in self._get_code_deploy_application())

        deployment_groups = self._get_deployment_groups(application_name)
        self.assertEqual(len(deployment_groups), 1)

        deployment_group_name = deployment_groups[0]
        deployment_config_name = self._get_deployment_group_configuration_name(deployment_group_name, application_name)
        self.assertEqual(deployment_config_name, "CodeDeployDefault.LambdaAllAtOnce")

    def _verify_no_deployment_then_update_and_verify_deployment(self, parameters=None):
        application_name = self.get_physical_id_by_type("AWS::CodeDeploy::Application")
        self.assertTrue(application_name in self._get_code_deploy_application())

        deployment_groups = self._get_deployment_groups(application_name)
        self.assertEqual(len(deployment_groups), 1)

        for deployment_group in deployment_groups:
            # Verify no deployments for deployment group before we make change to code uri forcing lambda deployment
            self.assertEqual(len(self._get_deployments(application_name, deployment_group)), 0)

        # Changing CodeUri should create a new version that deploys with CodeDeploy, and leave the existing version in stack
        self.set_template_resource_property(
            LAMBDA_FUNCTION_NAME, "CodeUri", self.file_to_s3_uri_map["code2.zip"]["uri"]
        )
        self.update_stack(parameters)

        for deployment_group in deployment_groups:
            deployments = self._get_deployments(application_name, deployment_group)
            self.assertEqual(len(deployments), 1)
            deployment_info = deployments[0]
            self.assertEqual(deployment_info["status"], "Succeeded")
            self._assert_deployment_contained_lambda_function_and_alias(
                deployment_info, LAMBDA_FUNCTION_NAME, LAMBDA_ALIAS
            )

    def _get_code_deploy_application(self):
        return self.client_provider.code_deploy_client.list_applications()["applications"]

    def _get_deployment_groups(self, application_name):
        return self.client_provider.code_deploy_client.list_deployment_groups(applicationName=application_name)[
            "deploymentGroups"
        ]

    def _get_deployments(self, application_name, deployment_group):
        deployments = self.client_provider.code_deploy_client.list_deployments(
            applicationName=application_name, deploymentGroupName=deployment_group
        )["deployments"]
        deployment_infos = [self._get_deployment_info(deployment_id) for deployment_id in deployments]
        return deployment_infos

    def _get_deployment_info(self, deployment_id):
        return self.client_provider.code_deploy_client.get_deployment(deploymentId=deployment_id)["deploymentInfo"]

    # Checks this deployment is connected to our specific lambda function and alias
    def _assert_deployment_contained_lambda_function_and_alias(
        self, deployment_info, lambda_function_name, lambda_alias
    ):
        instances = self._get_deployment_instances(deployment_info["deploymentId"])
        self.assertEqual(len(instances), 1)
        # Instance Ids for lambda functions in CodeDeploy have the pattern <lambda-function>:<alias>
        function_colon_alias = instances[0]
        self.assertTrue(":" in function_colon_alias)

        function_colon_alias_split = function_colon_alias.split(":")
        self.assertEqual(len(function_colon_alias_split), 2)
        self.assertEqual(
            function_colon_alias_split[0], self._get_physical_resource_id("AWS::Lambda::Function", lambda_function_name)
        )
        self.assertEqual(function_colon_alias_split[1], lambda_alias)

    def _get_deployment_instances(self, deployment_id):
        return self.client_provider.code_deploy_client.list_deployment_instances(deploymentId=deployment_id)[
            "instancesList"
        ]

    def _get_physical_resource_id(self, resource_type, logical_id):
        resources_with_this_type = self.get_stack_resources(resource_type)
        resources_with_this_id = next(
            (x for x in resources_with_this_type if x["LogicalResourceId"] == logical_id), None
        )
        return resources_with_this_id["PhysicalResourceId"]

    def _get_deployment_group_configuration_name(self, deployment_group_name, application_name):
        deployment_group = self.client_provider.code_deploy_client.get_deployment_group(
            applicationName=application_name, deploymentGroupName=deployment_group_name
        )
        return deployment_group["deploymentGroupInfo"]["deploymentConfigName"]
