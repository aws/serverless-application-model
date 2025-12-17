"""
AWS::Serverless::CapacityProvider resource transformer
"""

from typing import Any, Dict, List, Optional

from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.model import Resource
from samtranslator.model.capacity_provider.resources import LambdaCapacityProvider
from samtranslator.model.iam import IAMRole, IAMRolePolicies
from samtranslator.model.intrinsics import fnGetAtt
from samtranslator.model.resource_policies import ResourcePolicies
from samtranslator.model.role_utils.role_constructor import construct_role_for_resource
from samtranslator.model.tags.resource_tagging import get_tag_list
from samtranslator.translator.arn_generator import ArnGenerator


class CapacityProviderGenerator:
    """
    Generator for Lambda Capacity Provider resources
    """

    def __init__(self, logical_id: str, **kwargs: Any) -> None:
        """
        Initialize a CapacityProviderGenerator

        :param logical_id: Logical ID of the SAM Capacity Provider resource
        :param kwargs: Configuration parameters including:
            - capacity_provider_name: Name of the capacity provider
            - vpc_config: VPC configuration for the capacity provider
            - operator_role: IAM operator role ARN
            - tags: Resource tags
            - instance_requirements: Instance type requirements
            - scaling_config: Auto-scaling configuration
            - kms_key_arn: KMS key ARN for encryption
            - depends_on: Resources this capacity provider depends on
            - resource_attributes: Resource attributes to add to capacity provider
            - passthrough_resource_attributes: Resource attributes to pass to child resources
        """
        self.logical_id = logical_id
        self.capacity_provider_name = kwargs.get("capacity_provider_name")
        self.vpc_config = kwargs.get("vpc_config") or {}
        self.operator_role = kwargs.get("operator_role")
        self.tags = kwargs.get("tags")
        self.instance_requirements = kwargs.get("instance_requirements") or {}
        self.scaling_config = kwargs.get("scaling_config") or {}
        self.kms_key_arn = kwargs.get("kms_key_arn")
        self.depends_on = kwargs.get("depends_on")
        self.resource_attributes = kwargs.get("resource_attributes")
        self.passthrough_resource_attributes = kwargs.get("passthrough_resource_attributes")

    @cw_timer(prefix="Generator", name="CapacityProvider")
    def to_cloudformation(self) -> List[Resource]:
        """
        Transform the capacity provider configuration to CloudFormation resources

        :returns: List of CloudFormation resources
        """
        resources: List[Resource] = []

        # Create IAM roles if not provided;
        if not self.operator_role:
            # 1. Generate one and pass arn to capacity provider resource
            operator_iam_role: IAMRole = self._create_operator_role()
            resources.append(operator_iam_role)
            # 2. Pass ARN to capacity provider resource via self.operator_role
            self.operator_role = fnGetAtt(operator_iam_role.logical_id, "Arn")

        # Create the Lambda CapacityProvider resource
        capacity_provider = self._create_capacity_provider()
        resources.append(capacity_provider)

        return resources

    def _create_capacity_provider(self) -> LambdaCapacityProvider:
        """
        Create a Lambda CapacityProvider resource
        """
        capacity_provider = LambdaCapacityProvider(
            self.logical_id, depends_on=self.depends_on, attributes=self.resource_attributes
        )

        # Set the CapacityProviderName if provided
        if self.capacity_provider_name:
            capacity_provider.CapacityProviderName = self.capacity_provider_name

        # Clean up VpcConfig to remove None values for optional fields
        if self.vpc_config:
            vpc_config = {"SubnetIds": self.vpc_config["SubnetIds"]}
            if "SecurityGroupIds" in self.vpc_config and self.vpc_config["SecurityGroupIds"] is not None:
                vpc_config["SecurityGroupIds"] = self.vpc_config["SecurityGroupIds"]

            capacity_provider.VpcConfig = vpc_config

        # Set the OperatorRole if provided (will be updated later if role is auto-generated)
        if self.operator_role:
            capacity_provider.PermissionsConfig = {"CapacityProviderOperatorRoleArn": self.operator_role}

        # Set the Tags - always add SAM tag, plus any user-provided tags
        capacity_provider.Tags = self._transform_tags(self.tags)

        # Set the InstanceRequirements if provided
        if self.instance_requirements:
            capacity_provider.InstanceRequirements = self._transform_instance_requirements()

        # Set the ScalingConfig if provided
        if self.scaling_config:
            capacity_provider.CapacityProviderScalingConfig = self._transform_scaling_config()

        # Set the KMSKeyArn if provided
        if self.kms_key_arn:
            capacity_provider.KMSKeyArn = self.kms_key_arn

        # Pass through resource attributes
        if self.passthrough_resource_attributes:
            for attr_name, attr_value in self.passthrough_resource_attributes.items():
                capacity_provider.set_resource_attribute(attr_name, attr_value)

        return capacity_provider

    def _ensure_permissions_config(self, capacity_provider: LambdaCapacityProvider) -> None:
        """
        Ensure that the PermissionsConfig dictionary exists on the capacity provider
        """
        # Using getattr to avoid mypy unreachable statement error
        # This is because mypy thinks PermissionsConfig can never be None based on type definitions
        if getattr(capacity_provider, "PermissionsConfig", None) is None:
            capacity_provider.PermissionsConfig = {}

    def _transform_instance_requirements(self) -> Dict[str, Any]:
        """
        Transform the SAM InstanceRequirements to CloudFormation format
        """
        instance_requirements = {}

        if self.instance_requirements.get("Architectures") is not None:
            instance_requirements["Architectures"] = self.instance_requirements["Architectures"]

        if self.instance_requirements.get("AllowedTypes") is not None:
            instance_requirements["AllowedInstanceTypes"] = self.instance_requirements["AllowedTypes"]

        if self.instance_requirements.get("ExcludedTypes") is not None:
            instance_requirements["ExcludedInstanceTypes"] = self.instance_requirements["ExcludedTypes"]

        return instance_requirements

    def _transform_scaling_config(self) -> Dict[str, Any]:
        """
        Transform the SAM ScalingConfig to CloudFormation format
        """
        scaling_config = {}

        if self.scaling_config.get("MaxVCpuCount") is not None:
            scaling_config["MaxVCpuCount"] = self.scaling_config["MaxVCpuCount"]

        # Handle AverageCPUUtilization structure
        if self.scaling_config.get("AverageCPUUtilization") is not None:
            scaling_config["ScalingMode"] = "Manual"
            scaling_policies = []

            scaling_policies.append(
                {
                    "PredefinedMetricType": "LambdaCapacityProviderAverageCPUUtilization",
                    "TargetValue": self.scaling_config["AverageCPUUtilization"],
                }
            )

            scaling_config["ScalingPolicies"] = scaling_policies
        else:
            # Default to Auto scaling mode if no AverageCPUUtilization specified
            scaling_config["ScalingMode"] = "Auto"

        return scaling_config

    def _transform_tags(self, additional_tags: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """
        Helper function to generate tags with automatic SAM tag

        :param additional_tags: Optional additional tags to include
        :returns: List of tag dictionaries for CloudFormation
        """
        tags_dict = additional_tags.copy() if additional_tags else {}
        tags_dict["lambda:createdBy"] = "SAM"
        return get_tag_list(tags_dict)

    def _create_operator_role(self) -> IAMRole:
        """
        Create an IAM role for the Lambda capacity provider operator
        """

        role_logical_id = f"{self.logical_id}OperatorRole"

        # Use the IAM utility to create the assume role policy for Lambda
        assume_role_policy_document = IAMRolePolicies.lambda_assume_role_policy()

        # Create the SAM tag using the helper method
        tags = self._transform_tags()

        # Get the managed policy ARN with the correct partition
        managed_policy_arns = [ArnGenerator.generate_aws_managed_policy_arn("AWSLambdaManagedEC2ResourceOperator")]

        # Use the role constructor utility
        operator_role = construct_role_for_resource(
            resource_logical_id=self.logical_id,
            attributes=self.passthrough_resource_attributes,
            managed_policy_map=None,
            assume_role_policy_document=assume_role_policy_document,
            resource_policies=ResourcePolicies({}),  # Empty resource policies
            managed_policy_arns=managed_policy_arns,
            tags=tags,
        )

        # Override the logical ID to match the expected format
        operator_role.logical_id = role_logical_id

        return operator_role
