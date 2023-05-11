from typing import cast
from unittest import TestCase
from unittest.mock import Mock

from parameterized import parameterized
from samtranslator.model.eventsources.scheduler import SchedulerEventSource
from samtranslator.model.exceptions import InvalidEventException
from samtranslator.model.lambda_ import LambdaFunction
from samtranslator.model.scheduler import SchedulerSchedule


class ScheduleV2EventSourceInSamFunction(TestCase):
    def setUp(self):
        self.logical_id = "ScheduleEvent"
        self.schedule_event_source = SchedulerEventSource(self.logical_id)
        self.schedule_event_source.ScheduleExpression = "rate(1 minute)"
        self.schedule_event_source.FlexibleTimeWindow = {"Mode": "OFF"}
        self.func = LambdaFunction("func")

    @parameterized.expand([(None,), ("arn:aws:1234:iam:boundary/CustomerCreatedPermissionsBoundaryForSchedule",)])
    def test_to_cloudformation_returns_permission_and_schedule_resources(self, permissions_boundary):
        self.schedule_event_source.PermissionsBoundary = permissions_boundary
        resources = self.schedule_event_source.to_cloudformation(function=self.func)
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].resource_type, "AWS::Scheduler::Schedule")
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
                        "Principal": {"Service": ["scheduler.amazonaws.com"]},
                    }
                ],
            },
        )
        self.assertEqual(
            iam_role.Policies,
            [
                {
                    "PolicyName": "ScheduleEventLambdaPolicy",
                    "PolicyDocument": {
                        "Statement": [
                            {
                                "Action": "lambda:InvokeFunction",
                                "Resource": {"Fn::GetAtt": ["func", "Arn"]},
                                "Effect": "Allow",
                            }
                        ]
                    },
                }
            ],
        )
        if permissions_boundary:
            self.assertEqual(iam_role.PermissionsBoundary, permissions_boundary)

        schedule = cast(SchedulerSchedule, resources[0])
        self.assertEqual(schedule.ScheduleExpression, "rate(1 minute)")
        self.assertEqual(schedule.FlexibleTimeWindow, {"Mode": "OFF"})
        self.assertEqual(
            schedule.Target,
            {"Arn": {"Fn::GetAtt": ["func", "Arn"]}, "RoleArn": {"Fn::GetAtt": ["ScheduleEventRole", "Arn"]}},
        )
        self.assertIsNone(schedule.State)
        self.assertEqual(schedule.Name, self.logical_id)

    def test_to_cloudformation_when_omit_name(self):
        self.schedule_event_source.OmitName = True
        resources = self.schedule_event_source.to_cloudformation(function=self.func)
        self.assertEqual(resources[0].resource_type, "AWS::Scheduler::Schedule")

        schedule = resources[0]
        self.assertEqual(schedule.Name, None)

    def test_to_cloudformation_when_role_is_provided(self):
        self.schedule_event_source.RoleArn = "arn"
        resources = self.schedule_event_source.to_cloudformation(function=self.func)
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].resource_type, "AWS::Scheduler::Schedule")

        schedule = resources[0]
        self.assertEqual(schedule.Target["RoleArn"], "arn")

    def test_to_cloudformation_with_all_pass_through_properties(self):
        self.schedule_event_source.State = "ENABLED"
        self.schedule_event_source.Description = "description"
        self.schedule_event_source.StartDate = "start_date"
        self.schedule_event_source.EndDate = "end_date"
        self.schedule_event_source.ScheduleExpressionTimezone = "timezone"
        self.schedule_event_source.GroupName = "group_name"
        self.schedule_event_source.KmsKeyArn = "kms_key_arn"

        resources = self.schedule_event_source.to_cloudformation(function=self.func)
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].resource_type, "AWS::Scheduler::Schedule")

        schedule = cast(SchedulerSchedule, resources[0])
        self.assertEqual(schedule.ScheduleExpression, "rate(1 minute)")
        self.assertEqual(schedule.State, "ENABLED")
        self.assertEqual(schedule.Description, "description")
        self.assertEqual(schedule.StartDate, "start_date")
        self.assertEqual(schedule.EndDate, "end_date")
        self.assertEqual(schedule.ScheduleExpressionTimezone, "timezone")
        self.assertEqual(schedule.GroupName, "group_name")
        self.assertEqual(schedule.KmsKeyArn, "kms_key_arn")

    def test_to_cloudformation_with_retry_policy(self):
        retry_policy = {"MaximumRetryAttempts": "10", "MaximumEventAgeInSeconds": "300"}
        self.schedule_event_source.RetryPolicy = retry_policy
        resources = self.schedule_event_source.to_cloudformation(function=self.func)
        self.assertEqual(len(resources), 2)
        event_rule = resources[0]
        self.assertEqual(event_rule.Target["RetryPolicy"], retry_policy)

    def test_to_cloudformation_with_dlq_arn_provided(self):
        dead_letter_config = {"Arn": "DeadLetterQueueArn"}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        resources = self.schedule_event_source.to_cloudformation(function=self.func)
        self.assertEqual(len(resources), 2)
        event_rule = resources[0]
        self.assertEqual(event_rule.Target["DeadLetterConfig"], dead_letter_config)

    def test_to_cloudformation_invalid_both_dlq_arn_and_type_provided(self):
        dead_letter_config = {"Arn": "DeadLetterQueueArn", "Type": "SQS"}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        with self.assertRaises(InvalidEventException):
            self.schedule_event_source.to_cloudformation(function=self.func)

    def test_to_cloudformation_invalid_dlq_type_provided(self):
        dead_letter_config = {"Type": "SNS", "QueueLogicalId": "MyDLQ"}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        with self.assertRaises(InvalidEventException):
            self.schedule_event_source.to_cloudformation(function=self.func)

    def test_to_cloudformation_missing_dlq_type_or_arn(self):
        dead_letter_config = {"QueueLogicalId": "MyDLQ"}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        with self.assertRaises(InvalidEventException):
            self.schedule_event_source.to_cloudformation(function=self.func)

    def test_to_cloudformation_with_dlq_generated(self):
        dead_letter_config = {"Type": "SQS"}
        dead_letter_config_translated = {"Arn": {"Fn::GetAtt": [self.logical_id + "Queue", "Arn"]}}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        resources = self.schedule_event_source.to_cloudformation(function=self.func)
        self.assertEqual(len(resources), 3)
        event_rule = resources[0]
        self.assertEqual(event_rule.Target["DeadLetterConfig"], dead_letter_config_translated)

    def test_to_cloudformation_with_dlq_generated_with_custom_logical_id(self):
        dead_letter_config = {"Type": "SQS", "QueueLogicalId": "MyDLQ"}
        dead_letter_config_translated = {"Arn": {"Fn::GetAtt": ["MyDLQ", "Arn"]}}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        resources = self.schedule_event_source.to_cloudformation(function=self.func)
        self.assertEqual(len(resources), 3)
        event_rule = resources[0]
        self.assertEqual(event_rule.Target["DeadLetterConfig"], dead_letter_config_translated)

    def test_to_cloudformation_with_dlq_generated_with_intrinsic_function_custom_logical_id_raises_exception(self):
        dead_letter_config = {"Type": "SQS", "QueueLogicalId": {"Fn::Sub": "MyDLQ${Env}"}}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        with self.assertRaises(InvalidEventException):
            self.schedule_event_source.to_cloudformation(function=self.func)


