# cors-multiple-origin

*Example of Multiple-Origin CORS using API Gateway and Lambda*

[Cross-Origin Resource Sharing (CORS) - MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)

### Local development

First, [set up the SAM CLI](https://github.com/awslabs/aws-sam-cli#installation).

Now, test the application locally using:

`sam local start-api`

Note that there was an [issue](https://github.com/awslabs/aws-sam-cli/issues/400) that prevented OPTIONS requests from being handled when running with the SAM CLI version 0.3.0. This does not occur when the application is deployed.

Run the tests:

`npm install`

`npm test`

### Deploying

```bash
sam package \
    --template-file template.yaml \
    --output-template-file packaged.yaml \
    --s3-bucket $YOUR_BUCKET_NAME
```

```bash
sam deploy \
    --template-file packaged.yaml \
    --stack-name cors-multiple-origin \
    --capabilities CAPABILITY_IAM
```

### Getting the URL of the deployed instance

```bash
aws cloudformation describe-stacks \
    --stack-name cors-multiple-origin \
    --query 'Stacks[].Outputs'
```