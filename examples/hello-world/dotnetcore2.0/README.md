# AWS SAM Hello World Example #

A simple AWS SAM template that specifies a single Lambda function.

## Usage ##

To create and deploy the SAM Hello World example, first ensure that you've met the requirements described in the "[Creating a Deployment Package](https://docs.aws.amazon.com/lambda/latest/dg/deployment-package-v2.html)" section of the AWS Lambda Developer Guide. Then follow the steps below.

### Build your package ###

    dotnet restore
    dotnet publish -o artifacts

### Test your application locally ###

Use [SAM CLI](https://github.com/awslabs/aws-sam-cli) to run your Lambda function locally:

    sam local invoke "HelloWorldFunction" -e event.json

### Package artifacts ###

Run the following command, replacing `BUCKET-NAME` with the name of your bucket:

    sam package --template-file template.yaml --output-template-file packaged-template.yaml --s3-bucket BUCKET-NAME

This uploads the code to the bucket and creates a new template file, `packaged-template.yaml`, that you will use to deploy your serverless application.

### Deploy using AWS CloudFormation ###

Run the following command, replacing `MY-NEW-STACK` with a name for your CloudFormation stack:

    sam deploy --template-file packaged-template.yaml --capabilities CAPABILITY_NAMED_IAM --stack-name MY-NEW-STACK

This creates and executes an AWS CloudFormation Change Set and waits until the deployment completes. Run the following command to view the resources created:

    aws cloudformation describe-stack-resources --stack-name MY-NEW-STACK

### Next Steps ###

You can also use AWS SAM CLI to create sample serverless apps that include Amazon API Gateway resources. For further details, see [Create a Simple App](https://docs.aws.amazon.com/lambda/latest/dg/serverless_app.html) in the AWS Lambda Developer Guide. To get started, run the following command:

    sam init --help
