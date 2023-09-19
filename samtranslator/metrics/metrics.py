"""
Helper classes to publish metrics
"""
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from typing_extensions import TypedDict

from samtranslator.internal.deprecation_control import deprecated

LOG = logging.getLogger(__name__)


class MetricsPublisher(ABC):
    """Interface for all MetricPublishers"""

    @abstractmethod
    def publish(self, namespace: str, metrics: List["MetricDatum"]) -> None:
        """
        Abstract method to publish all metrics to CloudWatch

        :param namespace: namespace applied to all metrics published.
        :param metrics: list of metrics to be published
        """


class CWMetricsPublisher(MetricsPublisher):
    BATCH_SIZE = 20

    @deprecated()
    def __init__(self, cloudwatch_client) -> None:  # type: ignore[no-untyped-def]
        """
        Constructor

        :param cloudwatch_client: cloudwatch client required to publish metrics to cloudwatch
        """
        MetricsPublisher.__init__(self)
        self.cloudwatch_client = cloudwatch_client

    def publish(self, namespace, metrics):  # type: ignore[no-untyped-def]
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
                self._flush_metrics(namespace, batch)  # type: ignore[no-untyped-call]
                batch = []
        self._flush_metrics(namespace, batch)  # type: ignore[no-untyped-call]

    def _flush_metrics(self, namespace, metrics):  # type: ignore[no-untyped-def]
        """
        Internal method to publish all provided metrics to cloudwatch, please make sure that array size of metrics is <= 20.
        """
        metric_data = [m.get_metric_data() for m in metrics]
        try:
            if metric_data:
                self.cloudwatch_client.put_metric_data(Namespace=namespace, MetricData=metric_data)
        except Exception:
            LOG.exception(f"Failed to report {len(metric_data)} metrics")


class DummyMetricsPublisher(MetricsPublisher):
    def __init__(self) -> None:
        MetricsPublisher.__init__(self)

    def publish(self, namespace: str, metrics: List["MetricDatum"]) -> None:
        """Do not publish any metric, this is a dummy publisher used for offline use."""
        LOG.debug(f"Dummy publisher ignoring {len(metrics)} metrices")


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

    def __init__(
        self,
        name: str,
        value: Union[int, float],
        unit: str,
        dimensions: Optional[List["MetricDimension"]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
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

    def get_metric_data(self) -> Dict[str, Any]:
        return {
            "MetricName": self.name,
            "Value": self.value,
            "Unit": self.unit,
            "Dimensions": self.dimensions,
            "Timestamp": self.timestamp,
        }


class MetricDimension(TypedDict):
    Name: str
    Value: Any


class Metrics:
    def __init__(
        self, namespace: str = "ServerlessTransform", metrics_publisher: Optional[MetricsPublisher] = None
    ) -> None:
        """
        Constructor

        :param namespace: namespace under which all metrics will be published
        :param metrics_publisher: publisher to publish all metrics
        """
        self.metrics_publisher = metrics_publisher if metrics_publisher else DummyMetricsPublisher()
        self.metrics_cache: Dict[str, List[MetricDatum]] = {}
        self.namespace = namespace

    def __del__(self) -> None:
        if len(self.metrics_cache) > 0:
            # attempting to publish if user forgot to call publish in code
            LOG.warning(
                "There are unpublished metrics. Please make sure you call publish after you record all metrics."
            )
            self.publish()

    def _record_metric(
        self,
        name: str,
        value: Union[int, float],
        unit: str,
        dimensions: Optional[List["MetricDimension"]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Create and save metric object in internal cache.

        :param name: metric name
        :param value: value of metric
        :param unit: unit of metric (try using values from Unit class)
        :param dimensions: array of dimensions applied to the metric
        :param timestamp: timestamp of metric (datetime.datetime object)
        """
        self.metrics_cache.setdefault(name, []).append(MetricDatum(name, value, unit, dimensions, timestamp))

    def record_count(
        self,
        name: str,
        value: int,
        dimensions: Optional[List["MetricDimension"]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Create metric with unit Count.

        :param name: metric name
        :param value: value of metric
        :param unit: unit of metric (try using values from Unit class)
        :param dimensions: array of dimensions applied to the metric
        :param timestamp: timestamp of metric (datetime.datetime object)
        """
        self._record_metric(name, value, Unit.Count, dimensions, timestamp)

    def record_latency(
        self,
        name: str,
        value: Union[int, float],
        dimensions: Optional[List["MetricDimension"]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Create metric with unit Milliseconds.

        :param name: metric name
        :param value: value of metric
        :param unit: unit of metric (try using values from Unit class)
        :param dimensions: array of dimensions applied to the metric
        :param timestamp: timestamp of metric (datetime.datetime object)
        """
        self._record_metric(name, value, Unit.Milliseconds, dimensions, timestamp)

    def publish(self) -> None:
        """Calls publish method from the configured metrics publisher to publish metrics"""
        # flatten the key->list dict into a flat list; we don't care about the key as it's
        # the metric name which is also in the MetricDatum object
        all_metrics = []
        for m in self.metrics_cache.values():
            all_metrics.extend(m)
        self.metrics_publisher.publish(self.namespace, all_metrics)
        self.metrics_cache = {}

    def get_metric(self, name: str) -> List[MetricDatum]:
        """
        Returns a list of metrics from the internal cache for a metric name

        :param name: metric name
        :returns: List (possibly empty) of MetricDatum objects
        """
        return self.metrics_cache.get(name, [])
