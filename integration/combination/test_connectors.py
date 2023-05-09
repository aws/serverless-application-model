from time import sleep
from unittest import SkipTest

from parameterized import parameterized
from tenacity import retry, retry_if_exception, stop_after_attempt

from integration.conftest import clean_bucket
from integration.helpers.base_test import S3_BUCKET_PREFIX, BaseTest
from integration.helpers.resource import generate_suffix

retry_once = retry(
    stop=stop_after_attempt(2),
    # unittest raises SkipTest for skipping tests
    retry=retry_if_exception(lambda e: not isinstance(e, SkipTest)),
)


class TestConnectors(BaseTest):
    def tearDown(self):
        # Some tests will create items in S3 Bucket, which result in stack DELETE_FAILED state
        # manually empty the bucket to allow stacks to be deleted successfully.
        bucket_name = self.get_physical_id_by_type("AWS::S3::Bucket")
        if bucket_name:
            clean_bucket(bucket_name, self.client_provider.s3_client)
        super().tearDown()

    @parameterized.expand(
        [
            ("combination/connector_appsync_api_to_lambda",),
            ("combination/connector_appsync_to_lambda",),
            ("combination/connector_appsync_to_table",),
            ("combination/connector_function_to_function",),
            ("combination/connector_restapi_to_function",),
            ("combination/connector_httpapi_to_function",),
            ("combination/connector_function_to_bucket_read",),
            ("combination/connector_function_to_bucket_read_multiple",),
            ("combination/connector_function_to_bucket_write",),
            ("combination/connector_function_to_table_read",),
            ("combination/connector_function_to_table_write",),
            ("combination/connector_function_to_sfn_read",),
            ("combination/connector_function_to_sfn_write",),
            ("combination/connector_function_to_queue_write",),
            ("combination/connector_function_to_queue_read",),
            ("combination/connector_function_to_topic_write",),
            ("combination/connector_function_to_eventbus_write",),
            ("combination/connector_topic_to_queue_write",),
            ("combination/connector_event_rule_to_sqs_write",),
            ("combination/connector_event_rule_to_sns_write",),
            ("combination/connector_event_rule_to_sfn_write",),
            ("combination/connector_event_rule_to_eb_default_write",),
            ("combination/connector_event_rule_to_eb_custom_write",),
            ("combination/connector_event_rule_to_lambda_write",),
            ("combination/connector_event_rule_to_lambda_write_multiple",),
            ("combination/connector_sqs_to_function",),
            ("combination/connector_sns_to_function_write",),
            ("combination/connector_table_to_function_read",),
            ("combination/embedded_connector",),
        ]
    )
    @retry_once
    def test_connector_by_invoking_a_function(self, template_file_path):
        self.skip_using_service_detector(template_file_path)
        self.create_and_verify_stack(template_file_path)

        lambda_function_name = self.get_physical_id_by_logical_id("TriggerFunction")
        lambda_client = self.client_provider.lambda_client

        request_params = {
            "FunctionName": lambda_function_name,
            "InvocationType": "RequestResponse",
            "Payload": "{}",
        }
        response = lambda_client.invoke(**request_params)
        self.assertEqual(response.get("StatusCode"), 200)
        self.assertEqual(response.get("FunctionError"), None)

    @parameterized.expand(
        [
            ("combination/connector_function_to_location_place_index",),
        ]
    )
    @retry_once
    def test_connector_by_invoking_a_function_with_parameters(self, template_file_path):
        parameters = []
        parameters.append(self.generate_parameter("IndexName", f"PlaceIndex-{generate_suffix()}"))
        self.skip_using_service_detector(template_file_path)
        self.create_and_verify_stack(template_file_path, parameters)

        lambda_function_name = self.get_physical_id_by_logical_id("TriggerFunction")
        lambda_client = self.client_provider.lambda_client

        request_params = {
            "FunctionName": lambda_function_name,
            "InvocationType": "RequestResponse",
            "Payload": "{}",
        }
        response = lambda_client.invoke(**request_params)
        self.assertEqual(response.get("StatusCode"), 200)
        self.assertEqual(response.get("FunctionError"), None)

    @parameterized.expand(
        [
            ("combination/connector_sfn_to_function_without_policy",),
            ("combination/connector_sfn_to_table_read",),
            ("combination/connector_sfn_to_table_write",),
            ("combination/connector_sfn_to_sqs_write",),
            ("combination/connector_sfn_to_sns_write",),
            ("combination/connector_sfn_to_function_write",),
            ("combination/connector_sfn_to_bucket_write",),
            ("combination/connector_sfn_to_bucket_read",),
            ("combination/connector_sfn_to_sfn_async",),
            ("combination/connector_sfn_to_eb_default_write",),
            ("combination/connector_sfn_to_eb_custom_write",),
        ]
    )
    @retry_once
    def test_connector_by_sync_execute_an_state_machine(self, template_file_path):
        self.skip_using_service_detector(template_file_path)
        self.create_and_verify_stack(template_file_path)

        state_machine_arn = self.get_physical_id_by_logical_id("TriggerStateMachine")
        sfn_client = self.client_provider.sfn_client

        response = sfn_client.start_sync_execution(
            stateMachineArn=state_machine_arn,
        )
        # Without permission, it will be "FAILED"
        self.assertEqual(response.get("status"), "SUCCEEDED")

    @parameterized.expand(
        [
            ("combination/connector_sfn_to_sfn_sync",),
        ]
    )
    @retry_once
    def test_connector_by_async_execute_an_state_machine(self, template_file_path):
        self.skip_using_service_detector(template_file_path)
        self.create_and_verify_stack(template_file_path)

        state_machine_arn = self.get_physical_id_by_logical_id("TriggerStateMachine")
        sfn_client = self.client_provider.sfn_client

        response = sfn_client.start_execution(
            stateMachineArn=state_machine_arn,
        )
        execution_arn = response["executionArn"]

        status = None
        wait_tries = 5
        while wait_tries > 0:
            response = sfn_client.describe_execution(executionArn=execution_arn)
            status = response["status"]
            if status == "RUNNING":
                wait_tries -= 1
                sleep(5)
                continue
            else:
                break

        # Without permission, it will be "FAILED"
        self.assertEqual(status, "SUCCEEDED")

    @parameterized.expand(
        [
            ("combination/connector_bucket_to_function_write",),
        ]
    )
    @retry_once
    def test_connector_by_execute_a_s3_bucket(self, template_file_path):
        self.skip_using_service_detector(template_file_path)
        bucket_name = S3_BUCKET_PREFIX + "connector" + generate_suffix()
        self.create_and_verify_stack(
            template_file_path, [{"ParameterKey": "BucketName", "ParameterValue": bucket_name}]
        )

        lambda_function_name = self.get_physical_id_by_logical_id("TriggerFunction")
        lambda_client = self.client_provider.lambda_client

        request_params = {
            "FunctionName": lambda_function_name,
            "InvocationType": "RequestResponse",
            "Payload": "{}",
        }
        response = lambda_client.invoke(**request_params)
        self.assertEqual(response.get("StatusCode"), 200)
        self.assertEqual(response.get("FunctionError"), None)
