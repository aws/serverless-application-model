from unittest.case import skipIf

from parameterized import parameterized

from integration.config.service_names import HTTP_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([HTTP_API]), "HttpApi is not supported in this testing region")
class TestHttpApiWithFailOnWarnings(BaseTest):
    @parameterized.expand(
        [
            ("combination/http_api_with_fail_on_warnings_and_default_stage_name", True),
            ("combination/http_api_with_fail_on_warnings_and_default_stage_name", False),
        ]
    )
    def test_http_api_with_fail_on_warnings(self, file_name, disable_value):
        parameters = [
            {
                "ParameterKey": "FailOnWarningsValue",
                "ParameterValue": "true" if disable_value else "false",
                "UsePreviousValue": False,
                "ResolvedValue": "string",
            }
        ]

        self.create_and_verify_stack(file_name, parameters)

        http_api_id = self.get_physical_id_by_type("AWS::ApiGatewayV2::Api")
        apigw_v2_client = self.client_provider.api_v2_client

        api_result = apigw_v2_client.get_api(ApiId=http_api_id)
        self.assertEqual(api_result["ResponseMetadata"]["HTTPStatusCode"], 200)
