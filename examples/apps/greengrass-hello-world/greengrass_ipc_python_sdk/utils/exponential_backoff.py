#
# Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

from functools import wraps
import logging
import random
import sys
import time
import traceback

from greengrass_common.common_log_appender import local_cloudwatch_handler

# Log messages in the ipc client are not part of customer's log because anything that
# goes wrong here has nothing to do with customer's lambda code. Since we configured
# the root logger to log to customer's log, we need to turn off propagation.
runtime_logger = logging.getLogger(__name__)
runtime_logger.addHandler(local_cloudwatch_handler)
runtime_logger.propagate = False
# set to the lowest possible level so all log messages will be sent to local cloudwatch handler
runtime_logger.setLevel(logging.DEBUG)


class RetryTimeoutException(Exception):
    """
    Information regarding a timed-out task.
    """

    def __init__(self, task_name, have_tried, max_attempts, total_wait_time, multiplier, backoff_coefficient,
                 jitter_enabled, retry_errors):
        self.task_name = task_name
        self.have_tried = have_tried
        self.max_attempts = max_attempts
        self.total_wait_time = total_wait_time
        self.multiplier = multiplier
        self.backoff_coefficient = backoff_coefficient
        self.jitter_enabled = jitter_enabled
        self.retry_errors = retry_errors

    def __str__(self):
        return 'Task has timed out, task name: {0}, total retry count: {1}, total wait time: {2}, ' \
               'jitter enabled: {3}, retry errors: {4}'.format(self.task_name, self.max_attempts,
                                                               self.total_wait_time, self.jitter_enabled,
                                                               self.retry_errors)


def retry(time_unit, multiplier, backoff_coefficient, max_delay, max_attempts, expiration_duration, enable_jitter):
    """
    The retry function will keep retrying `task_to_try` until either:
    (1) it returns None, then retry() finishes
    (2) `max_attempts` is reached, then retry() raises an exception.
    (3) if retrying one more time will cause total wait time to go above: `expiration_duration`, then
    retry() raises an exception

    Beware that any exception raised by task_to_try won't get surfaced until (2) or (3) is satisfied.

    At step n, it sleeps for [0, delay), where delay is defined as the following:
    `delay = min(max_delay, multiplier * (backoff_coefficient ** (n - 1))) * time_unit` seconds

    Additionally, if you enable jitter, for each retry, the function will instead sleep for:
    random.random() * sleep, that is [0, sleep) seconds.

    :param time_unit: This field represents a fraction of a second, which is used as a
                     multiplier to compute the amount of time to sleep.
    :type time_unit: float

    :param multiplier: The initial wait duration for the first retry.
    :type multiplier: float

    :param backoff_coefficient: the base value for exponential retry.
    :type backoff_coefficient: float

    :param max_delay: The maximum amount of time to wait per try.
    :type max_delay: float

    :param max_attempts: This method will retry up to this value.
    :type max_attempts: int

    :param expiration_duration: the maximum amount of time retry can wait.
    :type expiration_duration: float

    :param enable_jitter: Setting this to true will add jitter.
    :type enable_jitter: bool
    """

    def deco_retry(task_to_try):
        @wraps(task_to_try)
        def retry_impl(*args, **kwargs):
            total_wait_time = 0
            have_tried = 0
            retry_errors = []
            while have_tried < max_attempts:
                try:
                    task_to_try(*args, **kwargs)
                    return
                except Exception as e:
                    retry_errors.append(e)
                    going_to_sleep_for = min(max_delay, multiplier * (backoff_coefficient ** have_tried))
                    if enable_jitter:
                        going_to_sleep_for = random.random() * going_to_sleep_for

                    duration = going_to_sleep_for * time_unit
                    if total_wait_time + duration > expiration_duration:
                        raise RetryTimeoutException(task_to_try.__name__, have_tried, max_attempts, total_wait_time,
                                                    multiplier, backoff_coefficient, enable_jitter, retry_errors)

                    runtime_logger.warn('Retrying [{0}], going to sleep for {1} seconds, exception stacktrace:\n{2}'
                                        .format(task_to_try.__name__, duration, traceback.format_exc()))
                    time.sleep(duration)
                    total_wait_time += duration
                have_tried += 1
            raise RetryTimeoutException(task_to_try.__name__, have_tried, max_attempts, total_wait_time, multiplier,
                                        backoff_coefficient, enable_jitter, retry_errors)

        return retry_impl
    return deco_retry
