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

    def generate_lmi_parameters(self):
        return [
            self.generate_parameter("SubnetId", self.companion_stack_outputs["LMISubnetId"]),
            self.generate_parameter("SecurityGroup", self.companion_stack_outputs["LMISecurityGroupId"]),
            self.generate_parameter("KMSKeyArn", self.companion_stack_outputs["LMIKMSKeyArn"]),
        ]

    def verify_capacity_provider_basic_config(self, cp_config, cp_name):
        """Verify basic capacity provider configuration (state, existence) and return ARN."""
        self.assertIsNotNone(cp_config, f"{cp_name} should have configuration")
        self.assertEqual(cp_config["State"], "Active", f"{cp_name} should be in Active state")
        capacity_provider_arn = cp_config.get("CapacityProviderArn")
        self.assertIsNotNone(capacity_provider_arn, f"{cp_name} should have a capacity provider ARN")
        return capacity_provider_arn

    def verify_capacity_provider_vpc_config(self, vpc_config, cp_name):
        """Verify capacity provider VPC configuration matches companion stack outputs."""
        self.assertIsNotNone(vpc_config, f"{cp_name} should have VPC configuration")
        self.assertIn(
            self.companion_stack_outputs["LMISubnetId"],
            vpc_config["SubnetIds"],
            f"{cp_name} should use the correct subnet",
        )
        self.assertIn(
            self.companion_stack_outputs["LMISecurityGroupId"],
            vpc_config["SecurityGroupIds"],
            f"{cp_name} should use the correct security group",
        )

    def verify_capacity_provider_permissions_config(self, permissions_config, cp_name):
        """Verify capacity provider has permissions configuration with operator role."""
        self.assertIsNotNone(permissions_config, f"{cp_name} should have permissions configuration")
        operator_role_arn = permissions_config.get("CapacityProviderOperatorRoleArn")
        self.assertIsNotNone(operator_role_arn, f"{cp_name} should have operator role ARN")
        return operator_role_arn

    def verify_function_capacity_provider_config(self, function_capacity_provider_config):
        """Verify and extract capacity provider ARN from function configuration."""
        self.assertIsNotNone(function_capacity_provider_config, "Function should have capacity provider configuration")
        self.assertIn(
            "LambdaManagedInstancesCapacityProviderConfig",
            function_capacity_provider_config,
            "Function LambdaManagedInstancesCapacityProviderConfig should have LambdaManagedInstancesCapacityProviderConfig",
        )

        lmi_config = function_capacity_provider_config["LambdaManagedInstancesCapacityProviderConfig"]
        function_capacity_provider_arn = lmi_config.get("CapacityProviderArn")
        self.assertIsNotNone(
            function_capacity_provider_arn, "Function capacity provider config should have a capacity provider ARN"
        )
        return function_capacity_provider_arn

    def verify_capacity_provider_arn_match(self, function_capacity_provider_arn, capacity_provider_arn):
        """Verify that the function references the correct capacity provider ARN."""
        self.assertEqual(
            function_capacity_provider_arn,
            capacity_provider_arn,
            "Function should reference the correct capacity provider ARN",
        )

    def test_function_with_capacity_provider_custom_role(self):
        """Test Lambda function with CapacityProviderConfig using custom operator role."""
        # Phase 1: Prepare parameters from companion stack
        parameters = self.generate_lmi_parameters()

        # Phase 2: Deploy and verify against expected JSON
        self.create_and_verify_stack("combination/function_lmi_custom", parameters)

        # Phase 3: Verify resource counts
        lambda_resources = self.get_stack_resources("AWS::Lambda::Function")
        self.assertEqual(len(lambda_resources), 1, "Should create exactly one Lambda function")

        capacity_provider_resources = self.get_stack_resources("AWS::Lambda::CapacityProvider")
        self.assertEqual(len(capacity_provider_resources), 1, "Should create exactly one CapacityProvider")

        # Phase 4: Validate function capacity provider configuration
        lambda_function = lambda_resources[0]

        function_capacity_provider_config = self.get_function_capacity_provider_config(
            lambda_function["PhysicalResourceId"]
        )
        function_capacity_provider_arn = self.verify_function_capacity_provider_config(
            function_capacity_provider_config
        )

        # Phase 5: Validate capacity provider details
        capacity_provider_config = self.get_lambda_capacity_provider_config("MyCapacityProvider")
        actual_capacity_provider_arn = self.verify_capacity_provider_basic_config(
            capacity_provider_config, "MyCapacityProvider"
        )

        # Verify the function uses the correct capacity provider ARN
        self.verify_capacity_provider_arn_match(function_capacity_provider_arn, actual_capacity_provider_arn)

        # Phase 6: Verify capacity provider uses custom operator role
        permissions_config = capacity_provider_config.get("PermissionsConfig")
        capacity_provider_operator_role_arn = self.verify_capacity_provider_permissions_config(
            permissions_config, "MyCapacityProvider"
        )

        # Get the physical ID of the custom role using its logical ID
        custom_operator_role_physical_id = self.get_physical_id_by_logical_id("MyCapacityProviderCustomRole")
        self.assertIsNotNone(custom_operator_role_physical_id, "MyCapacityProviderCustomRole should exist in the stack")

        # Verify the capacity provider uses the custom role by comparing physical IDs
        self.assertIn(
            custom_operator_role_physical_id,
            capacity_provider_operator_role_arn,
            f"Capacity provider should use the custom operator role with physical ID {custom_operator_role_physical_id}",
        )

    def test_function_with_capacity_provider_default_role(self):
        """Test Lambda function with CapacityProviderConfig using default operator role."""
        # Phase 1: Prepare parameters from companion stack
        parameters = self.generate_lmi_parameters()

        # Phase 2: Deploy and verify against expected JSON
        self.create_and_verify_stack("combination/function_lmi_default", parameters)

        # Phase 3: Verify resource counts
        lambda_resources = self.get_stack_resources("AWS::Lambda::Function")
        self.assertEqual(len(lambda_resources), 1, "Should create exactly one Lambda function")

        capacity_provider_resources = self.get_stack_resources("AWS::Lambda::CapacityProvider")
        self.assertEqual(len(capacity_provider_resources), 2, "Should create exactly two CapacityProviders")

        # Phase 4: Validate function capacity provider configuration
        my_function = lambda_resources[0]

        function_config = self.get_function_capacity_provider_config(my_function["PhysicalResourceId"])
        function_capacity_provider_arn = self.verify_function_capacity_provider_config(function_config)

        # Phase 5: Validate SimpleCapacityProvider configuration
        simple_cp_config = self.get_lambda_capacity_provider_config("SimpleCapacityProvider")
        simple_cp_arn = self.verify_capacity_provider_basic_config(simple_cp_config, "SimpleCapacityProvider")

        # Verify the function uses SimpleCapacityProvider
        self.verify_capacity_provider_arn_match(function_capacity_provider_arn, simple_cp_arn)

        # Verify SimpleCapacityProvider VPC configuration
        simple_vpc_config = simple_cp_config.get("VpcConfig")
        self.verify_capacity_provider_vpc_config(simple_vpc_config, "SimpleCapacityProvider")

        # Verify SimpleCapacityProvider uses SAM-generated default operator role
        simple_permissions_config = simple_cp_config.get("PermissionsConfig")
        self.verify_capacity_provider_permissions_config(simple_permissions_config, "SimpleCapacityProvider")

        # Phase 6: Validate AdvancedCapacityProvider configuration
        advanced_cp_config = self.get_lambda_capacity_provider_config("AdvancedCapacityProvider")
        self.verify_capacity_provider_basic_config(advanced_cp_config, "AdvancedCapacityProvider")

        # Verify AdvancedCapacityProvider VPC configuration
        advanced_vpc_config = advanced_cp_config.get("VpcConfig")
        self.verify_capacity_provider_vpc_config(advanced_vpc_config, "AdvancedCapacityProvider")

        # Verify AdvancedCapacityProvider permissions configuration
        advanced_permissions_config = advanced_cp_config.get("PermissionsConfig")
        self.verify_capacity_provider_permissions_config(advanced_permissions_config, "AdvancedCapacityProvider")

        # Verify AdvancedCapacityProvider instance requirements
        instance_requirements = advanced_cp_config.get("InstanceRequirements")
        self.assertIsNotNone(instance_requirements, "AdvancedCapacityProvider should have instance requirements")
        self.assertIn(
            "x86_64",
            instance_requirements.get("Architectures", []),
            "AdvancedCapacityProvider should have x86_64 architecture",
        )
        allowed_types = instance_requirements.get("AllowedInstanceTypes", [])
        self.assertIn("m5.large", allowed_types, "AdvancedCapacityProvider should allow m5.large")
        self.assertIn("m5.xlarge", allowed_types, "AdvancedCapacityProvider should allow m5.xlarge")
        self.assertIn("m5.2xlarge", allowed_types, "AdvancedCapacityProvider should allow m5.2xlarge")

        # Verify AdvancedCapacityProvider scaling configuration
        scaling_config = advanced_cp_config.get("CapacityProviderScalingConfig")
        self.assertIsNotNone(scaling_config, "AdvancedCapacityProvider should have scaling configuration")
        self.assertEqual(
            scaling_config.get("MaxVCpuCount"), 64, "AdvancedCapacityProvider should have MaxVCpuCount of 64"
        )
        scaling_policies = scaling_config.get("ScalingPolicies", [])
        self.assertTrue(len(scaling_policies) > 0, "AdvancedCapacityProvider should have scaling policies")
        cpu_policy = next(
            (
                p
                for p in scaling_policies
                if p.get("PredefinedMetricType") == "LambdaCapacityProviderAverageCPUUtilization"
            ),
            None,
        )
        self.assertIsNotNone(cpu_policy, "AdvancedCapacityProvider should have CPU utilization scaling policy")
        self.assertEqual(
            cpu_policy.get("TargetValue"), 70.0, "AdvancedCapacityProvider should have CPU utilization target of 70"
        )

        # Verify AdvancedCapacityProvider KMS key
        self.assertEqual(
            advanced_cp_config.get("KmsKeyArn"),
            self.companion_stack_outputs["LMIKMSKeyArn"],
            "AdvancedCapacityProvider should use the correct KMS key",
        )

    def get_function_capacity_provider_config(self, function_name, alias_name=None):
        lambda_client = self.client_provider.lambda_client

        try:
            # Build the function identifier - include alias if provided
            function_identifier = f"{function_name}:{alias_name}" if alias_name else function_name
            # Get the function configuration
            response = lambda_client.get_function_configuration(FunctionName=function_identifier)
            # Return the CapacityProviderConfig if it exists
            return response.get("CapacityProviderConfig")
        except Exception as e:
            # Log the error and return None for graceful handling
            print(f"Error getting function capacity provider config: {e}")
            return None

    def get_lambda_capacity_provider_config(self, capacity_provider_logical_id):
        lambda_client = self.client_provider.lambda_client

        try:
            # Get the physical ID from the logical ID
            capacity_provider_name = self.get_physical_id_by_logical_id(capacity_provider_logical_id)
            # Get the capacity provider configuration
            response = lambda_client.get_capacity_provider(CapacityProviderName=capacity_provider_name)
            return response.get("CapacityProvider")
        except Exception as e:
            # Log the error and return None for graceful handling
            print(f"Error getting capacity provider config for {capacity_provider_logical_id}: {e}")
            return None
