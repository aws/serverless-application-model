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
      Runtime: nodejs24.x
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


In the above example, both ``HelloWorldFunction`` and ``ThumbnailFunction`` will use nodejs24.x runtime, 180 seconds 
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
      PropagateTags:
      Tracing:
      KmsKeyArn:
      AutoPublishAlias:
      AutoPublishAliasAllProperties:
      Layers:
      DeploymentPreference:
      RolePath:
      PermissionsBoundary:
      ReservedConcurrentExecutions:
      ProvisionedConcurrencyConfig:
      AssumeRolePolicyDocument:
      EventInvokeConfig:
      FileSystemConfigs:
      CodeSigningConfigArn:
      Architectures:
      SnapStart:
      EphemeralStorage:
      FunctionUrlConfig:
      RuntimeManagementConfig:
      LoggingConfig:
      RecursiveLoop:
      SourceKMSKeyArn:
      TenancyConfig:
      DurableConfig:
      CapacityProviderConfig:
      FunctionScalingConfig:
      PublishToLatestPublished:
      VersionDeletionPolicy:

    Api:
      # Properties of AWS::Serverless::Api
      # Also works with Implicit APIs
      Auth:
      Name:
      DefinitionUri:
      CacheClusterEnabled:
      CacheClusterSize:
      MergeDefinitions:
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
      AlwaysDeploy:
      PropagateTags:
      SecurityPolicy:
      EndpointAccessMode:

    HttpApi:
      # Properties of AWS::Serverless::HttpApi
      # Also works with Implicit APIs
      Auth:
      AccessLogSettings:
      StageVariables:
      Tags:
      CorsConfiguration:
      DefaultRouteSettings:
      Domain:
      RouteSettings:
      FailOnWarnings:
      PropagateTags:

    SimpleTable:
      # Properties of AWS::Serverless::SimpleTable
      SSESpecification:

    StateMachine:
      # Properties of AWS::Serverless::StateMachine
      PropagateTags:

    LayerVersion:
      # Properties of AWS::Serverless::LayerVersion
      PublishLambdaVersion:

    CapacityProvider:
      # Properties of AWS::Serverless::CapacityProvider
      VpcConfig:
      OperatorRole:
      Tags:
      InstanceRequirements:
      ScalingConfig:
      KmsKeyArn:
      PropagateTags:
      ManagedResourceTags:

    WebSocketApi:
      # Properties of AWS::Serverless::WebSocketApi
      AccessLogSettings:
      ApiKeySelectionExpression:
      DefaultRouteSettings:
      DisableExecuteApiEndpoint:
      DisableSchemaValidation:
      Domain:
      FailOnWarnings:
      IpAddressType:
      PropagateTags:
      RouteSelectionExpression:
      RouteSettings:
      StageVariables:
      Tags:

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

Runtime of ``MyFunction`` will be set to python3.14

.. code:: yaml

  Globals:
    Function:
      Runtime: nodejs24.x

  Resources:
    MyFunction:
      Type: AWS::Serverless::Function
      Properties:
        Runtime: python3.14

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

Resource Properties with Custom Merge Strategy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Certain properties override the default list or map merge behavior described above.

**Replace** — resource value completely replaces global value (no concatenation):

- ``Function.Architectures``
- ``CapacityProvider.InstanceRequirements.Architectures``

.. code:: yaml

  Globals:
    Function:
      Architectures: [x86_64]

  Resources:
    MyFunction:
      Type: AWS::Serverless::Function
      Properties:
        Architectures: [arm64]
        # Result: [arm64] — not [x86_64, arm64]

**Prune and Merge** (``PRUNE_AND_MERGE``) — only keys declared in the resource survive; shared keys are deep-merged.
This prevents mutually exclusive properties from being merged together.

- ``CapacityProvider.ManagedResourceTags``

.. code:: yaml

  # Direction 1: Global sets Propagate, resource wants explicit Tags.
  Globals:
    CapacityProvider:
      ManagedResourceTags:
        Propagate: true

  Resources:
    MyCP:
      Type: AWS::Serverless::CapacityProvider
      Properties:
        ManagedResourceTags:
          Tags: {env: prod, app: svc}
          # Result: {Tags: {env: prod, app: svc}}
          # "Propagate" is dropped — not declared in resource.
          # Without prune-and-merge, the result would be
          # {Propagate: true, Tags: {env: prod, app: svc}}
          # which violates the mutual exclusivity rule.

.. code:: yaml

  # Direction 2: Global sets Tags, resource opts out entirely.
  Globals:
    CapacityProvider:
      ManagedResourceTags:
        Tags: {env: prod, team: plat}

  Resources:
    MyCP:
      Type: AWS::Serverless::CapacityProvider
      Properties:
        ManagedResourceTags:
          Propagate: false
          # Result: {Propagate: false} → PropagateTags Mode: "None"
          # Global "Tags" is dropped — resource only declared "Propagate".
          # The resource is explicitly opting out of tag propagation.

.. note::

   The prune-and-merge strategy applies symmetrically in both directions.
   Whichever keys the resource declares are the only ones that survive the merge.

   Contributors can register new per-property strategies in ``CUSTOM_STRATEGIES``
   in ``samtranslator/plugins/globals/globals.py``.