class ScheduleV2EventSourceInSamStateMachine(TestCase):
    def setUp(self):
        self.logical_id = "ScheduleEvent"

        self.schedule_event_source = SchedulerEventSource(self.logical_id)
        self.schedule_event_source.ScheduleExpression = "rate(1 minute)"
        self.schedule_event_source.FlexibleTimeWindow = {"Mode": "OFF"}

        self.state_machine = Mock()
        self.state_machine.get_runtime_attr = Mock()
        self.state_machine.get_runtime_attr.return_value = "arn:aws:statemachine:mock"
        self.state_machine.resource_attributes = {}
        self.state_machine.get_passthrough_resource_attributes = Mock()
        self.state_machine.get_passthrough_resource_attributes.return_value = {}

    @parameterized.expand([(None,), ("arn:aws:1234:iam:boundary/CustomerCreatedPermissionsBoundaryForSchedule",)])
    def test_to_cloudformation_returns_eventrule_and_role_resources(self, permissions_boundary):
        self.schedule_event_source.PermissionsBoundary = permissions_boundary
        resources = self.schedule_event_source.to_cloudformation(resource=self.state_machine)
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].resource_type, "AWS::Scheduler::Schedule")
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
                        "Principal": {"Service": ["scheduler.amazonaws.com"]},
                    }
                ],
            },
        )
        self.assertEqual(
            iam_role.Policies,
            [
                {
                    "PolicyName": "ScheduleEventStartExecutionPolicy",
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
        if permissions_boundary:
            self.assertEqual(iam_role.PermissionsBoundary, permissions_boundary)

        schedule = resources[0]
        self.assertEqual(schedule.ScheduleExpression, "rate(1 minute)")
        self.assertEqual(schedule.FlexibleTimeWindow, {"Mode": "OFF"})
        self.assertEqual(
            schedule.Target,
            {
                "Arn": "arn:aws:statemachine:mock",
                "RoleArn": {"Fn::GetAtt": [iam_role.logical_id, "Arn"]},
            },
        )

    def test_to_cloudformation_when_role_is_provided(self):
        self.schedule_event_source.RoleArn = "arn"
        resources = self.schedule_event_source.to_cloudformation(resource=self.state_machine)
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].resource_type, "AWS::Scheduler::Schedule")

        schedule = resources[0]
        self.assertEqual(schedule.Target["RoleArn"], "arn")

    def test_to_cloudformation_with_all_pass_through_properties(self):
        self.schedule_event_source.State = "ENABLED"
        self.schedule_event_source.Description = "description"
        self.schedule_event_source.StartDate = "start_date"
        self.schedule_event_source.EndDate = "end_date"
        self.schedule_event_source.ScheduleExpressionTimezone = "timezone"
        self.schedule_event_source.GroupName = "group_name"
        self.schedule_event_source.KmsKeyArn = "kms_key_arn"

        resources = self.schedule_event_source.to_cloudformation(resource=self.state_machine)
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].resource_type, "AWS::Scheduler::Schedule")

        schedule = resources[0]
        self.assertEqual(schedule.ScheduleExpression, "rate(1 minute)")
        self.assertEqual(schedule.State, "ENABLED")
        self.assertEqual(schedule.Description, "description")
        self.assertEqual(schedule.StartDate, "start_date")
        self.assertEqual(schedule.EndDate, "end_date")
        self.assertEqual(schedule.ScheduleExpressionTimezone, "timezone")
        self.assertEqual(schedule.GroupName, "group_name")
        self.assertEqual(schedule.KmsKeyArn, "kms_key_arn")

    def test_to_cloudformation_throws_when_no_resource(self):
        self.assertRaises(TypeError, self.schedule_event_source.to_cloudformation)

    def test_to_cloudformation_with_input(self):
        input_to_service = '{"test_key": "test_value"}'
        self.schedule_event_source.Input = input_to_service
        resources = self.schedule_event_source.to_cloudformation(resource=self.state_machine)
        self.assertEqual(len(resources), 2)
        event_rule = resources[0]
        self.assertEqual(event_rule.Target["Input"], input_to_service)

    def test_to_cloudformation_with_retry_policy(self):
        retry_policy = {"MaximumRetryAttempts": "10", "MaximumEventAgeInSeconds": "300"}
        self.schedule_event_source.RetryPolicy = retry_policy
        resources = self.schedule_event_source.to_cloudformation(resource=self.state_machine)
        self.assertEqual(len(resources), 2)
        event_rule = resources[0]
        self.assertEqual(event_rule.Target["RetryPolicy"], retry_policy)

    def test_to_cloudformation_with_dlq_arn_provided(self):
        dead_letter_config = {"Arn": "DeadLetterQueueArn"}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        resources = self.schedule_event_source.to_cloudformation(resource=self.state_machine)
        self.assertEqual(len(resources), 2)
        event_rule = resources[0]
        self.assertEqual(event_rule.Target["DeadLetterConfig"], dead_letter_config)

    def test_to_cloudformation_invalid_both_dlq_arn_and_type_provided(self):
        dead_letter_config = {"Arn": "DeadLetterQueueArn", "Type": "SQS"}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        with self.assertRaises(InvalidEventException):
            self.schedule_event_source.to_cloudformation(resource=self.state_machine)

    def test_to_cloudformation_invalid_dlq_type_provided(self):
        dead_letter_config = {"Type": "SNS", "QueueLogicalId": "MyDLQ"}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        with self.assertRaises(InvalidEventException):
            self.schedule_event_source.to_cloudformation(resource=self.state_machine)

    def test_to_cloudformation_missing_dlq_type_or_arn(self):
        dead_letter_config = {"QueueLogicalId": "MyDLQ"}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        with self.assertRaises(InvalidEventException):
            self.schedule_event_source.to_cloudformation(resource=self.state_machine)

    def test_to_cloudformation_with_dlq_generated(self):
        dead_letter_config = {"Type": "SQS"}
        dead_letter_config_translated = {"Arn": {"Fn::GetAtt": [self.logical_id + "Queue", "Arn"]}}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        resources = self.schedule_event_source.to_cloudformation(resource=self.state_machine)
        self.assertEqual(len(resources), 3)
        event_rule = resources[0]
        self.assertEqual(event_rule.Target["DeadLetterConfig"], dead_letter_config_translated)

    def test_to_cloudformation_with_dlq_generated_with_custom_logical_id(self):
        dead_letter_config = {"Type": "SQS", "QueueLogicalId": "MyDLQ"}
        dead_letter_config_translated = {"Arn": {"Fn::GetAtt": ["MyDLQ", "Arn"]}}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        resources = self.schedule_event_source.to_cloudformation(resource=self.state_machine)
        self.assertEqual(len(resources), 3)
        event_rule = resources[0]
        self.assertEqual(event_rule.Target["DeadLetterConfig"], dead_letter_config_translated)

    def test_to_cloudformation_with_dlq_generated_with_intrinsic_function_custom_logical_id_raises_exception(self):
        dead_letter_config = {"Type": "SQS", "QueueLogicalId": {"Fn::Sub": "MyDLQ${Env}"}}
        self.schedule_event_source.DeadLetterConfig = dead_letter_config
        with self.assertRaises(InvalidEventException):
            self.schedule_event_source.to_cloudformation(resource=self.state_machine)
