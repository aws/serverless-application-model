from __future__ import annotations

from typing import Literal, Optional, Union

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
    Version: PassThroughProp | None = passthrough_prop(
        CONTENT_URI_STEM,
        "Version",
        ["AWS::Lambda::LayerVersion.Content", "S3ObjectVersion"],
    )


class Properties(BaseModel):
    CompatibleArchitectures: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "CompatibleArchitectures",
        ["AWS::Lambda::LayerVersion", "Properties", "CompatibleArchitectures"],
    )
    CompatibleRuntimes: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "CompatibleRuntimes",
        ["AWS::Lambda::LayerVersion", "Properties", "CompatibleRuntimes"],
    )
    PublishLambdaVersion: bool | None  # TODO: add docs
    ContentUri: str | ContentUri = properties("ContentUri")
    Description: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "Description",
        ["AWS::Lambda::LayerVersion", "Properties", "Description"],
    )
    LayerName: PassThroughProp | None = properties("LayerName")
    LicenseInfo: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "LicenseInfo",
        ["AWS::Lambda::LayerVersion", "Properties", "LicenseInfo"],
    )
    RetentionPolicy: SamIntrinsicable[str] | None = properties("RetentionPolicy")


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::LayerVersion"]
    Properties: Properties


class Globals(BaseModel):
    PublishLambdaVersion: bool | None  # TODO: add docs
