"""
Method decorator for execution latency collection
"""
import functools
import logging
from datetime import datetime
from typing import Callable, Optional, TypeVar, Union, overload

from typing_extensions import ParamSpec

from samtranslator.metrics.metrics import DummyMetricsPublisher, Metrics
from samtranslator.model import Resource

LOG = logging.getLogger(__name__)

_PT = ParamSpec("_PT")  # parameters
_RT = TypeVar("_RT")  # return value


class MetricsMethodWrapperSingleton:
    """
    Keeps the instance of Metrics object.
    This singleton will be alive until lambda receives shutdown event
    """

    _DUMMY_INSTANCE = Metrics("ServerlessTransform", DummyMetricsPublisher())
    _METRICS_INSTANCE = _DUMMY_INSTANCE

    @staticmethod
    def set_instance(metrics: Metrics) -> None:
        MetricsMethodWrapperSingleton._METRICS_INSTANCE = metrics

    @staticmethod
    def get_instance() -> Metrics:
        """
        Return the instance, if nothing is set return a dummy one
        """
        return MetricsMethodWrapperSingleton._METRICS_INSTANCE


def _get_metric_name(prefix, name, func, args):  # type: ignore[no-untyped-def]
    """
    Returns the metric name depending on the parameters

    Parameters
    ----------
    prefix : str
        A string that will always be added in the beginning of metric name.
    name : str
        The name of the metric. If None is given, it will try to read from function and argument details.
    func : Function
        The function that is decorated. This will be used as metric name if name is not provided and caller is not an
        instance of Resource object.
    args : args
        Arguments that is originally passed to the caller. This function will check if first element in this function
        is a Resource then it reads the 'resource_type' property out of it to generate the metric name.
    """
    if name:
        metric_name = name
    elif args and isinstance(args[0], Resource):
        metric_name = args[0].resource_type
    else:
        metric_name = func.__name__

    if prefix:
        return f"{prefix}-{metric_name}"

    return metric_name


def _send_cw_metric(prefix, name, execution_time_ms, func, args):  # type: ignore[no-untyped-def]
    """
    Gets metric name from 'prefix', 'name', 'func' and 'args' parameters, then calls metrics instance from its
    singleton object to record the latency.
    """
    try:
        metric_name = _get_metric_name(prefix, name, func, args)  # type: ignore[no-untyped-call]
        LOG.debug("Execution took %sms for %s", execution_time_ms, metric_name)
        MetricsMethodWrapperSingleton.get_instance().record_latency(metric_name, execution_time_ms)
    except Exception as e:
        LOG.warning("Failed to add metrics", exc_info=e)


@overload
def cw_timer(
    *, name: Optional[str] = None, prefix: Optional[str] = None
) -> Callable[[Callable[_PT, _RT]], Callable[_PT, _RT]]:
    ...


@overload
def cw_timer(_func: Callable[_PT, _RT], name: Optional[str] = None, prefix: Optional[str] = None) -> Callable[_PT, _RT]:
    ...


def cw_timer(
    _func: Optional[Callable[_PT, _RT]] = None, name: Optional[str] = None, prefix: Optional[str] = None
) -> Union[Callable[_PT, _RT], Callable[[Callable[_PT, _RT]], Callable[_PT, _RT]]]:
    """
    A method decorator, that will calculate execution time of the decorated method, and store this information as a
    metric in CloudWatch by calling the metrics singleton instance.

    The metric name is calculated with parameters.
    - If 'name' is provided then it will be the metrics name.
    - If 'name' is not provided and caller method is an instance of 'Resource' object, then 'resource_type' will be used
    - If 'name' is not provided and caller is not instance of 'Resource' then it will be the name of the function

    If prefix is defined, it will be added in the beginning of what is been generated above
    """

    def cw_timer_decorator(func: Callable[_PT, _RT]) -> Callable[_PT, _RT]:
        @functools.wraps(func)
        def wrapper_cw_timer(*args, **kwargs) -> _RT:  # type: ignore[no-untyped-def]
            start_time = datetime.now()

            exec_result = func(*args, **kwargs)

            execution_time = datetime.now() - start_time
            execution_time_ms = execution_time.total_seconds() * 1000
            _send_cw_metric(prefix, name, execution_time_ms, func, args)  # type: ignore[no-untyped-call]

            return exec_result

        return wrapper_cw_timer

    return cw_timer_decorator if _func is None else cw_timer_decorator(_func)
