from unittest.case import skipIf

from integration.config.service_names import REST_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([REST_API]), "Rest API is not supported in this testing region")
class TestApiWithEndpointAccessMode(BaseTest):
    """
    Tests for AWS::Serverless::Api with EndpointAccessMode property
    """

    def test_api_with_endpoint_access_mode(self):
        self.create_and_verify_stack("single/api_with_endpoint_access_mode")

        rest_api_resources = self.get_stack_resources("AWS::ApiGateway::RestApi")
        self.assertEqual(len(rest_api_resources), 1)
