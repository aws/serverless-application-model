from __future__ import annotations

from typing import Any, Dict, Optional, Union

from typing_extensions import Literal

from samtranslator.internal.schema_source.common import (
    BaseModel,
    PassThroughProp,
    ResourceAttributes,
    SamIntrinsicable,
    get_prop,
    passthrough_prop,
)

PROPERTIES_STEM = "sam-resource-application"

location = get_prop("sam-property-application-applicationlocationobject")
properties = get_prop(PROPERTIES_STEM)


class Location(BaseModel):
    ApplicationId: SamIntrinsicable[str] = location("ApplicationId")
    SemanticVersion: SamIntrinsicable[str] = location("SemanticVersion")


class Properties(BaseModel):
    Location: Union[str, Location] = properties("Location")
    NotificationARNs: Optional[PassThroughProp] = passthrough_prop(
        PROPERTIES_STEM,
        "NotificationARNs",
        ["AWS::CloudFormation::Stack", "Properties", "NotificationARNs"],
    )
    Parameters: Optional[PassThroughProp] = passthrough_prop(
        PROPERTIES_STEM,
        "Parameters",
        ["AWS::CloudFormation::Stack", "Properties", "Parameters"],
    )
    Tags: Optional[Dict[str, Any]] = properties("Tags")
    TimeoutInMinutes: Optional[PassThroughProp] = passthrough_prop(
        PROPERTIES_STEM,
        "TimeoutInMinutes",
        ["AWS::CloudFormation::Stack", "Properties", "TimeoutInMinutes"],
    )


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::Application"]
    Properties: Properties
