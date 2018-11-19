# AWS WorkMail hello world

This is a hello world example of the WorkMail lambda feature. For more information see [AWS WorMail lambda documentation](https://docs.aws.amazon.com/workmail/latest/adminguide/lambda.html)

### Local development

First, [set up the SAM CLI](https://github.com/awslabs/aws-sam-cli/blob/develop/docs/installation.rst).

Now, test the application locally using:

`sam local invoke WorkMailHelloWorldFunction -e event.json`

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
 --stack-name workmail-hello-world \
 --capabilities CAPABILITY_IAM
```

### Configure WorkMail
Find the ARN of your new lambda function using:

```bash
aws cloudformation describe-stacks \
  --stack-name workmail-hello-world \
  --query 'Stacks[].Outputs[0].OutputValue'
```

Now you can go to WorkMail console and configure an outbound rule to use your new lambda.

