Safe Lambda deployments
=======================

.. contents::

Pushing to production can be nerve-racking even if you have 100% unit test coverage and state-of-art full CD system. 
It is a good practice to expose your new code to a small percentage of production traffic, run tests, watch for alarms 
and dial up traffic as you gain more confidence. The goal is to minimize production impact as much as possible. 

To enable traffic shifting deployments for Lambda Functions, we will use Lambda Aliases, which can balance incoming 
traffic between two different versions of your function, based on preassigned weights. Before deployment, 
the alias sends 100% of invokes to the version used in production. During deployment, we will upload the code to Lambda,
publish a new version, send a small percentage of traffic to new version, monitor, and validate before shifting 
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

Rest of this document dives deep into how this snippet works, available configurations, and debugging techniques 
when deployments don't work as expected.

Instant traffic shifting using Lambda Aliases
---------------------------------------------

Every Lambda function can have any number of Versions and Aliases
associated with them. Versions are immutable snapshot of function
including code & configuration. If you are familiar with git, they are
similar to commits. It is a good practice in general to publish a new
version every time you update your function code. When you invoke a
specific version (using function name + version number combination) you
are guaranteed to get the same code & configuration irrespective of
state of the function. This protects you against accidentally updating
production code.

To effectively use the versions, you should create an Alias which is
literally a pointer to a version. Aliases have a name and an ARN similar
to the function and accepted by the Invoke APIs. If you invoke an Alias,
Lambda will in turn invoke the version that the Alias is pointing to.

In production, you will first update your function code, publish a new
version, invoke the version directly to run tests against it, and after
you are satisfied flip the Alias to point to the new version. Traffic
will instantly shift from using your old version to the new version.

SAM provides a simple primitive to do this for you. Add the following
property to your ``AWS::Serverless::Function`` resource:

.. code:: yaml

    AutoPublishAlias: <alias-name>

This will: - Creates a Alias with ``<alias-name>`` - Creates & publishes
a Lambda version with the latest code & configuration derived from
``CodeUri`` property - Point the Alias to the latest published version -
Points all event sources to the Alias & not the function - When the
``CodeUri`` property of ``AWS::Serverless::Function`` changes, SAM will
automatically publish a new version & point the alias to the new version

In other words, your traffic will shift "instantly" to your new code.

    NOTE: ``AutoPublishAlias`` will publish a new version only when the
    ``CodeUri`` changes. Updates to other configuration (ex: MemorySize,
    Timeout) etc will *not* publish a new version. Hence your Alias will
    continue to point to old version that uses the old configurations.

Traffic shifting using CodeDeploy
----------------------------------

For production deployments, you want a more controlled traffic shifting
from old version to new version while monitoring alarms and triggering a
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
      Runtime: nodejs4.3
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

When you update your function code and deploy the SAM template using
CloudFormation, the following happens:

-  A new Lambda Version is published from the new code
-  Since a deployment preference is set, CodeDeploy takes over the job
   of actually shifting traffic from old version to new version.
-  Before traffic shifting starts, CodeDeploy will invoke the
   **PreTraffic Hook** Lambda Function. This Lambda function must call
   back to CodeDeploy with explicit Success or Failure. On Failure, it
   will abort and report a failure back to CloudFormation. On Success,
   CodeDeploy will proceed to traffic shifting.
-  ``Type: Linear10PercentEvery10Minutes`` instructs CodeDeploy to start with
   10% traffic on new version and add 10% every 10 minutes. It will complete traffic shifting in 100 minutes. 
-  During traffic shifting, if any of the CloudWatch Alarms go to
   *Alarm* state, CodeDeploy will immediately flip the Alias back to old
   version and report a failure to CloudFormation.
-  After traffic shifting completes, CodeDeploy will invoke the
   **PostTraffic Hook** Lambda Function. This is similar to PreTraffic
   Hook where the function must callback to CodeDeploy to report a
   Success or Failure. PostTraffic hook is a great place to run
   integration tests or other validation actions.
-  If everything went well, the Alias will be pointing to the new Lambda
   Version.

Traffic Shifting Configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the above example ``Linear10PercentEvery10Minutes`` is one of several preselected traffic shifting configurations 
available in CodeDeploy. You can pick the configuration that best suits your application. Here is the complete list:

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

- **CanaryXPercentYMinutes**: X percent of traffic will be routed to new Version once, and wait for Y minutes in this
  state before sending 100 percent of traffic to new version. Some people call this as Blue/Green deployment. 

  Ex: ``Canary10Percent15Minutes`` will send 10 percent traffic to new version and 15 minutes later complete deployment
  by sending all traffic to new version.

- **AllAtOnce**: This is an instant shifting of 100% of traffic to new version. This is useful if you want to run
  run pre/post hooks but don't want a gradual deployment. If you have a pipeline, you can set Beta/Gamma stages to 
  deploy instantly because the speed of deployments matter more than safety here.


PreTraffic & PostTraffic Hooks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CodeDeploy allows you to run an arbitrary Lambda Function before traffic shifting actually starts (PreTraffic Hook) 
and after it completes (PostTraffic Hook). With either hooks, you have the opportunity to run logic that determines
whether the deployment must succeed or fail. For example, with PreTraffic hook you could run integration tests against
the newly created Lambda version (but not serving traffic). With PostTraffic hook, you could run end-to-end validation
checks.

Hooks are extremely powerful because:

- **Not limited by Lambda function duration**: CodeDeploy invokes the hook function asynchrnously. The function will
  receive an identifier that should be used with an explicit call with CodeDeploy API to report success or failure. 
  Therefore you can build a workflow that runs for several minutes or hours before completing the hook by calling
  CodeDeploy API.

- **New Version is created before PreTraffic Hook runs**: Before PreTraffic hook runs, the Lambda Version containing 
  the new code has been created. But this version is not serving any traffic yet. Therefore, in your hook function, 
  you can directly invoke the version to run integration tests or even pre-warm the Lambda containers before exposing
  to production traffic.

- **Hooks are executed per-function**: Each Lambda function gets its own PreTraffic and PostTraffic hook (technically
  speaking hooks are executed once per DeploymentGroup, but in this case the DeploymentGroup contains only one Lambda
  Function). So you can customize the hooks logic to the function that is being deployed.

Checkout the examples folder for an example for how to create a hook function.

    NOTE: If the Hook functions are created by the same SAM template that is deployed, then make sure to turn off
    traffic shifting deployments for the hook functions. 

        .. code:: yaml

            DeploymentPreference: 
                Enabled: false
            
Internals
~~~~~~~~~
Internally, SAM will create the following resources in your CloudFormation stack to make all of this work:

-  One ``AWS::CodeDeploy::Application`` per stack.
-  One ``AWS::CodeDeploy::DeploymentGroup`` per
   ``AWS::Serverless::Function`` resource. Each Lambda Function in your
   SAM template belongs to its own Deployment Group.
-  Adds ``UpdatePolicy`` on ``AWS::Lambda::Alias`` resource that is
   connected to the function's Deployment Group resource.

CodeDeploy assumes that there are no dependencies between Deployment Groups and hence will deploy them in parallel.
Since every Lambda function is to its own CodeDeploy DeploymentGroup, they will be deployed in parallel. 


.. _Globals: globals.rst
