from unittest import TestCase
from unittest.mock import Mock

from samtranslator.model.exceptions import InvalidEventException
from samtranslator.model.stepfunctions.events import EventBridgeRule


class EventBridgeRuleSourceTests(TestCase):
    def setUp(self):
        self.logical_id = "EventBridgeRule"

        self.eb_event_source = EventBridgeRule(self.logical_id)
        self.eb_event_source.Pattern = {"detail": {"state": ["terminated"]}}

        self.state_machine = Mock()
        self.state_machine.get_runtime_attr = Mock()
        self.state_machine.get_runtime_attr.return_value = "arn:aws:statemachine:mock"
        self.state_machine.resource_attributes = {}
        self.state_machine.get_passthrough_resource_attributes = Mock()
        self.state_machine.get_passthrough_resource_attributes.return_value = {}

    def test_to_cloudformation_with_dlq_generated_with_custom_logical_id(self):
        dead_letter_config = {"Type": "SQS", "QueueLogicalId": "MyDLQ"}
        dead_letter_config_translated = {"Arn": {"Fn::GetAtt": ["MyDLQ", "Arn"]}}
        self.eb_event_source.DeadLetterConfig = dead_letter_config
        resources = self.eb_event_source.to_cloudformation(resource=self.state_machine)
        self.assertEqual(len(resources), 4)
        event_rule = resources[0]
        self.assertEqual(event_rule.Targets[0]["DeadLetterConfig"], dead_letter_config_translated)

    def test_to_cloudformation_with_dlq_generated_with_intrinsic_function_custom_logical_id_raises_exception(self):
        dead_letter_config = {"Type": "SQS", "QueueLogicalId": {"Fn::Sub": "MyDLQ${Env}"}}
        self.eb_event_source.DeadLetterConfig = dead_letter_config
        with self.assertRaises(InvalidEventException):
            self.eb_event_source.to_cloudformation(resource=self.state_machine)

    def test_to_cloudformation_with_state(self):
        self.eb_event_source.State = "DISABLED"
        resources = self.eb_event_source.to_cloudformation(resource=self.state_machine)
        state = resources[0].State
        self.assertEqual(state, "DISABLED")

    def test_name_when_provided(self):
        self.eb_event_source.RuleName = "MyRule"
        resources = self.eb_event_source.to_cloudformation(resource=self.state_machine)
        event_rule = resources[0]
        self.assertEqual(event_rule.Name, "MyRule")
