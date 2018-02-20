from __future__ import print_function

import json
import urllib
import boto3

print('Loading message function...')


def send_to_sns(message, context):

    # This function receives JSON input with three fields: the ARN of an SNS topic,
    # a string with the subject of the message, and a string with the body of the message.
    # The message is then sent to the SNS topic.
    #
    # Example:
    #   {
    #       "topic": "arn:aws:sns:REGION:123456789012:MySNSTopic",
    #       "subject": "This is the subject of the message.",
    #       "message": "This is the body of the message."
    #   }

    sns = boto3.client('sns')
    sns.publish(
        TopicArn=message['topic'],
        Subject=message['subject'],
        Message=message['body']
    )

    return ('Sent a message to an Amazon SNS topic.')
