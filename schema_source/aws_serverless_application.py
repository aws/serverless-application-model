from __future__ import annotations

from typing import Any, Dict, Optional, Union

from typing_extensions import Literal

from schema_source.common import BaseModel, PassThroughProp, ResourceAttributes, SamIntrinsicable, get_prop

location = get_prop("sam-property-application-applicationlocationobject")
properties = get_prop("sam-resource-application")


class Location(BaseModel):
    ApplicationId: SamIntrinsicable[str] = location("ApplicationId")
    SemanticVersion: SamIntrinsicable[str] = location("SemanticVersion")


class Properties(BaseModel):
    Location: Union[str, Location] = properties("Location")
    NotificationARNs: Optional[PassThroughProp] = properties("NotificationARNs")
    Parameters: Optional[PassThroughProp] = properties("Parameters")
    Tags: Optional[Dict[str, Any]] = properties("Tags")
    TimeoutInMinutes: Optional[PassThroughProp] = properties("TimeoutInMinutes")


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::Application"]
    Properties: Properties
