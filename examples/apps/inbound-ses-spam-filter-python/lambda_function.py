from __future__ import print_function

import boto3
import json
import os

from datetime import datetime

# Update the emailDomain environment variable to the correct domain, e.g. <MYDOMAIN>.com
EMAIL_DOMAIN = os.environ['emailDomain']


def print_with_timestamp(*args):
    print(datetime.utcnow().isoformat(), *args)


def lambda_handler(event, context):
    print_with_timestamp('Starting - inbound-ses-spam-filter')

    ses_notification = event['Records'][0]['ses']
    message_id = ses_notification['mail']['messageId']
    receipt = ses_notification['receipt']

    print_with_timestamp('Processing message:', message_id)

    # Check if any spam check failed
    if (receipt['spfVerdict']['status'] == 'FAIL' or
            receipt['dkimVerdict']['status'] == 'FAIL' or
            receipt['spamVerdict']['status'] == 'FAIL' or
            receipt['virusVerdict']['status'] == 'FAIL'):

        send_bounce_params = {
            'OriginalMessageId': message_id,
            'BounceSender': 'mailer-daemon@{}'.format(EMAIL_DOMAIN),
            'MessageDsn': {
                'ReportingMta': 'dns; {}'.format(EMAIL_DOMAIN),
                'ArrivalDate': datetime.now().isoformat()
            },
            'BouncedRecipientInfoList': []
        }

        for recipient in receipt['recipients']:
            send_bounce_params['BouncedRecipientInfoList'].append({
                'Recipient': recipient,
                'BounceType': 'ContentRejected'
            })

        print_with_timestamp('Bouncing message with parameters:')
        print_with_timestamp(json.dumps(send_bounce_params))

        try:
            ses_client = boto3.client('ses')
            bounceResponse = ses_client.send_bounce(**send_bounce_params)
            print_with_timestamp('Bounce for message ', message_id, ' sent, bounce message ID: ', bounceResponse['MessageId'])
            return {'disposition': 'stop_rule_set'}
        except Exception as e:
            print_with_timestamp(e)
            print_with_timestamp('An error occurred while sending bounce for message: ', message_id)
            raise e
    else:
        print_with_timestamp('Accepting message:', message_id)
