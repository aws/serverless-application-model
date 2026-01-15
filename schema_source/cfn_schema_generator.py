#!/usr/bin/env python3
"""
CloudFormation Schema Generator - Python Port
Minimal working port of the Go goformation schema generator.
"""

import gzip
import json
from pathlib import Path
from typing import Any, Dict, cast

import requests

# Configuration: Resources that support additional policies
# These are documented in CloudFormation but not in the schemas
# Source: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-attribute-creationpolicy.html
RESOURCES_WITH_CREATION_POLICY = {
    "AWS::AutoScaling::AutoScalingGroup",
    "AWS::EC2::Instance",
    "AWS::CloudFormation::WaitCondition",
}

# Source: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-attribute-updatepolicy.html
RESOURCES_WITH_UPDATE_POLICY = {
    "AWS::AutoScaling::AutoScalingGroup",
}

# Configuration: CloudFormation Parameter Types
# Source: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/parameters-section-structure.html
# These are intrinsic to CloudFormation and defined in the documentation, not in resource schemas
CFN_PARAMETER_TYPES = [
    # Basic types
    "String",
    "Number",
    "List<Number>",
    "CommaDelimitedList",
    # AWS-specific parameter types
    # Source: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-supplied-parameter-types.html
    "AWS::EC2::AvailabilityZone::Name",
    "AWS::EC2::Image::Id",
    "AWS::EC2::Instance::Id",
    "AWS::EC2::KeyPair::KeyName",
    "AWS::EC2::SecurityGroup::GroupName",
    "AWS::EC2::SecurityGroup::Id",
    "AWS::EC2::Subnet::Id",
    "AWS::EC2::Volume::Id",
    "AWS::EC2::VPC::Id",
    "AWS::Route53::HostedZone::Id",
    # List types for AWS resources
    "List<AWS::EC2::AvailabilityZone::Name>",
    "List<AWS::EC2::Image::Id>",
    "List<AWS::EC2::Instance::Id>",
    "List<AWS::EC2::SecurityGroup::GroupName>",
    "List<AWS::EC2::SecurityGroup::Id>",
    "List<AWS::EC2::Subnet::Id>",
    "List<AWS::EC2::Volume::Id>",
    "List<AWS::EC2::VPC::Id>",
    "List<AWS::Route53::HostedZone::Id>",
    "List<String>",
    # Systems Manager parameter types
    "AWS::SSM::Parameter::Name",
    "AWS::SSM::Parameter::Value<String>",
    "AWS::SSM::Parameter::Value<List<String>>",
    "AWS::SSM::Parameter::Value<CommaDelimitedList>",
    # SSM Parameter types with AWS-specific values
    "AWS::SSM::Parameter::Value<AWS::EC2::AvailabilityZone::Name>",
    "AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>",
    "AWS::SSM::Parameter::Value<AWS::EC2::Instance::Id>",
    "AWS::SSM::Parameter::Value<AWS::EC2::SecurityGroup::GroupName>",
    "AWS::SSM::Parameter::Value<AWS::EC2::SecurityGroup::Id>",
    "AWS::SSM::Parameter::Value<AWS::EC2::Subnet::Id>",
    "AWS::SSM::Parameter::Value<AWS::EC2::Volume::Id>",
    "AWS::SSM::Parameter::Value<AWS::EC2::VPC::Id>",
    "AWS::SSM::Parameter::Value<AWS::Route53::HostedZone::Id>",
    # SSM Parameter types with AWS-specific list values
    "AWS::SSM::Parameter::Value<List<AWS::EC2::AvailabilityZone::Name>>",
    "AWS::SSM::Parameter::Value<List<AWS::EC2::Image::Id>>",
    "AWS::SSM::Parameter::Value<List<AWS::EC2::Instance::Id>>",
    "AWS::SSM::Parameter::Value<List<AWS::EC2::SecurityGroup::GroupName>>",
    "AWS::SSM::Parameter::Value<List<AWS::EC2::SecurityGroup::Id>>",
    "AWS::SSM::Parameter::Value<List<AWS::EC2::Subnet::Id>>",
    "AWS::SSM::Parameter::Value<List<AWS::EC2::Volume::Id>>",
    "AWS::SSM::Parameter::Value<List<AWS::EC2::VPC::Id>>",
    "AWS::SSM::Parameter::Value<List<AWS::Route53::HostedZone::Id>>",
]

