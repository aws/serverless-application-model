"""
Helper classes to publish metrics
"""
import logging
from datetime import datetime

LOG = logging.getLogger(__name__)


class MetricsPublisher:
    """Interface for all MetricPublishers"""

    def __init__(self):
        pass

    def publish(self, namespace, metrics):
        raise NotImplementedError


class CWMetricsPublisher(MetricsPublisher):
    BATCH_SIZE = 20

    def __init__(self, cloudwatch_client):
        """
        Constructor

        :param cloudwatch_client: cloudwatch client required to publish metrics to cloudwatch
        """
        MetricsPublisher.__init__(self)
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
            if len(batch) == self.BATCH_SIZE:
                self._flush_metrics(namespace, batch)
                batch = []
        self._flush_metrics(namespace, batch)

    def _flush_metrics(self, namespace, metrics):
        """
        Internal method to publish all provided metrics to cloudwatch, please make sure that array size of metrics is <= 20.
        """
        metric_data = list(map(lambda m: m.get_metric_data(), metrics))
        try:
            if metric_data:
                self.cloudwatch_client.put_metric_data(Namespace=namespace, MetricData=metric_data)
        except Exception as e:
            LOG.exception("Failed to report {} metrics".format(len(metric_data)), exc_info=e)


class DummyMetricsPublisher(MetricsPublisher):
    def __init__(self):
        MetricsPublisher.__init__(self)

    def publish(self, namespace, metrics):
        """Do not publish any metric, this is a dummy publisher used for offline use."""
        LOG.debug("Dummy publisher ignoring {} metrices".format(len(metrics)))


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

    def __init__(self, name, value, unit, dimensions=None, timestamp=None):
        """
        Constructor

        :param name: metric name
        :param value: value of metric
        :param unit: unit of metric (try using values from Unit class)
        :param dimensions: array of dimensions applied to the metric
        :param timestamp: timestamp of metric (datetime.datetime object)
        """
        self.name = name
        self.value = value
        self.unit = unit
        self.dimensions = dimensions if dimensions else []
        self.timestamp = timestamp if timestamp else datetime.utcnow()

    def get_metric_data(self):
        return {
            "MetricName": self.name,
            "Value": self.value,
            "Unit": self.unit,
            "Dimensions": self.dimensions,
            "Timestamp": self.timestamp,
        }


class Metrics:
    def __init__(self, namespace="ServerlessTransform", metrics_publisher=None):
        """
        Constructor

        :param namespace: namespace under which all metrics will be published
        :param metrics_publisher: publisher to publish all metrics
        """
        self.metrics_publisher = metrics_publisher if metrics_publisher else DummyMetricsPublisher()
        self.metrics_cache = dict()
        self.namespace = namespace

    def __del__(self):
        if len(self.metrics_cache) > 0:
            # attempting to publish if user forgot to call publish in code
            LOG.warning(
                "There are unpublished metrics. Please make sure you call publish after you record all metrics."
            )
            self.publish()

    def _record_metric(self, name, value, unit, dimensions=None, timestamp=None):
        """
        Create and save metric object in internal cache.

        :param name: metric name
        :param value: value of metric
        :param unit: unit of metric (try using values from Unit class)
        :param dimensions: array of dimensions applied to the metric
        :param timestamp: timestamp of metric (datetime.datetime object)
        """
        self.metrics_cache.setdefault(name, []).append(MetricDatum(name, value, unit, dimensions, timestamp))

    def record_count(self, name, value, dimensions=None, timestamp=None):
        """
        Create metric with unit Count.

        :param name: metric name
        :param value: value of metric
        :param unit: unit of metric (try using values from Unit class)
        :param dimensions: array of dimensions applied to the metric
        :param timestamp: timestamp of metric (datetime.datetime object)
        """
        self._record_metric(name, value, Unit.Count, dimensions, timestamp)

    def record_latency(self, name, value, dimensions=None, timestamp=None):
        """
        Create metric with unit Milliseconds.

        :param name: metric name
        :param value: value of metric
        :param unit: unit of metric (try using values from Unit class)
        :param dimensions: array of dimensions applied to the metric
        :param timestamp: timestamp of metric (datetime.datetime object)
        """
        self._record_metric(name, value, Unit.Milliseconds, dimensions, timestamp)

    def publish(self):
        """Calls publish method from the configured metrics publisher to publish metrics"""
        # flatten the key->list dict into a flat list; we don't care about the key as it's
        # the metric name which is also in the MetricDatum object
        all_metrics = []
        for m in self.metrics_cache.values():
            all_metrics.extend(m)
        self.metrics_publisher.publish(self.namespace, all_metrics)
        self.metrics_cache = dict()

    def get_metric(self, name):
        """
        Returns a list of metrics from the internal cache for a metric name

        :param name: metric name
        :returns: List (possibly empty) of MetricDatum objects
        """
        return self.metrics_cache.get(name, [])
