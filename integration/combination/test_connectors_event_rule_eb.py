import logging
from unittest import SkipTest
from unittest.case import skipIf

from parameterized import parameterized
from tenacity import (
    after_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from integration.config.service_names import EVENT_RULE_WITH_EVENT_BUS
from integration.conftest import clean_bucket
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support

LOG = logging.getLogger(__name__)

retry_with_backoff = retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=16) + wait_random(0, 1),
    retry=retry_if_exception(lambda e: not isinstance(e, SkipTest)),
    after=after_log(LOG, logging.WARNING),
    reraise=True,
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
    def test_connector_event_rule_eb_by_invoking_a_function(self, template_file_path):
        self.skip_using_service_detector(template_file_path)
        self.create_and_verify_stack(template_file_path)

        lambda_function_name = self.get_physical_id_by_logical_id("TriggerFunction")
        self.verify_lambda_invocation(lambda_function_name)

    @retry_with_backoff
    def verify_lambda_invocation(self, lambda_function_name):
        """Verify Lambda function invocation with retry logic."""
        response = self.client_provider.lambda_client.invoke(
            FunctionName=lambda_function_name, InvocationType="RequestResponse", Payload="{}"
        )
        self.assertEqual(response.get("StatusCode"), 200)
        self.assertEqual(response.get("FunctionError"), None)
