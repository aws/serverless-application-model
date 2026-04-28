from typing import Literal, Union

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
    Id: str | None = resourcereference("Id")
    Arn: PassThroughProp | None = resourcereference("Arn")
    Name: PassThroughProp | None = resourcereference("Name")
    Qualifier: PassThroughProp | None = resourcereference("Qualifier")
    QueueUrl: PassThroughProp | None = resourcereference("QueueUrl")
    ResourceId: PassThroughProp | None = resourcereference("ResourceId")
    RoleName: PassThroughProp | None = resourcereference("RoleName")
    Type: str | None = resourcereference("Type")


class Properties(BaseModel):
    Source: ResourceReference = properties("Source")
    Destination: Union[ResourceReference, list[ResourceReference]] = properties("Destination")
    Permissions: list[Literal["Read", "Write"]] = properties("Permissions")


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::Connector"]
    Properties: Properties


class SourceReferenceProperties(BaseModel):
    Qualifier: PassThroughProp | None = sourcereference("Qualifier")


class EmbeddedConnectorProperties(BaseModel):
    SourceReference: SourceReferenceProperties | None = properties("SourceReference")
    Destination: Union[ResourceReference, list[ResourceReference]] = properties("Destination")
    Permissions: PermissionsType = properties("Permissions")


# TODO make connectors a part of all CFN Resources
class EmbeddedConnector(ResourceAttributes):
    Properties: EmbeddedConnectorProperties
