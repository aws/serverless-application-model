from datetime import datetime
from unittest import TestCase
from unittest.mock import ANY, MagicMock, call

from parameterized import param, parameterized
from samtranslator.metrics.metrics import (
    CWMetricsPublisher,
    DummyMetricsPublisher,
    MetricDatum,
    Metrics,
    MetricsPublisher,
    Unit,
)


class MetricPublisherTestHelper(MetricsPublisher):
    def __init__(self):
        MetricsPublisher.__init__(self)
        self.metrics_cache = []
        self.namespace = ""

    def publish(self, namespace, metrics):
        self.namespace = namespace
        self.metrics_cache = metrics


class TestMetrics(TestCase):
    @parameterized.expand(
        [
            param(
                "DummyNamespace",
                "CountMetric",
                12,
                [{"Name": "SAM", "Value": "Dim1"}, {"Name": "SAM", "Value": "Dim2"}],
                None,
            ),
            param(
                "DummyNamespace",
                "IAMError",
                59,
                [{"Name": "SAM", "Value": "Dim1"}, {"Name": "SAM", "Value": "Dim2"}],
                None,
            ),
            param(
                "DummyNamespace",
                "MyCount",
                77,
                [{"Name": "SAM", "Value": "Dim1"}, {"Name": "SAM", "Value": "Dim2"}],
                datetime(2022, 8, 11, 0, 0, 0),
            ),
        ]
    )
    def test_publishing_count_metric(self, namespace, name, value, dimensions, timestamp):
        mock_metrics_publisher = MetricPublisherTestHelper()
        metrics = Metrics(namespace, mock_metrics_publisher)
        kwargs = {
            "name": name,
            "value": value,
            "dimensions": dimensions,
        }
        if timestamp is not None:
            kwargs["timestamp"] = timestamp
        metrics.record_count(**kwargs)
        metrics.publish()
        self.assertEqual(len(mock_metrics_publisher.metrics_cache), 1)
        published_metric = mock_metrics_publisher.metrics_cache[0].get_metric_data()
        self.assertEqual(published_metric["MetricName"], name)
        self.assertEqual(published_metric["Dimensions"], dimensions)
        self.assertEqual(published_metric["Value"], value)
        if timestamp is not None:
            self.assertEqual(published_metric["Timestamp"], timestamp)

    @parameterized.expand(
        [
            param(
                "DummyNamespace",
                "SARLatency",
                1200,
                [{"Name": "SAM", "Value": "Dim1"}, {"Name": "SAM", "Value": "Dim2"}],
                None,
            ),
            param(
                "DummyNamespace",
                "IAMLatency",
                400,
                [{"Name": "SAM", "Value": "Dim1"}, {"Name": "SAM", "Value": "Dim2"}],
                None,
            ),
            param(
                "DummyNamespace",
                "OtherLatency",
                400000,
                [{"Name": "SAM", "Value": "Dim1"}, {"Name": "SAM", "Value": "Dim2"}],
                datetime(2021, 9, 20, 12, 0, 0),
            ),
        ]
    )
    def test_publishing_latency_metric(self, namespace, name, value, dimensions, timestamp):
        mock_metrics_publisher = MetricPublisherTestHelper()
        metrics = Metrics(namespace, mock_metrics_publisher)
        kwargs = {
            "name": name,
            "value": value,
            "dimensions": dimensions,
        }
        if timestamp is not None:
            kwargs["timestamp"] = timestamp
        metrics.record_latency(**kwargs)
        metrics.publish()
        self.assertEqual(len(mock_metrics_publisher.metrics_cache), 1)
        published_metric = mock_metrics_publisher.metrics_cache[0].get_metric_data()
        self.assertEqual(published_metric["MetricName"], name)
        self.assertEqual(published_metric["Dimensions"], dimensions)
        self.assertEqual(published_metric["Value"], value)
        if timestamp is not None:
            self.assertEqual(published_metric["Timestamp"], timestamp)

    @parameterized.expand(
        [
            param(
                "DummyNamespace",
                "CountMetric",
                12,
                [{"Name": "SAM", "Value": "Dim1"}, {"Name": "SAM", "Value": "Dim2"}],
            ),
            param(
                "DummyNamespace",
                "LatencyMetric",
                1200,
                [{"Name": "SAM", "Value": "Dim1"}, {"Name": "SAM", "Value": "Dim2"}],
            ),
        ]
    )
    def test_publishing_metric_without_calling_publish(self, namespace, name, value, dimensions):
        mock_metrics_publisher = MetricPublisherTestHelper()
        metrics = Metrics(namespace, mock_metrics_publisher)
        metrics.record_count(name, value, dimensions)
        del metrics
        self.assertEqual(len(mock_metrics_publisher.metrics_cache), 1)
        published_metric = mock_metrics_publisher.metrics_cache[0].get_metric_data()
        self.assertEqual(published_metric["MetricName"], name)
        self.assertEqual(published_metric["Dimensions"], dimensions)
        self.assertEqual(published_metric["Value"], value)

    @parameterized.expand(
        [
            param(
                "DummyNamespace",
                "SARLatency",
                1200,
                "IAMLatency",
                400,
                [{"Name": "SAM", "Value": "Dim1"}, {"Name": "SAM", "Value": "Dim2"}],
            ),
        ]
    )
    def test_get_metrics(self, namespace, name1, value1, name2, value2, dimensions):
        mock_metrics_publisher = MetricPublisherTestHelper()
        metrics = Metrics(namespace, mock_metrics_publisher)
        metrics.record_count(name1, value1, dimensions)
        metrics.record_latency(name2, value2, dimensions)
        # record the first metric twice
        metrics.record_count(name1, value1 * 2, dimensions)

        m1 = metrics.get_metric(name1)
        self.assertEqual(len(m1), 2)
        for i in range(1, 3):  # first value is 1*value1, 2nd is 2*value1
            metric_data = m1[i - 1].get_metric_data()
            self.assertEqual(metric_data["MetricName"], name1)
            self.assertEqual(metric_data["Value"], i * value1)
            self.assertEqual(metric_data["Dimensions"], dimensions)

        m2 = metrics.get_metric(name2)
        self.assertEqual(len(m2), 1)
        metric_data = m2[0].get_metric_data()
        self.assertEqual(metric_data["MetricName"], name2)
        self.assertEqual(metric_data["Value"], value2)
        self.assertEqual(metric_data["Dimensions"], dimensions)

        # non-existent metric should return an empty list
        m3 = metrics.get_metric(name1 + name2)
        self.assertListEqual(m3, [])


