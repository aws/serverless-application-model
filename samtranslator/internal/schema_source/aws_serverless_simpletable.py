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
        required=True,
    )
    Type: PassThroughProp = passthrough_prop(
        PRIMARY_KEY_STEM,
        "Type",
        ["AWS::DynamoDB::Table.AttributeDefinition", "AttributeType"],
        required=True,
    )


# Type alias to avoid field name shadowing class name
_PrimaryKey = PrimaryKey

# Type alias with underscore prefix to avoid shadowing by field name
_SSESpecification = Optional[PassThroughProp]


class Properties(BaseModel):
    PointInTimeRecoverySpecification: Optional[PassThroughProp] = None  # TODO: add docs
    PrimaryKey: Optional[_PrimaryKey] = properties("PrimaryKey")
    ProvisionedThroughput: Optional[PassThroughProp] = passthrough_prop(
        PROPERTIES_STEM,
        "ProvisionedThroughput",
        ["AWS::DynamoDB::Table", "Properties", "ProvisionedThroughput"],
    )
    SSESpecification: Optional[_SSESpecification] = passthrough_prop(
        PROPERTIES_STEM,
        "SSESpecification",
        ["AWS::DynamoDB::Table", "Properties", "SSESpecification"],
    )
    TableName: Optional[PassThroughProp] = passthrough_prop(
        PROPERTIES_STEM,
        "TableName",
        ["AWS::DynamoDB::Table", "Properties", "TableName"],
    )
    Tags: Optional[Dict[str, Any]] = properties("Tags")


class Globals(BaseModel):
    SSESpecification: Optional[_SSESpecification] = passthrough_prop(
        PROPERTIES_STEM,
        "SSESpecification",
        ["AWS::DynamoDB::Table", "Properties", "SSESpecification"],
    )


# Type alias to avoid field name shadowing class name in Pydantic V2
_Properties = Properties


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::SimpleTable"]
    Properties: Optional[_Properties] = None
    Connectors: Optional[Dict[str, EmbeddedConnector]] = None
