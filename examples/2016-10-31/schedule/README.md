## Schedule example

### Overview

The `ScheduledFunction` is of type `AWS::Serverless::Function`. This is a Serverless Application Model (SAM) resource that expands into multiple (3) top-level CloudFormation resources:

- `AWS::Lambda::Function`
- `AWS::Lambda::Permission`
- `AWS::Events::Rule`

`AWS::Lambda::Function` is the top-level CloudFormation resource to define an Amazon Lambda function. Because we want to schedule the function’s periodic execution, we include an `Events` property on our `AWS::Serverless::Function` resource. This allows us to define the function execution schedule *within* the context of the function’s properties. Behind-the-scenes, the `Events` property expands into a `AWS::Events::Rule` resource with an invocation rate of once every 5 minutes.

Lastly, in order for the CloudWatch Events API to invoke our function, it needs permissions to do so. `AWS::Lambda::Permission` grants CloudWatch Events the permission to invoke our function.

### Deployment

The [AWS SAM CLI](https://github.com/awslabs/aws-sam-cli) lets you locally build, test, and debug serverless applications defined by AWS SAM templates. You can also use SAM CLI to deploy your applications. [Install SAM CLI](https://docs.aws.amazon.com/lambda/latest/dg/sam-cli-requirements.html), and then follow the [Packaging and Deployment instructions](https://docs.aws.amazon.com/lambda/latest/dg/serverless-deploy-wt.html#serverless-deploy) to deploy your application.
