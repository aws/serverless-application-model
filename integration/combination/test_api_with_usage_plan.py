from unittest.case import skipIf

from integration.config.service_names import REST_API, USAGE_PLANS
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([USAGE_PLANS, REST_API]), "UsagePlans is not supported in this testing region")
class TestApiWithUsagePlan(BaseTest):
    def test_api_with_usage_plans(self):
        self.create_and_verify_stack("combination/api_with_usage_plan")

        outputs = self.get_stack_outputs()
        apigw_client = self.client_provider.api_client

        serverless_usage_plan_id = outputs["ServerlessUsagePlan"]
        my_api_usage_plan_id = outputs["MyApiUsagePlan"]

        serverless_usage_plan = apigw_client.get_usage_plan(usagePlanId=serverless_usage_plan_id)
        my_api_usage_plan = apigw_client.get_usage_plan(usagePlanId=my_api_usage_plan_id)

        self.assertEqual(len(my_api_usage_plan["apiStages"]), 1)
        self.assertEqual(my_api_usage_plan["throttle"]["burstLimit"], 100)
        self.assertEqual(my_api_usage_plan["throttle"]["rateLimit"], 50.0)
        self.assertEqual(my_api_usage_plan["quota"]["limit"], 500)
        self.assertEqual(my_api_usage_plan["quota"]["period"], "MONTH")
        self.assertEqual(len(serverless_usage_plan["apiStages"]), 2)
