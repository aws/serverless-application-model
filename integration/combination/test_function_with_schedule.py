from unittest.case import skipIf

from integration.config.service_names import SCHEDULE_EVENT
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support, generate_suffix


@skipIf(current_region_does_not_support([SCHEDULE_EVENT]), "ScheduleEvent is not supported in this testing region")
class TestFunctionWithSchedule(BaseTest):
    def test_function_with_schedule(self):
        schedule_name = "TestSchedule" + generate_suffix()
        parameters = [self.generate_parameter("ScheduleName", schedule_name)]

        self.create_and_verify_stack("combination/function_with_schedule", parameters)

        cloud_watch_events_client = self.client_provider.cloudwatch_event_client

        # get the cloudwatch schedule rule
        cw_rule_result = cloud_watch_events_client.describe_rule(Name=schedule_name)

        # checking if the name, description and state properties are correct
        self.assertEqual(cw_rule_result["Name"], schedule_name)
        self.assertEqual(cw_rule_result["Description"], "test schedule")
        self.assertEqual(cw_rule_result["State"], "ENABLED")
        self.assertEqual(cw_rule_result["ScheduleExpression"], "rate(5 minutes)")
