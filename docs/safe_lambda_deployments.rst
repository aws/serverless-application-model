Safe Lambda deployments
=======================

.. contents::

Pushing to production can be nerve-wracking even if you have 100% unit test coverage and a state-of-art full CD system. 
It is a good practice to expose your new code to a small percentage of production traffic, run tests, watch for alarms 
and dial up traffic as you gain more confidence. The goal is to minimize production impact as much as possible. 

To enable traffic shifting deployments for Lambda functions, we will use Lambda Aliases, which can balance incoming 
traffic between two different versions of your function, based on preassigned weights. Before deployment, 
the alias sends 100% of invokes to the version used in production. During deployment, we will upload the code to Lambda,
publish a new version, send a small percentage of traffic to the new version, monitor, and validate before shifting 
100% of traffic to the new version. You can do this manually by calling Lambda APIs or let AWS CodeDeploy automate 
it for you. CodeDeploy will shift traffic, monitor alarms, run validation logic and even trigger an automatic rollback 
if something goes wrong.

SAM comes built-in with CodeDeploy support. You can enable automated traffic shifting Lambda deployments by 
adding the following lines to your ``AWS::Serverless::Function`` resource property or in the 
`Globals`_ section.

.. code:: yaml

    AutoPublishAlias: live
    DeploymentPreference:
      Type: Linear10PercentEvery10Minutes

The rest of this document dives deep into how this snippet works, available configurations, and debugging techniques
when deployments don't work as expected.

Instant traffic shifting using Lambda Aliases
---------------------------------------------

Every Lambda function can have any number of Versions and Aliases
associated with them. Versions are immutable snapshots of a function
including code & configuration. If you are familiar with git, they are
similar to commits. In general, it is a good practice to publish a new
version every time you update your function code. When you invoke a
specific version (using the function name + version number combination) you
are guaranteed to get the same code & configuration irrespective of the
state of the function. This protects you against accidentally updating
production code.

To effectively use the versions, you should create an Alias which is
literally a pointer to a version. Aliases have a name and an ARN similar
to the function and are accepted by the Invoke APIs. If you invoke an Alias,
Lambda will in turn invoke the version that the Alias is pointing to.

In production, you will first update your function code, publish a new
version, invoke the version directly to run tests against it, and, after
you are satisfied, flip the Alias to point to the new version. Traffic
will instantly shift from using your old version to using the new version.

SAM provides a simple primitive to do this for you. Add the following
property to your ``AWS::Serverless::Function`` resource:

.. code:: yaml

    AutoPublishAlias: <alias-name>

This will:

- Create an Alias with ``<alias-name>`` 
- Create & publish a Lambda version with the latest code & configuration 
  derived from the ``CodeUri`` property. Optionally it is possible to specify
  property `AutoPublishCodeSha256` that will override the hash computed for
  Lambda ``CodeUri`` property.
- Point the Alias to the latest published version 
- Point all event sources to the Alias & not to the function 
- When the ``CodeUri`` property of ``AWS::Serverless::Function`` changes, 
  SAM will automatically publish a new version & point the alias to the 
  new version

In other words, your traffic will shift "instantly" to your new code.

    NOTE: ``AutoPublishAlias`` will publish a new version only when the
    ``CodeUri`` changes. Updates to other configuration (ex: MemorySize,
    Timeout) etc will *not* publish a new version. Hence your Alias will
    continue to point to old version that uses the old configurations.

Traffic shifting using CodeDeploy
----------------------------------

For production deployments, you may want more controlled traffic shifting
from an old version to a new version which monitors alarms and triggers a
rollback if necessary. CodeDeploy is an AWS service which can do this
for you. It uses Lambda Alias' ability to route a percentage of traffic
to two different Lambda Versions. To use this feature, set the
``DeploymentPreference`` property of ``AWS::Serverless::Function``
resource:

