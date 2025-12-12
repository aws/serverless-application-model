from unittest import TestCase

from samtranslator.model.capacity_provider.resources import LambdaCapacityProvider


class TestLambdaCapacityProvider(TestCase):
    def test_resource_type(self):
        """Test that the resource type is set correctly"""
        capacity_provider = LambdaCapacityProvider("MyCapacityProvider")
        self.assertEqual(capacity_provider.resource_type, "AWS::Lambda::CapacityProvider")

    def test_properties(self):
        """Test that properties are set correctly"""
        capacity_provider = LambdaCapacityProvider("MyCapacityProvider")

        # Set properties
        capacity_provider.CapacityProviderName = "test-provider"
        capacity_provider.VpcConfig = {"SubnetIds": ["subnet-123", "subnet-456"], "SecurityGroupIds": ["sg-123"]}
        capacity_provider.PermissionsConfig = {
            "InstanceProfileArn": "arn:aws:iam::123456789012:instance-profile/test",
            "CapacityProviderOperatorRoleArn": "arn:aws:iam::123456789012:role/test",
        }
        capacity_provider.Tags = [
            {"Key": "lambda:createdBy", "Value": "SAM"},
            {"Key": "Environment", "Value": "Production"},
        ]
        capacity_provider.InstanceRequirements = {"Architectures": ["arm64"], "AllowedInstanceTypes": ["c5.xlarge"]}
        capacity_provider.CapacityProviderScalingConfig = {
            "MaxVCpuCount": 10,
            "ScalingMode": "Manual",
            "ScalingPolicies": [
                {"PredefinedMetricType": "LambdaCapacityProviderAverageCPUUtilization", "TargetValue": 70.0}
            ],
        }
        capacity_provider.KmsKeyArn = "arn:aws:kms:us-west-2:123456789012:key/abcd1234-ab12-cd34-ef56-abcdef123456"

        # Verify properties
        self.assertEqual(capacity_provider.CapacityProviderName, "test-provider")
        self.assertEqual(
            capacity_provider.VpcConfig, {"SubnetIds": ["subnet-123", "subnet-456"], "SecurityGroupIds": ["sg-123"]}
        )
        self.assertEqual(
            capacity_provider.PermissionsConfig,
            {
                "InstanceProfileArn": "arn:aws:iam::123456789012:instance-profile/test",
                "CapacityProviderOperatorRoleArn": "arn:aws:iam::123456789012:role/test",
            },
        )
        self.assertEqual(
            capacity_provider.Tags,
            [{"Key": "lambda:createdBy", "Value": "SAM"}, {"Key": "Environment", "Value": "Production"}],
        )
        self.assertEqual(
            capacity_provider.InstanceRequirements, {"Architectures": ["arm64"], "AllowedInstanceTypes": ["c5.xlarge"]}
        )
        self.assertEqual(
            capacity_provider.CapacityProviderScalingConfig,
            {
                "MaxVCpuCount": 10,
                "ScalingMode": "Manual",
                "ScalingPolicies": [
                    {"PredefinedMetricType": "LambdaCapacityProviderAverageCPUUtilization", "TargetValue": 70.0}
                ],
            },
        )
        self.assertEqual(
            capacity_provider.KmsKeyArn, "arn:aws:kms:us-west-2:123456789012:key/abcd1234-ab12-cd34-ef56-abcdef123456"
        )

    def test_runtime_attributes(self):
        """Test that runtime attributes are generated correctly"""
        capacity_provider = LambdaCapacityProvider("MyCapacityProvider")

        # Test name attribute
        name_attr = capacity_provider.get_runtime_attr("name")
        self.assertEqual(name_attr, {"Ref": "MyCapacityProvider"})

        # Test arn attribute
        arn_attr = capacity_provider.get_runtime_attr("arn")
        self.assertEqual(arn_attr, {"Fn::GetAtt": ["MyCapacityProvider", "Arn"]})
