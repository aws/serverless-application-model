import logging
from unittest.case import skipIf

import pytest
from parameterized import parameterized

from integration.config.service_names import (
    ARM,
    CODE_DEPLOY,
    EVENT_INVOKE_CONFIG,
    HTTP_API,
    KMS,
    LAMBDA_URL,
    XRAY,
)
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support

LOG = logging.getLogger(__name__)


class TestBasicFunction(BaseTest):
    """
    Basic AWS::Lambda::Function tests
    """

    @parameterized.expand(
        [
            "single/basic_function",
            "single/basic_function_no_envvar",
            "single/basic_function_openapi",
        ]
    )
    def test_basic_function(self, file_name):
        """
        Creates a basic lambda function
        """
        self.create_and_verify_stack(file_name)

        self.set_template_resource_property("MyLambdaFunction", "Timeout", 10)
        self.update_stack()

        self.assertEqual(self.get_resource_status_by_logical_id("MyLambdaFunction"), "UPDATE_COMPLETE")

    def test_basic_function_with_role_path(self):
        self.create_and_verify_stack("single/function_with_role_path")

        lambda_client = self.client_provider.lambda_client
        function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        role_name = self.get_physical_id_by_type("AWS::IAM::Role")
        response = lambda_client.get_function(FunctionName=function_name)

        role_arn = response.get("Configuration", {}).get("Role")
        self.assertIsNotNone(role_arn)
        self.assertIn("/foo/bar/", role_arn)

        iam_client = self.client_provider.iam_client
        response = iam_client.get_role(RoleName=role_name)

        self.assertEqual(response["Role"]["Path"], "/foo/bar/")

    @parameterized.expand(
        [
            "single/function_with_http_api_events",
            "single/function_alias_with_http_api_events",
        ]
    )
    @pytest.mark.flaky(reruns=5)
    @skipIf(current_region_does_not_support([HTTP_API]), "HTTP API is not supported in this testing region")
    def test_function_with_http_api_events(self, file_name):
        self.create_and_verify_stack(file_name)

        endpoint = self.get_api_v2_endpoint("MyHttpApi")

        self._verify_get_request(endpoint, self.FUNCTION_OUTPUT)

    @parameterized.expand(
        [
            ("single/basic_function", ["x86_64"]),
            ("single/basic_function_no_envvar", ["x86_64"]),
            ("single/basic_function_openapi", ["x86_64"]),
            ("single/basic_function_with_arm_architecture", ["arm64"]),
            ("single/basic_function_with_x86_architecture", ["x86_64"]),
        ]
    )
    @skipIf(current_region_does_not_support([ARM]), "ARM is not supported in this testing region")
    def test_basic_function_with_architecture(self, file_name, architecture):
        """
        Creates a basic lambda function
        """
        self.create_and_verify_stack(file_name)

        lambda_client = self.client_provider.lambda_client
        function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        function_architecture = lambda_client.get_function_configuration(FunctionName=function_name)["Architectures"]

        self.assertEqual(function_architecture, architecture)

    @parameterized.expand(
        [
            ("single/basic_function_with_function_url_config", None),
            ("single/basic_function_with_function_url_with_autopuplishalias", "live"),
        ]
    )
    @skipIf(current_region_does_not_support([LAMBDA_URL]), "Lambda Url is not supported in this testing region")
    def test_basic_function_with_url_config(self, file_name, qualifier):
        """
        Creates a basic lambda function with Function Url enabled
        """
        self.create_and_verify_stack(file_name)

        lambda_client = self.client_provider.lambda_client

        function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        function_url_config = (
            lambda_client.get_function_url_config(FunctionName=function_name, Qualifier=qualifier)
            if qualifier
            else lambda_client.get_function_url_config(FunctionName=function_name)
        )
        cors_config = {
            "AllowOrigins": ["https://foo.com"],
            "AllowMethods": ["POST"],
            "AllowCredentials": True,
            "AllowHeaders": ["x-custom-header"],
            "ExposeHeaders": ["x-amzn-header"],
            "MaxAge": 10,
        }

        self.assertEqual(function_url_config["AuthType"], "NONE")
        self.assertEqual(function_url_config["Cors"], cors_config)
        self._assert_invoke(lambda_client, function_name, qualifier, 200)

    @skipIf(current_region_does_not_support([CODE_DEPLOY]), "CodeDeploy is not supported in this testing region")
    def test_function_with_deployment_preference_alarms_intrinsic_if(self):
        self.create_and_verify_stack("single/function_with_deployment_preference_alarms_intrinsic_if")

    @parameterized.expand(
        [
            ("single/basic_function_with_sns_dlq", "sns:Publish"),
            ("single/basic_function_with_sqs_dlq", "sqs:SendMessage"),
        ]
    )
    def test_basic_function_with_dlq(self, file_name, action):
        """
        Creates a basic lambda function with dead letter queue policy
        """
        dlq_policy_name = "DeadLetterQueuePolicy"
        self.create_and_verify_stack(file_name)

        lambda_function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        function_configuration = self.client_provider.lambda_client.get_function_configuration(
            FunctionName=lambda_function_name
        )
        dlq_arn = function_configuration["DeadLetterConfig"]["TargetArn"]
        self.assertIsNotNone(dlq_arn, "DLQ Arn should be set")

        role_name = self.get_physical_id_by_type("AWS::IAM::Role")
        role_policy_result = self.client_provider.iam_client.get_role_policy(
            RoleName=role_name, PolicyName=dlq_policy_name
        )
        statements = role_policy_result["PolicyDocument"]["Statement"]

        self.assertEqual(len(statements), 1, "Only one statement must be in policy")
        self.assertEqual(statements[0]["Action"], action)
        self.assertEqual(statements[0]["Resource"], dlq_arn)
        self.assertEqual(statements[0]["Effect"], "Allow")

    @skipIf(current_region_does_not_support([KMS]), "KMS is not supported in this testing region")
    def test_basic_function_with_kms_key_arn(self):
        """
        Creates a basic lambda function with KMS key arn
        """
        self.create_and_verify_stack("single/basic_function_with_kmskeyarn")

        lambda_function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        function_configuration = self.client_provider.lambda_client.get_function_configuration(
            FunctionName=lambda_function_name
        )
        kms_key_arn = function_configuration["KMSKeyArn"]

        self.assertIsNotNone(kms_key_arn, "Expecting KmsKeyArn to be set.")

    def test_basic_function_with_tags(self):
        """
        Creates a basic lambda function with tags
        """
        self.create_and_verify_stack("single/basic_function_with_tags")
        lambda_function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        get_function_result = self.client_provider.lambda_client.get_function(FunctionName=lambda_function_name)
        tags = get_function_result["Tags"]

        self.assertIsNotNone(tags, "Expecting tags on function.")
        self.assertTrue("lambda:createdBy" in tags, "Expected 'lambda:CreatedBy' tag key, but not found.")
        self.assertEqual("SAM", tags["lambda:createdBy"], "Expected 'SAM' tag value, but not found.")
        self.assertTrue("TagKey1" in tags)
        self.assertEqual(tags["TagKey1"], "TagValue1")
        self.assertTrue("TagKey2" in tags)
        self.assertEqual(tags["TagKey2"], "")

    @skipIf(
        current_region_does_not_support([EVENT_INVOKE_CONFIG]),
        "EventInvokeConfig is not supported in this testing region",
    )
    def test_basic_function_event_destinations(self):
        """
        Creates a basic lambda function with event destinations
        """
        self.create_and_verify_stack("single/basic_function_event_destinations")

        test_function_1 = self.get_physical_id_by_logical_id("MyTestFunction")
        test_function_2 = self.get_physical_id_by_logical_id("MyTestFunction2")

        function_invoke_config_result = self.client_provider.lambda_client.get_function_event_invoke_config(
            FunctionName=test_function_1, Qualifier="$LATEST"
        )
        self.assertIsNotNone(
            function_invoke_config_result["DestinationConfig"], "Expecting destination config to be set."
        )
        self.assertEqual(
            int(function_invoke_config_result["MaximumEventAgeInSeconds"]),
            70,
            "MaximumEventAgeInSeconds value is not set or incorrect.",
        )
        self.assertEqual(
            int(function_invoke_config_result["MaximumRetryAttempts"]),
            1,
            "MaximumRetryAttempts value is not set or incorrect.",
        )

        function_invoke_config_result = self.client_provider.lambda_client.get_function_event_invoke_config(
            FunctionName=test_function_2, Qualifier="live"
        )
        self.assertIsNotNone(
            function_invoke_config_result["DestinationConfig"], "Expecting destination config to be set."
        )
        self.assertEqual(
            int(function_invoke_config_result["MaximumEventAgeInSeconds"]),
            80,
            "MaximumEventAgeInSeconds value is not set or incorrect.",
        )
        self.assertEqual(
            int(function_invoke_config_result["MaximumRetryAttempts"]),
            2,
            "MaximumRetryAttempts value is not set or incorrect.",
        )

    @skipIf(current_region_does_not_support([XRAY]), "XRay is not supported in this testing region")
    def test_basic_function_with_tracing(self):
        """
        Creates a basic lambda function with tracing
        """
        self.create_and_verify_stack("single/basic_function_with_tracing", self.get_default_test_template_parameters())

        active_tracing_function_id = self.get_physical_id_by_logical_id("ActiveTracingFunction")
        pass_through_tracing_function_id = self.get_physical_id_by_logical_id("PassThroughTracingFunction")

        function_configuration_result = self.client_provider.lambda_client.get_function_configuration(
            FunctionName=active_tracing_function_id
        )
        self.assertIsNotNone(function_configuration_result["TracingConfig"], "Expecting tracing config to be set.")
        self.assertEqual(
            function_configuration_result["TracingConfig"]["Mode"],
            "Active",
            "Expecting tracing config mode to be set to Active.",
        )

        function_configuration_result = self.client_provider.lambda_client.get_function_configuration(
            FunctionName=pass_through_tracing_function_id
        )
        self.assertIsNotNone(function_configuration_result["TracingConfig"], "Expecting tracing config to be set.")
        self.assertEqual(
            function_configuration_result["TracingConfig"]["Mode"],
            "PassThrough",
            "Expecting tracing config mode to be set to PassThrough.",
        )

    def _assert_invoke(self, lambda_client, function_name, qualifier=None, expected_status_code=200):
        """
        Assert if a Lambda invocation returns the expected status code

        Parameters
        ----------
        lambda_client : boto3.BaseClient
            boto3 Lambda client
        function_name : string
            Function name
        qualifier : string
            Specify a version or alias to invoke a published version of the function
        expected_status_code : int
            Expected status code from the invocation
        """
        request_params = {
            "FunctionName": function_name,
            "Payload": "{}",
        }
        if qualifier:
            request_params["Qualifier"] = qualifier

        response = lambda_client.invoke(**request_params)
        self.assertEqual(response.get("StatusCode"), expected_status_code)

    def _verify_get_request(self, url, expected_text):
        response = self.verify_get_request_response(url, 200)
        self.assertEqual(response.text, expected_text)