.. code:: yaml

  MyLambdaFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: index.handler
      Runtime: nodejs12.x
      AutoPublishAlias: live
      DeploymentPreference:
        Type: Linear10PercentEvery10Minutes
        Alarms:
          # A list of alarms that you want to monitor
          - !Ref AliasErrorMetricGreaterThanZeroAlarm
          - !Ref LatestVersionErrorMetricGreaterThanZeroAlarm
        Hooks:
          # Validation Lambda functions that are run before & after traffic shifting
          PreTraffic: !Ref PreTrafficLambdaFunction
          PostTraffic: !Ref PostTrafficLambdaFunction
        # Provide a custom role for CodeDeploy traffic shifting here, if you don't supply one
        # SAM will create one for you with default permissions
        Role: !Ref IAMRoleForCodeDeploy # Parameter example, you can pass an IAM ARN

  AliasErrorMetricGreaterThanZeroAlarm:
    Type: "AWS::CloudWatch::Alarm"
    Properties:
      AlarmDescription: Lambda Function Error > 0
      ComparisonOperator: GreaterThanThreshold
      Dimensions:
        - Name: Resource
          Value: !Sub "${MyLambdaFunction}:live"
        - Name: FunctionName
          Value: !Ref MyLambdaFunction
      EvaluationPeriods: 2
      MetricName: Errors
      Namespace: AWS/Lambda
      Period: 60
      Statistic: Sum
      Threshold: 0

  LatestVersionErrorMetricGreaterThanZeroAlarm:
    Type: "AWS::CloudWatch::Alarm"
    Properties:
      AlarmDescription: Lambda Function Error > 0
      ComparisonOperator: GreaterThanThreshold
      Dimensions:
        - Name: Resource
          Value: !Sub "${MyLambdaFunction}:live"
        - Name: FunctionName
          Value: !Ref MyLambdaFunction
        - Name: ExecutedVersion
          Value: !GetAtt MyLambdaFunction.Version.Version
      EvaluationPeriods: 2
      MetricName: Errors
      Namespace: AWS/Lambda
      Period: 60
      Statistic: Sum
      Threshold: 0

  PreTrafficLambdaFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: preTrafficHook.handler
      Policies:
        - Version: "2012-10-17"
          Statement:
          - Effect: "Allow"
            Action:
              - "codedeploy:PutLifecycleEventHookExecutionStatus"
            Resource:
              !Sub 'arn:${AWS::Partition}:codedeploy:${AWS::Region}:${AWS::AccountId}:deploymentgroup:${ServerlessDeploymentApplication}/*'
        - Version: "2012-10-17"
          Statement:
          - Effect: "Allow"
            Action:
              - "lambda:InvokeFunction"
            Resource: !GetAtt MyLambdaFunction.Arn
      Runtime: nodejs12.x
      FunctionName: 'CodeDeployHook_preTrafficHook'
      DeploymentPreference:
        Enabled: False
        Role: ""
      Environment:
        Variables:
          CurrentVersion: !Ref MyLambdaFunction.Version

When you update your function code and deploy the SAM template using
CloudFormation, the following happens:

- CloudFormation publishes a new Lambda Version from the new code
- Since a deployment preference is set, CodeDeploy takes over the job of actually shifting traffic from old version to new version.
- Before traffic shifting starts, CodeDeploy will invoke the **PreTraffic Hook** Lambda function. This Lambda function must call back to CodeDeploy with an explicit status of Success or Failure, via the PutLifecycleEventHookExecutionStatus_ API. On Failure, CodeDeploy will abort and report a failure back to CloudFormation. On Success, CodeDeploy will proceed with the specified traffic shifting. Here_ is a sample Lambda Hook function.
- ``Type: Linear10PercentEvery10Minutes`` instructs CodeDeploy to start with 10% traffic on new version and add 10% every 10 minutes. It will complete traffic shifting in 100 minutes.
- During traffic shifting, if any of the CloudWatch Alarms go to *Alarm* state, CodeDeploy will immediately flip the Alias back to old version and report a failure to CloudFormation.
- After traffic shifting completes, CodeDeploy will invoke the **PostTraffic Hook** Lambda function. This is similar to PreTraffic Hook where the function must callback to CodeDeploy to report a Success or a Failure. PostTraffic hook is a great place to run integration tests or other validation actions.
- If everything went well, the Alias will be pointing to the new Lambda Version.
- If you supply the "Role" argument to the DeploymentPreference, it will prevent SAM from creating a role and instead use the provided CodeDeploy role for traffic shifting

