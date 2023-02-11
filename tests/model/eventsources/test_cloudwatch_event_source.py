from unittest import TestCase

from samtranslator.model.eventsources.push import CloudWatchEvent
from samtranslator.model.lambda_ import LambdaFunction


class CloudWatchEventSourceTests(TestCase):
    def setUp(self):
        self.logical_id = "EventLogicalId"
        self.func = LambdaFunction("func")

    def test_target_id_when_not_provided(self):
        cloudwatch_event_source = CloudWatchEvent(self.logical_id)
        cfn = cloudwatch_event_source.to_cloudformation(function=self.func)
        target_id = cfn[0].Targets[0]["Id"]
        self.assertEqual(target_id, "{}{}".format(self.logical_id, "LambdaTarget"))

    def test_target_id_when_provided(self):
        cloudwatch_event_source = CloudWatchEvent(self.logical_id)
        cloudwatch_event_source.Target = {"Id": "MyTargetId"}
        cfn = cloudwatch_event_source.to_cloudformation(function=self.func)
        target_id = cfn[0].Targets[0]["Id"]
        self.assertEqual(target_id, "MyTargetId")
