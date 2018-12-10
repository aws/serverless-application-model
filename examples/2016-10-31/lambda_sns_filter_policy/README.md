# Lambda function + Filtered SNS Subscription Example

This example shows you how to create a Lambda function with a SNS event source. 

The Lambda function does not receive all messages published to the SNS topic but only a subset. The messages are filtered based on the attributes attached to
 the message.
 
## Running the example 

Deploy the example into your account:

```bash
# Replace YOUR_S3_ARTIFACTS_BUCKET with the name of a bucket which already exists in your account
aws cloudformation package --template-file template.yaml --output-template-file template.packaged.yaml --s3-bucket YOUR_S3_ARTIFACTS_BUCKET

aws cloudformation deploy --template-file ./template.packaged.yaml --stack-name sam-example-lambda-sns-filter-policy --capabilities CAPABILITY_IAM
```

The Lambda function will only receive messages with the attribute `sport` set to `football`.

In the AWS console go to the topic sam-example-lambda-sns-filter-policy and push the Publish to Topic button.
At the bottom of the Publish page you can add message attributes. Add one attribute:
- key: sport
- Attribute type: String
- value: football

Enter an arbitrary message body and publish the message.
In Cloudwatch the log group /aws/lambda/sam-example-lambda-sns-filter-policy-notification-logger appears and the logging contains the message attributes of 
the received message.

Now publish a couple of other messages with other values for the attribute `sport` or without the attribute `sport`. 
The Lambda function will not receive these messages.  

## Additional resources
https://docs.aws.amazon.com/sns/latest/dg/message-filtering.html