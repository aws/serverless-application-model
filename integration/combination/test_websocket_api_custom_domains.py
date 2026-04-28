from unittest.case import skipIf

from integration.config.service_names import CUSTOM_DOMAIN, WEBSOCKET_API
from integration.helpers.base_internal_test import (
    CUSTOM_DOMAIN_TOP_LEVEL,
    FEATURE_TOGGLE_CUSTOM_DOMAIN_TOP_LEVEL,
    BaseInternalTest,
)
from integration.helpers.base_test import nonblocking
from integration.helpers.resource import current_region_does_not_support, current_region_not_included


# Custom domain tests require pre-created infrastructure (hosted zones, certificates)
# that only exists in us-east-1.
@skipIf(
    current_region_does_not_support([WEBSOCKET_API]) or current_region_not_included([CUSTOM_DOMAIN]),
    "WebSocketApi is not supported or CustomDomain infrastructure is not available in this testing region",
)
@nonblocking
class TestWebSocketApiCustomDomains(BaseInternalTest):
    def test_websocket_custom_api_domains_regional(self):
        self.create_and_verify_stack("combination/websocket_api_custom_domains_regional")

        domain_name_list = self.get_stack_resources("AWS::ApiGatewayV2::DomainName")
        self.assertEqual(1, len(domain_name_list))

        domain_name_id = self.get_physical_id_by_type("AWS::ApiGatewayV2::DomainName")

        api_gateway_client = self.client_provider.api_v2_client
        result = api_gateway_client.get_domain_name(DomainName=domain_name_id)

        if "FeatureToggle" in self.pipeline_prefix:
            self.assertEqual(
                f"websocket-sam-gamma-regional.{FEATURE_TOGGLE_CUSTOM_DOMAIN_TOP_LEVEL}", result["DomainName"]
            )
        else:
            self.assertEqual(f"websocket-sam-gamma-regional.{CUSTOM_DOMAIN_TOP_LEVEL}", result["DomainName"])

        domain_name_configs = result["DomainNameConfigurations"]
        self.assertEqual(1, len(domain_name_configs))
        domain_name_config = domain_name_configs[0]

        self.assertEqual("REGIONAL", domain_name_config["EndpointType"])
        self.assertEqual("TLS_1_2", domain_name_config["SecurityPolicy"])

        domain_name_configs = result["DomainNameConfigurations"]
        self.assertEqual(1, len(domain_name_configs))
