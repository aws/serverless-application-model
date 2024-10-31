from unittest import SkipTest
from unittest.case import skipIf

from parameterized import parameterized
from tenacity import retry, retry_if_exception, stop_after_attempt

from integration.config.service_names import EVENT_RULE_WITH_EVENT_BUS
from integration.conftest import clean_bucket
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support

retry_once = retry(
    stop=stop_after_attempt(2),
    # unittest raises SkipTest for skipping tests
    retry=retry_if_exception(lambda e: not isinstance(e, SkipTest)),
)


@skipIf(
    current_region_does_not_support([EVENT_RULE_WITH_EVENT_BUS]),
    "EVENT_RULE_WITH_EVENT_BUS is not supported in this testing region",
)
class TestConnectorsWithEventRuleToEB(BaseTest):
    def tearDown(self):
        # Some tests will create items in S3 Bucket, which result in stack DELETE_FAILED state
        # manually empty the bucket to allow stacks to be deleted successfully.
        bucket_name = self.get_physical_id_by_type("AWS::S3::Bucket")
        if bucket_name:
            clean_bucket(bucket_name, self.client_provider.s3_client)
        super().tearDown()

    @parameterized.expand(
        [
            ("combination/connector_event_rule_to_eb_default_write",),
            ("combination/connector_event_rule_to_eb_custom_write",),
        ]
    )
    @retry_once
    def test_connector_event_rule_eb_by_invoking_a_function(self, template_file_path):
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
