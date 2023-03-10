from unittest.case import skipIf

from integration.config.service_names import SNS
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([SNS]), "SNS is not supported in this testing region")
class TestFunctionWithSns(BaseTest):
    def test_function_with_sns_bucket_trigger(self):
        template_file_path = "combination/function_with_sns"
        self.skip_using_service_detector(template_file_path)
        self.create_and_verify_stack(template_file_path)

        sns_client = self.client_provider.sns_client

        sns_topic_arn = self.get_physical_id_by_type("AWS::SNS::Topic")
        lambda_function_endpoint = self.get_physical_id_by_type("AWS::Lambda::Function")

        subscriptions = sns_client.list_subscriptions_by_topic(TopicArn=sns_topic_arn)["Subscriptions"]
        self.assertEqual(len(subscriptions), 2)

        # checks if SNS has two subscriptions: lambda and SQS
        lambda_subscription = next((x for x in subscriptions if x["Protocol"] == "lambda"), None)

        self.assertIsNotNone(lambda_subscription)
        self.assertIn(lambda_function_endpoint, lambda_subscription["Endpoint"])
        self.assertEqual(lambda_subscription["Protocol"], "lambda")
        self.assertEqual(lambda_subscription["TopicArn"], sns_topic_arn)

        sqs_subscription = next((x for x in subscriptions if x["Protocol"] == "sqs"), None)

        self.assertIsNotNone(sqs_subscription)
        self.assertEqual(sqs_subscription["Protocol"], "sqs")
        self.assertEqual(sqs_subscription["TopicArn"], sns_topic_arn)

    def test_function_with_sns_intrinsics(self):
        template_file_path = "combination/function_with_sns_intrinsics"
        self.skip_using_service_detector(template_file_path)
        self.create_and_verify_stack(template_file_path)

        sns_client = self.client_provider.sns_client

        sns_topic_arn = self.get_physical_id_by_type("AWS::SNS::Topic")

        subscriptions = sns_client.list_subscriptions_by_topic(TopicArn=sns_topic_arn)["Subscriptions"]
        self.assertEqual(len(subscriptions), 1)

        subscription = subscriptions[0]

        self.assertIsNotNone(subscription)
        self.assertEqual(subscription["Protocol"], "sqs")
        self.assertEqual(subscription["TopicArn"], sns_topic_arn)

        subscription_arn = subscription["SubscriptionArn"]
        subscription_attributes = sns_client.get_subscription_attributes(SubscriptionArn=subscription_arn)
        self.assertEqual(subscription_attributes["Attributes"]["FilterPolicy"], '{"price_usd":[{"numeric":["<",100]}]}')
        self.assertEqual(subscription_attributes["Attributes"]["FilterPolicyScope"], "MessageAttributes")
