## Lambda@Edge sample

This example leverages [SAM Safe Deployments feature](https://github.com/awslabs/serverless-application-model/blob/master/docs/safe_lambda_deployments.rst) in order to ease Lambda@Edge deployments by automatically publishing a new version upon deployments. Since SAM supports standard Cloudformation resources Cloudfront Distribution configuration will be automatically updated as soon as a new Lambda function version is available.

The following Lambda function snippet uses ``AutoPublishAlias`` property which provides an additional property named `<LogicalName>.Version`:

```yaml
LambdaEdgeFunctionSample:
    Type: AWS::Serverless::Function
    Properties:
        CodeUri: s3://<bucket>/lambda_edge.zip
        Runtime: nodejs6.10
        Handler: app.handler
        Timeout: 5
        # More info at https://github.com/awslabs/serverless-application-model/blob/master/docs/safe_lambda_deployments.rst
        AutoPublishAlias: live 
```

We can now configure our [Cloudfront Distribution Lambda Association Property](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-cloudfront-distribution-lambdafunctionassociation.html) to always reference the latest available Lambda Function Version ARN:

```yaml
CFDistribution:
    Type: AWS::CloudFront::Distribution
    Properties:
    DistributionConfig:
        Enabled: 'true'
        ....
        DefaultCacheBehavior:
        
        # Lambda@Edge configuration requires a function version not alias
        LambdaFunctionAssociations:
            - 
            EventType: origin-request
            # <SAM-Function.Version> provides {FunctionARN}:{Version} which is exactly what Cloudfront expects
            # SAM Benefit here is upon function changes this function version will also be updated in Cloudfront
            LambdaFunctionARN: !Ref LambdaEdgeFunctionSample.Version
        ...
```

In this example, ``LambdaEdgeFunctionSample.Version`` will be evaluated as ``arn:aws:lambda:<aws-region>:<aws-account-id>:function:<lambda-function-name>:<version>`` which is expected input for Lambda@Edge. 
