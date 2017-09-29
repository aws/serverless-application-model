# How to create serverless applications using AWS SAM
AWS Serverless Application Model (AWS SAM) allows you to easily create and 
manage resources used in your serverless application using AWS CloudFormation. 
You can define your serverless application as a SAM template - a JSON or YAML 
configuration file that describes Lambda function, API endpoints and
other resources in your application. Using nifty commands, you upload this 
template to CloudFormation which creates all the individual resources and
groups them into a *CloudFormation Stack* for ease of management. 
When you update your SAM template, you will re-deploy the changes to 
this stack. AWS CloudFormation will take care of updating the individual
resources for you.


The remainder of document explains how to write SAM templates and 
deploy them via AWS CloudFormation. 

## Writing SAM Template
Checkout the [latest specification](versions/2016-10-31.md) for details on how to write a SAM template

## Packing Artifacts
Before you can deploy a SAM template, you should first upload your Lambda 
function code zip and API's OpenAPI File to S3. Set the `CodeUri` and 
`DefinitionUri` properties to the S3 URI of uploaded files. You
can choose to do this manually or use `aws cloudformation package` [CLI command](http://docs.aws.amazon.com/cli/latest/reference/cloudformation/package.html) to automate the task of uploading local artifacts to S3 bucket. The command returns a copy of your template, replacing references to local artifacts with S3 location where the command uploaded your artifacts. 

To use this command, set `CodeUri` property to be the path to your 
source code folder/zip/jar and `DefinitionUri` property to be a path to 
your OpenAPI file, as shown in the example below 

```YAML
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
```bash
$ aws cloudformation package \
    --template-file /path_to_template/template.yaml \
    --s3-bucket bucket-name \
    --output-template-file packaged-template.yaml
```

The packaged template will look something like this:
```YAML
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


## Deploying to AWS CloudFormation
SAM template is deployed to AWS CloudFormation by [creating a changeset](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets-create.html)
using the SAM template followed by [executing the changeset](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets-execute.html). 
Think of a ChangeSet as a diff between your current stack template and the new template that you are deploying. After you create a ChangeSet, you have the opportunity to examine the diff before executing it. Both the AWS Console and AWS CLI provide commands to create and execute a changeset. 

Alternatively, you can use `aws cloudformation deploy` CLI command to deploy the SAM template. Under-the-hood it creates and executes a changeset and waits until the deployment completes. It also prints debugging hints when the deployment fails. Run the following command to deploy the packaged template to a stack called `my-new-stack`:

```bash
$ aws cloudformation deploy \
    --template-file /path_to_template/packaged-template.yaml \
    --stack-name my-new-stack \
    --capabilities CAPABILITY_IAM
```

Refer to the [documentation](http://docs.aws.amazon.com/cli/latest/reference/cloudformation/deploy/index.html) for more details.

## Using Intrinsic Functions
CloudFormation provides handy functions you can use to generate values at runtime. These are called [Intrinsic Functions](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference.html). Since SAM is deployed using CloudFormation, you can use these intrinsic functions within SAM as well. Here are some examples:

#### Dynamically set S3 location of Lambda function code zip
```YAML
Transform: 'AWS::Serverless-2016-10-31'

# Parameters are CloudFormation features to pass input
# to your template when you create a stack
Parameters:
    BucketName:
        Type: String
    CodeKey:
        Type: String

Resources:
    MyFunction:
        Type: AWS::Serverless::Function
        Properties:
            Handler: index.handler
            Runtime: nodejs4.3
            CodeUri:
                # !Ref function allows you to fetch value 
                # of parameters and other resources at runtime
                Bucket: !Ref BucketName
                Key: !Ref CodeKey
```

#### Generate a different function name for each stack

```YAML
Transform: 'AWS::Serverless-2016-10-31'

# Parameters are CloudFormation features to pass input
# to your template when you create a stack
Parameters:
    FunctionNameSuffix:
        Type: String
    
Resources:
    MyFunction:
        Type: AWS::Serverless::Function
        Properties:

            # !Sub performs string substitution
            FunctionName: !Sub "mylambda-${FunctionNameSuffix}"

            Handler: index.handler
            Runtime: nodejs4.3
            CodeUri: s3://bucket/key
```

### Caveats:
#### ImportValue is partially supported
[`ImportValue`](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-importvalue.html) allows one stack to refer to value of properties from another stack. ImportValue is supported on most properties, except the very few that SAM needs to parse. Following properties are *not* supported:

- `RestApiId` of `AWS::Serverless::Function`
- `Policies` of `AWS::Serverless::Function`
- `StageName` of `AWS::Serverless::Api`








