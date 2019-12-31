# API Gateway + Lambda REQUEST Authorizer Example

This example shows you how to configure Event Invoke Config on a function.

## Running the example

Replace the Destination Arns for SQS, SNS, EventBridge with valid arns. 
Deploy the example into your account:

```bash
$ sam deploy \
    --template-file /path_to_template/packaged-template.yaml \
    --stack-name my-new-stack \
    --capabilities CAPABILITY_IAM
```

## Additional resources

- https://aws.amazon.com/blogs/compute/introducing-aws-lambda-destinations/
