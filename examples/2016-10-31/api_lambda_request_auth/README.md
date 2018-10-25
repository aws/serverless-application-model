# API Gateway + Lambda REQUEST Authorizer Example

This example shows you how to create an API Gateway API with a Lambda REQUEST Authorizer using SAM.

The Authorizer Lambda Function in this example simply accepts an `auth` query string with valid values `"allow"` and `"deny"`. See [Introducing custom authorizers in Amazon API Gateway](https://aws.amazon.com/blogs/compute/introducing-custom-authorizers-in-amazon-api-gateway/) for a more detailed example using JWT.

## Running the example

Optional: Uncomment the following lines in `template.yaml` to enable a publicly accessible endpoint:

```yaml
# Auth:
#   Authorizer: NONE
```

Deploy the example into your account:

```bash
# Replace YOUR_S3_ARTIFACTS_BUCKET with the name of a bucket which already exists in your account
aws cloudformation package --template-file template.yaml --output-template-file template.packaged.yaml --s3-bucket YOUR_S3_ARTIFACTS_BUCKET

aws cloudformation deploy --template-file ./template.packaged.yaml --stack-name sam-example-api-lambda-request-auth --capabilities CAPABILITY_IAM
```

Invoke the API's root endpoint `/` without an `auth` query string to see the API respond with a 200 (assuming you followed the optional step above). In the SAM template, we explicitly state `Authorizer: NONE` to make this a public/open endpoint (the Authorizer Lambda Function is not invoked).

```bash
api_url=$(aws cloudformation describe-stacks --stack-name sam-example-api-lambda-request-auth --query 'Stacks[].Outputs[?OutputKey==`ApiURL`].OutputValue' --output text)
curl $api_url
```

Invoke the API's `/users` endpoint without an `auth` query string to see a `401 {"message":"Unauthorized"}` response. Since we didn't specify an `auth` query string, API Gateway didn't even attempt to invoke our Authorizer Lambda Function.

```bash
curl $api_url"users"
```

Invoke the API's `/users` endpoint with an `auth=allow` query string to see a `200` response. Try changing the query string value to `"deny"` to see a `403` response and `"gibberish"` to see a `500` response.

```bash
curl $api_url"users?auth=allow"
```

## Additional resources

- https://aws.amazon.com/blogs/compute/introducing-custom-authorizers-in-amazon-api-gateway/
- https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html
