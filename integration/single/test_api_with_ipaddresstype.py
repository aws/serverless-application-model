from unittest.case import skipIf

from integration.config.service_names import REST_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([REST_API]), "Rest API is not supported in this testing region")
class TestApiWithIpAddressType(BaseTest):
    """
    Test AWS::Serverless::Api with IpAddressType in EndpointConfiguration
    """

    def test_api_with_ipaddresstype(self):
        """
        Creates an API with IpAddressType set to ipv4
        """
        parameters = [{"ParameterKey": "IpAddressType", "ParameterValue": "ipv4"}]
        self.create_and_verify_stack("single/api_with_ipaddresstype", parameters)

        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        rest_api = self.client_provider.api_client.get_rest_api(restApiId=rest_api_id)

        self.assertEqual(rest_api["endpointConfiguration"]["types"], ["REGIONAL"])
        self.assertEqual(rest_api["endpointConfiguration"]["ipAddressType"], "ipv4")
