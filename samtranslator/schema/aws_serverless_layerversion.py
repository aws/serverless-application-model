from __future__ import annotations

from typing import Optional, Union

from typing_extensions import Literal

from samtranslator.schema.common import PassThrough, BaseModel, SamIntrinsicable, get_prop

contenturi = get_prop("sam-property-layerversion-layercontent")
properties = get_prop("sam-resource-layerversion")


class ContentUri(BaseModel):
    Bucket: PassThrough = contenturi("Bucket")
    Key: PassThrough = contenturi("Key")
    Version: Optional[PassThrough] = contenturi("Version")


class Properties(BaseModel):
    CompatibleArchitectures: Optional[PassThrough] = properties("CompatibleArchitectures")
    CompatibleRuntimes: Optional[PassThrough] = properties("CompatibleRuntimes")
    ContentUri: Union[str, ContentUri] = properties("ContentUri")
    Description: Optional[PassThrough] = properties("Description")
    LayerName: Optional[PassThrough] = properties("LayerName")
    LicenseInfo: Optional[PassThrough] = properties("LicenseInfo")
    RetentionPolicy: Optional[SamIntrinsicable[str]] = properties("RetentionPolicy")


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::LayerVersion"]
    Properties: Properties
    Condition: Optional[PassThrough]
    DeletionPolicy: Optional[PassThrough]
