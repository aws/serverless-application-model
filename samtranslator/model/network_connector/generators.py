"""
AWS::Serverless::NetworkConnector resource transformer
"""

from typing import Any

from samtranslator.model import Resource
from samtranslator.model.iam import IAMRole, IAMRolePolicies
from samtranslator.model.intrinsics import fnGetAtt
from samtranslator.model.network_connector.resources import LambdaNetworkConnector
from samtranslator.model.tags.resource_tagging import get_tag_list


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

    def _create_operator_role(self) -> IAMRole:
        role_logical_id = f"{self.logical_id}OperatorRole"

        assume_role_policy = IAMRolePolicies.construct_assume_role_policy_for_service_principal("lambda.amazonaws.com")

        role = IAMRole(role_logical_id, attributes=self.passthrough_resource_attributes)
        role.AssumeRolePolicyDocument = assume_role_policy
        role.Policies = [
            {
                "PolicyName": "NetworkConnectorOperatorPolicy",
                "PolicyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "AllowCreateEniInAnySubnet",
                            "Effect": "Allow",
                            "Action": "ec2:CreateNetworkInterface",
                            "Resource": {"Fn::Sub": "arn:${AWS::Partition}:ec2:*:*:subnet/*"},
                        },
                        {
                            "Sid": "AllowCreateEniWithSecurityGroups",
                            "Effect": "Allow",
                            "Action": "ec2:CreateNetworkInterface",
                            "Resource": {"Fn::Sub": "arn:${AWS::Partition}:ec2:*:*:security-group/*"},
                        },
                        {
                            "Sid": "AllowCreateEniWithLambdaTagKeys",
                            "Effect": "Allow",
                            "Action": "ec2:CreateNetworkInterface",
                            "Resource": {"Fn::Sub": "arn:${AWS::Partition}:ec2:*:*:network-interface/*"},
                            "Condition": {
                                "ForAllValues:StringEquals": {
                                    "aws:TagKeys": [
                                        "aws:lambda:networkConnectorName",
                                        "aws:lambda:networkConnectorId",
                                    ]
                                }
                            },
                        },
                        {
                            "Sid": "TagENIOnCreate",
                            "Effect": "Allow",
                            "Action": "ec2:CreateTags",
                            "Resource": {"Fn::Sub": "arn:${AWS::Partition}:ec2:*:*:network-interface/*"},
                            "Condition": {
                                "StringEquals": {
                                    "ec2:CreateAction": "CreateNetworkInterface",
                                    "ec2:ManagedResourceOperator": "network-connectors.lambda.amazonaws.com",
                                }
                            },
                        },
                    ],
                },
            }
        ]

        role.Tags = self._transform_tags()

        return role

    def _transform_tags(self, tags: dict[str, Any] | None = None) -> list[dict[str, str]]:
        tags_dict = (tags or {}).copy()
        tags_dict["lambda:createdBy"] = "SAM"
        return get_tag_list(tags_dict)
