from typing import List
from unittest import TestCase
from unittest.mock import patch

from samtranslator.model import Resource
from samtranslator.model.capacity_provider.generators import CapacityProviderGenerator
from samtranslator.model.capacity_provider.resources import LambdaCapacityProvider
from samtranslator.model.intrinsics import fnGetAtt

# SAM should generate
#  - CapacityProvider
#  - OperatorRole
EXECPTED_SAM_AUTO_GENERATED_RESOURCES = 2


class TestCapacityProviderGenerator(TestCase):

    def setUp(self):
        self.logical_id = "MyCapacityProvider"
        self.vpc_config = {"SubnetIds": ["subnet-123", "subnet-456"], "SecurityGroupIds": ["sg-123"]}
        self.operator_role = "arn:aws:iam::123456789012:role/test"
        self.tags = {"Environment": "Production"}
        self.instance_requirements = {
            "Architectures": ["arm64"],
            "AllowedTypes": ["c5.xlarge"],
            "ExcludedTypes": ["t2.micro"],
        }
        self.scaling_config = {
            "MaxVCpuCount": 10,
            "AverageCPUUtilization": 70.0,
        }
        self.kms_key_arn = "arn:aws:kms:us-west-2:123456789012:key/abcd1234-ab12-cd34-ef56-abcdef123456"
        self.depends_on = ["AnotherResource"]
        self.resource_attributes = {"DeletionPolicy": "Retain"}
        self.passthrough_resource_attributes = {"Condition": "MyCondition"}

    def test_init(self):
        """Test initialization of CapacityProviderGenerator"""
        generator = CapacityProviderGenerator(
            self.logical_id,
            capacity_provider_name="test-provider",
            vpc_config=self.vpc_config,
            operator_role=self.operator_role,
            tags=self.tags,
            instance_requirements=self.instance_requirements,
            scaling_config=self.scaling_config,
            kms_key_arn=self.kms_key_arn,
            depends_on=self.depends_on,
            resource_attributes=self.resource_attributes,
            passthrough_resource_attributes=self.passthrough_resource_attributes,
        )

        self.assertEqual(generator.logical_id, self.logical_id)
        self.assertEqual(generator.capacity_provider_name, "test-provider")
        self.assertEqual(generator.vpc_config, self.vpc_config)
        self.assertEqual(generator.operator_role, self.operator_role)
        self.assertEqual(generator.tags, self.tags)
        self.assertEqual(generator.instance_requirements, self.instance_requirements)
        self.assertEqual(generator.scaling_config, self.scaling_config)
        self.assertEqual(generator.kms_key_arn, self.kms_key_arn)
        self.assertEqual(generator.depends_on, self.depends_on)
        self.assertEqual(generator.resource_attributes, self.resource_attributes)
        self.assertEqual(generator.passthrough_resource_attributes, self.passthrough_resource_attributes)

    def test_to_cloudformation_with_provided_permissions(self):
        """Test to_cloudformation with provided operator role"""
        operator_role = "arn:aws:iam::123456789012:role/test"

        generator = CapacityProviderGenerator(
            self.logical_id,
            capacity_provider_name="test-provider",
            vpc_config=self.vpc_config,
            operator_role=operator_role,
            tags=self.tags,
            instance_requirements=self.instance_requirements,
            scaling_config=self.scaling_config,
            kms_key_arn=self.kms_key_arn,
        )

        resources = generator.to_cloudformation()

        # Should only create the capacity provider resource
        self.assertEqual(len(resources), 1)
        self.assertIsInstance(resources[0], LambdaCapacityProvider)

        resources = self.extract_resource(resources)

        # Verify capacity provider properties
        capacity_provider = resources[self.logical_id]
        self.assertIsNotNone(capacity_provider)

        # Use to_dict() to verify properties
        properties = capacity_provider["Properties"]
        self.assertEqual(properties["CapacityProviderName"], "test-provider")
        self.assertEqual(
            properties["VpcConfig"], {"SubnetIds": ["subnet-123", "subnet-456"], "SecurityGroupIds": ["sg-123"]}
        )
        self.assertEqual(properties["PermissionsConfig"]["CapacityProviderOperatorRoleArn"], operator_role)
        self.assertEqual(properties["KmsKeyArn"], self.kms_key_arn)

    def test_to_cloudformation_with_auto_generated_permissions(self):
        """Test to_cloudformation with auto-generated operator role"""
        generator = CapacityProviderGenerator(
            self.logical_id,
            capacity_provider_name="test-provider",
            vpc_config=self.vpc_config,
            operator_role=None,
            tags=self.tags,
            instance_requirements=self.instance_requirements,
            scaling_config=self.scaling_config,
            kms_key_arn=self.kms_key_arn,
        )

        resources = generator.to_cloudformation()

        # Should create capacity provider and operator role (2 resources)
        self.assertEqual(len(resources), 2)

        resources = self.extract_resource(resources)

        capacity_provider = resources[self.logical_id]
        operator_role = resources[f"{self.logical_id}OperatorRole"]

        # Verify capacity provider
        self.assertEqual(capacity_provider["Type"], "AWS::Lambda::CapacityProvider")
        self.assertIn({"Key": "lambda:createdBy", "Value": "SAM"}, capacity_provider["Properties"]["Tags"])
        self.assertIn({"Key": "Environment", "Value": "Production"}, capacity_provider["Properties"]["Tags"])
        capacity_provider_properties = capacity_provider["Properties"]
        self.assertEqual(
            capacity_provider_properties["PermissionsConfig"]["CapacityProviderOperatorRoleArn"],
            fnGetAtt(f"{self.logical_id}OperatorRole", "Arn"),
        )

        # Verify operator role
        self.assertEqual(operator_role["Type"], "AWS::IAM::Role")
        self.assertIn({"Key": "lambda:createdBy", "Value": "SAM"}, operator_role["Properties"]["Tags"])
        self.assertNotIn({"Key": "Environment", "Value": "Production"}, operator_role["Properties"]["Tags"])

    def test_transform_instance_requirements(self):
        """Test _transform_instance_requirements method"""
        generator = CapacityProviderGenerator(self.logical_id, instance_requirements=self.instance_requirements)

        result = generator._transform_instance_requirements()

        self.assertEqual(
            result,
            {"Architectures": ["arm64"], "AllowedInstanceTypes": ["c5.xlarge"], "ExcludedInstanceTypes": ["t2.micro"]},
        )

    def test_transform_scaling_config_with_manual_policies(self):
        """Test _transform_scaling_config method with manual scaling policies"""
        generator = CapacityProviderGenerator(self.logical_id, scaling_config=self.scaling_config)

        result = generator._transform_scaling_config()

        self.assertEqual(
            result,
            {
                "MaxVCpuCount": 10,
                "ScalingMode": "Manual",
                "ScalingPolicies": [
                    {"PredefinedMetricType": "LambdaCapacityProviderAverageCPUUtilization", "TargetValue": 70.0},
                ],
            },
        )

    def test_transform_scaling_config_without_manual_policies(self):
        """Test _transform_scaling_config method without manual scaling policies"""
        scaling_config = {"MaxVCpuCount": 10}
        generator = CapacityProviderGenerator(self.logical_id, scaling_config=scaling_config)

        result = generator._transform_scaling_config()

        self.assertEqual(result, {"MaxVCpuCount": 10, "ScalingMode": "Auto"})

    def test_transform_tags(self):
        """Test _transform_tags method"""
        generator = CapacityProviderGenerator(self.logical_id, tags=self.tags)

        result = generator._transform_tags(self.tags)

        # Should include SAM tag and user-provided tags
        self.assertEqual(len(result), 2)
        self.assertIn({"Key": "lambda:createdBy", "Value": "SAM"}, result)
        self.assertIn({"Key": "Environment", "Value": "Production"}, result)

    def test_create_operator_role(self):
        """Test _create_operator_role method"""
        generator = CapacityProviderGenerator(
            self.logical_id, passthrough_resource_attributes=self.passthrough_resource_attributes
        )

        with patch("samtranslator.model.capacity_provider.generators.ArnGenerator") as mock_arn_generator:
            mock_arn_generator.generate_aws_managed_policy_arn.return_value = (
                "arn:aws:iam::aws:policy/AWSLambdaManagedEC2ResourceOperator"
            )

            result = generator._create_operator_role()

            self.assertEqual(result.logical_id, f"{self.logical_id}OperatorRole")

            # Use to_dict() to verify properties
            role_dict = result.to_dict()
            logical_id = f"{self.logical_id}OperatorRole"
            properties = role_dict[logical_id]["Properties"]

            # Verify assume role policy document
            assume_role_policy = properties["AssumeRolePolicyDocument"]
            self.assertEqual(assume_role_policy["Version"], "2012-10-17")
            self.assertEqual(len(assume_role_policy["Statement"]), 1)
            self.assertEqual(assume_role_policy["Statement"][0]["Principal"]["Service"], ["lambda.amazonaws.com"])

            # Verify managed policy ARNs
            self.assertEqual(len(properties["ManagedPolicyArns"]), 1)
            self.assertEqual(
                properties["ManagedPolicyArns"][0],
                "arn:aws:iam::aws:policy/AWSLambdaManagedEC2ResourceOperator",
            )

            # Verify passthrough attributes
            self.assertEqual(role_dict[logical_id]["Condition"], "MyCondition")

    def extract_resource(self, resource_array: List[Resource]):
        return {r.logical_id: r.to_dict()[r.logical_id] for r in resource_array}
