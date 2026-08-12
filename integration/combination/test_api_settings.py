import hashlib
from pathlib import Path
from unittest.case import skipIf

from parameterized import parameterized

from integration.config.service_names import REST_API
from integration.helpers.base_test import BaseTest, nonblocking
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([REST_API]), "Rest API is not supported in this testing region")
class TestApiSettings(BaseTest):
    def test_method_settings(self):
        self.create_and_verify_stack("combination/api_with_method_settings")

        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        apigw_client = self.client_provider.api_client
        response = apigw_client.get_stage(restApiId=rest_api_id, stageName="Prod")

        wildcard_path = "*/*"

        method_settings = response["methodSettings"]
        self.assertTrue(wildcard_path in method_settings, "MethodSettings for the wildcard path must be present")

        wildcard_path_setting = method_settings[wildcard_path]

        self.assertTrue(wildcard_path_setting["metricsEnabled"], "Metrics must be enabled")
        self.assertTrue(wildcard_path_setting["dataTraceEnabled"], "DataTrace must be enabled")
        self.assertEqual(wildcard_path_setting["loggingLevel"], "INFO", "LoggingLevel must be INFO")

    @parameterized.expand(
        [
            "combination/api_with_binary_media_types",
            "combination/api_with_binary_media_types_with_definition_body",
        ]
    )
    def test_binary_media_types(self, file_name):
        self.create_and_verify_stack(file_name, self.get_default_test_template_parameters())

        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        apigw_client = self.client_provider.api_client

        response = apigw_client.get_rest_api(restApiId=rest_api_id)
        self.assertEqual(set(response["binaryMediaTypes"]), {"image/jpg", "image/png", "image/gif"})

    @parameterized.expand(
        [
            "combination/api_with_request_models",
            "combination/api_with_request_models_openapi",
        ]
    )
    def test_request_models(self, file_name):
        self.create_and_verify_stack(file_name)

        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        apigw_client = self.client_provider.api_client

        response = apigw_client.get_models(restApiId=rest_api_id)
        request_models = response["items"]

        self.assertEqual(request_models[0]["name"], "user")
        self.assertEqual(
            request_models[0]["schema"],
            '{\n  "type" : "object",\n'
            + '  "properties" : {\n    "username" : {\n      "type" : "string"\n    }\n'
            + "  }\n}",
        )

    @nonblocking
    def test_request_parameters_open_api(self):
        self.create_and_verify_stack("combination/api_with_request_parameters_openapi")

        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        apigw_client = self.client_provider.api_client

        # Test if the request parameters got set on the method
        resources_response = apigw_client.get_resources(restApiId=rest_api_id)
        resources = resources_response["items"]

        resource = get_resource_by_path(resources, "/one")
        method = apigw_client.get_method(restApiId=rest_api_id, resourceId=resource["id"], httpMethod="GET")
        expected = {"method.request.querystring.type": True}
        self.assertEqual(expected, method["requestParameters"])

        # Test that the method settings got applied on the method
        stage_response = apigw_client.get_stage(restApiId=rest_api_id, stageName="Prod")
        method_settings = stage_response["methodSettings"]

        path = "one/GET"
        self.assertTrue(path in method_settings, "MethodSettings for the path must be present")

        path_settings = method_settings[path]
        self.assertEqual(path_settings["cacheTtlInSeconds"], 15)
        self.assertTrue(path_settings["cachingEnabled"], "Caching must be enabled")

    def test_binary_media_types_with_definition_body_openapi(self):
        parameters = self.get_default_test_template_parameters()
        binary_media = {
            "ParameterKey": "BinaryMediaCodeKey",
            "ParameterValue": "binary-media.zip",
            "UsePreviousValue": False,
            "ResolvedValue": "string",
        }
        parameters.append(binary_media)

        self.create_and_verify_stack("combination/api_with_binary_media_types_with_definition_body_openapi", parameters)

        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        apigw_client = self.client_provider.api_client

        response = apigw_client.get_rest_api(restApiId=rest_api_id)
        self.assertEqual(
            set(response["binaryMediaTypes"]), {"image/jpg", "image/png", "image/gif", "application/octet-stream"}
        )
        base_url = self.get_stack_output("ApiUrl")["OutputValue"]
        self.verify_binary_media_request(base_url + "none", 200)

    @parameterized.expand(
        [
            "combination/api_with_endpoint_configuration",
            "combination/api_with_endpoint_configuration_dict",
        ]
    )
    def test_end_point_configuration(self, file_name):
        self.create_and_verify_stack(file_name, self.get_default_test_template_parameters())

        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        apigw_client = self.client_provider.api_client

        response = apigw_client.get_rest_api(restApiId=rest_api_id)
        endpoint_config = response["endpointConfiguration"]
        self.assertEqual(endpoint_config["types"], ["REGIONAL"])

    def test_implicit_api_settings(self):
        self.create_and_verify_stack("combination/implicit_api_with_settings")

        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        apigw_client = self.client_provider.api_client

        response = apigw_client.get_stage(restApiId=rest_api_id, stageName="Prod")

        wildcard_path = "*/*"

        method_settings = response["methodSettings"]
        self.assertTrue(wildcard_path in method_settings, "MethodSettings for the wildcard path must be present")

        wildcard_path_setting = method_settings[wildcard_path]

        self.assertTrue(wildcard_path_setting["metricsEnabled"], "Metrics must be enabled")
        self.assertTrue(wildcard_path_setting["dataTraceEnabled"], "DataTrace must be enabled")
        self.assertEqual(wildcard_path_setting["loggingLevel"], "INFO", "LoggingLevel must be INFO")

        response = apigw_client.get_rest_api(restApiId=rest_api_id)
        endpoint_config = response["endpointConfiguration"]
        self.assertEqual(endpoint_config["types"], ["REGIONAL"])
        self.assertEqual(set(response["binaryMediaTypes"]), {"image/jpg", "image/png"})

    def verify_binary_media_request(self, url, expected_status_code):
        headers = {"accept": "image/png"}
        response = self.do_get_request_with_logging(url, headers)

        status = response.status_code
        expected_file_path = str(Path(self.code_dir, "AWS_logo_RGB.png"))

        with open(expected_file_path, mode="rb") as file:
            expected_file_content = file.read()
        expected_hash = hashlib.sha1(expected_file_content).hexdigest()

        if 200 <= status <= 299:
            actual_hash = hashlib.sha1(response.content).hexdigest()
            self.assertEqual(expected_hash, actual_hash)

        self.assertEqual(status, expected_status_code, " must return HTTP " + str(expected_status_code))


def get_resource_by_path(resources, path):
    for resource in resources:
        if resource["path"] == path:
            return resource
    return None
