# SQS Event Source Example

Example SAM template for processing messages on an SQS queue.

## Running the example

```bash
# Set YOUR_S3_ARTIFACTS_BUCKET to a bucket you own
YOUR_S3_ARTIFACTS_BUCKET='YOUR_S3_ARTIFACTS_BUCKET'; \
aws cloudformation package --template-file template.yaml --output-template-file cfn-transformed-template.yaml --s3-bucket $YOUR_S3_ARTIFACTS_BUCKET
aws cloudformation deploy --template-file ./cfn-transformed-template.yaml --stack-name lambda-sqs-processor --capabilities CAPABILITY_IAM
```

After your CloudFormation Stack has completed creation, send a message to the SQS queue to see it in action:

```bash
YOUR_SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/my-queue; \
aws sqs send-message --queue-url $YOUR_SQS_QUEUE_URL --message-body '{ "myMessage": "Hello SAM!" }'
```