from __future__ import annotations

from typing import Optional, Any, Dict, Union

from typing_extensions import Literal

from samtranslator.schema.common import PassThrough, BaseModel, SamIntrinsicable, get_prop

location = get_prop("sam-property-application-applicationlocationobject")
properties = get_prop("sam-resource-application")


class Location(BaseModel):
    ApplicationId: SamIntrinsicable[str] = location("ApplicationId")
    SemanticVersion: SamIntrinsicable[str] = location("SemanticVersion")


class Properties(BaseModel):
    Location: Union[str, Location] = properties("Location")
    NotificationARNs: Optional[PassThrough] = properties("NotificationARNs")
    Parameters: Optional[PassThrough] = properties("Parameters")
    Tags: Optional[Dict[str, Any]] = properties("Tags")
    TimeoutInMinutes: Optional[PassThrough] = properties("TimeoutInMinutes")


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::Application"]
    Properties: Properties
    Condition: Optional[PassThrough]
