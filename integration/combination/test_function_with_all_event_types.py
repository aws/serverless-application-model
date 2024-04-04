from unittest.case import skipIf

from integration.config.service_names import IOT, LOGS, SCHEDULE_EVENT
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support, generate_suffix


@skipIf(
    current_region_does_not_support([IOT, SCHEDULE_EVENT, LOGS]),
    "IoT, ScheduleEvent or a Logs resource is not supported in this testing region",
)
class TestFunctionWithAllEventTypes(BaseTest):
    def test_function_with_all_event_types(self):
        schedule_name = "TestSchedule" + generate_suffix()
        parameters = [self.generate_parameter("ScheduleName", schedule_name)]

        self.create_and_verify_stack("combination/function_with_all_event_types", parameters)

        # make sure bucket notification configurations are added
        s3_client = self.client_provider.s3_client
        s3_bucket_name = self.get_physical_id_by_type("AWS::S3::Bucket")

        configurations = s3_client.get_bucket_notification_configuration(Bucket=s3_bucket_name)[
            "LambdaFunctionConfigurations"
        ]
        actual_bucket_configuration_events = _get_actual_bucket_configuration_events(configurations)

        self.assertEqual(len(configurations), 2)
        self.assertEqual(actual_bucket_configuration_events, {"s3:ObjectRemoved:*", "s3:ObjectCreated:*"})

        # make sure two CW Events are created for MyAwesomeFunction
        cloudwatch_events_client = self.client_provider.cloudwatch_event_client
        lambda_client = self.client_provider.lambda_client

        my_awesome_function_name = self.get_physical_id_by_logical_id("MyAwesomeFunction")
        alias_arn = lambda_client.get_alias(FunctionName=my_awesome_function_name, Name="Live")["AliasArn"]

        rule_names = cloudwatch_events_client.list_rule_names_by_target(TargetArn=alias_arn)["RuleNames"]
        self.assertEqual(len(rule_names), 2)

        # make sure cloudwatch Schedule event has properties: name, state and description
        cw_rule_result = cloudwatch_events_client.describe_rule(Name=schedule_name)

        self.assertEqual(cw_rule_result["Name"], schedule_name)
        self.assertEqual(cw_rule_result["Description"], "test schedule")
        self.assertEqual(cw_rule_result["State"], "DISABLED")
        self.assertEqual(cw_rule_result["ScheduleExpression"], "rate(1 minute)")

        # make sure IOT Rule has lambda function action
        iot_client = self.client_provider.iot_client
        iot_rule_name = iot_client.list_topic_rules()["rules"][0]["ruleName"]

        action = iot_client.get_topic_rule(ruleName=iot_rule_name)["rule"]["actions"][0]["lambda"]
        self.assertEqual(action["functionArn"], alias_arn)

        # Assert CloudWatch Logs group
        log_client = self.client_provider.cloudwatch_log_client
        cloud_watch_log_group_name = self.get_physical_id_by_type("AWS::Logs::LogGroup")

        subscription_filters_result = log_client.describe_subscription_filters(logGroupName=cloud_watch_log_group_name)
        subscription_filter = subscription_filters_result["subscriptionFilters"][0]
        self.assertEqual(len(subscription_filters_result["subscriptionFilters"]), 1)
        self.assertTrue(alias_arn in subscription_filter["destinationArn"])
        self.assertEqual(subscription_filter["filterPattern"], "My pattern")

        # assert LambdaEventSourceMappings
        event_source_mappings = lambda_client.list_event_source_mappings()["EventSourceMappings"]
        event_source_mapping_configurations = [x for x in event_source_mappings if x["FunctionArn"] == alias_arn]
        event_source_mapping_arns = set([x["EventSourceArn"] for x in event_source_mapping_configurations])

        kinesis_client = self.client_provider.kinesis_client
        kinesis_stream_name = self.get_physical_id_by_type("AWS::Kinesis::Stream")
        kinesis_stream = kinesis_client.describe_stream(StreamName=kinesis_stream_name)["StreamDescription"]

        dynamo_db_stream_client = self.client_provider.dynamodb_streams_client
        ddb_table_name = self.get_physical_id_by_type("AWS::DynamoDB::Table")
        ddb_stream = dynamo_db_stream_client.list_streams(TableName=ddb_table_name)["Streams"][0]

        expected_mappings = {kinesis_stream["StreamARN"], ddb_stream["StreamArn"]}
        self.assertEqual(event_source_mapping_arns, expected_mappings)

        kinesis_stream_config = next(
            (x for x in event_source_mapping_configurations if x["EventSourceArn"] == kinesis_stream["StreamARN"]), None
        )
        self.assertIsNotNone(kinesis_stream_config)
        self.assertEqual(kinesis_stream_config["MaximumBatchingWindowInSeconds"], 20)
        dynamo_db_stream_config = next(
            (x for x in event_source_mapping_configurations if x["EventSourceArn"] == ddb_stream["StreamArn"]), None
        )
        self.assertIsNotNone(dynamo_db_stream_config)
        self.assertEqual(dynamo_db_stream_config["MaximumBatchingWindowInSeconds"], 20)

        # assert Notification Topic has lambda function endpoint
        sns_client = self.client_provider.sns_client
        sns_topic_arn = self.get_physical_id_by_type("AWS::SNS::Topic")
        subscriptions_by_topic = sns_client.list_subscriptions_by_topic(TopicArn=sns_topic_arn)["Subscriptions"]

        self.assertEqual(len(subscriptions_by_topic), 1)
        self.assertTrue(alias_arn in subscriptions_by_topic[0]["Endpoint"])
        self.assertEqual(subscriptions_by_topic[0]["Protocol"], "lambda")
        self.assertEqual(subscriptions_by_topic[0]["TopicArn"], sns_topic_arn)

    def test_function_with_all_event_types_condition_false(self):
        self.create_and_verify_stack("combination/function_with_all_event_types_condition_false")

        # make sure bucket notification configurations are added
        s3_client = self.client_provider.s3_client
        s3_bucket_name = self.get_physical_id_by_type("AWS::S3::Bucket")

        configurations = s3_client.get_bucket_notification_configuration(Bucket=s3_bucket_name)[
            "LambdaFunctionConfigurations"
        ]
        actual_bucket_configuration_events = _get_actual_bucket_configuration_events(configurations)

        self.assertEqual(len(configurations), 1)
        self.assertEqual(actual_bucket_configuration_events, {"s3:ObjectRemoved:*"})


def _get_actual_bucket_configuration_events(configurations):
    actual_bucket_configuration_events = set()

    for config in configurations:
        for event in config.get("Events"):
            actual_bucket_configuration_events.add(event)

    return actual_bucket_configuration_events
