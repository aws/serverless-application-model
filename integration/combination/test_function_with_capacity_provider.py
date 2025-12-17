from unittest.case import skipIf

import pytest

from integration.config.service_names import LAMBDA_MANAGED_INSTANCES
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(
    current_region_does_not_support([LAMBDA_MANAGED_INSTANCES]),
    "LambdaManagedInstance is not supported in this testing region",
)
class TestFunctionWithCapacityProvider(BaseTest):
    @pytest.fixture(autouse=True)
    def companion_stack_outputs(self, get_companion_stack_outputs):
        self.companion_stack_outputs = get_companion_stack_outputs

    def test_function_with_capacity_provider_custom_role(self):
        """Test Lambda function with CapacityProviderConfig using custom operator role."""
        # Phase 1: Prepare parameters from companion stack
        parameters = [
            self.generate_parameter("SubnetId", self.companion_stack_outputs["LMISubnetId"]),
            self.generate_parameter("SecurityGroup", self.companion_stack_outputs["LMISecurityGroupId"]),
            self.generate_parameter("KMSKeyArn", self.companion_stack_outputs["LMIKMSKeyArn"]),
        ]

        # Phase 2: Deploy and verify against expected JSON
        self.create_and_verify_stack("combination/function_lmi_custom", parameters)

        # Phase 3: Verify resource counts
        lambda_resources = self.get_stack_resources("AWS::Lambda::Function")
        self.assertEqual(len(lambda_resources), 1, "Should create exactly one Lambda function")

        capacity_provider_resources = self.get_stack_resources("AWS::Lambda::CapacityProvider")
        self.assertEqual(len(capacity_provider_resources), 1, "Should create exactly one CapacityProvider")

        iam_role_resources = self.get_stack_resources("AWS::IAM::Role")
        self.assertEqual(len(iam_role_resources), 2, "Should create exactly two IAM roles")

    def test_function_with_capacity_provider_default_role(self):
        """Test Lambda function with CapacityProviderConfig using default operator role.

        Note: This test is skipped until 12/01/2024 because the managed policy required for
        the default operator role is not available until then.
        """
        # Phase 1: Prepare parameters from companion stack
        parameters = [
            self.generate_parameter("SubnetId", self.companion_stack_outputs["LMISubnetId"]),
            self.generate_parameter("SecurityGroup", self.companion_stack_outputs["LMISecurityGroupId"]),
            self.generate_parameter("KMSKeyArn", self.companion_stack_outputs["LMIKMSKeyArn"]),
        ]

        # Phase 2: Deploy and verify against expected JSON
        self.create_and_verify_stack("combination/function_lmi_default", parameters)

        # Phase 3: Verify resource counts
        lambda_resources = self.get_stack_resources("AWS::Lambda::Function")
        self.assertEqual(len(lambda_resources), 1, "Should create exactly one Lambda function")

        capacity_provider_resources = self.get_stack_resources("AWS::Lambda::CapacityProvider")
        self.assertEqual(len(capacity_provider_resources), 1, "Should create exactly one CapacityProvider")

        iam_role_resources = self.get_stack_resources("AWS::IAM::Role")
        self.assertEqual(len(iam_role_resources), 2, "Should create exactly two IAM roles")
