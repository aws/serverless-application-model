#!/usr/bin/env python3
"""
Tests for CloudFormation Schema Generator
"""

import json
import os
import unittest
from unittest.mock import Mock, patch
from parameterized import parameterized
from schema_source.cfn_schema_generator import CloudFormationSchemaGenerator


class TestCloudFormationSchemaGeneratorUnit(unittest.TestCase):
    """Unit tests for CloudFormation Schema Generator"""
    
    def setUp(self):
        self.generator = CloudFormationSchemaGenerator()
    
    def test_generate_property_schema_polymorphic(self):
        """Test polymorphic property schema generation"""
        # Test polymorphic with PrimitiveTypes
        prop = {"PrimitiveTypes": ["String", "Integer"]}
        result = self.generator._generate_property_schema(prop, "AWS::Test::Resource")
        expected = {"anyOf": [{"type": ["string", "integer"]}]}
        self.assertEqual(result, expected)
        
        # Test polymorphic with no PrimitiveTypes (fallback)
        prop = {"ItemTypes": ["Type1", "Type2"]}
        result = self.generator._generate_property_schema(prop, "AWS::Test::Resource")
        expected = {"type": "object"}
        self.assertEqual(result, expected)
    
    def test_is_polymorphic(self):
        """Test polymorphic property detection"""
        # Test non-polymorphic property
        prop = {"PrimitiveType": "String"}
        self.assertFalse(self.generator._is_polymorphic(prop))
        
        # Test polymorphic properties
        prop = {"PrimitiveTypes": ["String", "Integer"]}
        self.assertTrue(self.generator._is_polymorphic(prop))
        
        prop = {"ItemTypes": ["Type1", "Type2"]}
        self.assertTrue(self.generator._is_polymorphic(prop))
        
        prop = {"Types": ["Type1", "Type2"]}
        self.assertTrue(self.generator._is_polymorphic(prop))
    
    def test_main_function_execution(self):
        """Test main function execution"""
        with patch('schema_source.cfn_schema_generator.CloudFormationSchemaGenerator') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            
            # Execute the main block by importing the module
            import sys
            if 'schema_source.cfn_schema_generator' in sys.modules:
                del sys.modules['schema_source.cfn_schema_generator']
            
            # Mock __name__ to be '__main__'
            with patch('schema_source.cfn_schema_generator.__name__', '__main__'):
                import schema_source.cfn_schema_generator
            
            mock_class.assert_called_once()
            mock_instance.generate.assert_called_once()


class TestCloudFormationSchemaGenerator(unittest.TestCase):
    """Parameterized tests using input/output file pairs"""
    
    def setUp(self):
        self.generator = CloudFormationSchemaGenerator()
        self.input_folder = "tests/schema/cfn_schema_generator/input_spec"
        self.output_folder = "tests/schema/cfn_schema_generator/output_schema"
    
    @staticmethod
    def _get_test_cases():
        """Get all test case files from input folder"""
        input_folder = "tests/schema/cfn_schema_generator/input_spec"
        if not os.path.exists(input_folder):
            return []
        
        test_cases = []
        for filename in os.listdir(input_folder):
            if filename.endswith('.json'):
                case_name = os.path.splitext(filename)[0]
                test_cases.append((case_name,))
        return test_cases
    
    @parameterized.expand(_get_test_cases(), skip_on_empty=True)
    def test_schema_generation(self, case_name):
        """Test schema generation for a specific case"""
        input_file = os.path.join(self.input_folder, f"{case_name}.json")
        expected_output_file = os.path.join(self.output_folder, f"{case_name}.json")
        
        # Skip if files don't exist
        if not os.path.exists(input_file):
            self.skipTest(f"Input file {input_file} not found")
        if not os.path.exists(expected_output_file):
            self.skipTest(f"Expected output file {expected_output_file} not found")
        
        # Load input spec
        with open(input_file, 'r') as f:
            spec = json.load(f)
        
        # Generate schema
        result = self.generator._generate_schema(spec)
        
        # Load expected output
        with open(expected_output_file, 'r') as f:
            expected = json.load(f)
        
        # Compare results
        self.assertEqual(result, expected, f"Generated schema for {case_name} does not match expected output")


if __name__ == '__main__':
    unittest.main()
