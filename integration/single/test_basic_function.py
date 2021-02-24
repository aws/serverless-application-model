from unittest.case import skipIf

import requests

from integration.helpers.resource import current_region_does_not_support
from parameterized import parameterized
from integration.helpers.base_test import BaseTest


class TestBasicFunction(BaseTest):
    """
    Basic AWS::Lambda::Function tests
    """

    @parameterized.expand(
        [
            "basic_function",
            "basic_function_no_envvar",
            "basic_function_openapi",
        ]
    )
    def test_basic_function(self, file_name):
        """
        Creates a basic lambda function
        """
        self.create_and_verify_stack(file_name)

        self.set_template_resource_property("MyLambdaFunction", "Timeout", 10)
        self.transform_template()
        self.deploy_stack()

        self.assertEqual(self.get_resource_status_by_logical_id("MyLambdaFunction"), "UPDATE_COMPLETE")

    @parameterized.expand(
        [
            "function_with_http_api_events",
            "function_alias_with_http_api_events",
        ]
    )
    def test_function_with_http_api_events(self, file_name):
        self.create_and_verify_stack(file_name)

        endpoint = self.get_api_v2_endpoint("MyHttpApi")

        self.assertEqual(requests.get(endpoint).text, self.FUNCTION_OUTPUT)

    def test_function_with_deployment_preference_alarms_intrinsic_if(self):
        self.create_and_verify_stack("function_with_deployment_preference_alarms_intrinsic_if")

    @parameterized.expand(
        [
            ("basic_function_with_sns_dlq", "sns:Publish"),
            ("basic_function_with_sqs_dlq", "sqs:SendMessage"),
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

    @skipIf(current_region_does_not_support(["KMS"]), "KMS is not supported in this testing region")
    def test_basic_function_with_kms_key_arn(self):
        """
        Creates a basic lambda function with KMS key arn
        """
        self.create_and_verify_stack("basic_function_with_kmskeyarn")

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
        self.create_and_verify_stack("basic_function_with_tags")
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

    def test_basic_function_event_destinations(self):
        """
        Creates a basic lambda function with event destinations
        """
        self.create_and_verify_stack("basic_function_event_destinations")

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

    @skipIf(current_region_does_not_support(["XRay"]), "XRay is not supported in this testing region")
    def test_basic_function_with_tracing(self):
        """
        Creates a basic lambda function with tracing
        """
        parameters = [
            {
                "ParameterKey": "Bucket",
                "ParameterValue": self.s3_bucket_name,
                "UsePreviousValue": False,
                "ResolvedValue": "string",
            },
            {
                "ParameterKey": "CodeKey",
                "ParameterValue": "code.zip",
                "UsePreviousValue": False,
                "ResolvedValue": "string",
            },
            {
                "ParameterKey": "SwaggerKey",
                "ParameterValue": "swagger1.json",
                "UsePreviousValue": False,
                "ResolvedValue": "string",
            },
        ]
        self.create_and_verify_stack("basic_function_with_tracing", parameters)

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
