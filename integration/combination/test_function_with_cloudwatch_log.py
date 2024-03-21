from unittest.case import skipIf

from integration.config.service_names import LOGS
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(
    current_region_does_not_support([LOGS]),
    "A Logs resource that is a part of this test is not supported in this testing region",
)
class TestFunctionWithCloudWatchLog(BaseTest):
    def test_function_with_cloudwatch_log(self):
        self.create_and_verify_stack("combination/function_with_cloudwatch_log")

        cloudwatch_log_group_name = self.get_physical_id_by_type("AWS::Logs::LogGroup")
        lambda_function_endpoint = self.get_physical_id_by_type("AWS::Lambda::Function")
        cloudwatch_log_client = self.client_provider.cloudwatch_log_client

        subscription_filter_result = cloudwatch_log_client.describe_subscription_filters(
            logGroupName=cloudwatch_log_group_name
        )
        subscription_filter = subscription_filter_result["subscriptionFilters"][0]

        self.assertEqual(len(subscription_filter_result["subscriptionFilters"]), 1)
        self.assertTrue(lambda_function_endpoint in subscription_filter["destinationArn"])
        self.assertEqual(subscription_filter["filterPattern"], "My filter pattern")
