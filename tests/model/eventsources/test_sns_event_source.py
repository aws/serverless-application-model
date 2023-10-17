from unittest import TestCase
from unittest.mock import Mock

from samtranslator.model.eventsources.push import SNS


class SnsEventSource(TestCase):
    def setUp(self):
        self.logical_id = "NotificationsProcessor"

        self.sns_event_source = SNS(self.logical_id)
        self.sns_event_source.Topic = "arn:aws:sns:MyTopic"

        self.function = Mock()
        self.function.get_runtime_attr = Mock()
        self.function.get_runtime_attr.return_value = "arn:aws:lambda:mock"
        self.function.resource_attributes = {}
        self.function.get_passthrough_resource_attributes = Mock()
        self.function.get_passthrough_resource_attributes.return_value = {}

        self.kwargs = {"function": self.function, "intrinsics_resolver": Mock()}

    def test_to_cloudformation_returns_permission_and_subscription_resources(self):
        resources = self.sns_event_source.to_cloudformation(**self.kwargs)
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].resource_type, "AWS::Lambda::Permission")
        self.assertEqual(resources[1].resource_type, "AWS::SNS::Subscription")

        subscription = resources[1]
        self.assertEqual(subscription.TopicArn, "arn:aws:sns:MyTopic")
        self.assertEqual(subscription.Protocol, "lambda")
        self.assertEqual(subscription.Endpoint, "arn:aws:lambda:mock")
        self.assertIsNone(subscription.Region)
        self.assertIsNone(subscription.FilterPolicy)
        self.assertIsNone(subscription.FilterPolicyScope)
        self.assertIsNone(subscription.RedrivePolicy)

    def test_to_cloudformation_passes_the_region(self):
        region = "us-west-2"
        self.sns_event_source.Region = region

        resources = self.sns_event_source.to_cloudformation(**self.kwargs)
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[1].resource_type, "AWS::SNS::Subscription")
        subscription = resources[1]
        self.assertEqual(subscription.Region, region)

    def test_to_cloudformation_passes_the_filter_policy(self):
        filterPolicy = {
            "attribute1": ["value1"],
            "attribute2": ["value2", "value3"],
            "attribute3": {"numeric": [">=", "100"]},
        }
        self.sns_event_source.FilterPolicy = filterPolicy

        resources = self.sns_event_source.to_cloudformation(**self.kwargs)
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[1].resource_type, "AWS::SNS::Subscription")
        subscription = resources[1]
        self.assertEqual(subscription.FilterPolicy, filterPolicy)

    def test_to_cloudformation_passes_the_filter_policy_scope(self):
        filterPolicyScope = "MessageAttributes"
        self.sns_event_source.FilterPolicyScope = filterPolicyScope

        resources = self.sns_event_source.to_cloudformation(**self.kwargs)
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[1].resource_type, "AWS::SNS::Subscription")
        subscription = resources[1]
        self.assertEqual(subscription.FilterPolicyScope, filterPolicyScope)

    def test_to_cloudformation_passes_the_redrive_policy(self):
        redrive_policy = {"deadLetterTargetArn": "arn:aws:sqs:us-east-2:123456789012:MyDeadLetterQueue"}
        self.sns_event_source.RedrivePolicy = redrive_policy

        resources = self.sns_event_source.to_cloudformation(**self.kwargs)
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[1].resource_type, "AWS::SNS::Subscription")
        subscription = resources[1]
        self.assertEqual(subscription.RedrivePolicy, redrive_policy)

    def test_to_cloudformation_throws_when_no_function(self):
        self.assertRaises(TypeError, self.sns_event_source.to_cloudformation)

    def test_to_cloudformation_throws_when_queue_url_or_queue_arn_not_given(self):
        sqsSubscription = {"BatchSize": 5}
        self.sns_event_source.SqsSubscription = sqsSubscription
        self.assertRaises(TypeError, self.sns_event_source.to_cloudformation)

    def test_to_cloudformation_when_sqs_subscription_disable(self):
        sqsSubscription = False
        self.sns_event_source.SqsSubscription = sqsSubscription

        resources = self.sns_event_source.to_cloudformation(**self.kwargs)
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].resource_type, "AWS::Lambda::Permission")
        self.assertEqual(resources[1].resource_type, "AWS::SNS::Subscription")

        subscription = resources[1]
        self.assertEqual(subscription.TopicArn, "arn:aws:sns:MyTopic")
        self.assertEqual(subscription.Protocol, "lambda")
        self.assertEqual(subscription.Endpoint, "arn:aws:lambda:mock")
        self.assertIsNone(subscription.Region)
        self.assertIsNone(subscription.FilterPolicy)
        self.assertIsNone(subscription.FilterPolicyScope)
        self.assertIsNone(subscription.RedrivePolicy)
