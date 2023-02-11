from unittest.case import skipIf

from parameterized import parameterized

from integration.config.service_names import REST_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([REST_API]), "RestApi is not supported in this testing region")
class TestApiWithDisableExecuteApiEndpoint(BaseTest):
    @parameterized.expand(
        [
            ("combination/api_with_disable_execute_api_endpoint", True),
            ("combination/api_with_disable_execute_api_endpoint", False),
        ]
    )
    def test_end_point_configuration(self, file_name, disable_value):
        parameters = [
            {
                "ParameterKey": "DisableExecuteApiEndpointValue",
                "ParameterValue": "true" if disable_value else "false",
                "UsePreviousValue": False,
                "ResolvedValue": "string",
            }
        ]

        self.create_and_verify_stack(file_name, parameters)

        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        apigw_client = self.client_provider.api_client

        response = apigw_client.get_rest_api(restApiId=rest_api_id)
        api_result = response["disableExecuteApiEndpoint"]
        self.assertEqual(api_result, disable_value)

    @parameterized.expand(
        [
            ("combination/api_with_disable_execute_api_endpoint_openapi_3", True),
            ("combination/api_with_disable_execute_api_endpoint_openapi_3", False),
        ]
    )
    def test_end_point_configuration_openapi(self, file_name, disable_value):
        parameters = [
            {
                "ParameterKey": "DisableExecuteApiEndpointValue",
                "ParameterValue": "true" if disable_value else "false",
                "UsePreviousValue": False,
                "ResolvedValue": "string",
            }
        ]

        self.create_and_verify_stack(file_name, parameters)

        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        apigw_client = self.client_provider.api_client

        response = apigw_client.get_rest_api(restApiId=rest_api_id)
        api_result = response["disableExecuteApiEndpoint"]
        self.assertEqual(api_result, disable_value)
