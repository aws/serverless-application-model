import boto3
import os
from helpers.base_test import BaseTest
from helpers.resources import Resources
from helpers.resource_types import ResourceTypes


class HttpApiCorsTest(BaseTest):
    http_api_with_cors_resources = (
        Resources()
        .created("HttpApiFunction", ResourceTypes.LAMBDA_FUNCTION)
        .created("HttpApiFunctionRole", ResourceTypes.IAM_ROLE)
        .created("HttpApiFunctionImplicitApiPermission", ResourceTypes.LAMBDA_PERMISSION)
        .created("ServerlessHttpApi", ResourceTypes.APIGWV2_HTTPAPI)
        .created("ServerlessHttpApiApiGatewayDefaultStage", ResourceTypes.APIGWV2_STAGE)
    )

    def tearDown(self):
        self.delete_stack()

    def test_cors(self):
        input_template = os.path.join(os.getcwd(), "end-to-end-tests/input", "http_api_cors", "template.yaml")
        capabilities = ["CAPABILITY_IAM"]
        stack_name = self.make_and_verify_stack(input_template, capabilities, self.http_api_with_cors_resources)
        outputs = self.get_outputs()
        apigatewayV2_client = boto3.client("apigatewayv2")
        api_result = apigatewayV2_client.get_api(ApiId=outputs.get("ApiId"))

        # test cors
        cors_configuration = api_result.get("CorsConfiguration")
        self.assertEquals(cors_configuration.get("AllowMethods"), ["GET"])
        self.assertEquals(cors_configuration.get("ExposeHeaders"), ["x-amzn-header"])
        self.assertEquals(cors_configuration.get("AllowOrigins"), ["https://foo.com"])
        self.assertEquals(cors_configuration.get("AllowHeaders"), ["x-apigateway-header"])

        # test tags
        # Every HttpApi should have a default tag created by SAM (httpapi:createdby: SAM)
        tags = api_result.get("Tags")
        self.assertEqual(len(tags), 1)
        self.assertEquals(tags.get("httpapi:createdBy"), "SAM")

        # test timeout in millis
        # verifying if TimeoutInMillis is set properly in the integration
        integrations = apigatewayV2_client.get_integrations(ApiId=outputs.get("ApiId")).get("Items")
        self.assertEquals(len(integrations), 1)
        self.assertEquals(integrations[0].get("TimeoutInMillis"), 15000)
        self.assertEquals(integrations[0].get("PayloadFormatVersion"), "1.0")
