import logging
from unittest.case import skipIf

from tenacity import after_log, retry, retry_if_exception_type, stop_after_attempt, wait_exponential, wait_random

from integration.config.service_names import GATEWAY_RESPONSES, REST_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support

LOG = logging.getLogger(__name__)


@skipIf(
    current_region_does_not_support([GATEWAY_RESPONSES, REST_API]),
    "GatewayResponses is not supported in this testing region",
)
class TestApiWithGatewayResponses(BaseTest):
    def test_gateway_responses(self):
        self.create_and_verify_stack("combination/api_with_gateway_responses")

        stack_outputs = self.get_stack_outputs()
        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        apigw_client = self.client_provider.api_client

        gateway_responses_result = apigw_client.get_gateway_responses(restApiId=rest_api_id)
        gateway_responses = gateway_responses_result["items"]
        gateway_response_type = "DEFAULT_4XX"
        gateway_response = get_gateway_response_by_type(gateway_responses, gateway_response_type)

        self.assertEqual(gateway_response["defaultResponse"], False, "gatewayResponse: Default Response must be false")
        self.assertEqual(
            gateway_response["responseType"],
            gateway_response_type,
            "gatewayResponse: response type must be " + gateway_response_type,
        )
        self.assertEqual(gateway_response.get("statusCode"), None, "gatewayResponse: status code must be none")

        base_url = stack_outputs["ApiUrl"]
        self._verify_request_response_and_cors(base_url + "iam", 403)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10) + wait_random(0, 1),
        retry=retry_if_exception_type(AssertionError),
        after=after_log(LOG, logging.WARNING),
        reraise=True,
    )
    def _verify_request_response_and_cors(self, url, expected_response):
        response = self.verify_get_request_response(url, expected_response)
        access_control_allow_origin = response.headers.get("Access-Control-Allow-Origin", "")
        self.assertEqual(access_control_allow_origin, "*", "Access-Control-Allow-Origin must be '*'")


def get_gateway_response_by_type(gateway_responses, gateway_response_type):
    for response in gateway_responses:
        if response["responseType"] == gateway_response_type:
            return response
    return None
