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
        capacity_provider = capacity_provider_resources[0]

        function_capacity_provider_config = self.get_function_capacity_provider_config(
            lambda_function["PhysicalResourceId"]
        )
        self.assertIsNotNone(function_capacity_provider_config, "Function should have capacity provider configuration")
        self.assertIn(
            "LambdaManagedInstancesCapacityProviderConfig",
            function_capacity_provider_config,
            "Function should have LambdaManagedInstancesCapacityProviderConfig",
        )

        lmi_config = function_capacity_provider_config["LambdaManagedInstancesCapacityProviderConfig"]
        function_capacity_provider_arn = lmi_config.get("CapacityProviderArn")
        self.assertIsNotNone(function_capacity_provider_arn, "Function should reference a capacity provider ARN")

        # Phase 5: Validate capacity provider details
        capacity_provider_config = self.get_lambda_capacity_provider_config(capacity_provider)
        self.assertIsNotNone(capacity_provider_config, "Capacity provider should have configuration")
        self.assertEqual(capacity_provider_config["State"], "Active", "Capacity provider should be in Active state")

        # Verify the function uses the correct capacity provider ARN
        actual_capacity_provider_arn = capacity_provider_config.get("CapacityProviderArn")
        self.assertEqual(
            function_capacity_provider_arn,
            actual_capacity_provider_arn,
            "Function should reference the correct capacity provider ARN",
        )

        # Phase 6: Verify capacity provider uses custom operator role
        permissions_config = capacity_provider_config.get("PermissionsConfig")
        self.assertIsNotNone(permissions_config, "Capacity provider should have permissions configuration")

        capacity_provider_operator_role_arn = permissions_config.get("CapacityProviderOperatorRoleArn")
        self.assertIsNotNone(
            capacity_provider_operator_role_arn, "Capacity provider should have custom operator role ARN"
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
        simple_capacity_provider = next(
            r for r in capacity_provider_resources if r["LogicalResourceId"] == "SimpleCapacityProvider"
        )
        advanced_capacity_provider = next(
            r for r in capacity_provider_resources if r["LogicalResourceId"] == "AdvancedCapacityProvider"
        )
        my_function = lambda_resources[0]

        function_config = self.get_function_capacity_provider_config(my_function["PhysicalResourceId"])
        self.assertIsNotNone(function_config, "Function should have capacity provider configuration")
        self.assertIn(
            "LambdaManagedInstancesCapacityProviderConfig",
            function_config,
            "Function should have LambdaManagedInstancesCapacityProviderConfig",
        )

        lmi_config = function_config["LambdaManagedInstancesCapacityProviderConfig"]
        function_capacity_provider_arn = lmi_config.get("CapacityProviderArn")
        self.assertIsNotNone(function_capacity_provider_arn, "Function should reference a capacity provider ARN")

        # Phase 5: Validate SimpleCapacityProvider configuration
        simple_cp_config = self.get_lambda_capacity_provider_config(simple_capacity_provider)
        self.assertIsNotNone(simple_cp_config, "SimpleCapacityProvider should have configuration")
        self.assertEqual(simple_cp_config["State"], "Active", "SimpleCapacityProvider should be in Active state")

        # Verify the function uses SimpleCapacityProvider
        simple_cp_arn = simple_cp_config.get("CapacityProviderArn")
        self.assertEqual(
            function_capacity_provider_arn, simple_cp_arn, "Function should reference SimpleCapacityProvider ARN"
        )

        # Verify SimpleCapacityProvider VPC configuration
        simple_vpc_config = simple_cp_config.get("VpcConfig")
        self.assertIsNotNone(simple_vpc_config, "SimpleCapacityProvider should have VPC configuration")
        self.assertIn(
            self.companion_stack_outputs["LMISubnetId"],
            simple_vpc_config["SubnetIds"],
            "SimpleCapacityProvider should use the correct subnet",
        )
        self.assertIn(
            self.companion_stack_outputs["LMISecurityGroupId"],
            simple_vpc_config["SecurityGroupIds"],
            "SimpleCapacityProvider should use the correct security group",
        )

        # Verify SimpleCapacityProvider uses SAM-generated default operator role
        simple_permissions_config = simple_cp_config.get("PermissionsConfig")
        self.assertIsNotNone(simple_permissions_config, "SimpleCapacityProvider should have permissions configuration")
        simple_operator_arn = simple_permissions_config.get("CapacityProviderOperatorRoleArn")
        self.assertIsNotNone(simple_operator_arn, "SimpleCapacityProvider should have operator role ARN")

        # Phase 6: Validate AdvancedCapacityProvider configuration
        advanced_cp_config = self.get_lambda_capacity_provider_config(advanced_capacity_provider)
        self.assertIsNotNone(advanced_cp_config, "AdvancedCapacityProvider should have configuration")
        self.assertEqual(advanced_cp_config["State"], "Active", "AdvancedCapacityProvider should be in Active state")

        # Verify AdvancedCapacityProvider VPC configuration
        advanced_vpc_config = advanced_cp_config.get("VpcConfig")
        self.assertIsNotNone(advanced_vpc_config, "AdvancedCapacityProvider should have VPC configuration")
        self.assertIn(
            self.companion_stack_outputs["LMISubnetId"],
            advanced_vpc_config["SubnetIds"],
            "AdvancedCapacityProvider should use the correct subnet",
        )
        self.assertIn(
            self.companion_stack_outputs["LMISecurityGroupId"],
            advanced_vpc_config["SecurityGroupIds"],
            "AdvancedCapacityProvider should use the correct security group",
        )

        # Verify AdvancedCapacityProvider permissions configuration
        advanced_permissions_config = advanced_cp_config.get("PermissionsConfig")
        self.assertIsNotNone(
            advanced_permissions_config,
            "AdvancedCapacityProvider should have permissions configuration",
        )

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

    def get_lambda_capacity_provider_config(self, capacity_provider_resource):
        lambda_client = self.client_provider.lambda_client

        try:
            # Extract capacity provider name from resource dict
            capacity_provider_name = capacity_provider_resource["PhysicalResourceId"]
            # Get the capacity provider configuration
            response = lambda_client.get_capacity_provider(CapacityProviderName=capacity_provider_name)
            return response.get("CapacityProvider")
        except Exception as e:
            # Log the error and return None for graceful handling
            print(f"Error getting capacity provider config for {capacity_provider_resource}: {e}")
            return None
