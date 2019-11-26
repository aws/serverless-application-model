#
# Copyright 2010-2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import json
import logging
from datetime import datetime
from decimal import Decimal

from greengrasssdk import Lambda
from greengrass_common.env_vars import MY_FUNCTION_ARN, SECRETS_MANAGER_FUNCTION_ARN

# Log messages in the SDK are part of customer's log because they're helpful for debugging
# customer's lambdas. Since we configured the root logger to log to customer's log and set the
# propagate flag of this logger to True. The log messages submitted from this logger will be
# sent to the customer's local Cloudwatch handler.
customer_logger = logging.getLogger(__name__)
customer_logger.propagate = True

KEY_NAME_PAYLOAD = 'Payload'
KEY_NAME_STATUS = 'Status'
KEY_NAME_MESSAGE = 'Message'
KEY_NAME_SECRET_ID = 'SecretId'
KEY_NAME_VERSION_ID = 'VersionId'
KEY_NAME_VERSION_STAGE = 'VersionStage'
KEY_NAME_CREATED_DATE = "CreatedDate"


class SecretsManagerError(Exception):
    pass


class Client:
    def __init__(self):
        self.lambda_client = Lambda.Client()

    def get_secret_value(self, **kwargs):
        r"""
        Call secrets manager lambda to obtain the requested secret value.

        :Keyword Arguments:
            * *SecretId* (``string``) --
              [REQUIRED]
              Specifies the secret containing the version that you want to retrieve. You can specify either the
              Amazon Resource Name (ARN) or the friendly name of the secret.
            * *VersionId* (``string``) --
              Specifies the unique identifier of the version of the secret that you want to retrieve. If you
              specify this parameter then don't specify ``VersionStage`` . If you don't specify either a
              ``VersionStage`` or ``SecretVersionId`` then the default is to perform the operation on the version
              with the ``VersionStage`` value of ``AWSCURRENT`` .

              This value is typically a UUID-type value with 32 hexadecimal digits.
            * *VersionStage* (``string``) --
              Specifies the secret version that you want to retrieve by the staging label attached to the
              version.

              Staging labels are used to keep track of different versions during the rotation process. If you
              use this parameter then don't specify ``SecretVersionId`` . If you don't specify either a
              ``VersionStage`` or ``SecretVersionId`` , then the default is to perform the operation on the
              version with the ``VersionStage`` value of ``AWSCURRENT`` .

        :returns: (``dict``) --
            * *ARN* (``string``) --
              The ARN of the secret.
            * *Name* (``string``) --
              The friendly name of the secret.
            * *VersionId* (``string``) --
              The unique identifier of this version of the secret.
            * *SecretBinary* (``bytes``) --
              The decrypted part of the protected secret information that was originally provided as
              binary data in the form of a byte array. The response parameter represents the binary data
              as a base64-encoded string.

              This parameter is not used if the secret is created by the Secrets Manager console.

              If you store custom information in this field of the secret, then you must code your Lambda
              rotation function to parse and interpret whatever you store in the ``SecretString`` or
              ``SecretBinary`` fields.
            * *SecretString* (``string``) --
              The decrypted part of the protected secret information that was originally provided as a
              string.

              If you create this secret by using the Secrets Manager console then only the ``SecretString``
              parameter contains data. Secrets Manager stores the information as a JSON structure of
              key/value pairs that the Lambda rotation function knows how to parse.

              If you store custom information in the secret by using the CreateSecret , UpdateSecret , or
              PutSecretValue API operations instead of the Secrets Manager console, or by using the
              *Other secret type* in the console, then you must code your Lambda rotation function to
              parse and interpret those values.
            * *VersionStages* (``list``) --
              A list of all of the staging labels currently attached to this version of the secret.
              * (``string``) --
            * *CreatedDate* (``datetime``) --
              The date and time that this version of the secret was created.
        """

        secret_id = self._get_required_parameter(KEY_NAME_SECRET_ID, **kwargs)
        version_id = kwargs.get(KEY_NAME_VERSION_ID, '')
        version_stage = kwargs.get(KEY_NAME_VERSION_STAGE, '')

        if version_id:  # TODO: Remove this once we support query by VersionId
            raise SecretsManagerError('Query by VersionId is not yet supported')
        if version_id and version_stage:
            raise ValueError('VersionId and VersionStage cannot both be specified at the same time')

        request_payload_bytes = self._generate_request_payload_bytes(secret_id=secret_id,
                                                                     version_id=version_id,
                                                                     version_stage=version_stage)

        customer_logger.debug('Retrieving secret value with id "{}", version id "{}"  version stage "{}"'
                              .format(secret_id, version_id, version_stage))
        response = self.lambda_client._invoke_internal(
            SECRETS_MANAGER_FUNCTION_ARN,
            request_payload_bytes,
            b'',  # We do not need client context for Secrets Manager back-end lambda
        )  # Use Request/Response here as we are mimicking boto3 Http APIs for SecretsManagerService

        payload = response[KEY_NAME_PAYLOAD].read()
        payload_dict = json.loads(payload.decode('utf-8'))

        # All customer facing errors are presented within the response payload. For example:
        # {
        #     "code": 404,
        #     "message": "Resource not found"
        # }
        if KEY_NAME_STATUS in payload_dict and KEY_NAME_MESSAGE in payload_dict:
            raise SecretsManagerError('Request for secret value returned error code {} with message {}'.format(
                payload_dict[KEY_NAME_STATUS], payload_dict[KEY_NAME_MESSAGE]
            ))

        # Time is serialized as epoch timestamp (int) upon IPC routing. We need to deserialize it back to datetime object in Python
        payload_dict[KEY_NAME_CREATED_DATE] = datetime.fromtimestamp(
            # Cloud response contains timestamp in milliseconds while datetime.fromtimestamp is expecting seconds
            Decimal(payload_dict[KEY_NAME_CREATED_DATE]) / Decimal(1000)
        )

        return payload_dict

    def _generate_request_payload_bytes(self, secret_id, version_id, version_stage):
        request_payload = {
            KEY_NAME_SECRET_ID: secret_id,
        }
        if version_stage:
            request_payload[KEY_NAME_VERSION_STAGE] = version_stage

        # TODO: Add VersionId once we support query by VersionId

        # The allowed chars for secret id and version stage are strictly enforced when customers are configuring them
        # through Secrets Manager Service in the cloud:
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_CreateSecret.html#API_CreateSecret_RequestSyntax
        return json.dumps(request_payload).encode()

    @staticmethod
    def _get_required_parameter(parameter_name, **kwargs):
        if parameter_name not in kwargs:
            raise ValueError('Parameter "{parameter_name}" is a required parameter but was not provided.'.format(
                parameter_name=parameter_name
            ))
        return kwargs[parameter_name]
