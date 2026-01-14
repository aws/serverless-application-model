#!/usr/bin/env python3
"""
CloudFormation Schema Generator
Downloads CloudFormation schemas from the official AWS zip archive.

Schema Construction Flow:
========================
1. Download CloudformationSchema.zip from AWS
   ↓
2. Extract individual resource schema files
   ↓
3. Merge schemas with minimal transformation:
   - Wrap resource properties in CloudFormation template structure
   - Add template-level properties (Parameters, Resources, etc.)
   - Preserve all AWS schema definitions as-is
"""

import json
import logging
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import requests

# Configure logging
logger = logging.getLogger(__name__)

# Configuration: AWS CloudFormation Schema URL
# This is the official AWS endpoint for CloudFormation schemas
# Source: https://docs.aws.amazon.com/cloudformation-cli/latest/userguide/resource-type-schema.html
CFN_SCHEMA_URL = "https://schema.cloudformation.us-east-1.amazonaws.com/CloudformationSchema.zip"

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


class CloudFormationSchemaGenerator:
    """CloudFormation schema generator using AWS's official schema zip archive

    This generator is designed to be simple and data-driven:
    - No type mapping (AWS provides correct types)
    - No property transformation (AWS schemas are already JSON Schema)
    - Minimal hardcoded logic (only CFN template wrapper)
    - Parameter types from AWS documentation
    """

    def __init__(
        self,
        template_properties: Optional[Dict[str, Any]] = None,
        resources_with_creation_policy: Optional[Set[str]] = None,
        resources_with_update_policy: Optional[Set[str]] = None,
        parameter_types: Optional[List[str]] = None,
    ):
        """Initialize generator with optional custom configuration

        Args:
            template_properties: Custom template wrapper properties (optional)
            resources_with_creation_policy: Resources supporting CreationPolicy (optional)
            resources_with_update_policy: Resources supporting UpdatePolicy (optional)
            parameter_types: Custom parameter types list (optional)
        """
        self.schema_url = CFN_SCHEMA_URL
        self.template_properties = template_properties or CFN_TEMPLATE_PROPERTIES
        self.resources_with_creation_policy = resources_with_creation_policy or RESOURCES_WITH_CREATION_POLICY
        self.resources_with_update_policy = resources_with_update_policy or RESOURCES_WITH_UPDATE_POLICY
        self.parameter_types = parameter_types or CFN_PARAMETER_TYPES

    def generate(self, output_file: str = ".tmp/cloudformation.schema.json") -> None:
        """Generate CloudFormation JSON schema from AWS zip archive"""
        # Download and extract schemas
        resource_schemas = self._download_and_extract_schemas()

        # Generate unified schema
        schema = self._generate_unified_schema(resource_schemas)

        # Write to file
        self._write_schema(schema, output_file)

    def _download_and_extract_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Download zip file and extract all resource schemas

        Returns:
            Dict mapping resource type names to their schema definitions
        """
        response = requests.get(self.schema_url, timeout=60)
        response.raise_for_status()

        resource_schemas: Dict[str, Dict[str, Any]] = {}

        with zipfile.ZipFile(BytesIO(response.content)) as zip_file:
            json_files = [name for name in zip_file.namelist() if name.endswith(".json")]

            for filename in json_files:
                try:
                    with zip_file.open(filename) as f:
                        schema = json.load(f)

                    type_name = schema.get("typeName")
                    if type_name:
                        resource_schemas[type_name] = schema
                except Exception as e:
                    # Skip invalid files - some files in the zip may not be valid JSON or resource schemas
                    logger.warning(f"Skipping invalid schema file {filename}: {e}")
                    continue

        return resource_schemas

    def _generate_unified_schema(self, resource_schemas: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate unified JSON schema from individual resource schemas

        Strategy: Minimal transformation, maximum reuse of AWS schemas
        """
        # Build resource references
        resource_refs = [{"$ref": f"#/definitions/{name}"} for name in sorted(resource_schemas.keys())]
        resource_refs.append({"$ref": "#/definitions/CustomResource"})

        # Build definitions
        definitions: Dict[str, Any] = {
            "Parameter": self._get_parameter_schema(),
            "CustomResource": self._get_custom_resource_schema(),
        }

        # Process each resource schema
        for type_name, schema in resource_schemas.items():
            # Wrap resource schema in CloudFormation template structure
            definitions[type_name] = self._wrap_resource_schema(type_name, schema)

            # Add nested definitions as-is (no transformation needed!)
            for def_name, def_schema in schema.get("definitions", {}).items():
                definitions[f"{type_name}.{def_name}"] = def_schema

        # Return unified schema
        return {
            "$id": "http://json-schema.org/draft-04/schema#",
            "type": "object",
            "additionalProperties": False,
            "properties": self._get_template_properties(resource_refs),
            "required": ["Resources"],
            "definitions": definitions,
        }

    def _wrap_resource_schema(self, type_name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Wrap AWS resource schema in CloudFormation template structure

        This is the only transformation we do - wrapping the AWS schema
        in CloudFormation's Type/Properties structure.
        """
        # Extract schema components (use as-is!)
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        additional_properties = schema.get("additionalProperties", False)

        # Build Properties schema (no transformation!)
        properties_schema: Dict[str, Any] = {
            "type": "object",
            "properties": properties,
            "additionalProperties": additional_properties,
        }
        if required:
            properties_schema["required"] = required

        # Build resource wrapper
        resource_properties: Dict[str, Any] = {
            "Type": {"enum": [type_name], "type": "string"},
            "Properties": properties_schema,
        }
        # Add template properties
        for key, value in self.template_properties.items():
            if key not in resource_properties:
                resource_properties[key] = value

        # Add optional policies based on configuration
        if type_name in self.resources_with_creation_policy:
            resource_properties["CreationPolicy"] = {"type": "object"}

        if type_name in self.resources_with_update_policy:
            resource_properties["UpdatePolicy"] = {"type": "object"}

        return {
            "type": "object",
            "additionalProperties": False,
            "properties": resource_properties,
            "required": ["Type", "Properties"] if required else ["Type"],
        }

    def _get_template_properties(self, resource_refs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Get CloudFormation template top-level properties"""
        return {
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
                "patternProperties": {"^[a-zA-Z0-9]+$": {"anyOf": resource_refs}},
                "additionalProperties": False,
            },
        }

    def _get_parameter_schema(self) -> Dict[str, Any]:
        """Get Parameter schema definition using configured parameter types"""
        return {
            "type": "object",
            "properties": {
                "Type": {
                    "type": "string",
                    "enum": self.parameter_types,
                },
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
            "additionalProperties": False,
            "required": ["Type"],
        }

    def _get_custom_resource_schema(self) -> Dict[str, Any]:
        """Get CustomResource schema definition"""
        return {
            "additionalProperties": False,
            "properties": {
                "Properties": {
                    "additionalProperties": True,
                    "properties": {"ServiceToken": {"type": "string"}},
                    "required": ["ServiceToken"],
                    "type": "object",
                },
                "Type": {"pattern": "^Custom::[a-zA-Z_@-]+$", "type": "string"},
            },
            "required": ["Type", "Properties"],
            "type": "object",
        }

    def _write_schema(self, schema: Dict[str, Any], output_file: str) -> None:
        """Write schema to file with proper formatting"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to JSON string and replace < and > with Unicode escapes
        json_str = json.dumps(schema, indent=4, sort_keys=True)
        json_str = json_str.replace("<", "\\u003c").replace(">", "\\u003e")
        output_path.write_text(json_str)


if __name__ == "__main__":
    generator = CloudFormationSchemaGenerator()
    generator.generate()
