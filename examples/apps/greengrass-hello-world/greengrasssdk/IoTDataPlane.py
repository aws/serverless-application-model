#
# Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import base64
import json
import logging

from greengrasssdk import Lambda
from greengrass_common.env_vars import SHADOW_FUNCTION_ARN, ROUTER_FUNCTION_ARN, MY_FUNCTION_ARN

# Log messages in the SDK are part of customer's log because they're helpful for debugging
# customer's lambdas. Since we configured the root logger to log to customer's log and set the
# propagate flag of this logger to True. The log messages submitted from this logger will be
# sent to the customer's local Cloudwatch handler.
customer_logger = logging.getLogger(__name__)
customer_logger.propagate = True


class ShadowError(Exception):
    pass


class Client:
    def __init__(self):
        self.lambda_client = Lambda.Client()

    def get_thing_shadow(self, **kwargs):
        r"""
        Call shadow lambda to obtain current shadow state.

        :Keyword Arguments:
            * *thingName* (``string``) --
              [REQUIRED]
              The name of the thing.

        :returns: (``dict``) --
        The output from the GetThingShadow operation
            * *payload* (``bytes``) --
              The state information, in JSON format.
        """
        thing_name = self._get_required_parameter('thingName', **kwargs)
        payload = b''

        return self._shadow_op('get', thing_name, payload)

    def update_thing_shadow(self, **kwargs):
        r"""
        Updates the thing shadow for the specified thing.

        :Keyword Arguments:
            * *thingName* (``string``) --
              [REQUIRED]
              The name of the thing.
            * *payload* (``bytes or seekable file-like object``) --
              [REQUIRED]
              The state information, in JSON format.

        :returns: (``dict``) --
        The output from the UpdateThingShadow operation
            * *payload* (``bytes``) --
              The state information, in JSON format.
        """
        thing_name = self._get_required_parameter('thingName', **kwargs)
        payload = self._get_required_parameter('payload', **kwargs)

        return self._shadow_op('update', thing_name, payload)

    def delete_thing_shadow(self, **kwargs):
        r"""
        Deletes the thing shadow for the specified thing.

        :Keyword Arguments:
            * *thingName* (``string``) --
              [REQUIRED]
              The name of the thing.

        :returns: (``dict``) --
        The output from the DeleteThingShadow operation
            * *payload* (``bytes``) --
              The state information, in JSON format.
        """
        thing_name = self._get_required_parameter('thingName', **kwargs)
        payload = b''

        return self._shadow_op('delete', thing_name, payload)

    def publish(self, **kwargs):
        r"""
        Publishes state information.

        :Keyword Arguments:
            * *topic* (``string``) --
              [REQUIRED]
              The name of the MQTT topic.
            * *payload* (``bytes or seekable file-like object``) --
              The state information, in JSON format.

        :returns: None
        """

        topic = self._get_required_parameter('topic', **kwargs)

        # payload is an optional parameter
        payload = kwargs.get('payload', b'')

        function_arn = ROUTER_FUNCTION_ARN
        client_context = {
            'custom': {
                'source': MY_FUNCTION_ARN,
                'subject': topic
            }
        }

        customer_logger.info('Publishing message on topic "{}" with Payload "{}"'.format(topic, payload))
        self.lambda_client._invoke_internal(
            function_arn,
            payload,
            base64.b64encode(json.dumps(client_context).encode())
        )

    def _get_required_parameter(self, parameter_name, **kwargs):
        if parameter_name not in kwargs:
            raise ValueError('Parameter "{parameter_name}" is a required parameter but was not provided.'.format(
                parameter_name=parameter_name
            ))
        return kwargs[parameter_name]

    def _shadow_op(self, op, thing_name, payload):
        topic = '$aws/things/{thing_name}/shadow/{op}'.format(thing_name=thing_name, op=op)
        function_arn = SHADOW_FUNCTION_ARN
        client_context = {
            'custom': {
                'subject': topic
            }
        }

        customer_logger.info('Calling shadow service on topic "{}" with payload "{}"'.format(topic, payload))
        response = self.lambda_client._invoke_internal(
            function_arn,
            payload,
            base64.b64encode(json.dumps(client_context).encode())
        )

        payload = response['Payload'].read()
        if response:
            response_payload_map = json.loads(payload.decode('utf-8'))
            if 'code' in response_payload_map and 'message' in response_payload_map:
                raise ShadowError('Request for shadow state returned error code {} with message "{}"'.format(
                    response_payload_map['code'], response_payload_map['message']
                ))

        return {'payload': payload}
