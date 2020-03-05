Globals Section
===============

.. contents::

Resources in a SAM template tend to have shared configuration such as Runtime, Memory, 
VPC Settings, Environment Variables, Cors, etc. Instead of duplicating this information in every resource, you can 
write them once in the ``Globals`` section and let all resources inherit it. 

Example:

.. code:: yaml

  Globals:
    Function:
      Runtime: nodejs6.10
      Timeout: 180
      Handler: index.handler
      Environment:
        Variables:
          TABLE_NAME: data-table
      
  Resources:
    HelloWorldFunction:
      Type: AWS::Serverless::Function
      Properties:
        Environment:
          Variables:
            MESSAGE: "Hello From SAM"

    ThumbnailFunction:
      Type: AWS::Serverless::Function
      Properties:
        Events:
          Thumbnail:
            Type: Api
            Properties:
              Path: /thumbnail
              Method: POST


In the above example, both ``HelloWorldFunction`` and ``ThumbnailFunction`` will use nodejs6.10 runtime, 180 seconds 
timeout and index.handler Handler. ``HelloWorldFunction`` adds MESSAGE environment variable in addition to the 
inherited TABLE_NAME. ``ThumbnailFunction`` inherits all the Globals properties and adds an API Event source.

Supported Resources and Properties
----------------------------------
Currently, the following resources and properties are being supported:

.. code:: yaml

  Globals:
    Function:
      # Properties of AWS::Serverless::Function
      Handler:
      Runtime:
      CodeUri: 
      DeadLetterQueue:
      Description:
      MemorySize:
      Timeout:
      VpcConfig:
      Environment:
      Tags:
      Tracing:
      KmsKeyArn:
      Layers:
      AutoPublishAlias:
      DeploymentPreference:
      PermissionsBoundary:
      ReservedConcurrentExecutions:
      EventInvokeConfig:

    Api:
      # Properties of AWS::Serverless::Api
      # Also works with Implicit APIs
      Auth:
      Name:
      DefinitionUri:
      CacheClusterEnabled:
      CacheClusterSize:
      Variables:
      EndpointConfiguration:
      MethodSettings:
      BinaryMediaTypes:
      MinimumCompressionSize:
      Cors:
      GatewayResponses:
      AccessLogSetting:
      CanarySetting:
      TracingEnabled:
      OpenApiVersion:
      Domain:

    HttpApi:
      # Properties of AWS::Serverless::HttpApi
      # Also works with Implicit APIs
      Auth:
      CorsConfiguration:
      AccessLogSettings:
      Tags:
      DefaultRouteSettings:
      RouteSettings:
      Domain:

    SimpleTable:
      # Properties of AWS::Serverless::SimpleTable
      SSESpecification:

Implicit APIs
~~~~~~~~~~~~~

APIs created by SAM when you have an API declared in the ``Events`` section are called "Implicit APIs". You can use 
Globals to override all properties of Implicit APIs as well. 

Unsupported Properties
~~~~~~~~~~~~~~~~~~~~~~

Following properties are **not** supported in Globals section. We made the explicit
call to not support them because it either made the template hard to understand or opened scope for potential security 
issues.

**AWS::Serverless::Function:**

* Role
* Policies
* FunctionName
* Events

**AWS::Serverless::Api:**

* StageName
* DefinitionBody

**AWS::Serverless::HttpApi:**

* StageName
* DefinitionBody
* DefinitionUri

Overridable
-----------

Properties declared in the Globals section can be overriden by the resource. For example, you can add new Variables
to environment variable map or override globally declared variables. But the resource **cannot** remove a property
specified in globals environment variables map. More generally, Globals declare properties shared by all your resources.
Some resources can provide new values for globally declared properties but cannot completely remove them. If some 
resources use a property but others do not, then you must not declare them in the Globals section.

Here is how overriding works for various data types:

Primitive Values are replaced
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*String, Number, Boolean etc*

Value specified in the resource will **replace** Global value

Example:

Runtime of ``MyFunction`` will be set to python3.6

.. code:: yaml

  Globals:
    Function:
      Runtime: nodejs4.3

  Resources:
    MyFunction:
      Type: AWS::Serverless::Function
      Properties:
        Runtime: python3.6

Maps are merged
~~~~~~~~~~~~~~~
*Maps are also known as dictionaries or collections of key/value pairs*

Map entries in the resource will be **merged** with global map entries. In case of duplicates the resource entry will override the global entry.

Example:

.. code:: yaml

  Globals:
    Function:
      Environment: 
        Variables:
          STAGE: Production
          TABLE_NAME: global-table

  Resources:
    MyFunction:
      Type: AWS::Serverless::Function
      Properties:
        Environment: 
          Variables:
            TABLE_NAME: resource-table
            NEW_VAR: hello

In the above example the environment variables of ``MyFunction`` will be set to:

.. code:: json

  {
    "STAGE": "Production", 
    "TABLE_NAME": "resource-table", 
    "NEW_VAR": "hello" 
  }

Lists are additive
~~~~~~~~~~~~~~~~~~~
*Lists are also known as arrays*

Global entries will be **prepended** to the list in the resource.

Example:

.. code:: yaml

  Globals:
    Function:
      VpcConfig:
        SecurityGroupIds:
          - sg-123
          - sg-456

  Resources:
    MyFunction:
      Type: AWS::Serverless::Function
      Properties:
        VpcConfig:
          SecurityGroupIds:
            - sg-first
 
In the above example the Security Group Ids of ``MyFunction``'s VPC Config will be set to:

.. code:: json

  [ "sg-123", "sg-456", "sg-first" ]
