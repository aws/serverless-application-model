# cors-multiple-origin

*Example of Multiple-Origin CORS using API Gateway and Lambda*

[Cross-Origin Resource Sharing (CORS) - MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)

### Local development

First, [set up the SAM CLI](https://github.com/awslabs/aws-sam-cli#installation).

Now, test the application locally using:

`sam local start-api`

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