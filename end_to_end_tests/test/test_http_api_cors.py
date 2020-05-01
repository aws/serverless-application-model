import boto3
import os
from .helpers.base_test import BaseTest
from .helpers.resources import Resources
from .helpers.resource_types import ResourceTypes


class HttpApiCorsTest(BaseTest):
    """
    contains methods for testing Cors for AWS::Serverless::HttpApi

    Methods
    -------
    :method test_cors(self)
        test cors, tags, timeout in millis and payload format version properties for AWS::Serverless::HttpApi resource
    """

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
        """
        test cors, tags, timeout in millis and payload format version properties for AWS::Serverless::HttpApi resource
        """
        input_template = os.path.join(os.getcwd(), "end_to_end_tests/input", "http_api_cors", "template.yaml")
        capabilities = ["CAPABILITY_IAM"]
        self.make_stack(input_template, capabilities)
        self.verify_stack(self.http_api_with_cors_resources)
        outputs = self.get_outputs()
        apigateway_v2_client = boto3.client("apigatewayv2")
        api_result = apigateway_v2_client.get_api(ApiId=outputs.get("ApiId"))

        # test cors
        cors_configuration = api_result.get("CorsConfiguration")
        self.assertEqual(cors_configuration.get("AllowMethods"), ["GET"])
        self.assertEqual(cors_configuration.get("ExposeHeaders"), ["x-amzn-header"])
        self.assertEqual(cors_configuration.get("AllowOrigins"), ["https://foo.com"])
        self.assertEqual(cors_configuration.get("AllowHeaders"), ["x-apigateway-header"])

        # test tags
        # Every HttpApi should have a default tag created by SAM (httpapi:createdby: SAM)
        tags = api_result.get("Tags")
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags.get("httpapi:createdBy"), "SAM")

        # test timeout in millis
        # verifying if TimeoutInMillis is set properly in the integration
        integrations = apigateway_v2_client.get_integrations(ApiId=outputs.get("ApiId")).get("Items")
        self.assertEqual(len(integrations), 1)
        self.assertEqual(integrations[0].get("TimeoutInMillis"), 15000)
        self.assertEqual(integrations[0].get("PayloadFormatVersion"), "1.0")