# Configuration: CloudFormation template wrapper properties
CFN_TEMPLATE_PROPERTIES = {
    "Type": {"type": "string"},
    "Properties": {"type": "object"},
    "Condition": {"type": "string"},
    "DeletionPolicy": {"enum": ["Delete", "Retain", "Snapshot"], "type": "string"},
    "DependsOn": {
        "anyOf": [
            {"pattern": "^[a-zA-Z0-9]+$", "type": "string"},
            {"items": {"pattern": "^[a-zA-Z0-9]+$", "type": "string"}, "type": "array"},
        ]
    },
    "Metadata": {"type": "object"},
    "UpdateReplacePolicy": {"enum": ["Delete", "Retain", "Snapshot"], "type": "string"},
}

# Template: Base object schema
BASE_OBJECT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
}

# Template: Parameter definition schema
PARAMETER_SCHEMA_TEMPLATE = {
    **BASE_OBJECT_SCHEMA,
    "properties": {
        "Type": {"type": "string", "enum": CFN_PARAMETER_TYPES},
        "AllowedPattern": {"type": "string"},
        "AllowedValues": {"type": "array"},
        "ConstraintDescription": {"type": "string"},
        "Default": {"type": "string"},
        "Description": {"type": "string"},
        "MaxLength": {"type": "string"},
        "MaxValue": {"type": "string"},
        "MinLength": {"type": "string"},
        "MinValue": {"type": "string"},
        "NoEcho": {"type": ["string", "boolean"]},
    },
    "required": ["Type"],
}

# Template: CustomResource definition schema
CUSTOM_RESOURCE_SCHEMA_TEMPLATE = {
    **BASE_OBJECT_SCHEMA,
    "properties": {
        "Properties": {
            "type": "object",
            "additionalProperties": True,
            "properties": {"ServiceToken": {"type": "string"}},
            "required": ["ServiceToken"],
        },
        "Type": {"pattern": "^Custom::[a-zA-Z_@-]+$", "type": "string"},
    },
    "required": ["Type", "Properties"],
}

# Template: Main CloudFormation schema structure
MAIN_SCHEMA_TEMPLATE = {
    "$id": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "AWSTemplateFormatVersion": {"type": "string", "enum": ["2010-09-09"]},
        "Description": {"description": "Template description", "type": "string", "maxLength": 1024},
        "Metadata": {"type": "object"},
        "Transform": {"oneOf": [{"type": ["string"]}, {"type": "array", "items": {"type": "string"}}]},
        "Parameters": {
            "type": "object",
            "patternProperties": {"^[a-zA-Z0-9]+$": {"$ref": "#/definitions/Parameter"}},
            "maxProperties": 50,
            "additionalProperties": False,
        },
        "Mappings": {
            "type": "object",
            "patternProperties": {"^[a-zA-Z0-9]+$": {"type": "object"}},
            "additionalProperties": False,
        },
        "Conditions": {
            "type": "object",
            "patternProperties": {"^[a-zA-Z0-9]+$": {"type": "object"}},
            "additionalProperties": False,
        },
        "Outputs": {
            "type": "object",
            "patternProperties": {"^[a-zA-Z0-9]+$": {"type": "object"}},
            "minProperties": 1,
            "maxProperties": 60,
            "additionalProperties": False,
        },
        "Resources": {
            "type": "object",
            "patternProperties": {"^[a-zA-Z0-9]+$": {"anyOf": []}},  # Will be filled in
            "additionalProperties": False,
        },
    },
    "required": ["Resources"],
    "definitions": {},  # Will be filled in
}

# Template: Array schema
ARRAY_SCHEMA_TEMPLATE = {
    "type": "array",
    "items": {},  # Will be filled in
}

