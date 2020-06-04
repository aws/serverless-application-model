from mock import Mock
from unittest import TestCase
from samtranslator.model.stepfunctions.events import Schedule


class ScheduleEventSource(TestCase):
    def setUp(self):
        self.logical_id = "ScheduleEvent"

        self.schedule_event_source = Schedule(self.logical_id)
        self.schedule_event_source.Schedule = "rate(1 minute)"

        self.state_machine = Mock()
        self.state_machine.get_runtime_attr = Mock()
        self.state_machine.get_runtime_attr.return_value = "arn:aws:statemachine:mock"
        self.state_machine.resource_attributes = {}
        self.state_machine.get_passthrough_resource_attributes = Mock()
        self.state_machine.get_passthrough_resource_attributes.return_value = {}

    def test_to_cloudformation_returns_eventrule_and_role_resources(self):
        resources = self.schedule_event_source.to_cloudformation(resource=self.state_machine)
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].resource_type, "AWS::Events::Rule")
        self.assertEqual(resources[1].resource_type, "AWS::IAM::Role")

        iam_role = resources[1]
        self.assertEqual(
            iam_role.AssumeRolePolicyDocument,
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": ["sts:AssumeRole"],
                        "Effect": "Allow",
                        "Principal": {"Service": ["events.amazonaws.com"]},
                    }
                ],
            },
        )
        self.assertEqual(
            iam_role.Policies,
            [
                {
                    "PolicyName": "ScheduleEventRoleStartExecutionPolicy",
                    "PolicyDocument": {
                        "Statement": [
                            {
                                "Action": "states:StartExecution",
                                "Resource": "arn:aws:statemachine:mock",
                                "Effect": "Allow",
                            }
                        ]
                    },
                }
            ],
        )

        event_rule = resources[0]
        self.assertEqual(event_rule.ScheduleExpression, "rate(1 minute)")
        self.assertEqual(
            event_rule.Targets,
            [
                {
                    "Id": "ScheduleEventStepFunctionsTarget",
                    "Arn": "arn:aws:statemachine:mock",
                    "RoleArn": {"Fn::GetAtt": [iam_role.logical_id, "Arn"]},
                }
            ],
        )

    def test_to_cloudformation_throws_when_no_resource(self):
        self.assertRaises(TypeError, self.schedule_event_source.to_cloudformation)

    def test_to_cloudformation_when_event_is_disabled(self):
        self.schedule_event_source.Enabled = False
        resources = self.schedule_event_source.to_cloudformation(resource=self.state_machine)
        self.assertEqual(len(resources), 2)
        event_rule = resources[0]
        self.assertEqual(event_rule.State, "DISABLED")

    def test_to_cloudformation_with_input(self):
        input_to_service = '{"test_key": "test_value"}'
        self.schedule_event_source.Input = input_to_service
        resources = self.schedule_event_source.to_cloudformation(resource=self.state_machine)
        self.assertEqual(len(resources), 2)
        event_rule = resources[0]
        self.assertEqual(event_rule.Targets[0]["Input"], input_to_service)
