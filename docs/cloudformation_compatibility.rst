CloudFormation Compatibility Section
====================================

.. contents::

SAM is built ontop of CloudFormation Transforms. Therefore, we need to support different CloudFormation Capabilities like: Attributes, Intrinsic functions, etc.

CloudFormation Resources Attributes

======================== ========================
     Attribute Name             Supported?
======================== ========================
CreationPolicy           Not Currently
DeletionPolicy           Not Currently
DependsOn                `DependsOn Attribute`_
Metadata                 Not Currently
UpdatePolicy             Not Currently
======================== ========================

.. _DependsOn Attribute:

DependsOn Attribute:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: yaml

  LambdaFunction:
    DependsOn: SomeOtherResources
    Type: AWS::Serverless::Function
    ...

CloudFormation Intrinsic Funtions
---------------------------------
Currently, we do not support all Intrinsic Functions for all Property Values in `AWS::Serverless::*` resources but is fully available in other CloudFormation resources. Please see below tables for a details on which Intrinsic Functions can be used on a given field.

The Condition Function is not currently supported on any ``AWS::Serverless::*`` Resource type


AWS::Serverless::Function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

============================ ================================== ========================
     Property Name           Intrinsic(s) Supported            Reasons
============================ ================================== ========================
Handler                            All
Runtime                            All
CodeUri (String - S3Uri)          None                      SAM does not parse any Parameters, which is needed to support Ref
CodeUri (Bucket & Key)             All
FunctionName                       All
Description                        All
MemorySize                         All
Timeout                            All
Role                               All
Policies                           All
Environment                        All
VpcConfig                          All
Events                             All
Tags                               All
Tracing                            All
KmsKeyArn                          All
DeadLetterQueue                    All
DeploymentPreference               All
Layers                             All
AutoPublishAlias             Ref of a CloudFormation Parameter  Alias resources created by SAM uses a LocicalId <FunctionLogicalId+AliasName>. So SAM either needs a string for alias name, or a Ref to template Parameter that SAM can resolve into a string.
AutoPublishCodeSha256              All
ReservedConcurrentExecutions       All
EventInvokeConfig                  All
============================ ================================== ========================

Events Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cognito
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
======================== ================================== ========================
     Property Name        Intrinsic(s) Supported            Reasons
======================== ================================== ========================
UserPool                 Ref of a AWS::Cognito::UserPool    Properties in the AWS::Cognito::UserPool are used to construct different attributes.
Trigger                  All
======================== ================================== ========================

S3
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
======================== ================================== ========================
     Property Name        Intrinsic(s) Supported            Reasons
======================== ================================== ========================
Bucket                   All
Events                   All
Filter                   All
======================== ================================== ========================

SNS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
======================== ================================== ========================
     Property Name        Intrinsic(s) Supported            Reasons
======================== ================================== ========================
Topic                    All
======================== ================================== ========================

Kinesis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
======================== ================================== ========================
     Property Name        Intrinsic(s) Supported            Reasons
======================== ================================== ========================
Stream                   All
Queue                    All
StartingPosition         All
BatchSize                All
======================== ================================== ========================

DynamoDB
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
======================== ================================== ========================
     Property Name        Intrinsic(s) Supported            Reasons
======================== ================================== ========================
Stream                   All
StartingPosition         All
BatchSize                All
SSESpecification         All
======================== ================================== ========================

Api
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
======================== ======================================== ========================
     Property Name        Intrinsic(s) Supported                  Reasons
======================== ======================================== ========================
Path                     None
Method                   None
RestApiId                Ref of a AWS::Serverless::Api Resource   Properties in the AWS::Serverless::API are used to construct different attributes, policies, etc. SAM expects a Path and Method to exist as defined by the AWs::Serverless::API Resource definition
======================== ======================================== ========================

Schedule
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
======================== ================================== ========================
     Property Name        Intrinsic(s) Supported            Reasons
======================== ================================== ========================
Schedule                 All
Input                    All
Name                     All
Description              All
Enabled                  All
======================== ================================== ========================

CloudWatchEvent (superseded by EventBridgeRule, see below)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
======================== ================================== ========================
     Property Name        Intrinsic(s) Supported            Reasons
======================== ================================== ========================
Pattern                  All
Input                    All
InputPath                All
======================== ================================== ========================

EventBridgeRule
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
======================== ================================== ========================
     Property Name        Intrinsic(s) Supported            Reasons
======================== ================================== ========================
Pattern                  All
Input                    All
InputPath                All
======================== ================================== ========================

IotRule
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
======================== ================================== ========================
     Property Name        Intrinsic(s) Supported            Reasons
======================== ================================== ========================
Sql                      All
AwsIotSqlVersion         All
======================== ================================== ========================

AlexaSkill
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This event has no Properties


AWS::Serverless::Api
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

================================== ======================== ========================
     Property Name                 Intrinsic(s) Supported          Reasons
================================== ======================== ========================
Name                                All
StageName                           All
DefinitionUri (String - S3URI)      None                     SAM does not parse any Parameters, which is needed to support Ref
DefinitionUri (Bucket & Key)        All
DefinitionBody                      All
CacheClusterEnabled                 All
CacheClusterSize                    All
Variables                           All
EndpointConfiguration               All
MethodSettings                      All
BinaryMediaTypes                    All
MinimumCompressionSize              All
Cors                                All
TracingEnabled                      All
OpenApiVersion                      None
Domain                              All
================================== ======================== ========================


AWS::Serverless::Application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

================================== ======================== ========================
     Property Name                 Intrinsic(s) Supported          Reasons
================================== ======================== ========================
Location                            None                     SAM expects exact values for the Location property
Parameters                          All
NotificationARNs                    All
Tags                                All
TimeoutInMinutes                    All
================================== ======================== ========================


AWS::Serverless::SimpleTable
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

======================== ======================== ========================
     Property Name        Intrinsic(s) Supported          Reasons
======================== ======================== ========================
PrimaryKey               None
ProvisionedThroughput    All
TableName                All
Tags                     All
======================== ======================== ========================
