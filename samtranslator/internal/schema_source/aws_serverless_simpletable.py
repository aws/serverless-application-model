from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from samtranslator.internal.schema_source.aws_serverless_connector import EmbeddedConnector
from samtranslator.internal.schema_source.common import (
    BaseModel,
    PassThroughProp,
    ResourceAttributes,
    get_prop,
    passthrough_prop,
)

PROPERTIES_STEM = "sam-resource-simpletable"
PRIMARY_KEY_STEM = "sam-property-simpletable-primarykeyobject"

primarykey = get_prop(PRIMARY_KEY_STEM)
properties = get_prop(PROPERTIES_STEM)


class PrimaryKey(BaseModel):
    Name: PassThroughProp = passthrough_prop(
        PRIMARY_KEY_STEM,
        "Name",
        ["AWS::DynamoDB::Table.AttributeDefinition", "AttributeName"],
    )
    Type: PassThroughProp = passthrough_prop(
        PRIMARY_KEY_STEM,
        "Type",
        ["AWS::DynamoDB::Table.AttributeDefinition", "AttributeType"],
    )


SSESpecification = Optional[PassThroughProp]


class Properties(BaseModel):
    PointInTimeRecoverySpecification: PassThroughProp | None  # TODO: add docs
    PrimaryKey: PrimaryKey | None = properties("PrimaryKey")
    ProvisionedThroughput: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "ProvisionedThroughput",
        ["AWS::DynamoDB::Table", "Properties", "ProvisionedThroughput"],
    )
    SSESpecification: SSESpecification | None = passthrough_prop(
        PROPERTIES_STEM,
        "SSESpecification",
        ["AWS::DynamoDB::Table", "Properties", "SSESpecification"],
    )
    TableName: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "TableName",
        ["AWS::DynamoDB::Table", "Properties", "TableName"],
    )
    Tags: dict[str, Any] | None = properties("Tags")


class Globals(BaseModel):
    SSESpecification: SSESpecification | None = passthrough_prop(
        PROPERTIES_STEM,
        "SSESpecification",
        ["AWS::DynamoDB::Table", "Properties", "SSESpecification"],
    )


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::SimpleTable"]
    Properties: Properties | None
    Connectors: dict[str, EmbeddedConnector] | None
