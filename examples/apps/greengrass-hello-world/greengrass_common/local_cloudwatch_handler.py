#
# Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
from __future__ import print_function

try:
    # Python 3
    from urllib.request import urlopen, Request
    from urllib.error import URLError
except ImportError:
    # Python 2
    from urllib2 import urlopen, Request, URLError

import functools
import inspect
import json
import logging
import os.path
import sys
import time
import traceback

from greengrass_common.env_vars import AUTH_TOKEN

HEADER_AUTH_TOKEN = 'Authorization'
LOCAL_CLOUDWATCH_API_VERSION = '2016-11-01'
LOCAL_CLOUDWATCH_ENDPOINT = 'http://localhost:8000/{version}/cloudwatch/logs/'.format(version=LOCAL_CLOUDWATCH_API_VERSION)

# http://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_PutLogEvents.html
MAX_REQUEST_SIZE = 1024 * 1024
LOG_EVENT_OVERHEAD = 26
BUFFER_SIZE = 10000
SECONDS_IN_ONE_DAY = 86400
# local Cloudwatch uses the log4j logging levels, so we need to convert Python's logging.WARNING
# and loggging.CRITICAL to levels understandable by local Cloudwatch, which is WARN and FATAL.
LOG_LEVEL_WARNING_TO_REPLACE = '[WARNING]'
LOG_LEVEL_CRITICAL_TO_REPLACE = '[CRITICAL]'


def wrap_urllib_exceptions(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except URLError:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            full_stack_trace = traceback.format_exception(exc_type, exc_value, exc_traceback)
            full_stack_trace.insert(0, 'Failed to send to Localwatch due to exception:\n')
            # when we can't talk to local cloudwatch, print to the STDERR
            # this will go to Daemon's STDERR
            print(''.join(full_stack_trace), file=sys.__stderr__)

    return wrapped


class LocalCloudwatchLogHandler(logging.Handler):

    def __init__(self, component_type, component_name, *args, **kwargs):
        logging.Handler.__init__(self, *args, **kwargs)
        self.oldest_time_stamp = time.time()
        self.total_log_event_byte_size = 0
        self.events_buffer = []
        self.log_group_name = os.path.join('/', component_type, component_name)
        self.auth_token = AUTH_TOKEN

    def write(self, data):
        data = str(data)
        if data == '\n':
            # when print(data) is invoked, it invokes write() twice. First,
            # writes the data, then writes a new line. This is to avoid
            # emitting log record with just a new-line character.
            return

        # creates https://docs.python.org/2/library/logging.html#logrecord-objects
        file_name, line_number = inspect.getouterframes(inspect.currentframe())[1][1:3]
        record = logging.makeLogRecord({"created": time.time(),
                                        "msg": data,
                                        "filename": os.path.basename(file_name),
                                        "lineno": line_number,
                                        "levelname": "DEBUG",
                                        "levelno": logging.DEBUG})
        self.emit(record)

    def _should_send(self, message, created_time):
        if created_time >= self.oldest_time_stamp + SECONDS_IN_ONE_DAY:
            return True
        elif self.total_log_event_byte_size + len(message) + LOG_EVENT_OVERHEAD > MAX_REQUEST_SIZE:
            return True
        elif len(self.events_buffer) == BUFFER_SIZE:
            return True
        else:
            return False

    def emit(self, record):
        # This is an implementation of the logging handler interface:
        # https://docs.python.org/2/library/logging.html#handler-objects
        msg = self.format(record)

        if msg.startswith(LOG_LEVEL_WARNING_TO_REPLACE):
            msg = ''.join(('[WARN]', msg[len(LOG_LEVEL_WARNING_TO_REPLACE):]))
        elif msg.startswith(LOG_LEVEL_CRITICAL_TO_REPLACE):
            msg = ''.join(('[FATAL]', msg[len(LOG_LEVEL_CRITICAL_TO_REPLACE):]))

        # TODO: Revert GG-5168, re-introduce _should_send check here and avoid
        # flushing per emit
        self.total_log_event_byte_size += len(msg) + LOG_EVENT_OVERHEAD
        self.events_buffer.append({'timestamp': int(round(record.created * 1000)), 'message': msg})
        self.flush()

    @wrap_urllib_exceptions
    def _send_to_local_cw(self):
        # construct a putLogEvents request and send it
        # http://boto3.readthedocs.io/en/latest/reference/services/logs.html#CloudWatchLogs.Client.put_log_events
        request_data = {
            'logGroupName': self.log_group_name,
            'logStreamName': 'fromPythonAppender',
            'logEvents': self.events_buffer
        }
        request = Request(LOCAL_CLOUDWATCH_ENDPOINT, json.dumps(request_data).encode('utf-8'))
        request.add_header(HEADER_AUTH_TOKEN, self.auth_token)

        urlopen(request)
        self._clear_buffer()

    def flush(self):
        if len(self.events_buffer) > 0:
            # don't bother to send a request if there's nothing to send
            # otherwise you'll just get an HTTP 400
            self._send_to_local_cw()

    def _clear_buffer(self):
        self.total_log_event_byte_size = 0
        del self.events_buffer[:]
