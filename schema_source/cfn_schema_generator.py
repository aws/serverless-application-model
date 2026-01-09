#!/usr/bin/env python3
"""
CloudFormation Schema Generator - Python Port
Minimal working port of the Go goformation schema generator.
"""

import json
import gzip
import requests
from typing import Dict, Any, List
import os


class CloudFormationSchemaGenerator:
    """Python port of the Go CloudFormation schema generator"""
    
    def __init__(self, spec_url: str = "https://d1uauaxba7bl26.cloudfront.net/latest/gzip/CloudFormationResourceSpecification.json"):
        self.spec_url = spec_url
        self.type_map = {
            "String": "string", "Long": "number", "Integer": "number", "Double": "number",
            "Boolean": "boolean", "Timestamp": "string", "Json": "object", "Map": "object"
        }
    
    def generate(self, output_file: str = ".tmp/cloudformation.schema.json") -> None:
        """Generate CloudFormation JSON schema"""
        print("Downloading CloudFormation Resource Specification...")
        spec = self._download_spec()
        
        print("Generating CloudFormation JSON schema...")
        schema = self._generate_schema(spec)
        
        # Write to file with custom JSON encoder to match expected format
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        with open(output_file, 'w') as f:
            # Convert to JSON string and replace < and > with Unicode escapes to match expected format
            json_str = json.dumps(schema, indent=4, sort_keys=True)
            json_str = json_str.replace('<', '\\u003c').replace('>', '\\u003e')
            f.write(json_str)
        
        print(f"Successfully generated CloudFormation schema: {output_file}")
    
    def _download_spec(self) -> Dict[str, Any]:
        """Download and parse CloudFormation specification"""
        response = requests.get(self.spec_url)
        response.raise_for_status()
        
        # Handle gzipped content - check if actually gzipped
        content = response.content
        if content.startswith(b'\x1f\x8b'):  # gzip magic number
            content = gzip.decompress(content)
        
        return json.loads(content)
    
    def _generate_schema(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JSON schema from CloudFormation specification"""
        
        resources = spec.get('ResourceTypes', {})
        properties = spec.get('PropertyTypes', {})
        
        # Build resource references for anyOf
        resource_refs = [{"$ref": f"#/definitions/{name}"} for name in resources.keys()]
        resource_refs.append({"$ref": "#/definitions/CustomResource"})
        
        # Build definitions
        definitions = {}
        
        # Add Parameter definition
        definitions["Parameter"] = {
            "type": "object",
            "properties": {
                "Type": {
                    "type": "string",
                    "enum": [
                        "String", "Number", "List<Number>", "CommaDelimitedList",
                        "AWS::EC2::AvailabilityZone::Name", "AWS::EC2::Image::Id",
                        "AWS::EC2::Instance::Id", "AWS::EC2::KeyPair::KeyName",
                        "AWS::EC2::SecurityGroup::GroupName", "AWS::EC2::SecurityGroup::Id",
                        "AWS::EC2::Subnet::Id", "AWS::EC2::Volume::Id", "AWS::EC2::VPC::Id",
                        "AWS::Route53::HostedZone::Id", 
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
                        "AWS::SSM::Parameter::Name",
                        "AWS::SSM::Parameter::Value<String>",
                        "AWS::SSM::Parameter::Value<List<String>>",
                        "AWS::SSM::Parameter::Value<CommaDelimitedList>",
                        "AWS::SSM::Parameter::Value<AWS::EC2::AvailabilityZone::Name>",
                        "AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>",
                        "AWS::SSM::Parameter::Value<AWS::EC2::Instance::Id>",
                        "AWS::SSM::Parameter::Value<AWS::EC2::SecurityGroup::GroupName>",
                        "AWS::SSM::Parameter::Value<AWS::EC2::SecurityGroup::Id>",
                        "AWS::SSM::Parameter::Value<AWS::EC2::Subnet::Id>",
                        "AWS::SSM::Parameter::Value<AWS::EC2::Volume::Id>",
                        "AWS::SSM::Parameter::Value<AWS::EC2::VPC::Id>",
                        "AWS::SSM::Parameter::Value<AWS::Route53::HostedZone::Id>",
                        "AWS::SSM::Parameter::Value<List<AWS::EC2::AvailabilityZone::Name>>",
                        "AWS::SSM::Parameter::Value<List<AWS::EC2::Image::Id>>",
                        "AWS::SSM::Parameter::Value<List<AWS::EC2::Instance::Id>>",
                        "AWS::SSM::Parameter::Value<List<AWS::EC2::SecurityGroup::GroupName>>",
                        "AWS::SSM::Parameter::Value<List<AWS::EC2::SecurityGroup::Id>>",
                        "AWS::SSM::Parameter::Value<List<AWS::EC2::Subnet::Id>>",
                        "AWS::SSM::Parameter::Value<List<AWS::EC2::Volume::Id>>",
                        "AWS::SSM::Parameter::Value<List<AWS::EC2::VPC::Id>>",
                        "AWS::SSM::Parameter::Value<List<AWS::Route53::HostedZone::Id>>"
                    ]
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
                "NoEcho": {"type": ["string", "boolean"]}
            },
            "additionalProperties": False,
            "required": ["Type"]
        }
        
        # Add CustomResource definition
        definitions["CustomResource"] = {
            "additionalProperties": False,
            "properties": {
                "Properties": {
                    "additionalProperties": True,
                    "properties": {"ServiceToken": {"type": "string"}},
                    "required": ["ServiceToken"],
                    "type": "object"
                },
                "Type": {"pattern": "^Custom::[a-zA-Z_@-]+$", "type": "string"}
            },
            "required": ["Type", "Properties"],
            "type": "object"
        }
        
        # Add resource definitions
        for name, resource in resources.items():
            definitions[name] = self._generate_resource_schema(name, resource, False)
        
        # Add property definitions
        for name, prop in properties.items():
            definitions[name] = self._generate_resource_schema(name, prop, True)
        
        # Main schema structure
        schema = {
            "$id": "http://json-schema.org/draft-04/schema#",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "AWSTemplateFormatVersion": {
                    "type": "string",
                    "enum": ["2010-09-09"]
                },
                "Description": {
                    "description": "Template description",
                    "type": "string",
                    "maxLength": 1024
                },
                "Metadata": {"type": "object"},
                "Transform": {
                    "oneOf": [
                        {"type": ["string"]},
                        {"type": "array", "items": {"type": "string"}}
                    ]
                },
                "Parameters": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-zA-Z0-9]+$": {"$ref": "#/definitions/Parameter"}
                    },
                    "maxProperties": 50,
                    "additionalProperties": False
                },
                "Mappings": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-zA-Z0-9]+$": {"type": "object"}
                    },
                    "additionalProperties": False
                },
                "Conditions": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-zA-Z0-9]+$": {"type": "object"}
                    },
                    "additionalProperties": False
                },
                "Outputs": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-zA-Z0-9]+$": {"type": "object"}
                    },
                    "minProperties": 1,
                    "maxProperties": 60,
                    "additionalProperties": False
                },
                "Resources": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-zA-Z0-9]+$": {"anyOf": resource_refs}
                    },
                    "additionalProperties": False
                }
            },
            "required": ["Resources"],
            "definitions": definitions
        }
        
        return schema
    
    def _generate_resource_schema(self, name: str, resource: Dict[str, Any], is_custom_property: bool) -> Dict[str, Any]:
        """Generate schema for a CloudFormation resource"""
        properties = resource.get('Properties', {})
        required = sorted([prop_name for prop_name, prop in properties.items() if prop.get('Required', False)])
        
        prop_schemas = {}
        for prop_name, prop in properties.items():
            prop_schemas[prop_name] = self._generate_property_schema(prop_name, prop, name)
        
        if is_custom_property:
            schema = {
                "additionalProperties": False,
                "properties": prop_schemas,
                "type": "object"
            }
            if required:
                schema["required"] = required
            return schema
        else:
            properties_schema = {
                "additionalProperties": False,
                "properties": prop_schemas,
                "type": "object"
            }
            if required:
                properties_schema["required"] = required
                
            resource_schema = {
                "additionalProperties": False,
                "properties": {
                    "Condition": {"type": "string"},
                    "DeletionPolicy": {"enum": ["Delete", "Retain", "Snapshot"], "type": "string"},
                    "DependsOn": {
                        "anyOf": [
                            {"pattern": "^[a-zA-Z0-9]+$", "type": "string"},
                            {"items": {"pattern": "^[a-zA-Z0-9]+$", "type": "string"}, "type": "array"}
                        ]
                    },
                    "Metadata": {"type": "object"},
                    "Properties": properties_schema,
                    "Type": {"enum": [name], "type": "string"},
                    "UpdateReplacePolicy": {"enum": ["Delete", "Retain", "Snapshot"], "type": "string"}
                },
                "required": ["Type", "Properties"] if required else ["Type"],
                "type": "object"
            }
            
            # Add CreationPolicy for specific resources (matching Go template)
            if name in ["AWS::AutoScaling::AutoScalingGroup", "AWS::EC2::Instance", "AWS::CloudFormation::WaitCondition"]:
                resource_schema["properties"]["CreationPolicy"] = {"type": "object"}
                
            # Add UpdatePolicy only for AutoScaling groups (matching Go template)
            if name == "AWS::AutoScaling::AutoScalingGroup":
                resource_schema["properties"]["UpdatePolicy"] = {"type": "object"}
                
            return resource_schema
    
    def _generate_property_schema(self, name: str, prop: Dict[str, Any], parent: str) -> Dict[str, Any]:
        """Generate schema for a CloudFormation property"""
        
        # Extract resource name from parent (e.g., "AWS::S3::Bucket" from "AWS::S3::Bucket.Property")
        resource_name = parent.split('.')[0] if '.' in parent else parent
        
        # Handle polymorphic properties (simplified)
        if self._is_polymorphic(prop):
            any_of = []
            if prop.get('PrimitiveTypes'):
                any_of.append({"type": [self.type_map.get(pt, "string") for pt in prop['PrimitiveTypes']]})
            return {"anyOf": any_of} if any_of else {"type": "object"}
        
        # Handle simple primitive types
        if prop.get('PrimitiveType'):
            return {"type": self.type_map.get(prop['PrimitiveType'], "string")}
        
        # Handle lists
        if prop.get('Type') == 'List':
            if prop.get('PrimitiveItemType'):
                return {"type": "array", "items": {"type": self.type_map.get(prop['PrimitiveItemType'], "string")}}
            elif prop.get('ItemType'):
                item_type = prop['ItemType']
                # Use global reference for Tag type (matching Go template logic)
                if item_type == "Tag":
                    return {"type": "array", "items": {"$ref": "#/definitions/Tag"}}
                else:
                    return {"type": "array", "items": {"$ref": f"#/definitions/{resource_name}.{item_type}"}}
        
        # Handle maps
        if prop.get('Type') == 'Map':
            if prop.get('PrimitiveItemType'):
                return {
                    "type": "object",
                    "patternProperties": {
                        "^[a-zA-Z0-9]+$": {
                            "type": self.type_map.get(prop['PrimitiveItemType'], "string")
                        }
                    },
                    "additionalProperties": True
                }
            elif prop.get('ItemType'):
                item_type = prop['ItemType']
                # Use global reference for Tag type (matching Go template logic)
                if item_type == "Tag":
                    ref = "#/definitions/Tag"
                else:
                    ref = f"#/definitions/{resource_name}.{item_type}"
                return {
                    "type": "object",
                    "patternProperties": {
                        "^[a-zA-Z0-9]+$": {
                            "$ref": ref
                        }
                    },
                    "additionalProperties": False
                }
        
        # Handle custom types
        if prop.get('Type') and prop['Type'] not in ['List', 'Map']:
            prop_type = prop['Type']
            # Use global reference for Tag type (matching Go template logic)
            if prop_type == "Tag":
                return {"$ref": "#/definitions/Tag"}
            else:
                return {"$ref": f"#/definitions/{resource_name}.{prop_type}"}
        
        return {"type": "object"}
    
    def _is_polymorphic(self, prop: Dict[str, Any]) -> bool:
        """Check if property can be multiple different types"""
        return bool(
            prop.get('PrimitiveTypes') or prop.get('PrimitiveItemTypes') or
            prop.get('ItemTypes') or prop.get('Types') or
            prop.get('InclusivePrimitiveItemTypes') or prop.get('InclusiveItemTypes')
        )


if __name__ == "__main__":
    generator = CloudFormationSchemaGenerator()
    generator.generate()
