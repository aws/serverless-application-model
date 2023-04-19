from __future__ import annotations

from typing import Optional, Union

from typing_extensions import Literal

from samtranslator.internal.schema_source.common import (
    BaseModel,
    PassThroughProp,
    ResourceAttributes,
    SamIntrinsicable,
    get_prop,
    passthrough_prop,
)

PROPERTIES_STEM = "sam-resource-layerversion"
CONTENT_URI_STEM = "sam-property-layerversion-layercontent"

contenturi = get_prop(CONTENT_URI_STEM)
properties = get_prop(PROPERTIES_STEM)


class ContentUri(BaseModel):
    Bucket: PassThroughProp = passthrough_prop(
        CONTENT_URI_STEM,
        "Bucket",
        ["AWS::Lambda::LayerVersion.Content", "S3Bucket"],
    )
    Key: PassThroughProp = passthrough_prop(
        CONTENT_URI_STEM,
        "Key",
        ["AWS::Lambda::LayerVersion.Content", "S3Key"],
    )
    Version: Optional[PassThroughProp] = passthrough_prop(
        CONTENT_URI_STEM,
        "Version",
        ["AWS::Lambda::LayerVersion.Content", "S3ObjectVersion"],
    )


class Properties(BaseModel):
    CompatibleArchitectures: Optional[PassThroughProp] = passthrough_prop(
        PROPERTIES_STEM,
        "CompatibleArchitectures",
        ["AWS::Lambda::LayerVersion", "Properties", "CompatibleArchitectures"],
    )
    CompatibleRuntimes: Optional[PassThroughProp] = passthrough_prop(
        PROPERTIES_STEM,
        "CompatibleRuntimes",
        ["AWS::Lambda::LayerVersion", "Properties", "CompatibleRuntimes"],
    )
    ContentUri: Union[str, ContentUri] = properties("ContentUri")
    Description: Optional[PassThroughProp] = passthrough_prop(
        PROPERTIES_STEM,
        "Description",
        ["AWS::Lambda::LayerVersion", "Properties", "Description"],
    )
    LayerName: Optional[PassThroughProp] = properties("LayerName")
    LicenseInfo: Optional[PassThroughProp] = passthrough_prop(
        PROPERTIES_STEM,
        "LicenseInfo",
        ["AWS::Lambda::LayerVersion", "Properties", "LicenseInfo"],
    )
    RetentionPolicy: Optional[SamIntrinsicable[str]] = properties("RetentionPolicy")


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::LayerVersion"]
    Properties: Properties
