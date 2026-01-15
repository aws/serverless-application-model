#!/usr/bin/env python3
"""
Tests for CloudFormation Schema Generator V2
"""

import json
import os
import unittest
from unittest.mock import ANY, Mock, patch

from parameterized import parameterized
from schema_source.cfn_schema_generator import CFN_SCHEMA_URL, CloudFormationSchemaGenerator


class TestCloudFormationSchemaGenerator(unittest.TestCase):
    """Unit tests for CloudFormation Schema Generator"""

    def setUp(self):
        self.generator = CloudFormationSchemaGenerator()

    @parameterized.expand(
        [
            ("template_properties",),
            ("resources_with_creation_policy",),
            ("resources_with_update_policy",),
            ("parameter_types",),
        ]
    )
    def test_initialization_with_defaults(self, attr_name):
        """Test generator initializes with default configuration"""
        generator = CloudFormationSchemaGenerator()
        self.assertIsNotNone(getattr(generator, attr_name))

    def test_initialization_schema_url_is_constant(self):
        """Test that schema URL is always the official AWS endpoint"""

        generator = CloudFormationSchemaGenerator()
        self.assertEqual(generator.schema_url, CFN_SCHEMA_URL)
        self.assertEqual(
            generator.schema_url, "https://schema.cloudformation.us-east-1.amazonaws.com/CloudformationSchema.zip"
        )

    @parameterized.expand(
        [
            ("template_properties", {"CustomProp": {"type": "string"}}),
            ("resources_with_creation_policy", {"AWS::Custom::Resource"}),
            ("resources_with_update_policy", {"AWS::Custom::Resource"}),
            ("parameter_types", ["String", "Number"]),
        ]
    )
    def test_initialization_with_custom_config(self, param_name, custom_value):
        """Test generator accepts custom configuration"""
        kwargs = {param_name: custom_value}
        generator = CloudFormationSchemaGenerator(**kwargs)
        self.assertEqual(getattr(generator, param_name), custom_value)

    def test_wrap_resource_schema_basic(self):
        """Test wrapping a basic resource schema"""
        type_name = "AWS::Test::Resource"
        schema = {
            "typeName": type_name,
            "properties": {"Name": {"type": "string"}, "Value": {"type": "integer"}},
            "required": ["Name"],
            "additionalProperties": False,
        }

        result = self.generator._wrap_resource_schema(type_name, schema)

        # Verify structure
        self.assertEqual(result["type"], "object")
        self.assertFalse(result["additionalProperties"])
        self.assertIn("properties", result)
        self.assertIn("required", result)

        # Verify Type property
        self.assertEqual(result["properties"]["Type"]["enum"], [type_name])

        # Verify Properties are preserved
        self.assertEqual(result["properties"]["Properties"]["properties"], schema["properties"])
        self.assertEqual(result["properties"]["Properties"]["required"], ["Name"])

    @parameterized.expand(
        [
            ("AWS::AutoScaling::AutoScalingGroup", "CreationPolicy"),
            ("AWS::EC2::Instance", "CreationPolicy"),
            ("AWS::CloudFormation::WaitCondition", "CreationPolicy"),
        ]
    )
    def test_wrap_resource_schema_with_creation_policy(self, type_name, policy_name):
        """Test wrapping resource that supports CreationPolicy"""
        schema = {"typeName": type_name, "properties": {}, "additionalProperties": False}
        result = self.generator._wrap_resource_schema(type_name, schema)

        self.assertIn(policy_name, result["properties"])
        self.assertEqual(result["properties"][policy_name]["type"], "object")

    @parameterized.expand(
        [
            ("AWS::AutoScaling::AutoScalingGroup", "UpdatePolicy"),
        ]
    )
    def test_wrap_resource_schema_with_update_policy(self, type_name, policy_name):
        """Test wrapping resource that supports UpdatePolicy"""
        schema = {"typeName": type_name, "properties": {}, "additionalProperties": False}
        result = self.generator._wrap_resource_schema(type_name, schema)

        self.assertIn(policy_name, result["properties"])
        self.assertEqual(result["properties"][policy_name]["type"], "object")

    @parameterized.expand(
        [
            ("String",),
            ("Number",),
            ("AWS::EC2::Instance::Id",),
            ("List<String>",),
            ("AWS::SSM::Parameter::Name",),
        ]
    )
    def test_get_parameter_schema_includes_type(self, param_type):
        """Test parameter schema includes specific parameter types"""
        result = self.generator._get_parameter_schema()
        param_types = result["properties"]["Type"]["enum"]
        self.assertIn(param_type, param_types)

    def test_get_parameter_schema_structure(self):
        """Test parameter schema has correct structure using ANY matcher"""
        result = self.generator._get_parameter_schema()

        expected_structure = {
            "type": "object",
            "properties": {
                "Type": {"type": ANY, "enum": ANY},
                "AllowedPattern": ANY,
                "AllowedValues": ANY,
                "ConstraintDescription": ANY,
                "Default": ANY,
                "Description": ANY,
                "MaxLength": ANY,
                "MaxValue": ANY,
                "MinLength": ANY,
                "MinValue": ANY,
                "NoEcho": ANY,
            },
            "additionalProperties": False,
            "required": ["Type"],
        }

        # Compare key structure elements
        self.assertEqual(result["type"], expected_structure["type"])
        self.assertEqual(result["required"], expected_structure["required"])
        self.assertEqual(result["additionalProperties"], expected_structure["additionalProperties"])
        self.assertIn("Type", result["properties"])
        self.assertIn("enum", result["properties"]["Type"])

    @parameterized.expand(
        [
            ("type", "object"),
            ("additionalProperties", False),
        ]
    )
    def test_get_custom_resource_schema_properties(self, key, expected_value):
        """Test custom resource schema properties"""
        result = self.generator._get_custom_resource_schema()
        self.assertEqual(result[key], expected_value)

    def test_get_custom_resource_schema_structure(self):
        """Test custom resource schema structure using ANY matcher"""
        result = self.generator._get_custom_resource_schema()

        expected_structure = {
            "type": "object",
            "additionalProperties": False,
            "required": ["Type", "Properties"],
            "properties": {
                "Type": {"pattern": "^Custom::[a-zA-Z_@-]+$", "type": ANY},
                "Properties": {
                    "additionalProperties": ANY,
                    "properties": {"ServiceToken": ANY},
                    "required": ["ServiceToken"],
                    "type": ANY,
                },
            },
        }

        # Compare structure
        self.assertEqual(result["type"], expected_structure["type"])
        self.assertEqual(result["required"], expected_structure["required"])
        self.assertEqual(result["additionalProperties"], expected_structure["additionalProperties"])
        self.assertEqual(result["properties"]["Type"]["pattern"], expected_structure["properties"]["Type"]["pattern"])
        self.assertEqual(
            result["properties"]["Properties"]["required"], expected_structure["properties"]["Properties"]["required"]
        )

    @parameterized.expand(
        [
            ("AWSTemplateFormatVersion",),
            ("Description",),
            ("Parameters",),
            ("Resources",),
            ("Outputs",),
            ("Conditions",),
            ("Mappings",),
            ("Metadata",),
            ("Transform",),
        ]
    )
    def test_get_template_properties_includes_section(self, section_name):
        """Test template properties includes required sections"""
        resource_refs = [{"$ref": "#/definitions/AWS::Test::Resource"}]
        result = self.generator._get_template_properties(resource_refs)
        self.assertIn(section_name, result)

    def test_get_template_properties_version(self):
        """Test template properties has correct version"""
        resource_refs = [{"$ref": "#/definitions/AWS::Test::Resource"}]
        result = self.generator._get_template_properties(resource_refs)
        self.assertEqual(result["AWSTemplateFormatVersion"]["enum"], ["2010-09-09"])

    def test_get_template_properties_resources_refs(self):
        """Test template properties includes resource references"""
        resource_refs = [{"$ref": "#/definitions/AWS::Test::Resource"}]
        result = self.generator._get_template_properties(resource_refs)
        self.assertEqual(result["Resources"]["patternProperties"]["^[a-zA-Z0-9]+$"]["anyOf"], resource_refs)

    @parameterized.expand(
        [
            ("type", "object"),
            ("required", ["Resources"]),
        ]
    )
    def test_generate_unified_schema_structure_properties(self, key, expected_value):
        """Test unified schema structure properties"""
        resource_schemas = {
            "AWS::Test::Resource": {
                "typeName": "AWS::Test::Resource",
                "properties": {"Name": {"type": "string"}},
                "definitions": {"TestType": {"type": "object"}},
            }
        }
        result = self.generator._generate_unified_schema(resource_schemas)
        self.assertEqual(result[key], expected_value)

    @parameterized.expand(
        [
            ("AWS::Test::Resource",),
            ("AWS::Test::Resource.TestType",),
            ("Parameter",),
            ("CustomResource",),
        ]
    )
    def test_generate_unified_schema_includes_definition(self, definition_name):
        """Test unified schema includes expected definitions"""
        resource_schemas = {
            "AWS::Test::Resource": {
                "typeName": "AWS::Test::Resource",
                "properties": {"Name": {"type": "string"}},
                "definitions": {"TestType": {"type": "object"}},
            }
        }
        result = self.generator._generate_unified_schema(resource_schemas)
        self.assertIn(definition_name, result["definitions"])

    @patch.object(CloudFormationSchemaGenerator, "_download_and_extract_schemas")
    @patch.object(CloudFormationSchemaGenerator, "_write_schema")
    def test_generate_end_to_end(self, mock_write, mock_download):
        """Test end-to-end generation flow"""
        # Mock download
        mock_download.return_value = {
            "AWS::Test::Resource": {
                "typeName": "AWS::Test::Resource",
                "properties": {"Name": {"type": "string"}},
            }
        }

        # Test
        output_file = ".tmp/test-schema.json"
        self.generator.generate(output_file)

        # Verify download was called
        mock_download.assert_called_once()

        # Verify write was called with schema
        mock_write.assert_called_once()
        call_args = mock_write.call_args
        schema = call_args[0][0]
        output_path = call_args[0][1]

        self.assertEqual(output_path, output_file)
        self.assertIn("definitions", schema)
        self.assertIn("AWS::Test::Resource", schema["definitions"])


