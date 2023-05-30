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
class TestCustomHttpApiDomains(BaseInternalTest):
    def test_custom_http_api_domains_regional(self):
        self.create_and_verify_stack("combination/http_api_with_custom_domains_regional")

        domain_name_list = self.get_stack_resources("AWS::ApiGatewayV2::DomainName")
        self.assertEqual(1, len(domain_name_list))

        domain_name_id = self.get_physical_id_by_type("AWS::ApiGatewayV2::DomainName")

        api_gateway_client = self.client_provider.api_v2_client
        result = api_gateway_client.get_domain_name(DomainName=domain_name_id)

        if "FeatureToggle" in self.pipeline_prefix:
            self.assertEqual("httpapi.ftl.sam-gamma-regional.com", result["DomainName"])
        else:
            self.assertEqual("httpapi.sam-gamma-regional.com", result["DomainName"])

        mtls_auth_config = result["MutualTlsAuthentication"]
        self.assertEqual(self.file_to_s3_uri_map["MTLSCert.pem"]["uri"], mtls_auth_config["TruststoreUri"])

        domain_name_configs = result["DomainNameConfigurations"]
        self.assertEqual(1, len(domain_name_configs))
        domain_name_config = domain_name_configs[0]

        self.assertEqual("REGIONAL", domain_name_config["EndpointType"])
        self.assertEqual("TLS_1_2", domain_name_config["SecurityPolicy"])

    def test_custom_http_api_domains_regional_ownership_verification(self):
        self.create_and_verify_stack("combination/http_api_with_custom_domains_regional_ownership_verification")

        domain_name_id = self.get_physical_id_by_type("AWS::ApiGatewayV2::DomainName")
        api_gateway_client = self.client_provider.api_v2_client
        result = api_gateway_client.get_domain_name(DomainName=domain_name_id)

        domain_name_configs = result["DomainNameConfigurations"]
        self.assertEqual(1, len(domain_name_configs))
        domain_name_config = domain_name_configs[0]

        self.assertIsNotNone(domain_name_config.get("OwnershipVerificationCertificateArn"))
