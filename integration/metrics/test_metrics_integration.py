import time
import uuid
from datetime import datetime, timedelta
from unittest import TestCase

import boto3
from samtranslator.metrics.metrics import (
    CWMetricsPublisher,
    Metrics,
)


class MetricsIntegrationTest(TestCase):
    """
    This class will use a unique metric namespace to create metrics. There is no cleanup done here
    because if a particular namespace is unsed for 2 weeks it'll be cleanedup by cloudwatch.
    """

    @classmethod
    def setUpClass(cls):
        cls.cw_client = boto3.client("cloudwatch")
        cls.cw_metric_publisher = CWMetricsPublisher(cls.cw_client)

    def test_publish_single_metric(self):
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        namespace = self.get_unique_namespace()
        metrics = Metrics(namespace, CWMetricsPublisher(self.cw_client))
        dimensions = [{"Name": "Dim1", "Value": "Val1"}, {"Name": "Dim2", "Value": "Val2"}]
        metrics.record_count("TestCountMetric", 1, dimensions=dimensions)
        metrics.record_count("TestCountMetric", 3, dimensions=dimensions)
        metrics.record_latency("TestLatencyMetric", 1200, dimensions=dimensions)
        metrics.record_latency("TestLatencyMetric", 1600, dimensions=dimensions)
        metrics.publish()
        total_count = self.get_metric_data(
            namespace,
            "TestCountMetric",
            dimensions,
            datetime(now.year, now.month, now.day),
            datetime(tomorrow.year, tomorrow.month, tomorrow.day),
        )
        latency_avg = self.get_metric_data(
            namespace,
            "TestLatencyMetric",
            dimensions,
            datetime(now.year, now.month, now.day),
            datetime(tomorrow.year, tomorrow.month, tomorrow.day),
            stat="Average",
        )

        self.assertEqual(total_count[0], 1 + 3)
        self.assertEqual(latency_avg[0], 1400)

    def get_unique_namespace(self):
        namespace = f"SinglePublishTest-{uuid.uuid1()}"
        while True:
            response = self.cw_client.list_metrics(Namespace=namespace)
            if not response["Metrics"]:
                return namespace
            namespace = f"SinglePublishTest-{uuid.uuid1()}"

    def get_metric_data(self, namespace, metric_name, dimensions, start_time, end_time, stat="Sum"):
        retries = 20
        while retries > 0:
            retries -= 1
            response = self.cw_client.get_metric_data(
                MetricDataQueries=[
                    {
                        "Id": namespace.replace("-", "_").lower(),
                        "MetricStat": {
                            "Metric": {"Namespace": namespace, "MetricName": metric_name, "Dimensions": dimensions},
                            "Period": 60,
                            "Stat": stat,
                        },
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
            )
            values = response["MetricDataResults"][0]["Values"]
            if values:
                return values
            print(f"No values found by for metric: {metric_name}. Waiting for 5 seconds...")
            time.sleep(5)
        return [0]
