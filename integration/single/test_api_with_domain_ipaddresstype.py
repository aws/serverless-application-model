from unittest.case import skipIf

from integration.config.service_names import CUSTOM_DOMAIN
from integration.helpers.base_internal_test import BaseInternalTest
from integration.helpers.base_test import nonblocking
from integration.helpers.resource import current_region_not_included


@skipIf(
    current_region_not_included([CUSTOM_DOMAIN]),
    "Custom domain is not supported in this testing region",
)
@nonblocking
class TestApiWithDomainIpAddressType(BaseInternalTest):
    """
    Test AWS::Serverless::Api with IpAddressType in Domain configuration
    """

    def test_api_with_domain_ipaddresstype(self):
        """
        Creates an API with custom domain and IpAddressType set to dualstack
        """
        self.create_and_verify_stack("single/api_with_domain_ipaddresstype")

        # Verify the domain name resource
        domain_name_id = self.get_physical_id_by_type("AWS::ApiGateway::DomainName")
        api_gateway_client = self.client_provider.api_client
        result = api_gateway_client.get_domain_name(domainName=domain_name_id)

        # Verify endpoint configuration
        end_point_config = result["endpointConfiguration"]
        end_point_types = end_point_config["types"]
        self.assertEqual(1, len(end_point_types))
        self.assertEqual("REGIONAL", end_point_types[0])

        # Verify IpAddressType is set correctly
        self.assertEqual("dualstack", end_point_config["ipAddressType"])
