from botocore.exceptions import ClientError
from collections import namedtuple
import logging

LOG = logging.getLogger(__name__)


class MetricsPublisher:
    """Interface for all MetricPublishers"""

    def publish(self, namespace, metrics):
        raise NotImplementedError


class CWMetricsPublisher(MetricsPublisher):
    def __init__(self, cloudwatch_client):
        """
        Constructor

        :param cloudwatch_client: cloudwatch client required to publish metrics to cloudwatch
        """

        self.cloudwatch_client = cloudwatch_client

    def publish(self, namespace, metrics):
        """
        Method to publish all metrics to Cloudwatch.

        :param namespace: namespace applied to all metrics published.
        :param metrics: list of metrics to be published
        """
        batch = []
        for metric in metrics:
            batch.append(metric)
            # Cloudwatch recommends not to send more than 20 metrics at a time
            if len(batch) == 20:
                self._flush_metrics(namespace, batch)
                batch = []
        self._flush_metrics(namespace, batch)

    def _flush_metrics(self, namespace, metrics):
        """
        Internal method to publish all provided metrics to cloudwatch, please make sure that array size of metrics is <= 20."""
        metric_data = list(map(lambda m: m.get_metric_data(), metrics))
        try:
            self.cloudwatch_client.put_metric_data(Namespace=namespace, MetricData=metric_data)
        except ClientError:
            LOG.exception("Failed to report {} metrics".format(len(metric_data)), metrics)


class DummyMetricsPublisher(MetricsPublisher):
    def publish(self, namespace, metrics):
        """Method to actually publish them metric"""


class Unit:
    Seconds = "Seconds"
    Microseconds = "Microseconds"
    Milliseconds = "Milliseconds"
    Bytes = "Bytes"
    Kilobytes = "Kilobytes"
    Megabytes = "Megabytes"
    Bits = "Bits"
    Kilobits = "Kilobits"
    Megabits = "Megabits"
    Percent = "Percent"
    Count = "Count"


class MetricDatum:
    """
    Class to hold Metric data.
    """

    def __init__(self, name, value, unit, dimensions=None):
        """
        Constructor

        :param name: metric name
        :param value: value of metric
        :param unit: unit of metric (try using values from Unit class)
        :param dimensions: array of dimensions applied to the metric
        """
        self.name = name
        self.value = value
        self.unit = unit
        self.dimensions = dimensions if dimensions else []

    def get_metric_data(self):
        return {"MetricName": self.name, "Value": self.value, "Unit": self.unit, "Dimensions": self.dimensions}


class Metrics:
    def __init__(self, namespace="ServerlessTransform", metrics_publisher=None):
        """
        Constructor

        :param namespace: namespace under which all metrics will be published
        :param metrics_publisher: publisher to publish all metrics
        """
        self.metrics_publisher = metrics_publisher if metrics_publisher else DummyMetricsPublisher()
        self.metrics_cache = []
        self.namespace = namespace

    def _record_metric(self, name, value, unit, dimensions=[]):
        """
        Create and save metric objects to an array.

        :param name: metric name
        :param value: value of metric
        :param unit: unit of metric (try using values from Unit class)
        :param dimensions: array of dimensions applied to the metric
        """
        self.metrics_cache.append(MetricDatum(name, value, unit, dimensions))

    def record_count(self, name, value, unit=Unit.Count, dimensions=[]):
        """
        Create metric with unit Count.

        :param name: metric name
        :param value: value of metric
        :param unit: unit of metric (try using values from Unit class)
        :param dimensions: array of dimensions applied to the metric
        """
        self._record_metric(name, value, unit, dimensions)

    def record_latency(self, name, value, unit=Unit.Milliseconds, dimensions=[]):
        """
        Create metric with unit Milliseconds.

        :param name: metric name
        :param value: value of metric
        :param unit: unit of metric (try using values from Unit class)
        :param dimensions: array of dimensions applied to the metric
        """
        self._record_metric(name, value, unit, dimensions)

    def publish(self):
        """Method to publish all metrics, do not forget to call this method."""
        self.metrics_publisher.publish(self.namespace, self.metrics_cache)
