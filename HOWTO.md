## How to Guide
AWS Serverless Application Model (AWS SAM) allows you to easily create and 
manage resources used in your serverless application using AWS CloudFormation. 
This document explains how to write SAM templates and deploy them to 
AWS CloudFormation. 

## Writing SAM Template
Checkout the [latest specification](versions/2016-10-31.md) for details on how to write a SAM template

## Packing Artifacts (Manual)
Before you can deploy a SAM template, you should first upload your Lambda 
function code zip and API's OpenAPI File to S3. Set the `CodeUri` and 
`DefinitionUri` properties to the S3 URI of uploaded files. 
Now your template is ready to be deployed.

```
MyLambdaFunction:
    Type: AWS::Serverless::Function
    Properties:
        CodeUri: s3://<mybucket>/<my-zipfile-path>
        ...

MyApi:
    Type: AWS::Serverless::Api
    Properties:
        DefinitionUri: s3://<mybucket>/<my-openapi-file-path>
        ...
```

## Packing Artifacts (Automated)
`aws cloudformation package` [CLI command](http://docs.aws.amazon.com/cli/latest/reference/cloudformation/package.html) automates the above step by uploading 
local artifacts, such as source code or OpenAPI file, to S3 bucket. The command
returns a copy of your template, replacing references to local artifacts with S3 location 
where the command uploaded your artifacts. 

To use this command, set `CodeUri` property to be the path to your 
source code folder/zip/jar and `DefinitionUri` property to be a path to 
your OpenAPI file, as shown in the example below 

```
MyLambdaFunction:
    Type: AWS::Serverless::Function
    Properties:
        CodeUri: ./code
        ...

MyApi:
    Type: AWS::Serverless::Api
    Properties:
        DefinitionUri: ./specs/swagger.yaml
        ...
```

Run the following command to upload your artifacts to S3 and output a 
packaged template that can be readily deployed to CloudFormation.
```
aws cloudformation package \
    --template-file /path_to_template/template.json \
    --s3-bucket bucket-name \
    --output-template-file packaged-template.json
```


## Deploying to AWS CloudFormation
SAM template is deployed to AWS CloudFormation by [creating a changeset](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets-create.html) \
using the SAM template followed by [executing the changeset](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets-execute.html). Both the AWS Console
and AWS CLI provide commands to create and execute a changeset. 

Alternatively, you can use `aws cloudformation deploy` CLI command which 
will do the changeset operations for you. The command will also wait until the 
deployment completes and print debugging hints when the deployment fails. 
Refer to the [documentation](http://docs.aws.amazon.com/cli/latest/reference/cloudformation/deploy/index.html) for more details. Example usage:

```
aws cloudformation deploy \
    --template-file /path_to_template/packaged-template.json \
    --stack-name my-new-stack \
    --parameter-overrides Key1=Value1 Key2=Value2
```
