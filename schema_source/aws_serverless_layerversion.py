from __future__ import annotations

from typing import Optional, Union

from typing_extensions import Literal

from schema_source.common import BaseModel, PassThroughProp, ResourceAttributes, SamIntrinsicable, get_prop

contenturi = get_prop("sam-property-layerversion-layercontent")
properties = get_prop("sam-resource-layerversion")


class ContentUri(BaseModel):
    Bucket: PassThroughProp = contenturi("Bucket")
    Key: PassThroughProp = contenturi("Key")
    Version: Optional[PassThroughProp] = contenturi("Version")


class Properties(BaseModel):
    CompatibleArchitectures: Optional[PassThroughProp] = properties("CompatibleArchitectures")
    CompatibleRuntimes: Optional[PassThroughProp] = properties("CompatibleRuntimes")
    ContentUri: Union[str, ContentUri] = properties("ContentUri")
    Description: Optional[PassThroughProp] = properties("Description")
    LayerName: Optional[PassThroughProp] = properties("LayerName")
    LicenseInfo: Optional[PassThroughProp] = properties("LicenseInfo")
    RetentionPolicy: Optional[SamIntrinsicable[str]] = properties("RetentionPolicy")


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::LayerVersion"]
    Properties: Properties
