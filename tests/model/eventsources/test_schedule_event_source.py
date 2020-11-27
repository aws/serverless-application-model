from mock import Mock
from unittest import TestCase
from samtranslator.model.eventsources.push import Schedule


class SnsEventSource(TestCase):
    def setUp(self):
        self.logical_id = "ExampleCron"

        self.schedule_event_source = Schedule(self.logical_id)
        self.schedule_event_source.Schedule = "cron(1 2 3 4 ? *)"

        self.function = Mock()
        self.function.get_runtime_attr = Mock()
        self.function.get_runtime_attr.return_value = "arn:aws:lambda:mock"
        self.function.resource_attributes = {}
        self.function.get_passthrough_resource_attributes = Mock()
        self.function.get_passthrough_resource_attributes.return_value = {}

    def test_to_cloudformation_returns_permission_and_schedule_resources(self):
        resources = self.schedule_event_source.to_cloudformation(function=self.function)
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].resource_type, "AWS::Events::Rule")
        self.assertEqual(resources[1].resource_type, "AWS::Lambda::Permission")

        schedule = resources[0]
        self.assertEqual(schedule.ScheduleExpression, "cron(1 2 3 4 ? *)")
        self.assertIsNone(schedule.State)

    def test_to_cloudformation_transforms_enabled_boolean_to_state(self):
        self.schedule_event_source.Enabled = True
        resources = self.schedule_event_source.to_cloudformation(function=self.function)
        schedule = resources[0]
        self.assertEqual(schedule.State, "ENABLED")

        self.schedule_event_source.Enabled = False
        resources = self.schedule_event_source.to_cloudformation(function=self.function)
        schedule = resources[0]
        self.assertEqual(schedule.State, "DISABLED")

    def test_to_cloudformation_passes_enabled_to_state(self):
        self.schedule_event_source.Enabled = {"Fn:If": [1, 2, 3]}
        resources = self.schedule_event_source.to_cloudformation(function=self.function)
        schedule = resources[0]
        self.assertEqual(schedule.State, {"Fn:If": [1, 2, 3]})