class TestCWMetricPublisher(TestCase):
    @parameterized.expand(
        [
            param(
                "DummyNamespace",
                "CountMetric",
                12,
                Unit.Count,
                [{"Name": "SAM", "Value": "Dim1"}, {"Name": "SAM", "Value": "Dim2"}],
                None,
            ),
            param(
                "DummyNamespace",
                "IAMError",
                59,
                Unit.Count,
                [{"Name": "SAM", "Value": "Dim1"}, {"Name": "SAM", "Value": "Dim2"}],
                datetime(2022, 8, 8, 8, 8, 8),
            ),
            param(
                "DummyNamespace",
                "SARLatency",
                1200,
                Unit.Milliseconds,
                [{"Name": "SAM", "Value": "Dim1"}, {"Name": "SAM", "Value": "Dim2"}],
                None,
            ),
            param(
                "DummyNamespace",
                "IAMLatency",
                400,
                Unit.Milliseconds,
                [{"Name": "SAM", "Value": "Dim1"}, {"Name": "SAM", "Value": "Dim2"}],
                datetime(2021, 9, 10, 10, 10, 10),
            ),
        ]
    )
    def test_publish_metric(self, namespace, name, value, unit, dimensions, timestamp):
        mock_cw_client = MagicMock()
        metric_publisher = CWMetricsPublisher(mock_cw_client)
        metric_datum = MetricDatum(name, value, unit, dimensions, timestamp)
        metrics = [metric_datum]
        metric_publisher.publish(namespace, metrics)
        expected_timestamp = timestamp if timestamp is not None else ANY
        mock_cw_client.put_metric_data.assert_has_calls(
            [
                call(
                    MetricData=[
                        {
                            "Dimensions": dimensions,
                            "Unit": unit,
                            "Value": value,
                            "MetricName": name,
                            "Timestamp": expected_timestamp,
                        }
                    ],
                    Namespace=namespace,
                )
            ]
        )

    def test_publish_more_than_20_metrics(self):
        total_metrics = 45
        mock_cw_client = MagicMock()
        metric_publisher = CWMetricsPublisher(mock_cw_client)
        metrics_list = []
        dimensions = []
        unit = Unit.Count
        metric_name = "CountMetric"
        namespace = "DummyNamespace"

        for i in range(total_metrics):
            metrics_list.append(MetricDatum(metric_name, i, unit, dimensions))
        metric_publisher.publish(namespace, metrics_list)

        # metrics should be published 3 times in batches
        self.assertEqual(mock_cw_client.put_metric_data.call_count, 3)

        # prepare expected calls for each batch
        metric_batches = []
        for i in range(total_metrics):
            batch_index = int(i / metric_publisher.BATCH_SIZE)
            print(batch_index)
            if len(metric_batches) <= batch_index:
                metric_batches.append([])
            metric_batches[batch_index].append(
                {"Dimensions": dimensions, "Unit": unit, "Value": i, "MetricName": metric_name, "Timestamp": ANY}
            )
        expected_calls = [call(MetricData=metrics, Namespace=namespace) for metrics in metric_batches]
        mock_cw_client.put_metric_data.assert_has_calls(expected_calls)

    def test_do_not_fail_on_cloudwatch_any_exception(self):
        mock_cw_client = MagicMock()
        mock_cw_client.put_metric_data = MagicMock()
        mock_cw_client.put_metric_data.side_effect = Exception("BOOM FAILED!!")
        metric_publisher = CWMetricsPublisher(mock_cw_client)
        single_metric = MetricDatum("Name", 20, Unit.Count, [])
        metric_publisher.publish("SomeNamespace", [single_metric])
        self.assertTrue(True)

    def test_for_code_coverage(self):
        dummy_publisher = DummyMetricsPublisher()
        dummy_publisher.publish("NS", [None])
        self.assertTrue(True)

    def test_publish_empty_metric(self):
        mock_cw_client = MagicMock()
        metric_publisher = CWMetricsPublisher(mock_cw_client)
        metrics = []
        namespace = "DummyNamespace"
        metric_publisher.publish(namespace, metrics)
        mock_cw_client.put_metric_data.assert_not_called()
