# API Gateway + Cognito Auth + Cognito Hosted Auth Example

This example shows you how to create an API Gateway API with a Cognito Authorizer using SAM.

## Running the example

Install the Node.js/NPM dependencies for your API's Lambda logic into the `src/` directory. This is necessary so that the dependencies get packaged up along with your Lambda function.

```bash
npm install . --prefix ./src
```

Deploy the example into your account (replace `YOUR_S3_ARTIFACTS_BUCKET` with an existing S3 bucket to store your app assets):

```bash
# The following default values are also allowed: STACK_NAME, COGNITO_USER_POOL_CLIENT_NAME, COGNITO_USER_POOL_DOMAIN_PREFIX
S3_BUCKET_NAME=YOUR_S3_ARTIFACTS_BUCKET \
npm run package-deploy
```

Cognito User Pools doesn't currently have CloudFormation support for configuring their Hosted Register/Signin UI. For now we will create these via the AWS CLI:

```bash
npm run configure-cognito-user-pool
```

Open the registration page created and hosted for you by Cognito in your browser. After the page loads, enter a Username and Password and click the Sign Up button.

```bash
npm run open-signup-page

# Alternatively, you can open the login page by running `npm run open-login-page`
```

After clicking Sign Up, you will be redirected to the UI client for your API.

To access the API UI directly as an unauthorized user (who has access to `GET /users` and `GET /users/{userId}`) you can run `npm run open-api-ui`.

## Additional resources

- https://aws.amazon.com/blogs/aws/launch-amazon-cognito-user-pools-general-availability-app-integration-and-federation/
- https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html
- https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-app-idp-settings.html
- https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-invoke-api-integrated-with-cognito-user-pool.html
- https://docs.aws.amazon.com/cognito/latest/developerguide/token-endpoint.html