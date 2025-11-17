from unittest import TestCase
from unittest.mock import Mock, patch

from parameterized import parameterized
from samtranslator.model import InvalidResourceException
from samtranslator.model.api.api_generator import ApiGenerator


class TestApiGenerator(TestCase):
    @parameterized.expand([("this should be a dict",), ("123",), ([{}],)])
    @patch("samtranslator.model.api.api_generator.AuthProperties")
    def test_construct_usage_plan_with_invalid_usage_plan_type(self, invalid_usage_plan, AuthProperties_mock):
        AuthProperties_mock.return_value = Mock(UsagePlan=invalid_usage_plan)
        api_generator = ApiGenerator(
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            auth={"some": "value"},
        )
        with self.assertRaises(InvalidResourceException) as cm:
            api_generator._construct_usage_plan()
            self.assertIn("Invalid type", str(cm.exception))

    @patch("samtranslator.model.api.api_generator.AuthProperties")
    def test_construct_usage_plan_with_invalid_usage_plan_fields(self, AuthProperties_mock):
        AuthProperties_mock.return_value = Mock(UsagePlan={"Unknown_field": "123"})
        api_generator = ApiGenerator(
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            auth={"some": "value"},
        )
        with self.assertRaises(InvalidResourceException) as cm:
            api_generator._construct_usage_plan()
            self.assertIn("Invalid property for", str(cm.exception))

    def test_add_cors_with_trailing_slash_paths(self):
        """Test that CORS doesn't create duplicate OPTIONS methods for paths with/without trailing slash"""
        # Create a simple swagger definition with paths that differ only by trailing slash
        definition_body = {
            "swagger": "2.0",
            "info": {"title": "TestAPI", "version": "1.0"},
            "paths": {
                "/datasets": {
                    "post": {
                        "x-amazon-apigateway-integration": {
                            "type": "aws_proxy",
                            "httpMethod": "POST",
                            "uri": "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/func/invocations"
                        }
                    }
                },
                "/datasets/": {
                    "put": {
                        "x-amazon-apigateway-integration": {
                            "type": "aws_proxy",
                            "httpMethod": "POST",
                            "uri": "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/func/invocations"
                        }
                    }
                }
            }
        }
        
        api_generator = ApiGenerator(
            logical_id="TestApi",
            cache_cluster_enabled=None,
            cache_cluster_size=None,
            variables=None,
            depends_on=None,
            definition_body=definition_body,
            definition_uri=None,
            name=None,
            stage_name="Prod",
            shared_api_usage_plan=None,  # Added required parameter
            template_conditions=None,  # Added required parameter
            tags=None,
            endpoint_configuration=None,
            method_settings=None,
            binary_media=None,
            minimum_compression_size=None,
            cors="'*'",  # Enable CORS
            auth=None,
            gateway_responses=None,
            access_log_setting=None,
            canary_setting=None,
            tracing_enabled=None,
            resource_attributes=None,
            passthrough_resource_attributes=None,
            open_api_version=None,
            models=None,
            domain=None,
            fail_on_warnings=None,
            description=None,
            mode=None,
            api_key_source_type=None,
            disable_execute_api_endpoint=None,
        )
        
        # Call _add_cors which should normalize paths and avoid duplicates
        api_generator._add_cors()
        
        # Check that OPTIONS method is not added to both /datasets and /datasets/
        # It should only be added once to avoid the duplicate OPTIONS error
        paths_with_options = [
            path for path, methods in api_generator.definition_body["paths"].items()
            if "options" in methods or "OPTIONS" in methods
        ]
        
        # We should have only ONE path with OPTIONS method (the normalized one)
        # Both /datasets and /datasets/ normalize to /datasets
        self.assertEqual(len(paths_with_options), 1, 
                        "CORS should only add OPTIONS to one of the paths that differ by trailing slash")

