# type: ignore
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel as LenientBaseModel
from pydantic import Extra, Field, constr


# By default strict
# https://pydantic-docs.helpmanual.io/usage/model_config/#change-behaviour-globally
class BaseModel(LenientBaseModel):
    class Config:
        extra = Extra.forbid


class ResourceReference(BaseModel):
    Id: Optional[str]
    Arn: Optional[Any]
    Name: Optional[Any]
    Qualifier: Optional[Any]
    QueueUrl: Optional[Any]
    ResourceId: Optional[Any]
    RoleName: Optional[Any]
    Type: Optional[Any]


class ConnectorProperties(BaseModel):
    Source: ResourceReference
    Destination: ResourceReference
    Permissions: List[Literal["Read", "Write"]]


class AwsServerlessConnector(BaseModel):
    Type: Literal["AWS::Serverless::Connector"]
    Properties: ConnectorProperties


class FunctionProperties(BaseModel):
    Runtime: str
    Handler: Any
    Timeout: Any
    InlineCode: Any
    Environment: Any
    Policies: Any


class AwsServerlessFunction(BaseModel):
    Type: Literal["AWS::Serverless::Function"]
    Properties: FunctionProperties


# Match anything not containing Serverless
class AnyCfnResource(LenientBaseModel):
    Type: constr(regex=r"^((?!Serverless).)*$")


class Model(LenientBaseModel):
    Resources: Dict[
        str,
        Union[
            AwsServerlessConnector,
            AwsServerlessFunction,
            AnyCfnResource,
        ],
    ]


if __name__ == "__main__":
    print(Model.schema_json(indent=2))
