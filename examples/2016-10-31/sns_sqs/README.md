# SNS-SQS Event Source Example

Example SAM template for processing messages on an SNS-SQS.

## Running the example

```bash
# Set YOUR_S3_ARTIFACTS_BUCKET to a bucket you own
YOUR_S3_ARTIFACTS_BUCKET='YOUR_S3_ARTIFACTS_BUCKET'; \
aws cloudformation package --template-file template.yaml --output-template-file cfn-transformed-template.yaml --s3-bucket $YOUR_S3_ARTIFACTS_BUCKET
aws cloudformation deploy --template-file ./cfn-transformed-template.yaml --stack-name lambda-sns-sqs-processor --capabilities CAPABILITY_IAM
```

After your CloudFormation Stack has completed creation, send a message to the SNS topic to see it in action:

```bash
YOUR_SNS_TOPIC_ARN=arn:aws:sns:us-east-1:[your_account_id]:[your_topic_name]; \
aws sqs send-message --target-arn $YOUR_SNS_TOPIC_ARN --message '{ "myMessage": "Hello SAM!" }'
```