from mock import Mock, patch
from unittest import TestCase
from samtranslator.model.eventsources.cloudwatchlogs import CloudWatchLogs

class CloudWatchLogsEventSource(TestCase):

    def setUp(self):
        self.logical_id = 'LogProcessor'

        self.cloudwatch_logs_event_source = CloudWatchLogs(self.logical_id)
        self.cloudwatch_logs_event_source.LogGroupName = 'MyLogGroup'
        self.cloudwatch_logs_event_source.FilterPattern = 'Fizbo'

        self.function = Mock()
        self.function.get_runtime_attr = Mock()
        self.function.get_runtime_attr.return_value = 'arn:aws:mock'

        self.permission = Mock()
        self.permission.logical_id = 'LogProcessorPermission'

    @patch('boto3.session.Session.region_name', 'ap-southeast-1')
    def test_get_source_arn(self):
        source_arn = self.cloudwatch_logs_event_source.get_source_arn()
        expected_source_arn = {'Fn::Sub': [
            'arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:${__LogGroupName__}:*', {'__LogGroupName__': 'MyLogGroup'}]}
        self.assertEquals(source_arn, expected_source_arn)

    def test_get_subscription_filter(self):
        subscription_filter = self.cloudwatch_logs_event_source.get_subscription_filter(
            self.function, self.permission)
        self.assertEquals(subscription_filter.LogGroupName, 'MyLogGroup')
        self.assertEquals(subscription_filter.FilterPattern, 'Fizbo')
        self.assertEquals(subscription_filter.DestinationArn, 'arn:aws:mock')

    @patch('boto3.session.Session.region_name', 'ap-southeast-1')
    def test_to_cloudformation_returns_permission_and_subscription_filter_resources(self):
        resources = self.cloudwatch_logs_event_source.to_cloudformation(
            function=self.function)
        self.assertEquals(len(resources), 2)
        self.assertEquals(resources[0].resource_type,
                          'AWS::Lambda::Permission')
        self.assertEquals(resources[1].resource_type,
                          'AWS::Logs::SubscriptionFilter')

    def test_to_cloudformation_throws_when_no_function(self):
        self.assertRaises(TypeError, self.cloudwatch_logs_event_source.to_cloudformation)
