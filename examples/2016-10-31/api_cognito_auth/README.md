# API Gateway + Cognito Auth + Cognito Hosted Auth Example

This example shows you how to create an API Gateway API with a Cognito Authorizer using SAM.

## Running the example

Install the Node.js/NPM dependencies for your API's Lambda logic. This is necessary so that the dependencies get packaged up along with your Lambda function.

```bash
cd src && npm install && cd ..
```

Deploy the example into your account:

```bash
STACK_NAME=sam-example-api-cognito-auth
S3_BUCKET_NAME=YOUR_S3_ARTIFACTS_BUCKET

aws cloudformation package \
--template-file template.yaml \
--output-template-file template.packaged.yaml \
--s3-bucket $S3_BUCKET_NAME

aws cloudformation deploy \
--template-file ./template.packaged.yaml \
--stack-name $STACK_NAME \
--capabilities CAPABILITY_IAM
```

# TODO: remove
# bin/sam-translate.py deploy --template-file=examples/2016-10-31/api_cognito_auth/template.yaml --s3-bucket $S3_BUCKET_NAME --capabilities CAPABILITY_NAMED_IAM --stack-name $STACK_NAME

Get the Cognito User Pool Id and Api Url from Stack Outputs.

```bash
COGNITO_USER_POOL_ID=$(aws cloudformation describe-stacks \
--stack-name sam-example-api-cognito-auth \
--query 'Stacks[].Outputs[?OutputKey==`CognitoUserPoolId`].OutputValue' \
--output text)

API_URL=$(aws cloudformation describe-stacks \
--stack-name sam-example-api-cognito-auth \
--query 'Stacks[].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
--output text)
```

Cognito User Pools doesn't currently have CloudFormation support for configuring their Hosted Register/Signin UI. For now we will create these via the AWS CLI.

```bash
COGNITO_USER_POOL_CLIENT_NAME="ui-client"
COGNITO_USER_POOL_CALLBACK_URL=$API_URL
COGNITO_USER_POOL_LOGOUT_URL=$API_URL

COGNITO_USER_POOL_CLIENT_ID=$(aws cognito-idp create-user-pool-client \
--user-pool-id $COGNITO_USER_POOL_ID \
--client-name $COGNITO_USER_POOL_CLIENT_NAME \
--supported-identity-providers COGNITO \
--callback-urls "[\"$COGNITO_USER_POOL_CALLBACK_URL\"]" \
--logout-urls "[\"$COGNITO_USER_POOL_LOGOUT_URL\"]" \
--allowed-o-auth-flows code implicit \
--allowed-o-auth-scopes openid email \
--allowed-o-auth-flows-user-pool-client \
--query 'UserPoolClient.ClientId' \
--output text)

COGNITO_USER_POOL_TIMESTAMP_SUFFIX=$(date +%s)
COGNITO_USER_POOL_DOMAIN_PREFIX="my-company-$COGNITO_USER_POOL_TIMESTAMP_SUFFIX"

aws cognito-idp create-user-pool-domain \
--domain $COGNITO_USER_POOL_DOMAIN_PREFIX \
--user-pool-id $COGNITO_USER_POOL_ID
```

Finally, let's open the registration page created and hosted for you by Cognito in your browser. After the page loads, enter a Username and Password and click the Sign Up button.

```bash
open https://$COGNITO_USER_POOL_DOMAIN_PREFIX.auth.us-east-1.amazoncognito.com/signup?response_type=token&client_id=$COGNITO_USER_POOL_CLIENT_ID&redirect_uri=$COGNITO_USER_POOL_CALLBACK_URL

# The login page can be accessed here
# open https://$COGNITO_USER_POOL_DOMAIN_PREFIX.auth.us-east-1.amazoncognito.com/login?response_type=token&client_id=$COGNITO_USER_POOL_CLIENT_ID&redirect_uri=$COGNITO_USER_POOL_CALLBACK_URL
```

After clicking Sign Up, you will be redirected to the UI client for your API.

To access the API UI directly as an unauthorized user (who has access to `GET /users` and `GET /users/{userId}`) you can run `open $API_URL`.

## Additional resources

- https://aws.amazon.com/blogs/aws/launch-amazon-cognito-user-pools-general-availability-app-integration-and-federation/
- https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html
- https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-app-idp-settings.html
- https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-invoke-api-integrated-with-cognito-user-pool.html
- https://docs.aws.amazon.com/cognito/latest/developerguide/token-endpoint.html