from typing import List, Literal, Optional, Union

from samtranslator.internal.schema_source.common import (
    BaseModel,
    PassThroughProp,
    PermissionsType,
    ResourceAttributes,
    get_prop,
)

resourcereference = get_prop("sam-property-connector-resourcereference")
properties = get_prop("sam-resource-connector")
sourcereference = get_prop("sam-property-connector-sourcereference")


class ResourceReference(BaseModel):
    Id: Optional[str] = resourcereference("Id")
    Arn: Optional[PassThroughProp] = resourcereference("Arn")
    Name: Optional[PassThroughProp] = resourcereference("Name")
    Qualifier: Optional[PassThroughProp] = resourcereference("Qualifier")
    QueueUrl: Optional[PassThroughProp] = resourcereference("QueueUrl")
    ResourceId: Optional[PassThroughProp] = resourcereference("ResourceId")
    RoleName: Optional[PassThroughProp] = resourcereference("RoleName")
    Type: Optional[str] = resourcereference("Type")


class Properties(BaseModel):
    # Required fields - not using get_prop() to ensure they are truly required in Pydantic v2
    Source: ResourceReference
    Destination: Union[ResourceReference, List[ResourceReference]]
    Permissions: List[Literal["Read", "Write"]]


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::Connector"]
    Properties: Properties


class SourceReferenceProperties(BaseModel):
    Qualifier: Optional[PassThroughProp] = sourcereference("Qualifier")


class EmbeddedConnectorProperties(BaseModel):
    SourceReference: Optional[SourceReferenceProperties] = properties("SourceReference")
    Destination: Union[ResourceReference, List[ResourceReference]] = properties("Destination")
    Permissions: PermissionsType = properties("Permissions")


# TODO make connectors a part of all CFN Resources
class EmbeddedConnector(ResourceAttributes):
    Properties: EmbeddedConnectorProperties
