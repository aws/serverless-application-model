"""

Hello world example for AWS WorkMail

Parameters
----------
event: dict, required
    AWS WorkMail Message Summary Input Format
    For more information, see https://docs.aws.amazon.com/workmail/latest/adminguide/lambda.html  

    {
        "summaryVersion": "2018-10-10",                              # AWS WorkMail Message Summary Version
        "envelope": {
            "mailFrom" : {
                "address" : "from@domain.test"                       # String containing from email address
            },
            "recipients" : [                                         # List of all recipient email addresses
               { "address" : "recipient1@domain.test" },
               { "address" : "recipient2@domain.test" }
            ]
        },
        "sender" : {
            "address" :  "sender@domain.test"                        # String containing sender email address
        },
        "subject" : "Hello From Amazon WorkMail!",                   # String containing email subject (Truncated to first 256 chars)"
        "truncated": false                                           # boolean indicating if any field in message was truncated due to size limitations
    }

context: object, required
    Lambda Context runtime methods and attributes

    Attributes
    ----------

    context.aws_request_id: str
         Lambda request ID
    context.client_context: object
         Additional context when invoked through AWS Mobile SDK
    context.function_name: str
         Lambda function name
    context.function_version: str
         Function version identifier
    context.get_remaining_time_in_millis: function
         Time in milliseconds before function times out
    context.identity:
         Cognito identity provider context when invoked through AWS Mobile SDK
    context.invoked_function_arn: str
         Function ARN
    context.log_group_name: str
         Cloudwatch Log group name
    context.log_stream_name: str
         Cloudwatch Log stream name
    context.memory_limit_in_mb: int
        Function memory

        https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

Returns
------
Nothing
"""
def lambda_handler(event, context):
    try:
        fromAddress = event['envelope']['mailFrom']['address']
        subject = event['subject']
        print(f"Received Email from {fromAddress} with Subject {subject}")

    except Exception as e:
        # Send some context about this error to Lambda Logs
        print(e)
        raise e

