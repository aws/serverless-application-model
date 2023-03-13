from unittest import TestCase
from unittest.mock import ANY, Mock, patch

from samtranslator.metrics.method_decorator import (
    MetricsMethodWrapperSingleton,
    _get_metric_name,
    _send_cw_metric,
    cw_timer,
)
from samtranslator.model import Resource


class MyClass:
    @cw_timer
    def my_method(self):
        return True


class TestMetricsMethodWrapperSingleton(TestCase):
    def test_default_instance(self):
        default_instance = MetricsMethodWrapperSingleton.get_instance()
        self.assertEqual(default_instance, MetricsMethodWrapperSingleton._DUMMY_INSTANCE)

    def test_given_instance(self):
        given_instance = Mock()
        MetricsMethodWrapperSingleton.set_instance(given_instance)
        self.assertEqual(given_instance, MetricsMethodWrapperSingleton.get_instance())


class TestMetricsMethodDecoratorMetricName(TestCase):
    def test_get_metric_name_with_name(self):
        given_metric_name = "MetricName"
        metric_name = _get_metric_name(None, given_metric_name, None, [])
        self.assertEqual(metric_name, given_metric_name)

    def test_get_metric_name_with_name_and_prefix(self):
        given_metric_name = "MetricName"
        given_prefix = "Prefix"
        metric_name = _get_metric_name(given_prefix, given_metric_name, None, [])
        self.assertEqual(metric_name, f"{given_prefix}-{given_metric_name}")

    def test_get_metric_name_with_function(self):
        def my_function():
            return True

        metric_name = _get_metric_name(None, None, my_function, [])
        self.assertEqual(metric_name, "my_function")

    def test_get_metric_name_with_resource_type(self):
        given_resource_type = "AWS::Serverless::MyResource"
        mock_resource = Mock(spec=Resource, resource_type=given_resource_type)

        metric_name = _get_metric_name(None, None, None, [mock_resource])
        self.assertEqual(metric_name, given_resource_type)

    @patch("samtranslator.metrics.method_decorator.MetricsMethodWrapperSingleton")
    @patch("samtranslator.metrics.method_decorator._get_metric_name")
    def test_send_cw_metric(self, patched_metric_name, patched_singleton):
        given_execution_time = Mock()
        given_metric_name = "MetricName"
        patched_metric_name.return_value = given_metric_name

        _send_cw_metric(None, given_metric_name, given_execution_time, None, [])
        patched_metric_name.assert_called_with(None, given_metric_name, None, [])
        patched_singleton.get_instance.assert_called_once()
        patched_singleton.get_instance().record_latency.assert_called_with(given_metric_name, given_execution_time)

    def test_cw_timer_decorator(self):
        given_metrics_instance = Mock()
        MetricsMethodWrapperSingleton.set_instance(given_metrics_instance)

        my_class = MyClass()
        return_value = my_class.my_method()

        self.assertTrue(return_value)
        given_metrics_instance.record_latency.assert_called_with("my_method", ANY)

    def test_cw_timer_should_not_break_the_method(self):
        given_metrics_instance = Mock()
        given_metrics_instance.record_latency.side_effect = Exception()
        MetricsMethodWrapperSingleton.set_instance(given_metrics_instance)

        my_class = MyClass()
        return_value = my_class.my_method()

        self.assertTrue(return_value)
        given_metrics_instance.record_latency.assert_called_with("my_method", ANY)
