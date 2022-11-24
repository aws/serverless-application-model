from __future__ import annotations

from typing import Optional, Any, Dict

from typing_extensions import Literal

from samtranslator.schema.common import PassThrough, BaseModel, get_prop

primarykey = get_prop("sam-property-simpletable-primarykeyobject")
properties = get_prop("sam-resource-simpletable")


class PrimaryKey(BaseModel):
    Name: PassThrough = primarykey("Name")
    Type: PassThrough = primarykey("Type")


SSESpecification = Optional[PassThrough]


class Properties(BaseModel):
    PrimaryKey: Optional[PrimaryKey] = properties("PrimaryKey")
    ProvisionedThroughput: Optional[PassThrough] = properties("ProvisionedThroughput")
    SSESpecification: Optional[SSESpecification] = properties("SSESpecification")
    TableName: Optional[PassThrough] = properties("TableName")
    Tags: Optional[Dict[str, Any]] = properties("Tags")


class Globals(BaseModel):
    SSESpecification: Optional[SSESpecification] = properties("SSESpecification")


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::SimpleTable"]
    Properties: Optional[Properties]
