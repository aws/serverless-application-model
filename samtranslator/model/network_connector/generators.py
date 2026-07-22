"""
AWS::Serverless::NetworkConnector resource transformer
"""

from typing import Any

from samtranslator.model import Resource
from samtranslator.model.iam import IAMRolePolicies
from samtranslator.model.intrinsics import fnGetAtt
from samtranslator.model.network_connector.resources import LambdaNetworkConnector
from samtranslator.model.resource_policies import ResourcePolicies
from samtranslator.model.role_utils import construct_role_for_resource
from samtranslator.model.tags.resource_tagging import get_tag_list
from samtranslator.translator.arn_generator import ArnGenerator


class NetworkConnectorGenerator:
    """
    Generator for Lambda NetworkConnector resources
    """

    def __init__(  # noqa: PLR0913
        self,
        logical_id: str,
        vpc_config: dict[str, Any],
        name: Any | None = None,
        operator_role: Any | None = None,
        tags: dict[str, Any] | None = None,
        depends_on: list[str] | None = None,
        resource_attributes: dict[str, Any] | None = None,
        passthrough_resource_attributes: dict[str, Any] | None = None,
    ) -> None:
        self.logical_id = logical_id
        self.name = name
        self.vpc_config = vpc_config
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
                "AssociatedComputeResourceTypes": ["MicroVm"],
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

        operator_role = construct_role_for_resource(
            resource_logical_id=self.logical_id,
            attributes=self.passthrough_resource_attributes,
            managed_policy_map=None,
            assume_role_policy_document=assume_role_policy_document,
            resource_policies=ResourcePolicies({}),
            managed_policy_arns=managed_policy_arns,
            tags=tags,
        )

        operator_role.logical_id = role_logical_id

        return operator_role

    def _transform_tags(self, tags: dict[str, Any] | None = None) -> list[dict[str, str]]:
        tags_dict = (tags or {}).copy()
        tags_dict["lambda:createdBy"] = "SAM"
        return get_tag_list(tags_dict)
