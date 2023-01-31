from __future__ import annotations

from typing import Any, Dict, Optional

from typing_extensions import Literal

from schema_source.aws_serverless_connector import EmbeddedConnector
from schema_source.common import BaseModel, PassThroughProp, ResourceAttributes, get_prop

primarykey = get_prop("sam-property-simpletable-primarykeyobject")
properties = get_prop("sam-resource-simpletable")


class PrimaryKey(BaseModel):
    Name: PassThroughProp = primarykey("Name")
    Type: PassThroughProp = primarykey("Type")


SSESpecification = Optional[PassThroughProp]


class Properties(BaseModel):
    PrimaryKey: Optional[PrimaryKey] = properties("PrimaryKey")
    ProvisionedThroughput: Optional[PassThroughProp] = properties("ProvisionedThroughput")
    SSESpecification: Optional[SSESpecification] = properties("SSESpecification")
    TableName: Optional[PassThroughProp] = properties("TableName")
    Tags: Optional[Dict[str, Any]] = properties("Tags")


class Globals(BaseModel):
    SSESpecification: Optional[SSESpecification] = properties("SSESpecification")


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::SimpleTable"]
    Properties: Optional[Properties]
    Connectors: Optional[Dict[str, EmbeddedConnector]]
