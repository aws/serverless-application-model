#
# Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import json
from functools import wraps
from greengrass_common.env_vars import MY_FUNCTION_ARN


def mock(func):
    """
    mock decorates _invoke_internal by checking if MY_FUNCTION_ARN is present
    if MY_FUNCTION_ARN is present, the actual _invoke_internal is invoked
    otherwise, the mock _invoke_internal is invoked
    """
    @wraps(func)
    def mock_invoke_internal(self, function_arn, payload, client_context, invocation_type="RequestResponse"):
        if MY_FUNCTION_ARN is None:
            if invocation_type == 'RequestResponse':
                return {
                    'Payload': json.dumps({
                        'TestKey': 'TestValue'
                    }),
                    'FunctionError': ''
                }
            elif invocation_type == 'Event':
                return {
                    'Payload': b'',
                    'FunctionError': ''
                }
            else:
                raise Exception('Unsupported invocation type {}'.format(invocation_type))
        else:
            return func(self, function_arn, payload, client_context, invocation_type)
    return mock_invoke_internal
