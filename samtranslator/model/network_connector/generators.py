"""
AWS::Serverless::NetworkConnector resource transformer
"""

from typing import Any

from samtranslator.model import Resource
from samtranslator.model.iam import IAMRolePolicies
from samtranslator.model.intrinsics import fnGetAtt, fnSub, is_intrinsic
from samtranslator.model.network_connector.resources import LambdaNetworkConnector
from samtranslator.model.resource_policies import ResourcePolicies
from samtranslator.model.role_utils import construct_role_for_resource
from samtranslator.model.tags.resource_tagging import get_tag_list
from samtranslator.translator.arn_generator import ArnGenerator

# The compute resource types that may be associated with a network connector. Defaults to MicroVm
# (the original consumer) when a customer does not specify ComputeTypes on AWS::Serverless::NetworkConnector.
# Immutable so the shared default can never be mutated in place (the intrinsics resolver rewrites list
# elements of the generated template in place, and the translator process is reused across transforms).
DEFAULT_COMPUTE_TYPES = ("MicroVm",)

# The managed AWSLambdaNetworkConnectorOperatorPolicy doesn't grant Elastic IP permissions, so the generated
# operator role gets this statement when the connector may use service-managed Elastic IP addresses.
ELASTIC_IP_POLICY_NAME = "NetworkConnectorElasticIpPolicy"
ELASTIC_IP_DISABLED_TYPE = "None"


class NetworkConnectorGenerator:
    """
    Generator for Lambda NetworkConnector resources
    """

    def __init__(  # noqa: PLR0913
        self,
        logical_id: str,
        vpc_config: dict[str, Any],
        name: Any | None = None,
        compute_types: list[Any] | None = None,
        operator_role: Any | None = None,
        tags: dict[str, Any] | None = None,
        depends_on: list[str] | None = None,
        resource_attributes: dict[str, Any] | None = None,
        passthrough_resource_attributes: dict[str, Any] | None = None,
    ) -> None:
        self.logical_id = logical_id
        self.name = name
        self.vpc_config = vpc_config
        self.compute_types = list(compute_types) if compute_types else list(DEFAULT_COMPUTE_TYPES)
        self.operator_role = operator_role
        self.tags = tags
        self.depends_on = depends_on
        self.resource_attributes = resource_attributes
        self.passthrough_resource_attributes = passthrough_resource_attributes

    def to_cloudformation(self) -> list[Resource]:
        resources: list[Resource] = []

        if not self.operator_role:
            role = self._create_operator_role()
            resources.append(role)
            self.operator_role = fnGetAtt(role.logical_id, "Arn")

        connector = self._create_network_connector()
        resources.append(connector)

        return resources

    def _create_network_connector(self) -> LambdaNetworkConnector:
        connector = LambdaNetworkConnector(
            self.logical_id, depends_on=self.depends_on, attributes=self.resource_attributes
        )

        if self.name:
            connector.Name = self.name

        connector.Configuration = {
            "VpcEgressConfiguration": {
                **self.vpc_config,
                "AssociatedComputeResourceTypes": self.compute_types,
            }
        }
        connector.OperatorRole = self.operator_role
        connector.Tags = self._transform_tags(self.tags)

        if self.passthrough_resource_attributes:
            for attr_name, attr_value in self.passthrough_resource_attributes.items():
                connector.set_resource_attribute(attr_name, attr_value)

        return connector

    def _create_operator_role(self) -> Resource:
        role_logical_id = f"{self.logical_id}OperatorRole"

        assume_role_policy_document = IAMRolePolicies.construct_assume_role_policy_for_service_principal(
            "lambda.amazonaws.com"
        )

        tags = self._transform_tags()

        managed_policy_arns = [ArnGenerator.generate_aws_managed_policy_arn("AWSLambdaNetworkConnectorOperatorPolicy")]

        policy_documents = [self._elastic_ip_policy()] if self._may_use_elastic_ip() else None

        operator_role = construct_role_for_resource(
            resource_logical_id=self.logical_id,
            attributes=self.passthrough_resource_attributes,
            managed_policy_map=None,
            assume_role_policy_document=assume_role_policy_document,
            resource_policies=ResourcePolicies({}),
            managed_policy_arns=managed_policy_arns,
            policy_documents=policy_documents,
            tags=tags,
        )

        operator_role.logical_id = role_logical_id

        return operator_role

    def _may_use_elastic_ip(self) -> bool:
        """
        Whether the connector may use service-managed Elastic IP addresses. An intrinsic Type (or configuration)
        can't be resolved at transform time, so only an omitted configuration or a literal "None" Type is treated
        as not using Elastic IP addresses.
        """
        elastic_ip_config = self.vpc_config.get("ElasticIpConfiguration") if isinstance(self.vpc_config, dict) else None
        if elastic_ip_config is None:
            return False
        if not isinstance(elastic_ip_config, dict) or is_intrinsic(elastic_ip_config):
            return True
        return bool(elastic_ip_config.get("Type") != ELASTIC_IP_DISABLED_TYPE)

    @staticmethod
    def _elastic_ip_policy() -> dict[str, Any]:
        return {
            "PolicyName": ELASTIC_IP_POLICY_NAME,
            "PolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        # Allocating only creates new addresses.
                        "Effect": "Allow",
                        "Action": "ec2:AllocateAddress",
                        "Resource": fnSub("arn:${AWS::Partition}:ec2:*:*:elastic-ip/*"),
                    },
                    {
                        # Only addresses tagged for a connector.
                        "Effect": "Allow",
                        "Action": "ec2:AssociateAddress",
                        "Resource": fnSub("arn:${AWS::Partition}:ec2:*:*:elastic-ip/*"),
                        "Condition": {"StringLike": {"aws:ResourceTag/aws:lambda:networkConnectorId": "nc-*"}},
                    },
                    {
                        # Both actions also apply to the network interface; limit them to the connector's own ENIs.
                        "Effect": "Allow",
                        "Action": ["ec2:AllocateAddress", "ec2:AssociateAddress"],
                        "Resource": fnSub("arn:${AWS::Partition}:ec2:*:*:network-interface/*"),
                        "Condition": {
                            "StringEquals": {"ec2:ManagedResourceOperator": "network-connectors.lambda.amazonaws.com"}
                        },
                    },
                ],
            },
        }

    def _transform_tags(self, tags: dict[str, Any] | None = None) -> list[dict[str, str]]:
        tags_dict = (tags or {}).copy()
        tags_dict["lambda:createdBy"] = "SAM"
        return get_tag_list(tags_dict)
