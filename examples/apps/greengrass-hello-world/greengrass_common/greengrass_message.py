#
# Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import base64
import json
import logging
from greengrass_common.common_log_appender import local_cloudwatch_handler

# Log messages here are not part of customer's log because anything that
# goes wrong here has nothing to do with customer's lambda code. Since we configured
# the root logger to log to customer's log, we need to turn off propagation.
runtime_logger = logging.getLogger(__name__)
runtime_logger.addHandler(local_cloudwatch_handler)
runtime_logger.propagate = False
# set to the lowest possible level so all log messages will be sent to local cloudwatch handler
runtime_logger.setLevel(logging.DEBUG)


class GreengrassMessage:
    """
    Holds the payload and extension_map fields making up messages exchanged over the IPC. Provides methods for encoding
    and decoding to/from strings.
    """

    def __init__(self, payload=b'', **extension_map):
        self.payload = payload
        self.extension_map = extension_map

    @classmethod
    def decode(cls, encoded_string):
        if encoded_string:
            try:
                data_map = json.loads(encoded_string)
            except (ValueError, TypeError) as e:
                runtime_logger.exception(e)
                raise ValueError('Could not load provided encoded string "{}" as JSON due to exception: {}'.format(
                    repr(encoded_string), str(e)
                ))

            try:
                payload = base64.b64decode(data_map['Payload'])
            except (ValueError, TypeError) as e:
                runtime_logger.exception(e)
                raise ValueError(
                    'Could not decode payload of Greengrass Message data'
                    '"{}" from base64 due to exception: {}'.format(repr(data_map), str(e))
                )

            extension_map = data_map['ExtensionMap_']
        else:
            payload = None
            extension_map = {}

        return cls(payload, **extension_map)

    def encode(self):
        try:
            # .decode to convert bytes -> string
            payload = base64.b64encode(self.payload).decode()
        except (ValueError, TypeError) as e:
            runtime_logger.exception(e)
            raise ValueError('Could not encode Greengrass Message payload "{}" as base64 due to exception: {}'.format(
                repr(self.payload), str(e)
            ))

        try:
            return json.dumps({'Payload': payload, 'ExtensionMap_': self.extension_map})
        except (ValueError, TypeError) as e:
            runtime_logger.exception(e)
            raise ValueError('Could not encode Greengrass Message fields "{}" as JSON due to exception: {}'.format(
                str(self), str(e)
            ))

    def __str__(self):
        return str({'Payload': self.payload, 'ExtensionMap_': self.extension_map})
