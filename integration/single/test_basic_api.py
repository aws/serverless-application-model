import json
import logging
import time
from unittest.case import skipIf

from tenacity import after_log, retry_if_exception_type, stop_after_attempt, wait_exponential, wait_random

from integration.config.service_names import MODE, REST_API
from integration.helpers.base_test import BaseTest
from integration.helpers.exception import StatusCodeError
from integration.helpers.resource import current_region_does_not_support

LOG = logging.getLogger(__name__)


@skipIf(current_region_does_not_support([REST_API]), "Rest API is not supported in this testing region")
class TestBasicApi(BaseTest):
    """
    Basic AWS::Serverless::Api tests
    """

    def test_basic_api(self):
        """
        Creates an API and updates its DefinitionUri
        """
        self.create_and_verify_stack("single/basic_api")

        first_dep_ids = self.get_stack_deployment_ids()
        self.assertEqual(len(first_dep_ids), 1)

        self.set_template_resource_property("MyApi", "DefinitionUri", self.get_s3_uri("swagger2.json"))
        self.update_stack()

        second_dep_ids = self.get_stack_deployment_ids()
        self.assertEqual(len(second_dep_ids), 1)

        self.assertEqual(len(set(first_dep_ids).intersection(second_dep_ids)), 0)

    @skipIf(current_region_does_not_support([MODE]), "Mode is not supported in this testing region")
    def test_basic_api_with_mode(self):
        """
        Creates an API and updates its DefinitionUri
        """
        # Create an API with get and put
        self.create_and_verify_stack("single/basic_api_with_mode")

        stack_output = self.get_stack_outputs()
        api_endpoint = stack_output.get("ApiEndpoint")

        self.verify_get_request_response(f"{api_endpoint}/get", 200)

        # Removes get from the API
        self.update_and_verify_stack(file_path="single/basic_api_with_mode_update")

        # API Gateway by default returns 403 if a path do not exist
        self.verify_get_request_response.retry_with(
            stop=stop_after_attempt(20),
            wait=wait_exponential(multiplier=1, min=4, max=10) + wait_random(0, 1),
            retry=retry_if_exception_type(StatusCodeError),
            after=after_log(LOG, logging.WARNING),
            reraise=True,
        )(self, f"{api_endpoint}/get", 403)

        LOG.log(msg=f"retry times {self.verify_get_request_response.retry.statistics}", level=logging.WARNING)

    def test_basic_api_inline_openapi(self):
        """
        Creates an API with and inline OpenAPI and updates its DefinitionBody basePath
        """
        self.create_and_verify_stack("single/basic_api_inline_openapi")

        first_dep_ids = self.get_stack_deployment_ids()
        self.assertEqual(len(first_dep_ids), 1)

        body = self.get_template_resource_property("MyApi", "DefinitionBody")
        body["basePath"] = "/newDemo"
        self.set_template_resource_property("MyApi", "DefinitionBody", body)
        self.update_stack()

        second_dep_ids = self.get_stack_deployment_ids()
        self.assertEqual(len(second_dep_ids), 1)

        self.assertEqual(len(set(first_dep_ids).intersection(second_dep_ids)), 0)

    def test_basic_api_inline_swagger(self):
        """
        Creates an API with an inline Swagger and updates its DefinitionBody basePath
        """
        self.create_and_verify_stack("single/basic_api_inline_swagger")

        first_dep_ids = self.get_stack_deployment_ids()
        self.assertEqual(len(first_dep_ids), 1)

        body = self.get_template_resource_property("MyApi", "DefinitionBody")
        body["basePath"] = "/newDemo"
        self.set_template_resource_property("MyApi", "DefinitionBody", body)
        self.update_stack()

        second_dep_ids = self.get_stack_deployment_ids()
        self.assertEqual(len(second_dep_ids), 1)

        self.assertEqual(len(set(first_dep_ids).intersection(second_dep_ids)), 0)

    def test_basic_api_with_tags(self):
        """
        Creates an API with tags
        """
        self.create_and_verify_stack("single/basic_api_with_tags")

        stages = self.get_api_stack_stages()
        self.assertEqual(len(stages), 2)

        stage = next(s for s in stages if s["stageName"] == "my-new-stage-name")
        self.assertIsNotNone(stage)
        self.assertEqual(stage["tags"]["TagKey1"], "TagValue1")
        self.assertEqual(stage["tags"]["TagKey2"], "")

    def test_state_machine_with_api_single_quotes_input(self):
        """
        Pass single quotes in input JSON to a StateMachine
        See https://github.com/aws/serverless-application-model/issues/1895

        This test is known to sometimes be flaky, but we want to avoid marking it as non-blocking as this is a basic api test.
        Instead, we set the EndpointConfiguration to REGIONAL and added logging to the api request
        If this test continues to fail it should be marked as non-blocking
        """
        self.create_and_verify_stack("single/state_machine_with_api")

        stack_output = self.get_stack_outputs()
        api_endpoint = stack_output.get("ApiEndpoint")

        input_json = {"f'oo": {"hello": "'wor'l'd'''"}}

        # This will be the wait time before triggering the APIGW request
        time.sleep(10)

        response = self.verify_post_request(api_endpoint, input_json, 200)

        LOG.log(msg=f"retry times {self.verify_get_request_response.retry.statistics}", level=logging.WARNING)

        execution_arn = response.json()["executionArn"]
        execution = self.client_provider.sfn_client.describe_execution(executionArn=execution_arn)
        execution_input = json.loads(execution["input"])
        self.assertEqual(execution_input, input_json)
