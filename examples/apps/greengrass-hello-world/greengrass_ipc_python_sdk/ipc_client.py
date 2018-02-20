#
# Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import collections
import functools
import logging
import json

try:
    # Python 3
    from urllib.request import urlopen, Request
    from urllib.error import URLError
except ImportError:
    # Python 2
    from urllib2 import urlopen, Request, URLError

from greengrass_common.env_vars import AUTH_TOKEN
from greengrass_common.common_log_appender import local_cloudwatch_handler

# Log messages in the ipc client are not part of customer's log because anything that
# goes wrong here has have nothing to do with customer's lambda code. Since we configured
# the root logger to log to customer's log, we need to turn off propagation.
runtime_logger = logging.getLogger(__name__)
runtime_logger.addHandler(local_cloudwatch_handler)
runtime_logger.propagate = False
# set to the lowest possible level so all log messages will be sent to local cloudwatch handler
runtime_logger.setLevel(logging.DEBUG)

HEADER_INVOCATION_ID = 'X-Amz-InvocationId'
HEADER_CLIENT_CONTEXT = 'X-Amz-Client-Context'
HEADER_AUTH_TOKEN = 'Authorization'
HEADER_INVOCATION_TYPE = 'X-Amz-Invocation-Type'
HEADER_FUNCTION_ERR_TYPE = 'X-Amz-Function-Error'
IPC_API_VERSION = '2016-11-01'


