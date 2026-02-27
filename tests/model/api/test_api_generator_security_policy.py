from unittest import TestCase
from unittest.mock import Mock

from samtranslator.model.api.api_generator import ApiGenerator


class TestApiGeneratorSecurityPolicy(TestCase):
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

    def test_security_policy_tls_1_3(self):
        api_generator = ApiGenerator(**self.default_args, security_policy="SecurityPolicy_TLS13_1_3_2025_09")

        rest_api = api_generator._construct_rest_api()

        self.assertEqual(rest_api.SecurityPolicy, "SecurityPolicy_TLS13_1_3_2025_09")

    def test_no_security_policy(self):
        api_generator = ApiGenerator(**self.default_args, security_policy=None)

        rest_api = api_generator._construct_rest_api()

        self.assertIsNone(rest_api.SecurityPolicy)
