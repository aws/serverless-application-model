from unittest.case import skipIf

from integration.config.service_names import REST_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([REST_API]), "REST API is not supported in this testing region")
class TestFunctionWithImplicitApiWithTimeout(BaseTest):
    def test_function_with_implicit_api_with_timeout(self):
        self.create_and_verify_stack("combination/function_with_implicit_api_with_timeout")

        # verify that TimeoutInMillis is set to expected value in the integration
        expected_timeout = 5000
        apigw_client = self.client_provider.api_client
        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        resources = apigw_client.get_resources(restApiId=rest_api_id)["items"]

        resource = get_resource_by_path(resources, "/hello")
        method = apigw_client.get_method(restApiId=rest_api_id, resourceId=resource["id"], httpMethod="GET")
        method_integration = method["methodIntegration"]
        self.assertEqual(method_integration["timeoutInMillis"], expected_timeout)


def get_resource_by_path(resources, path):
    for resource in resources:
        if resource["path"] == path:
            return resource
    return None
