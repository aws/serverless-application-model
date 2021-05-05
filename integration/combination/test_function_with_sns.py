from integration.helpers.base_test import BaseTest


class TestFunctionWithSns(BaseTest):
    def test_function_with_sns_bucket_trigger(self):
        self.create_and_verify_stack("combination/function_with_sns")

        sns_client = self.client_provider.sns_client

        sns_topic_arn = self.get_physical_id_by_type("AWS::SNS::Topic")
        lambda_function_endpoint = self.get_physical_id_by_type("AWS::Lambda::Function")

        subscriptions = sns_client.list_subscriptions_by_topic(TopicArn=sns_topic_arn)["Subscriptions"]
        self.assertEqual(len(subscriptions), 2)

        # checks if SNS has two subscriptions: lambda and SQS
        lambda_subscription = next((x for x in subscriptions if x["Protocol"] == "lambda"), None)

        self.assertIsNotNone(lambda_subscription)
        self.assertTrue(lambda_function_endpoint in lambda_subscription["Endpoint"])
        self.assertEqual(lambda_subscription["Protocol"], "lambda")
        self.assertEqual(lambda_subscription["TopicArn"], sns_topic_arn)

        sqs_subscription = next((x for x in subscriptions if x["Protocol"] == "sqs"), None)

        self.assertIsNotNone(sqs_subscription)
        self.assertEqual(sqs_subscription["Protocol"], "sqs")
        self.assertEqual(sqs_subscription["TopicArn"], sns_topic_arn)