# Template: Map/Object schema with pattern properties
MAP_SCHEMA_TEMPLATE = {
    "type": "object",
    "patternProperties": {"^[a-zA-Z0-9]+$": {}},  # Will be filled in
    "additionalProperties": False,
}


class CloudFormationSchemaGenerator:
    """Python port of the Go CloudFormation schema generator"""

    def __init__(
        self,
        spec_url: str = "https://d1uauaxba7bl26.cloudfront.net/latest/gzip/CloudFormationResourceSpecification.json",
    ):
        self.spec_url = spec_url
        self.type_map = {
            "String": "string",
            "Long": "number",
            "Integer": "number",
            "Double": "number",
            "Boolean": "boolean",
            "Timestamp": "string",
            "Json": "object",
            "Map": "object",
        }

    def generate(self, output_file: str = ".tmp/cloudformation.schema.json") -> None:
        """Generate CloudFormation JSON schema"""
        spec = self._download_spec()

        schema = self._generate_schema(spec)

        # Write to file with custom JSON encoder to match expected format
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w") as f:
            # Convert to JSON string and replace < and > with Unicode escapes to match expected format
            json_str = json.dumps(schema, indent=4, sort_keys=True)
            json_str = json_str.replace("<", "\\u003c").replace(">", "\\u003e")
            f.write(json_str)

    def _download_spec(self) -> Dict[str, Any]:
        """Download and parse CloudFormation specification"""
        response = requests.get(self.spec_url, timeout=30)
        response.raise_for_status()

        # Handle gzipped content - check if actually gzipped
        content = response.content
        if content.startswith(b"\x1f\x8b"):  # gzip magic number
            content = gzip.decompress(content)

        result: Dict[str, Any] = json.loads(content)
        return result

    def _generate_schema(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JSON schema from CloudFormation specification"""
        resources = spec.get("ResourceTypes", {})
        properties = spec.get("PropertyTypes", {})

        # Build resource references for anyOf
        resource_refs = [{"$ref": f"#/definitions/{name}"} for name in resources]
        resource_refs.append({"$ref": "#/definitions/CustomResource"})

        # Start with main schema template and fill in the details
        main_properties = cast(Dict[str, Any], MAIN_SCHEMA_TEMPLATE["properties"])
        resources_property = cast(Dict[str, Any], main_properties["Resources"])

        schema = {
            **MAIN_SCHEMA_TEMPLATE,
            "properties": {
                **main_properties,
                "Resources": {
                    **resources_property,
                    "patternProperties": {"^[a-zA-Z0-9]+$": {"anyOf": resource_refs}},
                },
            },
        }

        # Build definitions from templates
        definitions: Dict[str, Any] = {}
        definitions["Parameter"] = PARAMETER_SCHEMA_TEMPLATE
        definitions["CustomResource"] = CUSTOM_RESOURCE_SCHEMA_TEMPLATE

        # Add resource definitions
        for name, resource in resources.items():
            definitions[name] = self._generate_resource_schema(name, resource, False)

        # Add property definitions
        for name, prop in properties.items():
            definitions[name] = self._generate_resource_schema(name, prop, True)

        schema["definitions"] = definitions
        return schema

    def _generate_resource_schema(
        self, name: str, resource: Dict[str, Any], is_custom_property: bool
    ) -> Dict[str, Any]:
        """Generate schema for a CloudFormation resource"""
        properties = resource.get("Properties", {})
        required = sorted([prop_name for prop_name, prop in properties.items() if prop.get("Required", False)])

        prop_schemas = {}
        for prop_name, prop in properties.items():
            prop_schemas[prop_name] = self._generate_property_schema(prop_name, prop, name)

        # For custom properties (nested property types), use simple object schema
        if is_custom_property:
            schema = {
                **BASE_OBJECT_SCHEMA,
                "properties": prop_schemas,
            }
            if required:
                schema["required"] = required
            return schema

        # For resources, start with base object schema and build up
        properties_schema = {
            **BASE_OBJECT_SCHEMA,
            "properties": prop_schemas,
        }
        if required:
            properties_schema["required"] = required

        # Build resource schema from template
        resource_schema = {
            **BASE_OBJECT_SCHEMA,
            "properties": {
                **CFN_TEMPLATE_PROPERTIES,
                # Override with resource-specific values
                "Type": {"enum": [name], "type": "string"},
                "Properties": properties_schema,
            },
            "required": ["Type", "Properties"] if required else ["Type"],
        }

        # Add optional policies for specific resources
        if name in RESOURCES_WITH_CREATION_POLICY:
            properties_obj = cast(Dict[str, Any], resource_schema["properties"])
            properties_obj["CreationPolicy"] = {"type": "object"}

        if name in RESOURCES_WITH_UPDATE_POLICY:
            properties_obj = cast(Dict[str, Any], resource_schema["properties"])
            properties_obj["UpdatePolicy"] = {"type": "object"}

        return resource_schema

    def _generate_property_schema(  # noqa: PLR0911
        self, name: str, prop: Dict[str, Any], parent: str
    ) -> Dict[str, Any]:
        """Generate schema for a CloudFormation property"""
        # Extract resource name from parent (e.g., "AWS::S3::Bucket" from "AWS::S3::Bucket.Property")
        resource_name = parent.split(".")[0] if "." in parent else parent

        # Handle polymorphic properties (simplified)
        if self._is_polymorphic(prop):
            any_of = []
            if prop.get("PrimitiveTypes"):
                any_of.append({"type": [self.type_map.get(pt, "string") for pt in prop["PrimitiveTypes"]]})
            return {"anyOf": any_of} if any_of else {"type": "object"}

        # Handle simple primitive types
        if prop.get("PrimitiveType"):
            return {"type": self.type_map.get(prop["PrimitiveType"], "string")}

        # Handle lists
        if prop.get("Type") == "List":
            if prop.get("PrimitiveItemType"):
                return {
                    **ARRAY_SCHEMA_TEMPLATE,
                    "items": {"type": self.type_map.get(prop["PrimitiveItemType"], "string")},
                }
            if prop.get("ItemType"):
                item_type = prop["ItemType"]
                # Use global reference for Tag type (matching Go template logic)
                ref = "#/definitions/Tag" if item_type == "Tag" else f"#/definitions/{resource_name}.{item_type}"
                return {
                    **ARRAY_SCHEMA_TEMPLATE,
                    "items": {"$ref": ref},
                }

        # Handle maps
        if prop.get("Type") == "Map":
            if prop.get("PrimitiveItemType"):
                return {
                    **MAP_SCHEMA_TEMPLATE,
                    "patternProperties": {
                        "^[a-zA-Z0-9]+$": {"type": self.type_map.get(prop["PrimitiveItemType"], "string")}
                    },
                    "additionalProperties": True,
                }
            if prop.get("ItemType"):
                item_type = prop["ItemType"]
                # Use global reference for Tag type (matching Go template logic)
                ref = "#/definitions/Tag" if item_type == "Tag" else f"#/definitions/{resource_name}.{item_type}"
                return {
                    **MAP_SCHEMA_TEMPLATE,
                    "patternProperties": {"^[a-zA-Z0-9]+$": {"$ref": ref}},
                }

        # Handle custom types
        if prop.get("Type") and prop["Type"] not in ["List", "Map"]:
            prop_type = prop["Type"]
            # Use global reference for Tag type (matching Go template logic)
            if prop_type == "Tag":
                return {"$ref": "#/definitions/Tag"}
            return {"$ref": f"#/definitions/{resource_name}.{prop_type}"}

        return {"type": "object"}

    def _is_polymorphic(self, prop: Dict[str, Any]) -> bool:
        """Check if property can be multiple different types"""
        return bool(
            prop.get("PrimitiveTypes")
            or prop.get("PrimitiveItemTypes")
            or prop.get("ItemTypes")
            or prop.get("Types")
            or prop.get("InclusivePrimitiveItemTypes")
            or prop.get("InclusiveItemTypes")
        )


if __name__ == "__main__":
    generator = CloudFormationSchemaGenerator()
    generator.generate()
