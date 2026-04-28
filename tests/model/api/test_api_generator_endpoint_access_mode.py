from unittest import TestCase
from unittest.mock import Mock

from samtranslator.model.api.api_generator import ApiGenerator


class TestApiGeneratorEndpointAccessMode(TestCase):
    def setUp(self):
        self.logical_id = "MyApi"
        self.default_args = {
            "logical_id": self.logical_id,
            "cache_cluster_enabled": None,
            "cache_cluster_size": None,
            "variables": None,
            "depends_on": None,
            "definition_body": {"swagger": "2.0"},
            "definition_uri": None,
            "name": None,
            "stage_name": "Prod",
            "shared_api_usage_plan": Mock(),
            "template_conditions": Mock(),
            "method_settings": None,
            "endpoint_configuration": {"Type": "REGIONAL"},
            "access_log_setting": None,
            "canary_setting": None,
            "tracing_enabled": None,
            "open_api_version": None,
            "always_deploy": None,
        }

    def test_endpoint_access_mode_set(self):
        api_generator = ApiGenerator(**self.default_args, endpoint_access_mode="STRICT")

        rest_api = api_generator._construct_rest_api()

        self.assertEqual(rest_api.EndpointAccessMode, "STRICT")

    def test_no_endpoint_access_mode(self):
        api_generator = ApiGenerator(**self.default_args, endpoint_access_mode=None)

        rest_api = api_generator._construct_rest_api()

        self.assertIsNone(rest_api.EndpointAccessMode)
