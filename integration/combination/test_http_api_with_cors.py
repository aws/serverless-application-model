from unittest.case import skipIf

from integration.config.service_names import HTTP_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([HTTP_API]), "HttpApi is not supported in this testing region")
class TestHttpApiWithCors(BaseTest):
    def test_cors(self):
        self.create_and_verify_stack("combination/http_api_with_cors")

        api_2_client = self.client_provider.api_v2_client
        api_id = self.get_stack_outputs()["ApiId"]
        api_result = api_2_client.get_api(ApiId=api_id)

        # verifying in cors configuration is set correctly at api level
        cors_configuration = api_result["CorsConfiguration"]
        self.assertEqual(cors_configuration["AllowMethods"], ["GET"], "Allow-Methods must have proper value")
        self.assertEqual(
            cors_configuration["AllowOrigins"], ["https://foo.com"], "Allow-Origins must have proper value"
        )
        self.assertEqual(
            cors_configuration["AllowHeaders"], ["x-apigateway-header"], "Allow-Headers must have proper value"
        )
        self.assertEqual(
            cors_configuration["ExposeHeaders"], ["x-amzn-header"], "Expose-Headers must have proper value"
        )
        self.assertIsNone(cors_configuration.get("MaxAge"), "Max-Age must be null as it is not set in the template")
        self.assertIsNone(
            cors_configuration.get("AllowCredentials"),
            "Allow-Credentials must be null as it is not set in the template",
        )

        # Every HttpApi should have a default tag created by SAM (httpapi:createdby: SAM)
        tags = api_result["Tags"]
        self.assertGreaterEqual(len(tags), 1)
        self.assertEqual(tags["httpapi:createdBy"], "SAM")

        # verifying if TimeoutInMillis is set properly in the integration
        integrations = api_2_client.get_integrations(ApiId=api_id)["Items"]
        self.assertEqual(len(integrations), 1)
        self.assertEqual(
            integrations[0]["TimeoutInMillis"], 15000, "valid integer value must be given for timeout in millis"
        )
        self.assertEqual(
            integrations[0]["PayloadFormatVersion"], "1.0", "valid string must be given for payload format version"
        )
