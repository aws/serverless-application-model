'''
This function uses the LogicMonitor REST API to create LogicMonitor OpsNotes
for CloudWatch Events.
Once the Ops Notes have been created for monitored resources that have
associated events, you'll see them on all graphs for those resources.
Assuming you already have monitored AWS resources in LogicMonitor, you'll
need to perform the following steps:

Follow these steps to provision LogicMonitor API Tokens as environment
variables for the Lambda Function:

    1. Navigate to https://<your-account-name>.logicmonitor.com.

    2. Locate the Users & Roles section within the Settings Page.

    3. Identify an existing user or create a new existing user with
       permission to manage all devices. As a best practice, we recommend
       creating a designated API user for the integration.

    4. Create a set of API Tokens from the Manage User dialog for the
       user in step 3. Copy the Access Id and Access Key values for use
       n the next section.


To add your LogicMonitor API Tokens as environment variables, follow these
steps:

    1. Create or use an existing KMS Key
       http://docs.aws.amazon.com/kms/latest/developerguide/create-keys.html

    2. Click the "Enable Encryption Helpers" checkbox

    3. Paste the value of the Access Id in the API_ACCESS_ID environment
       variable and click encrypt.

    4. Paste the value of the Access Key in the API_ACCESS_KEY environment
       variable and click encrypt.

    5. Provide your LogicMonitor account name as the value of the
       ACCOUNT_NAME environment variable and click encrypt.


Follow these steps to configure CloudWatch Events Rules that will trigger
the Lambda Function:

    1. Create a CloudWatch Event Rule that matches the events you'd like
       to show up in your LogicMonitor account
       https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/
       WhatIsCloudWatchEvents.html

    2. Configure the rule to trigger this Lambda Function.


This code requires the upload of a zip to include the "requests" library.
Do no edit this in the lambda UI.
'''

from __future__ import print_function

import requests
import os
import hashlib
import base64
import time
import hmac
import json
import boto3
from base64 import b64decode

from six import string_types

print('Loading function')


# Use LogicMonitor's API to search for a monitored device given an ARN
def find_device_by_arn(args):
    device_info = lm_api("GET", "", "/device/devices",
                         "?filter=systemProperties.value:{}".format(
                             args['arn']),
                         args['account_name'], args['api_access_id'],
                         args['api_access_key'])
    if len(device_info['data']['items']) == 1:
        return device_info['data']['items'][0]
    else:
        return None


# Add a LogicMonitor OpsNote to a particular device, given the deviceId
# and the note / tags that should be included
def add_opsNote(args, device):
    data = {"scopes": [{"type": "device", "deviceId": device['id']}],
            "note": '{}: {}'.format(args['tag'], args['note']),
            "tags": [{"name": args['tag']}]}
    opsNote_response = lm_api("POST", json.dumps(data), "/setting/opsnotes",
                              "", args['account_name'], args['api_access_id'],
                              args['api_access_key'])
    return opsNote_response


# Generic helper fuction to abstract the interation with the LM API
# Handles generation of authentication header string and
# interfacing with the HTTPs endpoint
def lm_api(verb, data, resource, query, account_name, access_id, access_key):
    # generic definition for all lm RESTful resources
    url = ('https://{}.logicmonitor.com/santaba/rest{}{}'.format(account_name,
                                                                 resource,
                                                                 query))

    # Lets set the epoch so that it doesn't change between the
    # two locations we need to use it
    epoch = str(int(time.time() * 1000))

    # Time to start building the auth strings for our headers
    auth_contents = verb + epoch + data + resource
    digest = hmac.new(access_key, msg=auth_contents,
                      digestmod=hashlib.sha256).hexdigest()
    signature = base64.b64encode(digest)
    auth = 'LMv1 {}:{}:{}'.format(access_id, signature, epoch)

    # Abstract the calling of the http verb as we are already defining
    # it above. Make sure that we insert the customer Auth header
    response = getattr(requests, verb.lower())(url,
                                               data=data,
                                               headers={'Content-Type':
                                                        'application/json',
                                                        'Authorization': auth})

    # In the case that we have a 200 response we should have a
    # json response content. However let's verify to make sure
    if (response.status_code is requests.codes.ok and
            response.headers['Content-Type'] == "application/json"):
        return response.json()
    else:
        # Raise exception for bad status
        response.raise_for_status()
        # Return response content in the case of good status but
        # bad response header
        return response.text


# Decrypt value using KMS
def decrypt(text):
    kms = boto3.client("kms")
    response = kms.decrypt(CiphertextBlob=b64decode(text))
    return response["Plaintext"]


# Main event function
def lambda_handler(event, context):
    # Get LogicMonitor API keys / account name from environment variables,
    # where API keys are encrypted
    args = {}
    args['account_name'] = os.environ["ACCOUNT_NAME"]
    encrypted_id = os.environ["API_ACCESS_ID"]
    encrypted_key = os.environ["API_ACCESS_KEY"]

    # Decrypt LM API keys
    args['api_access_id'] = decrypt(encrypted_id)
    args['api_access_key'] = decrypt(encrypted_key).replace("'", "")

    # Define the OpsNote message content to the event detail object
    args['note'] = json.dumps(event['detail'], indent=4)

    # Define OpsNote tag as the type of event
    args['tag'] = event['detail-type']

    # For every resource listed for the event, identify the ARN, search
    # LogicMonitor using that ARN and add OpsNotes to any identified devices
    for resource in event['resources']:
        # Set ARN
        args['arn'] = resource
        # Search for LM devices by ARN
        device = find_device_by_arn(args)
        # If a device was found, add an OpsNote
        if device:
            print("Found device:")
            print(device)
            resp = add_opsNote(args, device)
            print("Added Ops Note:")
            print(resp)

        # Log note if a device was found for at least one ARN
        # in the event resources
        if device:
            print("Found at least one device and added Ops Notes")
            return resp

        # If no devices matched an ARN for the event resources,
        # look for devices matching ARNs in event details
        else:
            print("Could not find any devices with resource ARN " +
                  args['arn'] + "- checking event details...")
            # Identify ARN in event detail
            for key, value in event['detail'].iteritems():
                if isinstance(value, string_types):
                    if 'arn' in value:
                        args['arn'] = value
                        # Search for LM devices based on identified ARN
                        print("Found arn: {} - checking devices...".format(
                            args['arn']))
                        device = find_device_by_arn(args)
                        # If a device is found, add an OpsNote
                        if device:
                            print("Found device:")
                            print(device)
                            resp = add_opsNote(args, device)
                            print("Added Ops Note:")
                            print(resp)
                            return resp
            # If no devices are found, note that no monitored devices matched
            # the ARNs recorded for the event
            print("Could not find any devices with ARNs in event detail")
            print("Exiting")
            return
