from typing import Optional, Any, Dict, Union

from typing_extensions import Literal

from samtranslator.schema.common import PassThrough, BaseModel, SamIntrinsicable


class Location(BaseModel):
    ApplicationId: SamIntrinsicable[str]
    SemanticVersion: SamIntrinsicable[str]


class Properties(BaseModel):
    Location: Union[str, Location]
    NotificationARNs: Optional[PassThrough]
    Parameters: Optional[PassThrough]
    Tags: Optional[Dict[str, Any]]
    TimeoutInMinutes: Optional[PassThrough]


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::Application"]
    Properties: Properties
    Condition: Optional[PassThrough]
