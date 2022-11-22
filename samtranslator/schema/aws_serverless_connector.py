from typing import Optional, List

from typing_extensions import Literal

from samtranslator.schema.common import PassThrough, BaseModel


class ResourceReference(BaseModel):
    Id: Optional[str]
    Arn: Optional[PassThrough]
    Name: Optional[PassThrough]
    Qualifier: Optional[PassThrough]
    QueueUrl: Optional[PassThrough]
    ResourceId: Optional[PassThrough]
    RoleName: Optional[PassThrough]
    Type: Optional[str]


class Properties(BaseModel):
    Source: ResourceReference
    Destination: ResourceReference
    Permissions: List[Literal["Read", "Write"]]


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::Connector"]
    Properties: Properties
