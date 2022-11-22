from typing import Optional, Any, Dict

from typing_extensions import Literal

from samtranslator.schema.common import PassThrough, BaseModel


class PrimaryKey(BaseModel):
    Name: PassThrough
    Type: PassThrough


class Properties(BaseModel):
    PrimaryKey: Optional[PrimaryKey]
    ProvisionedThroughput: Optional[PassThrough]
    SSESpecification: Optional[PassThrough]
    TableName: Optional[PassThrough]
    Tags: Optional[Dict[str, Any]]


class Globals(BaseModel):
    SSESpecification: Optional[PassThrough]


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::SimpleTable"]
    Properties: Optional[Properties]
