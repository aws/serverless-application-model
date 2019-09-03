# api_lambda_auth_cors

## About

This example shows how to configure a TOKEN Lambda Authorizer as the `DefaultAuthorizer` for an API with CORS enabled.

## Installation

1. Provide a bucket name and deploy the resources
    ```bash 
    S3_BUCKET_NAME=your-bucket-name-here \ 
    npm run package-deploy
    ```
1. Install the required NPM dependencies
    ```bash
    npm install
    ```
1. Start the web server
    ```bash
    npm run start
    ```
1. Open `http://localhost:8080` in a browser, click the button and an alert will appear with the lambda response

## Cleanup

1. `aws cloudformation delete-stack --stack-name authorizer-cors-example`
