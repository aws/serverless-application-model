from typing import Optional, List

from typing_extensions import Literal

from samtranslator.schema.common import PassThroughProp, BaseModel, get_prop

resourcereference = get_prop("sam-property-connector-resourcereference")
properties = get_prop("sam-resource-connector")

PermissionsType = List[Literal["Read", "Write"]]


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
    Source: ResourceReference = properties("Source")
    Destination: ResourceReference = properties("Destination")
    Permissions: PermissionsType = properties("Permissions")


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::Connector"]
    Properties: Properties


class SourceReference(BaseModel):
    Qualifier: Optional[PassThroughProp] = resourcereference("Qualifier")


class EmbeddedConnectorProperties(BaseModel):
    SourceReference: Optional[SourceReference]  # TODO: add docs for SourceReference
    Destination: ResourceReference = properties("Destination")
    Permissions: PermissionsType = properties("Permissions")


# TODO make connectors a part of all CFN Resources
class EmbeddedConnector(BaseModel):
    Properties: EmbeddedConnectorProperties
    DependsOn: Optional[PassThroughProp]
    DeletionPolicy: Optional[PassThroughProp]
    Metadata: Optional[PassThroughProp]
    UpdatePolicy: Optional[PassThroughProp]