NOTE: Verify that your AWS SDK version supports PutLifecycleEventHookExecutionStatus. For example, Python requires SDK version 1.4.8 or newer.

.. _PutLifecycleEventHookExecutionStatus: https://docs.aws.amazon.com/codedeploy/latest/APIReference/API_PutLifecycleEventHookExecutionStatus.html

.. _Here: https://github.com/awslabs/serverless-application-model/blob/master/examples/2016-10-31/lambda_safe_deployments/src/preTrafficHook.js

Traffic Shifting Configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the above example ``Linear10PercentEvery10Minutes`` is one of several preselected traffic shifting configurations 
available in CodeDeploy. You can pick the configuration that best suits your application. See docs_ for the complete list:

.. _docs: https://github.com/awslabs/serverless-application-model/blob/master/docs/safe_lambda_deployments.rst#traffic-shifting-configurations

- Canary10Percent30Minutes
- Canary10Percent5Minutes
- Canary10Percent10Minutes
- Canary10Percent15Minutes
- AllAtOnce
- Linear10PercentEvery10Minutes
- Linear10PercentEvery1Minute
- Linear10PercentEvery2Minutes
- Linear10PercentEvery3Minutes

They work as follows:

- **LinearXPercentYMinutes**: Traffic to new version will linearly increase in steps of X percentage every Y minutes. 

  Ex: ``Linear10PercentEvery10Minutes`` will add 10 percentage of traffic every 10 minute to complete in 100 minutes.

- **CanaryXPercentYMinutes**: X percent of traffic will be routed to new version for Y minutes. After Y minutes,
  100 percent of traffic will be sent to new version. Some people call this as Blue/Green deployment. 

  Ex: ``Canary10Percent15Minutes`` will send 10 percent traffic to new version and 15 minutes later complete deployment
  by sending all traffic to new version.

- **AllAtOnce**: This is an instant shifting of 100% of traffic to new version. This is useful if you want to run
  run pre/post hooks but don't want a gradual deployment. If you have a pipeline, you can set Beta/Gamma stages to 
  deploy instantly because the speed of deployments matter more than safety here.
- **Custom**: Aside from Above mentioned Configurations, Custom Codedeploy configuration are also supported.
  (Example. Type: CustomCodeDeployConfiguration)

PreTraffic & PostTraffic Hooks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CodeDeploy allows you to run an arbitrary Lambda function before traffic shifting actually starts (PreTraffic Hook) 
and after it completes (PostTraffic Hook). With either hook, you have the opportunity to run logic that determines
whether the deployment must succeed or fail. For example, with PreTraffic hook you could run integration tests against
the newly created Lambda version (but not serving traffic). With PostTraffic hook, you could run end-to-end validation
checks.

Hooks are extremely powerful because:

- **Not limited by Lambda function duration**: CodeDeploy invokes the hook function asynchronously. The function will
  receive a ``deploymentId`` and ``lifecycleEventHookExecutionId`` that should be used with a call to the CodeDeploy API to report success or failure. 
  Therefore you can build a workflow that runs for several minutes or hours before completing the hook by calling the 
  CodeDeploy API.

- **New Version is created before PreTraffic Hook runs**: Before PreTraffic hook runs, the Lambda Version containing 
  the new code has been created but this version is not serving any traffic yet. Therefore, in your hook function, 
  you can directly invoke the Version to run integration tests or even pre-warm the Lambda containers before exposing it
  to production traffic.

    NOTE: The event payload delivered to the Hook function will not contain the Lambda ARN to be tested.
    We recommend adding an Environment variable to the Hook function that maintains the current Version of the Lambda requiring safe deployments

.. code:: yaml

  Environment:
    Variables:
      CurrentVersion: !Ref MySafeLambdaFunction.Version


