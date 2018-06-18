## Schedule example

### Overview

The `ScheduledFunction` is of type `AWS::Serverless::Function`. This is a Serverless Application Model (SAM) resource that expands into multiple (3) top-level CloudFormation resources:

- `AWS::Lambda::Function`
- `AWS::Lambda::Permission`
- `AWS::Events::Rule`

`AWS::Lambda::Function` is the top-level CloudFormation resource to define an Amazon Lambda function. Because we want to schedule the function’s periodic execution, we include an `Events` property on our `AWS::Serverless::Function` resource. This allows us to define the function execution schedule *within* the context of the function’s properties. Behind-the-scenes, the `Events` property expands into a `AWS::Events::Rule` resource with an invocation rate of once every 5 minutes.

Lastly, in order for the CloudWatch Events API to invoke our function, it needs permissions to do so. `AWS::Lambda::Permission` grants CloudWatch Events the permission to invoke our function.

### Deployment

The [AWS SAM CLI](https://github.com/awslabs/aws-sam-cli) builds on top of the SAM specification by providing a single tool to manage the packaging and deployment of serverless applications. Once the `sam` tool is installed, the application deployment process occurs in two phases.

First, use `sam` to upload the binary to S3 and reference it in a newly created `packaged.yaml` CloudFormation configuration.

```bash
$ sam package --s3-bucket test-global-config-us-east-1 \
              --template-file template.yaml \
              --output-template-file packaged.yaml
```

Before using `sam` to deploy using the contents of `packaged.yaml`, run a quick `diff` to see what changed.

```bash
$ diff template.yaml packaged.yaml
```

Lastly, use `sam` again to deploy the template through a CloudFormation stack named `Test`.

```bash
$ sam deploy --template-file packaged.yaml \
             --stack-name Test \
             --capabilities CAPABILITY_IAM
```
