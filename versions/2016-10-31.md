# AWS Serverless Application Model (SAM)

#### Version 2016-10-31

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](http://www.ietf.org/rfc/rfc2119.txt).

The AWS Serverless Application Model (SAM) is licensed under [The Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0.html).

## Table of contents
* [Introduction](#introduction)
* [Specification](#specification)
  * [Format](#format)
  * [Example: AWS SAM template](#example-aws-sam-template)
  * [Globals Section](#globals-section)
  * [Resource types](#resource-types)
  * [Event source types](#event-source-types)
  * [Property types](#property-types)
  * [Data types](#data-types)
  * [Referable properties of SAM resources](#referable-properties-of-sam-resources)


## Introduction
NOTE: SAM specification documentation is in process of being migrated to official [AWS SAM docs](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) page, please take a look at the [SAM specification](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification.html) there.

[AWS SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification.html) is a model used to define serverless applications on AWS.

Serverless applications are applications composed of functions triggered by events. A typical serverless application consists of one or more AWS Lambda functions triggered by events such as object uploads to [Amazon S3](https://aws.amazon.com/s3), [Amazon SNS](https://aws.amazon.com/sns) notifications, and API actions. Those functions can stand alone or leverage other resources such as [Amazon DynamoDB](https://aws.amazon.com/dynamodb) tables or S3 buckets. The most basic serverless application is simply a function.

AWS SAM is based on [AWS CloudFormation](https://aws.amazon.com/cloudformation/). A serverless application is defined in a [CloudFormation template](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/gettingstarted.templatebasics.html) and deployed as a [CloudFormation stack](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/updating.stacks.walkthrough.html). An AWS SAM template is a CloudFormation template.

AWS SAM defines a set of objects which can be included in a CloudFormation template to describe common components of serverless applications easily.


## Specification

### Format

The files describing a serverless application in accordance with AWS SAM are [JSON](http://www.json.org/) or [YAML](http://yaml.org/spec/1.1/) formatted text files. These files are [CloudFormation templates](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-guide.html).

AWS SAM introduces several new resources and property types that can be embedded into the [Resources](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/resources-section-structure.html) section of the template. The templates may include all other template sections and use [CloudFormation intrinsic functions](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference.html) to access properties available only at runtime.

In order to include objects defined by AWS SAM within a CloudFormation template, the template must include a `Transform` section in the document root with a value of `AWS::Serverless-2016-10-31`.

 - [Resource types](#resource-types)
 - [Event source types](#event-source-types)
 - [Property types](#property-types)
 - [Globals Section](#globals-section)


### Example: AWS SAM template

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: 'AWS::Serverless-2016-10-31'
Resources:
  MyFunction:
    Type: 'AWS::Serverless::Function'
    Properties:
      Handler: index.handler
      Runtime: nodejs6.10
      CodeUri: 's3://my-bucket/function.zip'
```

All property names in AWS SAM are **case sensitive**.

### Globals Section
Globals is a section in your SAM template to define properties common to all your Serverless Function and APIs. All the `AWS::Serverless::Function` and
`AWS::Serverless::Api` resources will inherit the properties defined here.

Read the [Globals Guide](../docs/globals.rst) for more detailed information.

Example:

```yaml
Globals:
  Function:
    Runtime: nodejs6.10
    Timeout: 180
    Handler: index.handler
    Environment:
      Variables:
        TABLE_NAME: data-table
  Api:
    EndpointConfiguration: REGIONAL
    Cors: "'www.example.com'"
    Domain:
      DomainName: www.my-domain.com
      CertificateArn: my-valid-cert-arn
      EndpointConfiguration: EDGE

  SimpleTable:
    SSESpecification:
      SSEEnabled: true
```


### Resource types
 - [AWS::Serverless::Function](#awsserverlessfunction)
 - [AWS::Serverless::Api](#awsserverlessapi)
 - [AWS::Serverless::HttpApi](#awsserverlesshttpapi)
 - [AWS::Serverless::Application](#awsserverlessapplication)
 - [AWS::Serverless::SimpleTable](#awsserverlesssimpletable)
 - [AWS::Serverless::LayerVersion](#awsserverlesslayerversion)

#### AWS::Serverless::Function

Creates a Lambda function, IAM execution role, and event source mappings which trigger the function.

##### Properties

Property Name | Type | Description
---|:---:|---
Handler | `string` | **Required.** Function within your code that is called to begin execution.
Runtime | `string` | **Required.** The runtime environment.
CodeUri | `string` <span>&#124;</span> [S3 Location Object](#s3-location-object) | **Either CodeUri or InlineCode must be specified.** S3 Uri or location to the function code. The S3 object this Uri references MUST be a [Lambda deployment package](http://docs.aws.amazon.com/lambda/latest/dg/deployment-package-v2.html).
InlineCode | `string` | **Either CodeUri or InlineCode must be specified.** The inline code for the lambda.
FunctionName | `string` | A name for the function. If you don't specify a name, a unique name will be generated for you. [More Info](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-function.html#cfn-lambda-function-functionname)
Description | `string` | Description of the function.
MemorySize | `integer` | Size of the memory allocated per invocation of the function in MB. Defaults to 128.
Timeout | `integer` | Maximum time that the function can run before it is killed in seconds. Defaults to 3.
Role | `string` | ARN of an IAM role to use as this function's execution role. If omitted, a default role is created for this function.
AssumeRolePolicyDocument | [IAM policy document object](http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies.html) | AssumeRolePolicyDocument of the default created role for this function.
Policies | `string` <span>&#124;</span> List of `string` <span>&#124;</span> [IAM policy document object](http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies.html) <span>&#124;</span> List of [IAM policy document object](http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies.html) <span>&#124;</span> List of [SAM Policy Templates](../docs/policy_templates.rst) | Names of AWS managed IAM policies or IAM policy documents or SAM Policy Templates that this function needs, which should be appended to the default role for this function. If the Role property is set, this property has no meaning.
PermissionsBoundary | `string` | ARN of a permissions boundary to use for this function's execution role.
Environment | [Function environment object](#environment-object) | Configuration for the runtime environment.
VpcConfig | [VPC config object](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-lambda-function-vpcconfig.html) | Configuration to enable this function to access private resources within your VPC.
Events | Map of `string` to [Event source object](#event-source-object) | A map (string to [Event source object](#event-source-object)) that defines the events that trigger this function. Keys are limited to alphanumeric characters.
Tags | Map of `string` to `string` | A map (string to string) that specifies the tags to be added to this function. Keys and values are limited to alphanumeric characters. Keys can be 1 to 127 Unicode characters in length and cannot be prefixed with `aws:`. Values can be 1 to 255 Unicode characters in length. When the stack is created, SAM will automatically add a `lambda:createdBy:SAM` tag to this Lambda function. Tags will also be applied to default roles generated by the function.
Tracing | `string` | String that specifies the function's [X-Ray tracing mode](http://docs.aws.amazon.com/lambda/latest/dg/lambda-x-ray.html). Accepted values are `Active` and `PassThrough`
KmsKeyArn | `string` | The Amazon Resource Name (ARN) of an AWS Key Management Service (AWS KMS) key that Lambda uses to encrypt and decrypt your function's environment variables.
DeadLetterQueue | `map` <span>&#124;</span> [DeadLetterQueue Object](#deadletterqueue-object) | Configures SNS topic or SQS queue where Lambda sends events that it can't process.
DeploymentPreference | [DeploymentPreference Object](#deploymentpreference-object) | Settings to enable Safe Lambda Deployments. Read the [usage guide](../docs/safe_lambda_deployments.rst) for detailed information.
Layers | list of `string` | List of LayerVersion ARNs that should be used by this function. The order specified here is the order that they will be imported when running the Lambda function.
AutoPublishAlias | `string` | Name of the Alias. Read [AutoPublishAlias Guide](../docs/safe_lambda_deployments.rst#instant-traffic-shifting-using-lambda-aliases) for how it works
VersionDescription | `string` | A string that specifies the Description field which will be added on the new lambda version
ReservedConcurrentExecutions | `integer` | The maximum of concurrent executions you want to reserve for the function. For more information see [AWS Documentation on managing concurrency](https://docs.aws.amazon.com/lambda/latest/dg/concurrent-executions.html)
ProvisionedConcurrencyConfig | [ProvisionedConcurrencyConfig Object](#provisioned-concurrency-config-object) | Configure provisioned capacity for a number of concurrent executions on Lambda Alias property.
EventInvokeConfig | [EventInvokeConfig object](#event-invoke-config-object) | Configure options for [asynchronous invocation](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html) on the function.
Architectures | List of `string` | The CPU architecture to run on (x86_64 or arm64), accepts only one value. Defaults to x86_64.

##### Return values

###### Ref

When the logical ID of this resource is provided to the [Ref](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-ref.html) intrinsic function, it returns the resource name of the underlying Lambda function.

###### Fn::GetAtt

When the logical ID of this resource is provided to the [Fn::GetAtt](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-getatt.html) intrinsic function, it returns a value for a specified attribute of this type. This section lists the available attributes.

Attribute Name | Description
---|---
Arn | The ARN of the Lambda function.

###### Referencing Lambda Version & Alias resources

When you use `AutoPublishAlias` property, SAM will generate a Lambda Version and Alias resource for you. If you want to refer to these properties in an intrinsic function such as Ref or Fn::GetAtt, you can append `.Version` or `.Alias` suffix to the function's Logical ID. SAM will convert it to the correct Logical ID of the auto-generated Version or Alias resource respectively.

Example:

Assume the following Serverless Function

```yaml
Resources:
  MyLambdaFunction:
    Type: AWS::Serverless::Function
    Properties:
      ...
      AutoPublishAlias: live
      ...
```

Version can be referenced as:
```yaml
"Ref": "MyLambdaFunction.Version"
```

Alias can be referenced as:
```yaml
"Ref": "MyLambdaFunction.Alias"
```

This can be used with other intrinsic functions such as "Fn::GetAtt" or "Fn::Sub" or "Fn::Join" as well.

###### Example: AWS::Serverless::Function

```yaml
Handler: index.js
Runtime: nodejs6.10
CodeUri: 's3://my-code-bucket/my-function.zip'
Description: Creates thumbnails of uploaded images
MemorySize: 1024
Timeout: 15
Policies:
 - AWSLambdaExecute # Managed Policy
 - Version: '2012-10-17' # Policy Document
   Statement:
     - Effect: Allow
       Action:
         - s3:GetObject
         - s3:GetObjectACL
       Resource: 'arn:aws:s3:::my-bucket/*'
Environment:
  Variables:
    TABLE_NAME: my-table
Events:
  PhotoUpload:
    Type: S3
    Properties:
      Bucket: my-photo-bucket # bucket must be created in the same template
Tags:
  AppNameTag: ThumbnailApp
  DepartmentNameTag: ThumbnailDepartment
Layers:
  - !Sub arn:${AWS::Partition}:lambda:${AWS::Region}:123456789012:layer:MyLayer:1
```

#### AWS::Serverless::Api

Creates a collection of Amazon API Gateway resources and methods that can be invoked through HTTPS endpoints.

An `AWS::Serverless::Api` resource need not be explicitly added to a AWS Serverless Application Model template. A resource of this type is implicitly created from the union of [Api](#api) events defined on `AWS::Serverless::Function` resources defined in the template that do not refer to an `AWS::Serverless::Api` resource. An `AWS::Serverless::Api` resource should be used to define and document the API using [OpenAPI](https://github.com/OAI/OpenAPI-Specification), which provides more ability to configure the underlying Amazon API Gateway resources.

##### Properties

Property Name | Type | Description
---|:---:|---
Name | `string` | A name for the API Gateway RestApi resource.
StageName | `string` | **Required** The name of the stage, which API Gateway uses as the first path segment in the invoke Uniform Resource Identifier (URI).
DefinitionUri | `string` <span>&#124;</span> [S3 Location Object](#s3-location-object) | S3 URI or location to the OpenAPI document describing the API. If neither `DefinitionUri` nor `DefinitionBody` are specified, SAM will generate a `DefinitionBody` for you based on your template configuration. **Note** Intrinsic functions are not supported in external OpenAPI files, instead use DefinitionBody to define OpenAPI definition.
DefinitionBody | `JSON or YAML Object` | OpenAPI specification that describes your API. If neither `DefinitionUri` nor `DefinitionBody` are specified, SAM will generate a `DefinitionBody` for you based on your template configuration.
CacheClusterEnabled | `boolean` | Indicates whether cache clustering is enabled for the stage.
CacheClusterSize | `string` | The stage's cache cluster size.
Variables | Map of `string` to `string` | A map (string to string map) that defines the stage variables, where the variable name is the key and the variable value is the value. Variable names are limited to alphanumeric characters. Values must match the following regular expression: `[A-Za-z0-9._~:/?#&amp;=,-]+`.
MethodSettings | List of [CloudFormation MethodSettings property](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-apitgateway-stage-methodsetting.html) | Configures all settings for API stage including Logging, Metrics, CacheTTL, Throttling. This value is passed through to CloudFormation. So any values supported by CloudFormation ``MethodSettings`` property can be used here.
Tags | Map of `string` to `string` | A map (string to string) that specifies the tags to be added to this API Stage. Keys and values are limited to alphanumeric characters.
EndpointConfiguration | `string` or [API EndpointConfiguration Object](#api-endpointconfiguration-object) | Specify the type of endpoint for API endpoint. Specify the type as `REGIONAL` or `EDGE`. To use a `PRIVATE` endpoint, specify a dictionary with additional [API EndpointConfiguration Object](#api-endpointconfiguration-object). (See examples in [template.yaml](../examples/2016-10-31/api_endpointconfiguration/template.yaml))
BinaryMediaTypes | List of `string` |  List of MIME types that your API could return. Use this to enable binary support for APIs. Use `~1` instead of `/` in the mime types (See examples in [template.yaml](../examples/2016-10-31/implicit_api_settings/template.yaml)).
MinimumCompressionSize | `int` | Allow compression of response bodies based on client's Accept-Encoding header. Compression is triggered when response body size is greater than or equal to your configured threshold. The maximum body size threshold is 10 MB (10,485,760 Bytes). The following compression types are supported: gzip, deflate, and identity.
Cors | `string` or [Cors Configuration](#cors-configuration) | Enable CORS for all your APIs. Specify the domain to allow as a string or specify a dictionary with additional [Cors Configuration](#cors-configuration). NOTE: Cors requires SAM to modify your OpenAPI definition. Hence it works only inline OpenAPI defined with `DefinitionBody`.
Auth | [API Auth Object](#api-auth-object) | Auth configuration for this API. Define Lambda and Cognito `Authorizers` and specify a `DefaultAuthorizer` for this API. Can specify default ApiKey restriction using `ApiKeyRequired`. Also define `ResourcePolicy` and specify `CustomStatements` which is a list of policy statements that will be added to the resource policies on the API. To whitelist specific AWS accounts, add `AwsAccountWhitelist: [<list of account ids>]` under ResourcePolicy. Similarly, `AwsAccountBlacklist`, `IpRangeWhitelist`, `IpRangeBlacklist`, `SourceVpcWhitelist`, `SourceVpcBlacklist` are also supported.
GatewayResponses | Map of [Gateway Response Type](https://docs.aws.amazon.com/apigateway/api-reference/resource/gateway-response/) to [Gateway Response Object](#gateway-response-object) | Configures Gateway Reponses for an API. Gateway Responses are responses returned by API Gateway, either directly or through the use of Lambda Authorizers. Keys for this object are passed through to Api Gateway, so any value supported by `GatewayResponse.responseType` is supported here.
AccessLogSetting | [CloudFormation AccessLogSetting property](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-apigateway-stage-accesslogsetting.html) | Configures Access Log Setting for a stage. This value is passed through to CloudFormation, so any value supported by `AccessLogSetting` is supported here.
CanarySetting | [CloudFormation CanarySetting property](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-apigateway-stage-canarysetting.html) | Configure a Canary Setting to a Stage of a regular deployment. This value is passed through to Cloudformation, so any value supported by `CanarySetting` is supported here.
TracingEnabled | `boolean` | Indicates whether active tracing with X-Ray is enabled for the stage.
Models | `List of JSON or YAML objects` | JSON schemas that describes the models to be used by API methods.
Domain | [Domain Configuration Object](#domain-configuration-object) | Configuration settings for custom domains on API. Must contain `DomainName` and `CertificateArn`
OpenApiVersion | `string` | Version of OpenApi to use. This can either be `'2.0'` for the swagger spec or one of the OpenApi 3.0 versions, like `'3.0.1'`. Setting this property to any valid value will also remove the stage `Stage` that SAM creates.
Description | `string` | A description of the REST API resource.

##### Return values

###### Ref

When the logical ID of this resource is provided to the [Ref intrinsic function](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-ref.html), it returns the resource name of the underlying API Gateway RestApi.

##### Example: AWS::Serverless::Api

```yaml
StageName: prod
DefinitionUri: openapi.yml
```

###### Referencing generated resources - Stage & Deployment

SAM will generate an API Gateway Stage and API Gateway Deployment for every `AWS::Serverless::Api` resource. If you want to refer to these properties with the intrinsic function !Ref, you can append `.Stage` and `.Deployment` suffix to the API's Logical ID. SAM will convert it to the correct Logical ID of the auto-generated Stage or Deployment resource respectively.

#### AWS::Serverless::HttpApi

Creates a collection of Amazon API Gateway resources and methods that can be invoked through HTTPS endpoints.

An `AWS::Serverless::HttpApi` resource need not be explicitly added to a AWS Serverless Application Model template. A resource of this type is implicitly created from the union of [HttpApi](#httpapi) events defined on `AWS::Serverless::Function` resources defined in the template that do not refer to an `AWS::Serverless::HttpApi` resource. An `AWS::Serverless::HttpApi` resource should be used to define and document the API using OpenApi 3.0, which provides more ability to configure the underlying Amazon API Gateway resources.

For complete documentation about this new feature and examples, see the [HTTP API SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-resource-httpapi.html)

##### Properties

Property Name | Type | Description
---|:---:|---
StageName | `string` | The name of the API stage. If a name is not given, SAM will use the `$default` stage from Api Gateway.
DefinitionUri | `string` <span>&#124;</span> [S3 Location Object](#s3-location-object) | S3 URI or location to the Swagger document describing the API. If neither `DefinitionUri` nor `DefinitionBody` are specified, SAM will generate a `DefinitionBody` for you based on your template configuration. **Note** Intrinsic functions are not supported in external OpenApi files, instead use DefinitionBody to define OpenApi definition.
DefinitionBody | `JSON or YAML Object` | OpenApi specification that describes your API. If neither `DefinitionUri` nor `DefinitionBody` are specified, SAM will generate a `DefinitionBody` for you based on your template configuration.
Auth | [HTTP API Auth Object](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-property-httpapi-httpapiauth.html) | Configure authorization to control access to your API Gateway API.
Tags | Map of `string` to `string` | A map (string to string) that specifies the [tags](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-resource-tags.html) to be added to this HTTP API. When the stack is created, SAM will automatically add the following tag: `httpapi:createdBy: SAM`.
AccessLogSettings | [AccessLogSettings](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-apigatewayv2-stage-accesslogsettings.html) | Settings for logging access in a stage.
CorsConfiguration | `boolean` or [CorsConfiguration Object](#cors-configuration-object) | Enable CORS for all your Http APIs. Specify `true` for adding Cors with domain '*' to your Http APIs or specify a dictionary with additional [CorsConfiguration-Object](#cors-configuration-object). SAM adds `x-amazon-apigateway-cors` header in open api definition for your Http API when this property is defined. NOTE: Cors requires SAM to modify your OpenAPI definition. Hence it works only inline OpenAPI defined with `DefinitionBody`.
DefaultRouteSettings | [RouteSettings](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-apigatewayv2-stage-routesettings.html) | The default route settings for this HTTP API.
RouteSettings | [RouteSettings](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-apigatewayv2-stage-routesettings.html) | Per-route route settings for this HTTP API.
Domain | [Domain Configuration Object](#domain-configuration-object) | Configuration settings for custom domains on API. Must contain `DomainName` and `CertificateArn`
StageVariables | Map of `string` to `string` | A map that defines the stage variables for a Stage. Variable names can have alphanumeric and underscore characters, and the values must match [A-Za-z0-9-._~:/?#&=,]+.
FailOnWarnings | `boolean` | Specifies whether to rollback the API creation (true) or not (false) when a warning is encountered. The default value is false.
Description | `string` | A description of the HTTP API resource.

##### Return values

###### Ref

When the logical ID of this resource is provided to the [Ref intrinsic function](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-ref.html), it returns the resource name of the underlying API Gateway Api.

#### AWS::Serverless::Application

Embeds a serverless application from the [AWS Serverless Application Repository](https://serverlessrepo.aws.amazon.com/) or from an Amazon S3 bucket as a nested application. Nested applications are deployed as nested stacks, which can contain multiple other resources, including other `AWS::Serverless::Application` resources.

##### Properties

Property Name | Type | Description
---|:---:|---
Location | `string` or [Application Location Object](#application-location-object) | **Required** Template URL or location of nested application. If a template URL is given, it must follow the format specified in the [CloudFormation TemplateUrl documentation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-stack.html#cfn-cloudformation-stack-templateurl) and contain a valid CloudFormation or SAM template.
Parameters | Map of `string` to `string` | Application parameter values.
NotificationARNs | List of `string` |  A list of existing Amazon SNS topics where notifications about stack events are sent.
Tags | Map of `string` to `string` | A map (string to string) that specifies the [tags](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-resource-tags.html) to be added to this application. When the stack is created, SAM will automatically add the following tags: lambda:createdBy:SAM, serverlessrepo:applicationId:\<applicationId>, serverlessrepo:semanticVersion:\<semanticVersion>.
TimeoutInMinutes | `integer` | The length of time, in minutes, that AWS CloudFormation waits for the nested stack to reach the CREATE_COMPLETE state. The default is no timeout. When AWS CloudFormation detects that the nested stack has reached the CREATE_COMPLETE state, it marks the nested stack resource as CREATE_COMPLETE in the parent stack and resumes creating the parent stack. If the timeout period expires before the nested stack reaches CREATE_COMPLETE, AWS CloudFormation marks the nested stack as failed and rolls back both the nested stack and parent stack.

Other provided top-level resource attributes, e.g., Condition, DependsOn, etc, are automatically passed through to the underlying AWS::CloudFormation::Stack resource.


##### Return values

###### Ref

When the logical ID of this resource is provided to the [Ref intrinsic function](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-ref.html), it returns the resource name of the underlying CloudFormation nested stack.

###### Fn::GetAtt

When the logical ID of this resource is provided to the [Fn::GetAtt intrinsic function](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-getatt.html), it returns a value for a specified attribute of this type. This section lists the available attributes.

Attribute Name | Description
---|---
Outputs.*ApplicationOutputName* | The value of the stack output with name *ApplicationOutputName*.

##### Example: AWS::Serverless::Application

```yaml
Resources:
  MyApplication:
    Type: AWS::Serverless::Application
    Properties:
      Location:
        ApplicationId: 'arn:aws:serverlessrepo:us-east-1:012345678901:applications/my-application'
        SemanticVersion: 1.0.0
      Parameters:
        StringParameter: parameter-value
        IntegerParameter: 2
  MyOtherApplication:
    Type: AWS::Serverless::Application
    Properties:
      Location: https://s3.amazonaws.com/demo-bucket/template.yaml
Outputs:
  MyNestedApplicationOutput:
    Value: !GetAtt MyApplication.Outputs.ApplicationOutputName
    Description: Example nested application output
```

#### AWS::Serverless::SimpleTable

The `AWS::Serverless::SimpleTable` resource creates a DynamoDB table with a single attribute primary key. It is useful when data only needs to be accessed via a primary key. To use the more advanced functionality of DynamoDB, use an [AWS::DynamoDB::Table](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-dynamodb-table.html) resource instead.

##### Properties

Property Name | Type | Description
---|:---:|---
PrimaryKey | [Primary Key Object](#primary-key-object) | Attribute name and type to be used as the table's primary key. **This cannot be modified without replacing the resource.** Defaults to `String` attribute named `id`.
ProvisionedThroughput | [Provisioned Throughput Object](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-dynamodb-provisionedthroughput.html) | Read and write throughput provisioning information. If ProvisionedThroughput is not specified BillingMode will be specified as PAY_PER_REQUEST
Tags | Map of `string` to `string` | A map (string to string) that specifies the tags to be added to this table. Keys and values are limited to alphanumeric characters.
TableName | `string` | Name for the DynamoDB Table
SSESpecification | [DynamoDB SSESpecification](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-dynamodb-table-ssespecification.html) | Specifies the settings to enable server-side encryption.

##### Return values

###### Ref

When the logical ID of this resource is provided to the [Ref](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-ref.html) intrinsic function, it returns the resource name of the underlying DynamoDB table.

##### Example: AWS::Serverless::SimpleTable

```yaml
Properties:
  TableName: my-table
  PrimaryKey:
    Name: id
    Type: String
  ProvisionedThroughput:
    ReadCapacityUnits: 5
    WriteCapacityUnits: 5
  Tags:
    Department: Engineering
    AppType: Serverless
  SSESpecification:
    SSEEnabled: true
```

#### AWS::Serverless::LayerVersion

Creates a Lambda LayerVersion that contains library or runtime code needed by a Lambda Function. When a Serverless LayerVersion is transformed, SAM also transforms the logical id of the resource so that old LayerVersions are not automatically deleted by CloudFormation when the resource is updated.

Property Name | Type | Description
---|:---:|---
LayerName | `string` | Name of this layer. If you don't specify a name, the logical id of the resource will be used as the name.
Description | `string` | Description of this layer.
ContentUri | `string` <span>&#124;</span> [S3 Location Object](#s3-location-object) | **Required.** S3 Uri or location for the layer code.
CompatibleArchitectures | List of `string` | List or architectures compatibles with this LayerVersion.
CompatibleRuntimes | List of `string`| List of runtimes compatible with this LayerVersion.
LicenseInfo | `string` | Information about the license for this LayerVersion.
RetentionPolicy | `string` | Options are `Retain` and `Delete`. Defaults to `Retain`. When `Retain` is set, SAM adds `DeletionPolicy: Retain` to the transformed resource so CloudFormation does not delete old versions after an update.

##### Return values

###### Ref

When the logical ID of this resource is provided to the [Ref](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-ref.html) intrinsic function, it returns the resource ARN of the underlying Lambda LayerVersion.

##### Example: AWS::Serverless::LayerVersion

```yaml
Properties:
  LayerName: MyLayer
  Description: Layer description
  ContentUri: 's3://my-bucket/my-layer.zip'
  CompatibleRuntimes:
    - nodejs6.10
    - nodejs8.10
  LicenseInfo: 'Available under the MIT-0 license.'
  RetentionPolicy: Retain
```


### Event source types
 - [S3](#s3)
 - [SNS](#sns)
 - [Kinesis](#kinesis)
 - [MSK](#msk)
 - [DynamoDB](#dynamodb)
 - [SQS](#sqs)
 - [Api](#api)
 - [HttpApi](#httpapi)
 - [Schedule](#schedule)
 - [CloudWatchEvent](#cloudwatchevent)
 - [EventBridgeRule](#eventbridgerule)
 - [CloudWatchLogs](#cloudwatchlogs)
 - [IoTRule](#iotrule)
 - [AlexaSkill](#alexaskill)
 - [Cognito](#cognito)

#### S3

The object describing an event source with type `S3`.

##### Properties

Property Name | Type | Description
---|:---:|---
Bucket | `string` | **Required.** S3 bucket name.
Events | `string` <span>&#124;</span> List of `string` | **Required.** See [Amazon S3 supported event types](http://docs.aws.amazon.com/AmazonS3/latest/dev/NotificationHowTo.html#supported-notification-event-types) for valid values.
Filter | [Amazon S3 notification filter](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-notificationconfiguration-config-filter.html) | Rules to filter events on.

NOTE: To specify an S3 bucket as an event source for a Lambda function, both resources have to be declared in the same template. AWS SAM does not support specifying an existing bucket as an event source.

##### Example: S3 event source object

```yaml
Type: S3
Properties:
  Bucket: my-photo-bucket # bucket must be created in the same template
  Events: s3:ObjectCreated:*
  Filter:
    S3Key:
      Rules:
        - Name: prefix|suffix
          Value: my-prefix|my-suffix
```

#### SNS

The object describing an event source with type `SNS`.

##### Properties

Property Name | Type | Description
---|:---:|---
Topic | `string` | **Required.** Topic ARN.
Region | `string` | Region.
FilterPolicy | [Amazon SNS filter policy](https://docs.aws.amazon.com/sns/latest/dg/message-filtering.html) | Policy assigned to the topic subscription in order to receive only a subset of the messages.
SqsSubscription | `boolean` | Set to `true` to enable batching SNS topic notifications in an SQS queue.

##### Example: SNS event source object

```yaml
Type: SNS
Properties:
  Topic: arn:aws:sns:us-east-1:123456789012:my_topic
  FilterPolicy:
    store:
      - example_corp
    price_usd:
      - numeric:
          - ">="
          - 100
```

#### Kinesis

The object describing an event source with type `Kinesis`.

##### Properties

Property Name | Type | Description
---|:---:|---
Stream | `string` | **Required.** ARN of the Amazon Kinesis stream.
StartingPosition | `string` | **Required.** One of `TRIM_HORIZON` or `LATEST`.
BatchSize | `integer` | Maximum number of stream records to process per function invocation.
Enabled | `boolean` | Indicates whether Lambda begins polling the event source.
MaximumBatchingWindowInSeconds | `integer` | The maximum amount of time to gather records before invoking the function.
MaximumRetryAttempts | `integer` | The number of times to retry a record before it is bypassed. If an `OnFailure` destination is set, metadata describing the records will be sent to the destination. If no destination is set, the records will be bypassed
BisectBatchOnFunctionError | `boolean` | A boolean flag which determines whether a failed batch will be split in two after a failed invoke.
MaximumRecordAgeInSeconds | `integer` | The maximum age of a record that will be invoked by Lambda. If an `OnFailure` destination is set, metadata describing the records will be sent to the destination. If no destination is set, the records will be bypassed
DestinationConfig | [Destination Config Object](#destination-config-object) | Expired record metadata/retries and exhausted metadata is sent to this destination after they have passed the defined limits.
ParallelizationFactor | `integer` | Allocates multiple virtual shards, increasing the Lambda invokes by the given factor and speeding up the stream processing.
TumblingWindowInSeconds | `integer` |  Tumbling window (non-overlapping time window) duration to perform aggregations.
FunctionResponseTypes | `list` | Response types enabled for your function.

**NOTE:** `SQSSendMessagePolicy` or `SNSPublishMessagePolicy` needs to be added in `Policies` for publishing messages to the `SQS` or `SNS` resource mentioned in `OnFailure` property


##### Example: Kinesis event source object

```yaml
Type: Kinesis
Properties:
  Stream: arn:aws:kinesis:us-east-1:123456789012:stream/my-stream
  StartingPosition: TRIM_HORIZON
  BatchSize: 10
  MaximumBatchingWindowInSeconds: 10
  Enabled: true
  ParallelizationFactor: 8
  MaximumRetryAttempts: 100
  BisectBatchOnFunctionError: true
  MaximumRecordAgeInSeconds: 604800
  DestinationConfig:
    OnFailure:
      Type: SQS
      Destination: !GetAtt MySqsQueue.Arn
  TumblingWindowInSeconds: 0
  FunctionResponseTypes:
    - ReportBatchItemFailures
```


#### MSK

The object describing an event source with type `MSK`.

##### Properties

Property Name | Type | Description
---|:---:|---
Stream | `string` | **Required.** ARN of the Amazon MSK stream.
StartingPosition | `string` | **Required.** One of `TRIM_HORIZON` or `LATEST`.
Topics | `list` | **Required.** List of Topics created in the Amazon MSK Stream

##### Example: MSK event source object

```yaml
Type: MSK
Properties:
  Stream: arn:aws:kafka:us-west-2:123456789012:cluster/mycluster/6cc0432b-8618-4f44-bccc-e1fbd8fb7c4d-2
  StartingPosition: LATEST
  Topics:
    - "Topic1"
    - "Topic2"
```

#### DynamoDB

The object describing an event source with type `DynamoDB`.

##### Properties

Property Name | Type | Description
---|:---:|---
Stream | `string` | **Required.** ARN of the DynamoDB stream.
StartingPosition | `string` | **Required.** One of `TRIM_HORIZON` or `LATEST`.
BatchSize | `integer` | Maximum number of stream records to process per function invocation.
Enabled | `boolean` | Indicates whether Lambda begins polling the event source.
MaximumBatchingWindowInSeconds | `integer` | The maximum amount of time to gather records before invoking the function.
MaximumRetryAttempts | `integer` | The number of times to retry a record before it is bypassed. If an `OnFailure` destination is set, metadata describing the records will be sent to the destination. If no destination is set, the records will be bypassed
BisectBatchOnFunctionError | `boolean` | A boolean flag which determines whether a failed batch will be split in two after a failed invoke.
MaximumRecordAgeInSeconds | `integer` | The maximum age of a record that will be invoked by Lambda. If an `OnFailure` destination is set, metadata describing the records will be sent to the destination. If no destination is set, the records will be bypassed
DestinationConfig | [DestinationConfig Object](#destination-config-object) | Expired record metadata/retries and exhausted metadata is sent to this destination after they have passed the defined limits.
ParallelizationFactor | `integer` | Allocates multiple virtual shards, increasing the Lambda invokes by the given factor and speeding up the stream processing.
TumblingWindowInSeconds | `integer` |  Tumbling window (non-overlapping time window) duration to perform aggregations.
FunctionResponseTypes | `list` | Response types enabled for your function.

##### Example: DynamoDB event source object

```yaml
Type: DynamoDB
Properties:
  Stream: arn:aws:dynamodb:us-east-1:123456789012:table/TestTable/stream/2016-08-11T21:21:33.291
  StartingPosition: TRIM_HORIZON
  BatchSize: 10
  MaximumBatchingWindowInSeconds: 10
  Enabled: false
  ParallelizationFactor: 8
  MaximumRetryAttempts: 100
  BisectBatchOnFunctionError: true
  MaximumRecordAgeInSeconds: 86400
  DestinationConfig:
    OnFailure:
      Type: SQS
      Destination: !GetAtt MySqsQueue.Arn
  TumblingWindowInSeconds: 0
  FunctionResponseTypes
    - ReportBatchItemFailures
```

#### SQS

The object describing an event source with type `SQS`.

##### Properties

Property Name | Type | Description
---|:---:|---
Queue | `string` | **Required.** ARN of the SQS queue.
BatchSize | `integer` | Maximum number of messages to process per function invocation.
Enabled | `boolean` | Indicates whether Lambda begins polling the event source.

##### Example: SQS event source object

```yaml
Type: SQS
Properties:
  Queue: arn:aws:sqs:us-west-2:012345678901:my-queue
  BatchSize: 10
  Enabled: false
```

#### Destination Config Object

Expired record metatadata/retries exhausted metadata is sent to this destination after they have passed the defined limits.

##### Properties
Property Name | Type | Description
---|:---:|---
DestinationConfig | [OnFailure Object](#onfailure-object) | On failure all the messages get redirected to the given destination arn.

#### OnFailure Object
Property Name | Type | Description
---|:---:|---
Destination | `string` | Destination arn to redirect to either a SQS or a SNS resource
Type | `string` | This field accepts either `SQS` or `SNS` as input. This sets the required policies for sending or publishing messages to SQS or SNS resource on failure


##### Example
```yaml
  DestinationConfig:
    OnFailure:
      Type: SQS # or SNS. this is optional. If this is not added then `SQSSendMessagePolicy` or `SNSPublishMessagePolicy` needs to be added in `Policies` for publishing messages to the `SQS` or `SNS` resource mentioned in `OnFailure` property
      Destination: arn:aws:sqs:us-west-2:012345678901:my-queue # required
```

#### Api

The object describing an event source with type `Api`.

If an [AWS::Serverless::Api](#aws-serverless-api) resource is defined, the path and method values MUST correspond to an operation in the OpenAPI definition of the API. If no [AWS::Serverless::Api](#aws-serverless-api) is defined, the function input and output are a representation of the HTTP request and HTTP response. For example, using the JavaScript API, the status code and body of the response can be controlled by returning an object with the keys `statusCode` and `body`.

##### Properties

Property Name | Type | Description
---|:---:|---
Path | `string` | **Required.** Uri path for which this function is invoked. MUST start with `/`.
Method | `string` | **Required.** HTTP method for which this function is invoked.
RestApiId | `string` | Identifier of a RestApi resource which MUST contain an operation with the given path and method. Typically, this is set to [reference](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-ref.html) an `AWS::Serverless::Api` resource defined in this template. If not defined, a default `AWS::Serverless::Api` resource is created using a generated Swagger document containing a union of all paths and methods defined by `Api` events defined in this template that do not specify a RestApiId.
Auth | [Function Auth Object](#function-auth-object) | Auth configuration for this specific Api+Path+Method. Useful for overriding the API's `DefaultAuthorizer` setting auth config on an individual path when no `DefaultAuthorizer` is specified or overriding the default `ApiKeyRequired` setting.
RequestModel | [Function Request Model Object](#function-request-model-object) | Request model configuration for this specific Api+Path+Method.
RequestParameters | List of `string` <span>&#124;</span> List of [Function Request Parameter Object](#function-request-parameter-object) | Request parameters configuration for this specific Api+Path+Method. All parameter names must start with `method.request` and must be limited to `method.request.header`, `method.request.querystring`, or `method.request.path`. If a parameter is a `string` and NOT a [Function Request Parameter Object](#function-request-parameter-object) then `Required` and `Caching` will default to `False`.

##### Example: Api event source object

```yaml
Type: Api
Properties:
  Path: /photos
  Method: post
```

#### HttpApi

The object describing an event source with type `HttpApi`.

If an [AWS::Serverless::HttpApi](#aws-serverless-httpapi) resource is defined, the path and method values MUST correspond to an operation in the Swagger definition of the API. If no [AWS::Serverless::HttpApi](#aws-serverless-httpapi) is defined, the function input and output are a representation of the HTTP request and HTTP response. For example, using the JavaScript API, the status code and body of the response can be controlled by returning an object with the keys `statusCode` and `body`.

See the [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-property-function-httpapi.html) for full information about this feature.

##### Properties

Property Name | Type | Description
---|:---:|---
Path | `string` | Uri path for which this function is invoked. MUST start with `/`.
Method | `string` | HTTP method for which this function is invoked.
ApiId | `string` | Identifier of a HttpApi resource which MUST contain an operation with the given path and method. Typically, this is set to [reference](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-ref.html) an `AWS::Serverless::HttpApi` resource defined in this template. If not defined, a default `AWS::Serverless::HttpApi` resource is created using a generated OpenApi document contains a union of all paths and methods defined by `HttpApi` events defined in this template that do not specify an ApiId.
Auth | [Function Auth Object](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-property-function-httpapifunctionauth.html) | Auth configuration for this specific Api+Path+Method. Useful for overriding the API's `DefaultAuthorizer` setting auth config on an individual path when no `DefaultAuthorizer` is specified.
TimeoutInMillis | `int` | Custom timeout between 50 and 29,000 milliseconds. The default value is 5,000 milliseconds, or 5 seconds for HTTP APIs.
PayloadFormatVersion | `string` | Specify the format version of the payload sent to the Lambda HTTP API integration. If this field is not given, SAM defaults to "2.0".

##### Example: HttpApi event source object

```yaml
Type: HttpApi
Properties:
  Path: /photos
  Method: post
```

#### Schedule

The object describing an event source with type `Schedule`.

##### Properties

Property Name | Type | Description
---|:---:|---
Schedule | `string` | **Required.** Schedule expression, which MUST follow the [schedule expression syntax rules](http://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html).
Input | `string` | JSON-formatted string to pass to the function as the event body.
Name | `string` | A name for the Schedule. If you don't specify a name, a unique name will be generated.
Description | `string` | Description of Schedule.
Enabled | `boolean` | Indicated whether the Schedule is enabled.

##### Example: Schedule event source object

```yaml
Type: Schedule
Properties:
  Schedule: rate(5 minutes)
  Name: my-schedule
  Description: Example schedule
  Enabled: True
```

#### CloudWatchEvent

The object describing an event source with type `CloudWatchEvent`.

The CloudWatch Events service has been re-launched as Amazon EventBridge with full backwards compatibility. Please see the subsequent [EventBridgeRule](#eventbridgerule) section.

##### Properties

Property Name | Type | Description
---|:---:|---
Pattern | [Event Pattern Object](http://docs.aws.amazon.com/AmazonCloudWatch/latest/events/CloudWatchEventsandEventPatterns.html) | **Required.** Pattern describing which CloudWatch events trigger the function. Only matching events trigger the function.
EventBusName | `string` | The event bus to associate with this rule. If you omit this, the default event bus is used.
Input | `string` | JSON-formatted string to pass to the function as the event body. This value overrides the matched event.
InputPath | `string` | JSONPath describing the part of the event to pass to the function.

##### Example: CloudWatchEvent event source object

```yaml
Type: CloudWatchEvent
Properties:
  Pattern:
    detail:
      state:
        - terminated
```

#### EventBridgeRule

The object describing an event source with type `EventBridgeRule`.

##### Properties

Property Name | Type | Description
---|:---:|---
Pattern | [Event Pattern Object](https://docs.aws.amazon.com/eventbridge/latest/userguide/eventbridge-and-event-patterns.html) | **Required.** Pattern describing which EventBridge events trigger the function. Only matching events trigger the function.
EventBusName | `string` | The event bus to associate with this rule. If you omit this, the default event bus is used.
Input | `string` | JSON-formatted string to pass to the function as the event body. This value overrides the matched event.
InputPath | `string` | JSONPath describing the part of the event to pass to the function.

##### Example: EventBridge event source object

```yaml
Type: EventBridgeRule
Properties:
  Pattern:
    detail:
      state:
        - terminated
```

#### CloudWatchLogs

The object describing an event source with type `CloudWatchLogs`.

##### Properties

Property Name | Type | Description
---|:---:|---
LogGroupName | `string` | **Required.** Name of the CloudWatch Log Group from which to process logs.
FilterPattern | `string` | **Required.** A CloudWatch Logs [FilterPattern](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html) to specify which logs in the Log Group to process.

##### Example: CloudWatchLogs event source object

```yaml
Type: CloudWatchLogs
Properties:
  LogGroupName: MyLogGroup
  FilterPattern: Error
```

#### IoTRule

The object describing an event source with type `IoTRule`.

##### Properties

Property Name | Type | Description
---|:---:|---
Sql | `string` | **Required.** The SQL statement that queries the topic. For more information, see [Rules for AWS IoT](http://docs.aws.amazon.com/iot/latest/developerguide/iot-rules.html#aws-iot-sql-reference) in the *AWS IoT Developer Guide*.
AwsIotSqlVersion | `string` | The version of the SQL rules engine to use when evaluating the rule.

##### Example: IoTRule event source object

```yaml
Type: IoTRule
Properties:
  Sql: "SELECT * FROM 'iot/test'"
```

#### AlexaSkill

The object describing an event source with type `AlexaSkill`.

Specifying `AlexaSkill` event creates a resource policy that allows the Amazon Alexa service to call your Lambda function. To configure the Alexa service to work with your Lambda function, go to the Alexa Developer portal.

### Property types
 - [Environment object](#environment-object)
 - [Event source object](#event-source-object)
 - [Primary key object](#primary-key-object)

#### Environment object

The object describing the environment properties of a function.

##### Properties

Property Name | Type | Description
---|:---:|---
Variables | Map of `string` to `string` | A map (string to string map) that defines the environment variables, where the variable name is the key and the variable value is the value. Variable names are limited to alphanumeric characters and the first character must be a letter. Values are limited to alphanumeric characters and the following special characters `_(){}[]$*+-\/"#',;.@!?`.

##### Example: Environment object

```yaml
Variables:
  TABLE_NAME: my-table
  STAGE: prod
```

#### Cognito

The object describing an event source with type `Cognito`.

##### Properties

Property Name | Type | Description
---|:---:|---
UserPool | `string` | **Required.** Reference to UserPool in the same template
Trigger | `string` <span>&#124;</span> List of `string` | **Required.** See [Amazon S3 supported event types](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-cognito-userpool-lambdaconfig.html) for valid values.

NOTE: To specify a Cognito UserPool as an event source for a Lambda function, both resources have to be declared in the same template. AWS SAM does not support specifying an existing UserPool as an event source.

##### Example: Cognito event source object

```yaml
Type: Cognito
Properties:
  UserPool: Ref: MyUserPool
  Trigger: PreSignUp
```

#### Event source object

The object describing the source of events which trigger the function.

##### Properties

Property Name | Type | Description
---|:---:|---
Type | `string` | **Required.** Event type. Event source types include '[S3](#s3), '[SNS](#sns)', '[Kinesis](#kinesis)', '[MSK](#msk)', [DynamoDB](#dynamodb)', '[SQS](#sqs)', '[Api](#api)', '[Schedule](#schedule)', '[CloudWatchEvent](#cloudwatchevent)', '[CloudWatchLogs](#cloudwatchlogs)', '[IoTRule](#iotrule)', '[AlexaSkill](#alexaskill)'. For more information about the types, see [Event source types](#event-source-types).
Properties | * | **Required.** Object describing properties of this event mapping. Must conform to the defined `Type`. For more information about all types, see [Event source types](#event-source-types).

##### Example: Event source object

```yaml
Type: S3
Properties:
  Bucket: my-photo-bucket # bucket must be created in the same template
```

```yaml
Type: AlexaSkill
```

#### Provisioned Concurrency Config object

The object describing provisioned concurrency settings on a Lambda Alias

##### Properties
Property Name | Type | Description
---|:---:|---
ProvisionedConcurrentExecutions | `integer` | Number of concurrent executions to be provisioned for the Lambda function. Required parameter.

#### Event Invoke Config object

The object describing event invoke config on a Lambda function.

```yaml
  MyFunction:
    Type: 'AWS::Serverless::Function'
    Properties:
      EventInvokeConfig:
        MaximumEventAgeInSeconds: Integer (Min: 60, Max: 21600)
        MaximumRetryAttempts: Integer (Min: 0, Max: 2)
        DestinationConfig:
          OnSuccess:
            Type: [SQS | SNS | EventBridge | Function]
            Destination: ARN of [SQS | SNS | EventBridge | Function]
          OnFailure:
            Type: [SQS | SNS | EventBridge | Function]
            Destination: ARN of [SQS | SNS | EventBridge | Function]
```

##### Properties
Property Name | Type | Description
---|:---:|---
MaximumEventAgeInSeconds | `integer` | The maximum age of a request that Lambda sends to a function for processing. Optional parameter.
MaximumRetryAttempts | `integer` | The maximum number of times to retry when the function returns an error. Optional parameter.
DestinationConfig | [Destination Config Object](#event-invoke-destination-config-object) | A destination for events after they have been sent to a function for processing. Optional parameter.

#### Event Invoke Destination Config object
The object describing destination config for Event Invoke Config.

##### Properties
Property Name | Type | Description
---|:---:|---
OnSuccess | [Destination Config OnSuccess Object](#event-invoke-destination-config-destination-object) | A destination for events that succeeded processing.
OnFailure | [Destination Config OnFailure Object](#event-invoke-destination-config-destination-object) | A destination for events that failed processing.

#### Event Invoke Destination Config Destination object
The object describing destination config for Event Invoke Config.

##### Properties
Property Name | Type | Description
---|:---:|---
Type | `string` | Type of the Resource to be invoked. Values could be [SQS | SNS | EventBridge | Lambda]
Destination | `string` | ARN of the resource to be invoked. Fn::If and Ref is supported on this property.

The corresponding policies for the resource are generated in SAM.
Destination Property is required if Type is EventBridge and Lambda. If Type is SQS or SNS, and Destination is None, SAM auto creates these resources in the template.

##### Generated Resources
Property Name | Type | Alias to Ref the Auto-Created Resource
---|:---:|---
SQS | `AWS::SQS::Queue` | `<FunctionLogicalName>.DestinationQueue`
SNS | `AWS::SNS::Topic` | `<FunctionLogicalName>.DestinationTopic`

#### Primary key object

The object describing the properties of a primary key.

##### Properties

Property Name | Type | Description
---|:---:|---
Name | `string` | Attribute name of the primary key. Defaults to `id`.
Type | `string` | Attribute type of the primary key. MUST be one of `String`, `Number`, or `Binary`. Defaults to `String`.

##### Example: Primary key object

```yaml
Properties:
  PrimaryKey:
    Name: id
    Type: String
```

### Data Types

- [S3 Location Object](#s3-location-object)
- [Application Location Object](#application-id-object)
- [DeadLetterQueue Object](#deadletterqueue-object)
- [Cors Configuration](#cors-configuration)
- [API EndpointConfiguration Object](#api-endpointconfiguration-object)
- [API Auth Object](#api-auth-object)
- [Function Auth Object](#function-auth-object)
- [Function Request Model Object](#function-request-model-object)
- [Function Request Parameter Object](#function-request-parameter-object)
- [Gateway Response Object](#gateway-response-object)
- [CorsConfiguration Object](#cors-configuration-object)

#### S3 Location Object

Specifies the location of an S3 object as a dictionary containing `Bucket`, `Key`, and optional `Version` properties.

Example:

```yaml
CodeUri:
  Bucket: mybucket-name
  Key: code.zip
  Version: 121212
```

#### Application Location Object

Specifies the location of an application hosted in the [AWS Serverless Application Repository](https://aws.amazon.com/serverless/serverlessrepo/) as a dictionary containing ApplicationId and SemanticVersion properties.

Example:

```yaml
Location: # Both parameters are required
  ApplicationId: 'arn:aws:serverlessrepo:us-east-1:012345678901:applications/my-application'
  SemanticVersion: 1.0.0
```

#### DeadLetterQueue Object
Specifies an SQS queue or SNS topic that AWS Lambda (Lambda) sends events to when it can't process them. For more information about DLQ functionality, refer to the official documentation at http://docs.aws.amazon.com/lambda/latest/dg/dlq.html. SAM will automatically add appropriate permission to your Lambda function execution role to give Lambda service access to the resource. `sqs:SendMessage` will be added for SQS queues and `sns:Publish` for SNS topics.

Syntax:

```yaml
DeadLetterQueue:
  Type: `SQS` or `SNS`
  TargetArn: ARN of the SQS queue or SNS topic to use as DLQ.
```

#### DeploymentPreference Object
Specifies the configurations to enable Safe Lambda Deployments. Read the [usage guide](../docs/safe_lambda_deployments.rst) for detailed information. The following shows all available properties of this object.
TriggerConfigurations takes a list of [TriggerConfig](https://docs.aws.amazon.com/codedeploy/latest/APIReference/API_TriggerConfig.html) objects.

```yaml
DeploymentPreference:
  Enabled: True # Set to False to disable. Supports all intrinsics.
  Type: Linear10PercentEvery10Minutes
  Alarms:
    # A list of alarms that you want to monitor
    - !Ref AliasErrorMetricGreaterThanZeroAlarm
    - !Ref LatestVersionErrorMetricGreaterThanZeroAlarm
  Hooks:
    # Validation Lambda functions that are run before & after traffic shifting
    PreTraffic: !Ref PreTrafficLambdaFunction
    PostTraffic: !Ref PostTrafficLambdaFunction
  TriggerConfigurations:
    # A list of trigger configurations you want to associate with the deployment group. Used to notify an SNS topic on
    # lifecycle events.
    - TriggerEvents:
      # A list of events to trigger on.
      - DeploymentSuccess
      - DeploymentFailure
      TriggerName: TestTrigger
      TriggerTargetArn: !Ref MySNSTopic
```

#### Cors Configuration
Enable and configure CORS for the APIs. Enabling CORS will allow your API to be called from other domains. Assume your API is served from 'www.example.com' and you want to allow.

```yaml
Cors:
  AllowMethods: Optional. String containing the HTTP methods to allow.
  # For example, "'GET,POST,DELETE'". If you omit this property, then SAM will automatically allow all the methods configured for each API.
  # Checkout [HTTP Spec](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Methods) more details on the value.

  AllowHeaders: Optional. String of headers to allow.
  # For example, "'X-Forwarded-For'". Checkout [HTTP Spec](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Headers) for more details on the value

  AllowOrigin: Required. String of origin to allow.
  # For example, "'www.example.com'". Checkout [HTTP Spec](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Origin) for more details on this value.

  MaxAge: Optional. String containing the number of seconds to cache CORS Preflight request.
  # For example, "'600'" will cache request for 600 seconds. Checkout [HTTP Spec](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Max-Age) for more details on this value

  AllowCredentials: Optional. Boolean indicating whether request is allowed to contain credentials.
  # Header is omitted when false. Checkout [HTTP Spec](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Credentials) for more details on this value.
```

> NOTE: API Gateway requires literal values to be a quoted string, so don't forget the additional quotes in the  `Allow___` values. ie. "'www.example.com'" is correct whereas "www.example.com" is wrong.

#### API EndpointConfiguration Object

```yaml
EndpointConfiguration:
  Type: PRIVATE # OPTIONAL | Default value is REGIONAL. Accepted values are EDGE, REGIONAL, PRIVATE
  VPCEndpointIds: [<list of vpc endpoint ids>] # REQUIRED if Type is PRIVATE
```

#### API Auth Object

Configure Auth on APIs.


```yaml
Auth:
  ApiKeyRequired: true # OPTIONAL
  UsagePlan: # OPTIONAL
    CreateUsagePlan: PER_API # REQUIRED if UsagePlan property is set. accepted values: PER_API, SHARED, NONE
  DefaultAuthorizer: MyCognitoAuth # OPTIONAL, if you use IAM permissions, specify AWS_IAM.
  AddDefaultAuthorizerToCorsPreflight: false # OPTIONAL; Default: true
  ResourcePolicy:
    CustomStatements:
      - Effect: Allow
        Principal: *
        Action: execute-api:Invoke
        ...
    AwsAccountWhitelist: [<list of account ids>]
    AwsAccountBlacklist: [<list of account ids>]
    IpRangeWhitelist: [<list of ip ranges>]
    IpRangeBlacklist: [<list of ip ranges>]
    SourceVpcWhitelist: [<list of vpc/vpce endpoint ids>]
    SourceVpcBlacklist: [<list of vpc/vpce endpoint ids>]
  # For AWS_IAM:
  # DefaultAuthorizer: AWS_IAM
  # InvokeRole: NONE # CALLER_CREDENTIALS by default unless overridden
    Authorizers: [<list of authorizers, see below >]
```

**Authorizers:**
Define Lambda and Cognito `Authorizers` and specify a `DefaultAuthorizer`. If you use IAM permission, only specify `AWS_IAM` to a `DefaultAuthorizer`. For more information, see the documentation on [Lambda Authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html) and [Amazon Cognito User Pool Authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html) and [IAM Permissions](https://docs.aws.amazon.com/apigateway/latest/developerguide/permissions.html).
  
```yaml
Auth:
  Authorizers:
    MyCognitoAuth:
      UserPoolArn: !GetAtt MyCognitoUserPool.Arn # Can also accept an array
      AuthorizationScopes:
        - scope1 # List of authorization scopes
      Identity: # OPTIONAL
        Header: MyAuthorizationHeader # OPTIONAL; Default: 'Authorization'
        ValidationExpression: myauthvalidationexpression # OPTIONAL

    MyLambdaTokenAuth:
      FunctionPayloadType: TOKEN # OPTIONAL; Defaults to 'TOKEN' when `FunctionArn` is specified
      FunctionArn: !GetAtt MyAuthFunction.Arn
      FunctionInvokeRole: arn:aws:iam::123456789012:role/S3Access # OPTIONAL
      Identity:
        Header: MyCustomAuthHeader # OPTIONAL; Default: 'Authorization'
        ValidationExpression: mycustomauthexpression # OPTIONAL
        ReauthorizeEvery: 20 # OPTIONAL; Service Default: 300

    MyLambdaRequestAuth:
      FunctionPayloadType: REQUEST
      FunctionArn: !GetAtt MyAuthFunction.Arn
      FunctionInvokeRole: arn:aws:iam::123456789012:role/S3Access # OPTIONAL
      Identity:
        # Must specify at least one of Headers, QueryStrings, StageVariables, or Context
        Headers: # OPTIONAL
          - Authorization1
        QueryStrings: # OPTIONAL
          - Authorization2
        StageVariables: # OPTIONAL
          - Authorization3
        Context: # OPTIONAL
          - Authorization4
        ReauthorizeEvery: 0 # OPTIONAL; Service Default: 300
```

**ApiKey:** Configure ApiKey restriction for all methods and paths on an API.  This setting can be overriden on individual `AWS::Serverless::Function` using the [Function Auth Object](#function-auth-object).  Typically this would be used to require ApiKey on all methods and then override it on select methods that you want to be public.

```yaml
Auth:
  ApiKeyRequired: true
```

**ResourcePolicy:**
Configure Resource Policy for all methods and paths on an API. This setting can also be defined on individual `AWS::Serverless::Function` using the [Function Auth Object](#function-auth-object). This is required for APIs with `EndpointConfiguration: PRIVATE`.


```yaml
Auth:
  ResourcePolicy:
    CustomStatements: # Supports Ref and Fn::If conditions, does not work with AWS::NoValue in policy statements
      - Effect: Allow
        Principal: *
        Action: execute-api:Invoke
        ...
    AwsAccountWhitelist: [<list of account ids>] # Supports Ref
    AwsAccountBlacklist: [<list of account ids>] # Supports Ref
    IpRangeWhitelist: [<list of ip ranges>] # Supports Ref
    IpRangeBlacklist: [<list of ip ranges>] # Supports Ref
    SourceVpcWhitelist: [<list of vpc/vpce endpoint ids>] # Supports Ref
    SourceVpcBlacklist: [<list of vpc/vpce endpoint ids>] # Supports Ref

```

**UsagePlan:**
Create Usage Plan for API Auth. Usage Plans can be set in Globals level as well for RestApis. 
SAM creates a single Usage Plan, Api Key and Usage Plan Api Key resources if `CreateUsagePlan` is `SHARED` and a Usage Plan, Api Key and Usage Plan Api Key resources per Api when `CreateUsagePlan` is `PER_API`. 

```yaml
    Auth:
      UsagePlan:  
        CreateUsagePlan: PER_API # Required  supported values: SHARED | NONE | PER_API
```
#### Function Auth Object

Configure Auth for a specific Api+Path+Method.

```yaml
Auth:
  Authorizer: MyCognitoAuth # OPTIONAL, if you use IAM permissions in each functions, specify AWS_IAM.
  AuthorizationScopes: # OPTIONAL
    - scope1
    - scope2
```

If you have specified a Global Authorizer on the API and want to make a specific Function public, override with the following:

```yaml
Auth:
  Authorizer: 'NONE'
```

Require api keys for a specific Api+Path+Method.

```yaml
Auth:
  ApiKeyRequired: true
```

If you have specified `ApiKeyRequired: true` globally on the API and want to make a specific Function public, override with the following:

```yaml
Auth:
  ApiKeyRequired: false
```

#### Function Request Model Object

Configure Request Model for a specific Api+Path+Method.

```yaml
RequestModel:
  Model: User # REQUIRED; must match the name of a model defined in the Models property of the AWS::Serverless::API
  Required: true # OPTIONAL; boolean
```

#### Function Request Parameter Object

Configure Request Parameter for a specific Api+Path+Method.

```yaml
- method.request.header.Authorization:
    Required: true
    Caching: true
```

#### Gateway Response Object

Configure Gateway Responses on APIs. These are associated with the ID of a Gateway Response [response type][].
For more information, see the documentation on [`AWS::ApiGateway::GatewayResponse`][].

```yaml
GatewayResponses:
  UNAUTHORIZED:
    StatusCode: 401 # Even though this is the default value for UNAUTHORIZED.
    ResponseTemplates:
      "application/json": '{ "message": $context.error.messageString }'
    ResponseParameters:
      Paths:
        path-key: "'value'"
      QueryStrings:
        query-string-key: "'value'"
      Headers:
        Access-Control-Expose-Headers: "'WWW-Authenticate'"
        Access-Control-Allow-Origin: "'*'"
        WWW-Authenticate: >-
          'Bearer realm="admin"'
```

All properties of a Gateway Response object are optional. API Gateway has knowledge of default status codes to associate with Gateway Responses, so – for example – `StatusCode` is only used in order to override this value.

> NOTE: API Gateway spec allows values under the `ResponseParameters` and `ResponseTemplates` properties to be templates. In order to send constant values, don't forget the additional quotes. ie. "'WWW-Authenticate'" is correct whereas "WWW-Authenticate" is wrong.

[response type]: https://docs.aws.amazon.com/apigateway/api-reference/resource/gateway-response/
[`AWS::ApiGateway::GatewayResponse`]: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-apigateway-gatewayresponse.html

### Domain Configuration object
Enable custom domains to be configured with your Api. Currently only supports Creating Api gateway resources for custom domains.

```yaml
Domain:
  DomainName: String # REQUIRED | custom domain name being configured on the api, "www.example.com"
  CertificateArn: String # REQUIRED | Must be a valid [certificate ARN](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-certificatemanager-certificate.html), and for EDGE endpoint configuration the certificate must be in us-east-1
  EndpointConfiguration: "EDGE" # optional | Default value is REGIONAL | Accepted values are EDGE | REGIONAL
  BasePath:
    - String # optional | Default value is '/' | List of basepaths to be configured with the ApiGateway Domain Name
  Route53: # optional | Default behavior is to treat as None - does not create Route53 resources | Enable these settings to create Route53 Recordsets
    HostedZoneId: String # ONE OF `HostedZoneId`, `HostedZoneName` REQUIRED | Must be a hostedzoneid value of a [`AWS::Route53::HostedZone`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-route53-hostedzone.html) resource
    HostedZoneName: String # ONE OF `HostedZoneId`, `HostedZoneName` REQUIRED | Must be the `Name` of an [`AWS::Route53::HostedZone`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-route53-hostedzone.html) resource
    EvaluateTargetHealth: Boolean # optional | default value is false
    DistributionDomainName: String # OPTIONAL if the EndpointConfiguration is EDGE | Default points to Api Gateway Distribution | Domain name of a [cloudfront distribution](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-cloudfront-distribution.html)
    IpV6: Boolean # optional | default value is false
```

#### Cors Configuration Object
Enable and configure CORS for the HttpAPIs. Enabling CORS will allow your Http API to be called from other domains.
It set to `true` SAM adds '*' for the allowed origins.
When CorsConfiguration is set at property level and also in OpenApi, SAM merges them by overriding the header values in OpenApi with the `CorsConfiguration` property values
When intrinsic functions are used either set the CORS configuration as a property or define CORS in OpenApi definition.
Checkout [HTTPAPI Gateway Developer guide](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-cors.html) for more details on these values
```yaml
CorsConfiguration:
  AllowMethods: Optional. List containing the HTTP methods to allow for the HttpApi.  
  AllowHeaders: Optional. List of headers to allow. 
  AllowOrigins: Optional. List of origins to allow. 
  MaxAge: Optional. Integer containing the number of seconds to cache CORS Preflight request. 
  # For example, 600 will cache request for 600 seconds.
  AllowCredentials: Optional. Boolean indicating whether request is allowed to contain credentials.
  ExposeHeaders: Optional. List of allowed headers
```

##### Example
```yaml
    CorsConfiguration: #true
      AllowHeaders:
        - "*"
      AllowMethods:
        - "GET"
      AllowOrigins:
        - "https://www.example.com"
      ExposeHeaders:
        - "*"
```

### Referable properties of SAM resources
- [AWS::Serverless::Function](#referable-properties-of-serverless-function)
- [AWS::Serverless::Api](#referable-properties-of-serverless-RestApi)
- [AWS::Serverless::HttpApi](#referable-properties-of-serverless-HttpApi)

#### Referable properties of Serverless Function
Property Name | Reference | LogicalId | Description
---|:---:|---|---
Alias | `function-logical-id`.Alias | `function-logical-id`Alias`alias-name` | SAM generates an `AWS::Lambda::Alias` resource when `AutoPublishAlias` property is set. This resource can be referenced in intrinsic functions by using the resource logical ID or  `function-logical-id`.Alias
Version | `function-logical-id`.Version | `function-logical-id`Version`sha` | SAM generates an `AWS::Lambda::Version` resource when `AutoPublishAlias` property is set. This resource can be referenced in intrinsic functions by using the resource logical ID or  `function-logical-id`.Version
DestinationTopic | `function-logical-id`.DestinationTopic |`function-logical-id`EventInvokeConfig`OnSuccess/OnFailure`Topic| SAM auto creates an `AWS::SNS::Topic` resource when `Destination` property of `DestinationConfig` property in `EventInvokeConfig` property is not specified. This generated resource can be referenced by using `function-logical-id`.DestinationTopic
DestinationQueue | `function-logical-id`.DestinationQueue |`function-logical-id`EventInvokeConfig`OnSuccess/OnFailure`Queue | SAM auto creates an `AWS::SQS::Queue` resource when `Destination` property of `DestinationConfig` property in `EventInvokeConfig` property is not specified. This generated resource can be referenced by using `function-logical-id`.DestinationQueue

#### Referable properties of Serverless RestApi

Property Name | Reference | LogicalId | Description
---|:---:|---|---
Stage | `restapi-logical-id`.Stage | `restapi-logical-id` `StageName`Stage | SAM generates `AWS::ApiGateway::Stage` resource when `AWS::Serverless::Api` resource is defined. This resource can be referenced in intrinsic function using the resource logical id or `restapi-logical-id`.Stage
Deployment | `restapi-logical-id`.Deployment | `restapi-logical-id`Deployment`sha` | SAM generates `AWS::ApiGateway::Deployment` resource when `AWS::Serverless::Api` resource is defined. This resource can be referenced in intrinsic function using the resource logical id or `restapi-logical-id`.Deployment
DomainName | `restapi-logical-id`.DomainName | `domain-logical-id` | `AWS::ApiGateway::DomainName` resource can be referenced by using the resource logical id or `restapi-logical-id`.DomainName when `DomainName` resource is defined in `Domain` property of `AWS::Serverless::Api`
UsagePlan | `restapi-logical-id`.UsagePlan | `restapi-logical-id`UsagePlan | SAM generates UsagePlan, UsagePlanKey and ApiKey resources when `UsagePlan` property is set. UsagePlan resource can be referenced in intrinsic function using the resource logical id or `restapi-logical-id`.UsagePlan
UsagePlanKey | `restapi-logical-id`.UsagePlanKey |`restapi-logical-id`UsagePlanKey | SAM generates UsagePlan, UsagePlanKey and ApiKey resources when `UsagePlan` property is set. UsagePlanKey resource can be referenced in intrinsic function using the resource logical id or `restapi-logical-id`.UsagePlanKey
ApiKey | `restapi-logical-id`.ApiKey |`restapi-logical-id`ApiKey | SAM generates UsagePlan, UsagePlanKey and ApiKey resources when `UsagePlan` property is set. ApiKey resource can be referenced in intrinsic function using the resource logical id or `restapi-logical-id`.ApiKey
        
#### Referable properties of Serverless HttpApi

Property Name | Reference | LogicalId | Description
---|:---:|---|---
Stage | `httpapi-logical-id`.Stage | `httpapi-logical-id`ApiGatewayDefaultStage or `httpapi-logical-id` `StageName`Stage | SAM generates `AWS::ApiGatewayV2::Stage` resource with `httpapi-logical-id`ApiGatewayDefaultStage logical id if `StageName` property is not defined. If an explicit `StageName` property is defined them SAM generates `AWS::ApiGatewayV2::Stage` resource with `httpapi-logical-id` `StageName`Stage logicalId. This resource can be referenced in intrinsic functions using `httpapi-logical-id`.Stage
DomainName | `httpapi-logical-id`.DomainName | `domain-logical-id` | `AWS::ApiGatewayV2::DomainName` resource can be referenced by using the resource logical id or `restapi-logical-id`.DomainName when `DomainName` resource is defined in `Domain` property of `AWS::Serverless::Api`
