from unittest.case import skipIf

from integration.config.service_names import STATE_MACHINE_WITH_APIS
from integration.helpers.base_test import BaseTest
from integration.helpers.common_api import get_policy_statements
from integration.helpers.resource import current_region_does_not_support


@skipIf(
    current_region_does_not_support([STATE_MACHINE_WITH_APIS]),
    "StateMachine with APIs is not supported in this testing region",
)
class TestStateMachineWithApi(BaseTest):
    def test_state_machine_with_api(self):
        self.create_and_verify_stack("combination/state_machine_with_api")
        outputs = self.get_stack_outputs()
        region = outputs["Region"]
        partition = outputs["Partition"]
        state_name_machine_arn = outputs["MyStateMachineArn"]
        implicit_api_role_name = outputs["MyImplicitApiRoleName"]
        implicit_api_role_arn = outputs["MyImplicitApiRoleArn"]
        explicit_api_role_name = outputs["MyExplicitApiRoleName"]
        explicit_api_role_arn = outputs["MyExplicitApiRoleArn"]

        rest_apis = self.get_stack_resources("AWS::ApiGateway::RestApi")
        implicit_rest_api_id = next(
            (x["PhysicalResourceId"] for x in rest_apis if x["LogicalResourceId"] == "ServerlessRestApi"), None
        )
        explicit_rest_api_id = next(
            (x["PhysicalResourceId"] for x in rest_apis if x["LogicalResourceId"] == "ExistingRestApi"), None
        )

        self._test_api_integration_with_state_machine(
            implicit_rest_api_id,
            "POST",
            "/pathpost",
            implicit_api_role_name,
            implicit_api_role_arn,
            "MyStateMachinePostApiRoleStartExecutionPolicy",
            state_name_machine_arn,
            partition,
            region,
        )
        self._test_api_integration_with_state_machine(
            explicit_rest_api_id,
            "GET",
            "/pathget",
            explicit_api_role_name,
            explicit_api_role_arn,
            "MyStateMachineGetApiRoleStartExecutionPolicy",
            state_name_machine_arn,
            partition,
            region,
        )

    def _test_api_integration_with_state_machine(
        self, api_id, method, path, role_name, role_arn, policy_name, state_machine_arn, partition, region
    ):
        apigw_client = self.client_provider.api_client

        resources = apigw_client.get_resources(restApiId=api_id)["items"]
        resource = get_resource_by_path(resources, path)

        post_method = apigw_client.get_method(restApiId=api_id, resourceId=resource["id"], httpMethod=method)
        method_integration = post_method["methodIntegration"]
        self.assertEqual(method_integration["credentials"], role_arn)

        # checking if the uri in the API integration is set for Step Functions State Machine execution
        expected_integration_uri = "arn:" + partition + ":apigateway:" + region + ":states:action/StartExecution"
        self.assertEqual(method_integration["uri"], expected_integration_uri)

        # checking if the role used by the event rule to trigger the state machine execution is correct
        start_execution_policy = get_policy_statements(role_name, policy_name, self.client_provider.iam_client)
        self.assertEqual(len(start_execution_policy), 1, "Only one statement must be in Start Execution policy")

        start_execution_policy_statement = start_execution_policy[0]

        self.assertFalse(isinstance(start_execution_policy_statement["Action"], list))
        policy_action = start_execution_policy_statement["Action"]
        self.assertEqual(
            policy_action,
            "states:StartExecution",
            "Action referenced in event role policy must be 'states:StartExecution'",
        )

        self.assertFalse(isinstance(start_execution_policy_statement["Resource"], list))
        referenced_state_machine_arn = start_execution_policy_statement["Resource"]
        self.assertEqual(
            referenced_state_machine_arn,
            state_machine_arn,
            "State machine referenced in event role policy is incorrect",
        )


def get_resource_by_path(resources, path):
    return next((resource for resource in resources if resource["path"] == path), None)
