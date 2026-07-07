import logging
from unittest.case import skipIf

import pytest

from integration.helpers.base_test import BaseTest

LOG = logging.getLogger(__name__)


@skipIf(True, "NetworkConnector is not yet GA - enable when RIP feature flag is available")
class TestBasicNetworkConnector(BaseTest):
    """
    Basic AWS::Serverless::NetworkConnector tests
    """

    @pytest.fixture(autouse=True)
    def companion_stack_outputs(self, get_companion_stack_outputs):
        self.companion_stack_outputs = get_companion_stack_outputs

    def generate_nc_parameters(self):
        return [
            self.generate_parameter("SubnetId", self.companion_stack_outputs["LMISubnetId"]),
            self.generate_parameter("SecurityGroup", self.companion_stack_outputs["LMISecurityGroupId"]),
        ]

    def test_basic_network_connector(self):
        """
        Creates a NetworkConnector with auto-generated OperatorRole
        """
        parameters = self.generate_nc_parameters()
        self.create_and_verify_stack("single/basic_network_connector", parameters)

        # Verify the auto-generated OperatorRole exists and has correct trust policy
        role_name = self.get_physical_id_by_logical_id("MyNetworkConnectorOperatorRole")
        iam_client = self.client_provider.iam_client
        role = iam_client.get_role(RoleName=role_name)

        trust_policy = role["Role"]["AssumeRolePolicyDocument"]
        principals = []
        for stmt in trust_policy["Statement"]:
            if stmt["Effect"] != "Allow":
                continue
            service = stmt["Principal"].get("Service", [])
            if isinstance(service, str):
                principals.append(service)
            else:
                principals.extend(service)
        self.assertIn("lambda.amazonaws.com", principals)

        # Verify managed policy
        attached = iam_client.list_attached_role_policies(RoleName=role_name)
        policy_arns = [p["PolicyArn"] for p in attached["AttachedPolicies"]]
        self.assertTrue(
            any("AWSLambdaNetworkConnectorOperatorPolicy" in arn for arn in policy_arns),
            "OperatorRole should have AWSLambdaNetworkConnectorOperatorPolicy attached",
        )

    def test_network_connector_with_custom_role(self):
        """
        Creates a NetworkConnector with customer-provided OperatorRole (no auto-generation)
        """
        parameters = self.generate_nc_parameters()
        self.create_and_verify_stack("single/basic_network_connector_with_role", parameters)

        stack_resources = self.get_stack_resources("AWS::IAM::Role")
        role_logical_ids = [r["LogicalResourceId"] for r in stack_resources]

        self.assertIn("CustomOperatorRole", role_logical_ids)
        self.assertNotIn(
            "MyNetworkConnectorWithRoleOperatorRole",
            role_logical_ids,
            "Should NOT auto-generate OperatorRole when OperatorRole is provided",
        )
