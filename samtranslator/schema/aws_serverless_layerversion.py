from typing import Optional, Union

from typing_extensions import Literal

from samtranslator.schema.common import PassThrough, BaseModel, SamIntrinsic


class ContentUri(BaseModel):
    Bucket: PassThrough
    Key: PassThrough
    Version: Optional[PassThrough]


class Properties(BaseModel):
    CompatibleArchitectures: Optional[PassThrough]
    CompatibleRuntimes: Optional[PassThrough]
    ContentUri: Union[str, ContentUri]
    Description: Optional[PassThrough]
    LayerName: Optional[PassThrough]
    LicenseInfo: Optional[PassThrough]
    RetentionPolicy: Optional[Union[str, SamIntrinsic]]


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::LayerVersion"]
    Properties: Properties
    Condition: Optional[PassThrough]
    DeletionPolicy: Optional[PassThrough]
