from __future__ import annotations

from typing import Optional, Any, Dict

from typing_extensions import Literal

from samtranslator.schema.common import PassThroughProp, BaseModel, get_prop
from samtranslator.schema.aws_serverless_connector import EmbeddedConnector

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


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::SimpleTable"]
    Properties: Optional[Properties]
    Connectors: Optional[Dict[str, EmbeddedConnector]]
