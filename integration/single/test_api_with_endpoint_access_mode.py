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
        # Create stack with STRICT
        parameters = [
            {"ParameterKey": "SecurityPolicyValue", "ParameterValue": "SecurityPolicy_TLS13_1_3_2025_09"},
            {"ParameterKey": "EndpointAccessModeValue", "ParameterValue": "STRICT"},
        ]
        self.create_and_verify_stack("single/api_with_endpoint_access_mode", parameters)

        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        rest_api = self.client_provider.api_client.get_rest_api(restApiId=rest_api_id)

        self.assertEqual(rest_api["securityPolicy"], "SecurityPolicy_TLS13_1_3_2025_09")
        self.assertEqual(rest_api["endpointAccessMode"], "STRICT")

        # Update stack with BASIC
        update_parameters = [
            {"ParameterKey": "SecurityPolicyValue", "ParameterValue": "SecurityPolicy_TLS13_1_3_2025_09"},
            {"ParameterKey": "EndpointAccessModeValue", "ParameterValue": "BASIC"},
        ]
        self.update_stack(parameters=update_parameters)

        rest_api = self.client_provider.api_client.get_rest_api(restApiId=rest_api_id)

        self.assertEqual(rest_api["securityPolicy"], "SecurityPolicy_TLS13_1_3_2025_09")
        self.assertEqual(rest_api["endpointAccessMode"], "BASIC")
