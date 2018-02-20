#
# Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# this log appender is shared among all components of python lambda runtime, including:
# greengrass_common/greengrass_message.py, greengrass_ipc_python_sdk/ipc_client.py,
# greengrass_ipc_python_sdk/utils/exponential_backoff.py, lambda_runtime/lambda_runtime.py.
# so that all log records will be emitted to local Cloudwatch.
import logging.handlers

from greengrass_common.local_cloudwatch_handler import LocalCloudwatchLogHandler

# https://docs.python.org/2/library/logging.html#logrecord-attributes
LOCAL_CLOUDWATCH_FORMAT = '[%(levelname)s]-%(filename)s:%(lineno)d,%(message)s'

local_cloudwatch_handler = LocalCloudwatchLogHandler('GreengrassSystem', 'python_runtime')
local_cloudwatch_handler.setFormatter(logging.Formatter(LOCAL_CLOUDWATCH_FORMAT))