- **Hooks are executed per-function**: Each Lambda function gets its own PreTraffic and PostTraffic hook (technically
  speaking hooks are executed once per DeploymentGroup, but in this case the DeploymentGroup contains only one Lambda
  Function). So you can customize the hooks logic to the function that is being deployed.

    NOTE: If the Hook functions are created by the same SAM template that is deployed, then make sure to turn off
    traffic shifting deployments for the hook functions. Also, the Role SAM generates for a Lambda Execution Role does not include all permissions needed for Pre and Post hook functions, since it
    will not contain the necessary permissions to call the CodeDeploy APIs or Invoke your new Lambda function for testing.
    Instead, use the Policies_ attribute to provide the CodeDeploy and Lambda permissions needed. The example also shows a Policy that provides access to the CodeDeploy resource that SAM automatically generates.
    Finally, use the ``FunctionName`` property to control the exact name of the Lambda function CloudFormation creates. Otherwise, CloudFormation will create your Lambda function with the Stack name and a unique ID added as part of the name.

.. _Policies: https://github.com/awslabs/serverless-application-model/blob/master/versions/2016-10-31.md#resource-types

.. code:: yaml

    FunctionName: 'CodeDeployHook_preTrafficHook'
    DeploymentPreference:
        Enabled: False
    Policies:
        - Version: "2012-10-17"
          Statement:
          - Effect: "Allow"
            Action:
              - "codedeploy:PutLifecycleEventHookExecutionStatus"
            Resource: "*"
        - Version: "2012-10-17"
          Statement:
          - Effect: "Allow"
            Action:
              - "lambda:InvokeFunction"
            Resource: !GetAtt MyLambdaFunction.Arn

Checkout the lambda_safe_deployments_ folder for an example for how to create SAM template that contains a hook function.

.. _lambda_safe_deployments: https://github.com/awslabs/serverless-application-model/blob/master/examples/2016-10-31/lambda_safe_deployments

Internals
~~~~~~~~~
Internally, SAM will create the following resources in your CloudFormation stack to make all of this work:

-  One ``AWS::CodeDeploy::Application`` per stack, that is referencable via ${ServerlessDeploymentApplication}
-  One ``AWS::CodeDeploy::DeploymentGroup`` per
   ``AWS::Serverless::Function`` resource. Each Lambda Function in your
   SAM template belongs to its own Deployment Group.
-  Adds ``UpdatePolicy`` on ``AWS::Lambda::Alias`` resource that is
   connected to the function's Deployment Group resource.
-  One ``AWS::IAM::Role`` called "CodeDeployServiceRole", if no custom role is provided

CodeDeploy assumes that there are no dependencies between Deployment Groups and hence will deploy them in parallel.
Since every Lambda function is to its own CodeDeploy DeploymentGroup, they will be deployed in parallel.
The CodeDeploy service will assume the new CodeDeployServiceRole to Invoke any Pre/Post hook functions and perform the traffic shifting and Alias updates.

  NOTE: The CodeDeployServiceRole only allows InvokeFunction on functions with names prefixed with  ``CodeDeployHook_``. For example,  you should name your Hook functions as such: ``CodeDeployHook_PreTrafficHook``.

Production errors preventing deployments
~~~~~~~~~
In some situations, an issue that is happening in production may prevent you from deploying a fix. This may happen when a deployment happens when traffic is too low to register enough errors to trigger a roll back, or where someone is sending malicious traffic through to a lambda and you haven’t accounted for the scenario where they do. 

When this happens, the alarm for errors in the current lambda version is in an error state, which will cause code deploy to roll back any attempted deploys straight away.

To release code in this situation, you need to

- Go into the CodeDeploy console
- Select the application you want to deploy to
- Select the corresponding Deployment Group
- Select “Edit”
- Select “Advanced - optional”
- Select "ignore alarm configuration"
- Save the changes

Run your deployment as usual

Then once deployment has successfully run, return to the CodeDeploy console, and follow the above steps but this time deselect “ignore alarm configuration”.

.. _Globals: globals.rst
