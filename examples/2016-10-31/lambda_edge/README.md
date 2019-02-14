## Lambda@Edge sample

This example leverages [SAM Safe Deployments feature](https://github.com/awslabs/serverless-application-model/blob/master/docs/safe_lambda_deployments.rst) in order to ease Lambda@Edge deployments by automatically publishing a new version upon deployments. Since SAM supports standard Cloudformation resources Cloudfront Distribution configuration will be automatically updated as soon as a new Lambda function version is available.

The following Lambda function snippet uses ``AutoPublishAlias`` property which provides an additional property named `<LogicalName>.Version`:

```yaml
LambdaEdgeFunctionSample:
    Type: AWS::Serverless::Function
    Properties:
        CodeUri: src/
        Runtime: nodejs6.10
        Handler: index.handler
        Role: !GetAtt LambdaEdgeFunctionRole.Arn
        Timeout: 5
        # More info at https://github.com/awslabs/serverless-application-model/blob/master/docs/safe_lambda_deployments.rst
        AutoPublishAlias: live 
```

We must also create a custom IAM Role which allows `lambda.amazonaws.com` and `edgelambda.amazonaws.com` services to assume the role and execute the function.

```yaml
LambdaEdgeFunctionRole:
    Type: "AWS::IAM::Role"
    Properties:
        Path: "/"
        ManagedPolicyArns:
            - "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        AssumeRolePolicyDocument:
          Version: "2012-10-17"
          Statement:
            - Sid: "AllowLambdaServiceToAssumeRole"
              Effect: "Allow"
              Action:
                - "sts:AssumeRole"
              Principal:
                Service:
                  - "lambda.amazonaws.com"
                  - "edgelambda.amazonaws.com"
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

### Deploying this sample

Before you go and deploy this it is important to note that Lambda@Edge expects your Lambda function to be deployed in N.**us-east-1** (N. Virginia) and therefore you must have both a S3 Bucket and this stack to be deployed in **us-east-1**.

```bash
aws cloudformation package \
    --template-file template.yaml \
    --output-template-file packaged.yaml \
    --s3-bucket S3_BUCKET_IN_US_EAST_1 \
    --region us-east-1

aws cloudformation deploy \
    --template-file packaged.yaml \
    --stack-name lambda-edge-sample2 \
    --capabilities CAPABILITY_IAM \
    --region us-east-1
```

If you don't have a S3 bucket in us-east-1 you can quickly create one and replace the placeholder in the command above:

```bash
aws s3 mb s3://S3-BUCKET-NAME --region us-east-1
```
