from typing import Optional, List, Union

from typing_extensions import Literal

from samtranslator.schema.common import PassThrough, BaseModel, get_prop

resourcereference = get_prop("sam-property-connector-resourcereference")
properties = get_prop("sam-resource-connector")


class ResourceReference(BaseModel):
    Id: Optional[str] = resourcereference("Id")
    Arn: Optional[PassThrough] = resourcereference("Arn")
    Name: Optional[PassThrough] = resourcereference("Name")
    Qualifier: Optional[PassThrough] = resourcereference("Qualifier")
    QueueUrl: Optional[PassThrough] = resourcereference("QueueUrl")
    ResourceId: Optional[PassThrough] = resourcereference("ResourceId")
    RoleName: Optional[PassThrough] = resourcereference("RoleName")
    Type: Optional[str] = resourcereference("Type")


class Properties(BaseModel):
    Source: ResourceReference = properties("Source")
    Destination: Union[ResourceReference, List[ResourceReference]] = properties("Destination")
    Permissions: List[Literal["Read", "Write"]] = properties("Permissions")


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::Connector"]
    Properties: Properties
