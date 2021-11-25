from unittest.case import skipIf

from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support
from integration.config.service_names import SCHEDULE_EVENT


@skipIf(current_region_does_not_support([SCHEDULE_EVENT]), "ScheduleEvent is not supported in this testing region")
class TestFunctionWithSchedule(BaseTest):
    def test_function_with_schedule(self):
        self.create_and_verify_stack("combination/function_with_schedule")

        stack_outputs = self.get_stack_outputs()

        cloud_watch_events_client = self.client_provider.cloudwatch_event_client

        # get the cloudwatch schedule rule
        schedule_name = stack_outputs["ScheduleName"]
        cw_rule_result = cloud_watch_events_client.describe_rule(Name=schedule_name)

        # checking if the name, description and state properties are correct
        self.assertEqual(cw_rule_result["Name"], schedule_name)
        self.assertEqual(cw_rule_result["Description"], "test schedule")
        self.assertEqual(cw_rule_result["State"], "ENABLED")
        self.assertEqual(cw_rule_result["ScheduleExpression"], "rate(5 minutes)")
