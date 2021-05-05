"""
Retry decorator to retry decorated function based on Exception with exponential backoff and number of attempts built-in.
"""
import math
import time
from functools import wraps


def retry(exc, attempts=3, delay=0.05, exc_raise=Exception, exc_raise_msg=""):
    """
    Retry decorator which defaults to 3 attempts based on exponential backoff
    and a delay of 50ms.
    After retries are exhausted, a custom Exception and Error message are raised.

    :param exc: Exception to be caught for retry
    :param attempts: number of attempts before exception is allowed to be raised.
    :param delay: an initial delay which will exponentially increase based on the retry attempt.
    :param exc_raise: Final Exception to raise.
    :param exc_raise_msg: Final message for the Exception to be raised.
    :return:
    """

    def retry_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            remaining_attempts = attempts
            retry_attempt = 1
            while remaining_attempts >= 1:
                try:
                    return func(*args, **kwargs)
                except exc:
                    time.sleep(math.pow(2, retry_attempt) * delay)
                    retry_attempt = retry_attempt + 1
                    remaining_attempts = remaining_attempts - 1
            raise exc_raise(exc_raise_msg)

        return wrapper

    return retry_wrapper