class TestCloudFormationSchemaGeneratorIntegration(unittest.TestCase):
    """Integration test using real CloudFormation schema zip file"""

    def setUp(self):
        self.generator = CloudFormationSchemaGenerator()
        self.input_file = "tests/schema/cfn_schema_generator/input/CloudformationSchema.zip"
        self.expected_output_file = "tests/schema/cfn_schema_generator/output_schema/cloudformation.schema.json"

    def test_schema_generation_from_zip(self):
        """Test schema generation from CloudformationSchema.zip matches expected output"""
        # Skip if files don't exist
        if not os.path.exists(self.input_file):
            self.skipTest(f"Input file {self.input_file} not found")
        if not os.path.exists(self.expected_output_file):
            self.skipTest(f"Expected output file {self.expected_output_file} not found")

        # Read the zip file content
        with open(self.input_file, "rb") as f:
            zip_content = f.read()

        # Mock the HTTP request to use local file instead
        with patch("schema_source.cfn_schema_generator.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.content = zip_content
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            # Generate schema to temporary location
            test_output_file = ".tmp/test-cloudformation.schema.json"
            self.generator.generate(test_output_file)

        # Load generated schema
        with open(test_output_file) as f:
            generated_schema = json.load(f)

        # Load expected output
        with open(self.expected_output_file) as f:
            expected_schema = json.load(f)

        # Compare schemas - they should be identical
        self.assertEqual(
            generated_schema,
            expected_schema,
            "Generated schema does not match expected output",
        )

        # Clean up test output
        if os.path.exists(test_output_file):
            os.remove(test_output_file)