def wrap_urllib_exceptions(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except URLError as e:
            runtime_logger.exception(e)
            raise IPCException(str(e))

    return wrapped


class IPCException(Exception):
    pass


WorkItem = collections.namedtuple('WorkItem', ['invocation_id', 'payload', 'client_context'])
GetWorkResultOutput = collections.namedtuple('GetWorkResultOutput', ['payload', 'func_err'])


class IPCClient:
    """
    Client for IPC that provides methods for getting/posting work for functions,
    as well as getting/posting results of the work.
    """

    def __init__(self, endpoint='localhost', port=8000):
        """
        :param endpoint: Endpoint used to connect to IPC.
            Generally, IPC and functions always run on the same box,
            so endpoint should always be 'localhost' in production.
            You can override it for testing purposes.
        :type endpoint: str

        :param port: Port number used to connect to the :code:`endpoint`.
            Similarly to :code:`endpoint`, can be overridden for testing purposes.
        :type port: int
        """
        self.endpoint = endpoint
        self.port = port
        self.auth_token = AUTH_TOKEN

    @wrap_urllib_exceptions
    def post_work(self, function_arn, input_bytes, client_context, invocation_type="RequestResponse"):
        """
        Send work item to specified :code:`function_arn`.

        :param function_arn: Arn of the Lambda function intended to receive the work for processing.
        :type function_arn: string

        :param input_bytes: The data making up the work being posted.
        :type input_bytes: bytes

        :param client_context: The base64 encoded client context byte string that will be provided to the Lambda
        function being invoked.
        :type client_context: bytes

        :returns: Invocation ID for obtaining result of the work.
        :type returns: str
        """
        url = self._get_url(function_arn)
        runtime_logger.info('Posting work for function [{}] to {}'.format(function_arn, url))

        request = Request(url, input_bytes or b'')
        request.add_header(HEADER_CLIENT_CONTEXT, client_context)
        request.add_header(HEADER_AUTH_TOKEN, self.auth_token)
        request.add_header(HEADER_INVOCATION_TYPE, invocation_type)

        response = urlopen(request)

        invocation_id = response.info().get(HEADER_INVOCATION_ID)
        runtime_logger.info('Work posted with invocation id [{}]'.format(invocation_id))
        return invocation_id

    @wrap_urllib_exceptions
    def get_work(self, function_arn):
        """
        Retrieve the next work item for specified :code:`function_arn`.

        :param function_arn: Arn of the Lambda function intended to receive the work for processing.
        :type function_arn: string

        :returns: Next work item to be processed by the function.
        :type returns: WorkItem
        """
        url = self._get_work_url(function_arn)
        runtime_logger.info('Getting work for function [{}] from {}'.format(function_arn, url))

        request = Request(url)
        request.add_header(HEADER_AUTH_TOKEN, self.auth_token)

        response = urlopen(request)

        invocation_id = response.info().get(HEADER_INVOCATION_ID)
        client_context = response.info().get(HEADER_CLIENT_CONTEXT)

        runtime_logger.info('Got work item with invocation id [{}]'.format(invocation_id))
        return WorkItem(
            invocation_id=invocation_id,
            payload=response.read(),
            client_context=client_context)

    @wrap_urllib_exceptions
    def post_work_result(self, function_arn, work_item):
        """
        Post the result of processing work item by :code:`function_arn`.

        :param function_arn: Arn of the Lambda function intended to receive the work for processing.
        :type function_arn: string

        :param work_item: The WorkItem holding the results of the work being posted.
        :type work_item: WorkItem

        :returns: None
        """
        url = self._get_work_url(function_arn)

        runtime_logger.info('Posting work result for invocation id [{}] to {}'.format(work_item.invocation_id, url))
        request = Request(url, work_item.payload or b'')

        request.add_header(HEADER_INVOCATION_ID, work_item.invocation_id)
        request.add_header(HEADER_AUTH_TOKEN, self.auth_token)

        urlopen(request)

        runtime_logger.info('Posted work result for invocation id [{}]'.format(work_item.invocation_id))

    @wrap_urllib_exceptions
    def post_handler_err(self, function_arn, invocation_id, handler_err):
        """
        Post the error message from executing the function handler for :code:`function_arn`
        with specifid :code:`invocation_id`


        :param function_arn: Arn of the Lambda function which has the handler error message.
        :type function_arn: string

        :param invocation_id: Invocation ID of the work that is being requested
        :type invocation_id: string

        :param handler_err: the error message caught from handler
        :type handler_err: string
        """
        url = self._get_work_url(function_arn)

        runtime_logger.info('Posting handler error for invocation id [{}] to {}'.format(invocation_id, url))

        payload = json.dumps({
            "errorMessage": handler_err,
        }).encode('utf-8')

        request = Request(url, payload)
        request.add_header(HEADER_INVOCATION_ID, invocation_id)
        request.add_header(HEADER_FUNCTION_ERR_TYPE, "Handled")
        request.add_header(HEADER_AUTH_TOKEN, self.auth_token)

        urlopen(request)

        runtime_logger.info('Posted handler error for invocation id [{}]'.format(invocation_id))

    @wrap_urllib_exceptions
    def get_work_result(self, function_arn, invocation_id):
        """
        Retrieve the result of the work processed by :code:`function_arn`
        with specified :code:`invocation_id`.

        :param function_arn: Arn of the Lambda function intended to receive the work for processing.
        :type function_arn: string

        :param invocation_id: Invocation ID of the work that is being requested
        :type invocation_id: string

        :returns: The get work result output contains result payload and function error type if the invoking is failed.
        :type returns: GetWorkResultOutput
        """
        url = self._get_url(function_arn)

        runtime_logger.info('Getting work result for invocation id [{}] from {}'.format(invocation_id, url))

        request = Request(url)
        request.add_header(HEADER_INVOCATION_ID, invocation_id)
        request.add_header(HEADER_AUTH_TOKEN, self.auth_token)

        response = urlopen(request)

        runtime_logger.info('Got result for invocation id [{}]'.format(invocation_id))

        payload = response.read()
        func_err = response.info().get(HEADER_FUNCTION_ERR_TYPE)

        return GetWorkResultOutput(
            payload=payload,
            func_err=func_err)

    def _get_url(self, function_arn):
        return 'http://{endpoint}:{port}/{version}/functions/{function_arn}'.format(
            endpoint=self.endpoint, port=self.port, version=IPC_API_VERSION, function_arn=function_arn
        )

    def _get_work_url(self, function_arn):
        return '{base_url}/work'.format(base_url=self._get_url(function_arn))
