from unittest.case import skipIf

from integration.config.service_names import CUSTOM_DOMAIN, SECURITY_POLICY_REST_API
from integration.helpers.base_internal_test import BaseInternalTest
from integration.helpers.base_test import nonblocking
from integration.helpers.resource import current_region_does_not_support, current_region_not_included


@skipIf(
    current_region_not_included([CUSTOM_DOMAIN]) or current_region_does_not_support([SECURITY_POLICY_REST_API]),
    "Custom domain or SecurityPolicy are not supported in this testing region",
)
@nonblocking
class TestApiWithCustomDomainSecurityPolicy(BaseInternalTest):
    """
    Test AWS::Serverless::Api with SecurityPolicy and EndpointAccessMode in Domain configuration
    """

    def test_api_with_custom_domain_security_policy_regional(self):
        self.create_and_verify_stack("single/api_with_custom_domain_security_policy_regional")

        domain_name_id = self.get_physical_id_by_type("AWS::ApiGateway::DomainName")
        result = self.client_provider.api_client.get_domain_name(domainName=domain_name_id)

        end_point_config = result["endpointConfiguration"]
        self.assertEqual(["REGIONAL"], end_point_config["types"])
        self.assertEqual("SecurityPolicy_TLS13_1_3_2025_09", result["securityPolicy"])
        self.assertEqual("STRICT", result["endpointAccessMode"])

    def test_api_with_custom_domain_security_policy_edge(self):
        self.create_and_verify_stack("single/api_with_custom_domain_security_policy_edge")

        domain_name_id = self.get_physical_id_by_type("AWS::ApiGateway::DomainName")
        result = self.client_provider.api_client.get_domain_name(domainName=domain_name_id)

        end_point_config = result["endpointConfiguration"]
        self.assertEqual(["EDGE"], end_point_config["types"])
        self.assertEqual("SecurityPolicy_TLS13_2025_EDGE", result["securityPolicy"])
        self.assertEqual("STRICT", result["endpointAccessMode"])
