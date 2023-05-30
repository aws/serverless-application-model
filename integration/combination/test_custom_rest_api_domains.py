from unittest.case import skipIf

from integration.config.service_names import CUSTOM_DOMAIN
from integration.helpers.base_internal_test import BaseInternalTest
from integration.helpers.base_test import nonblocking
from integration.helpers.resource import current_region_not_included


@skipIf(
    current_region_not_included([CUSTOM_DOMAIN]),
    "CustomDomain is not supported in this testing region",
)
@nonblocking
class TestCustomRestApiDomains(BaseInternalTest):
    def test_custom_rest_api_domains_edge(self):
        self.create_and_verify_stack("combination/api_with_custom_domains_edge")

        domain_name_list = self.get_stack_resources("AWS::ApiGateway::DomainName")
        self.assertEqual(1, len(domain_name_list))

        domain_name_id = self.get_physical_id_by_type("AWS::ApiGateway::DomainName")
        api_gateway_client = self.client_provider.api_client
        result = api_gateway_client.get_domain_name(domainName=domain_name_id)

        if "FeatureToggle" in self.pipeline_prefix:
            self.assertEqual("ftl.sam-gamma-edge.com", result["domainName"])
        else:
            self.assertEqual("sam-gamma-edge.com", result["domainName"])

        end_point_config = result["endpointConfiguration"]
        end_point_types = end_point_config["types"]
        self.assertEqual(1, len(end_point_types))
        self.assertEqual("EDGE", end_point_types[0])

    def test_custom_rest_api_domains_regional(self):
        self.create_and_verify_stack("combination/api_with_custom_domains_regional")

        domain_name_list = self.get_stack_resources("AWS::ApiGateway::DomainName")
        self.assertEqual(1, len(domain_name_list))

        domain_name_id = self.get_physical_id_by_type("AWS::ApiGateway::DomainName")

        api_gateway_client = self.client_provider.api_client
        result = api_gateway_client.get_domain_name(domainName=domain_name_id)

        if "FeatureToggle" in self.pipeline_prefix:
            self.assertEqual("ftl.sam-gamma-regional.com", result["domainName"])
        else:
            self.assertEqual("sam-gamma-regional.com", result["domainName"])

        self.assertEqual("TLS_1_2", result["securityPolicy"])

        end_point_config = result["endpointConfiguration"]
        end_point_types = end_point_config["types"]
        self.assertEqual(1, len(end_point_types))
        self.assertEqual("REGIONAL", end_point_types[0])

        mtls_auth_config = result["mutualTlsAuthentication"]
        self.assertEqual(self.file_to_s3_uri_map["MTLSCert.pem"]["uri"], mtls_auth_config["truststoreUri"])

    def test_custom_rest_api_domains_regional_ownership_verification(self):
        self.create_and_verify_stack("combination/api_with_custom_domains_regional_ownership_verification")

        domain_name_id = self.get_physical_id_by_type("AWS::ApiGateway::DomainName")
        api_gateway_client = self.client_provider.api_client
        result = api_gateway_client.get_domain_name(domainName=domain_name_id)

        self.assertIsNotNone(result.get("ownershipVerificationCertificateArn"))
