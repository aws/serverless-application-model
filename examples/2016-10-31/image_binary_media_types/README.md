# API Gateway + Lambda Content gitsHandling Example

This example shows you how to create an API Gateway API with a Lambda that returns image/png content using contentHandling

The Lambda Function in this example simply returns a png image when invoked on a public endpoint

## Running the example

Note: The following lines in `template.yaml` to enable a publicly accessible endpoint:

```yaml
Auth:
  Authorizer: NONE
```
Please add the appropriate auth mechanism to make it more secure.

Deploy the example into your account:

```bash
# Replace YOUR_S3_ARTIFACTS_BUCKET with the name of a bucket which already exists in your account
aws cloudformation package --template-file template.yaml --output-template-file template.packaged.yaml --s3-bucket YOUR_S3_ARTIFACTS_BUCKET

aws cloudformation deploy --template-file ./template.packaged.yaml --stack-name sam-example-api-lambda-image-content --capabilities CAPABILITY_IAM
```

Invoke the API's root endpoint `/none` to see the API respond with a 200 (assuming you followed the optional step above). You will find the response body contains a png file. In the SAM template, we explicitly state `Authorizer: NONE` to make this a public/open endpoint (the Authorizer Lambda Function is not invoked).

Make sure you set the client's request headers with "accept" : "image/png" to make this example work.

## Additional resources

- https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-payload-encodings-configure-with-control-service-api.html
- https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-payload-encodings-workflow.html
