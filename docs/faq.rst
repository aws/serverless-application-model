
FAQ
===

Frequently Asked Questions

.. contents::
  :local:

How to manage multiple environments?
------------------------------------

  *Terminology clarification: Environment and Stage can normally be used interchangeably but since AWS API Gateway relies on a concrete concept of Stages we'll use the term Environment here to avoid confusion.*

**We recommend a one-to-one mapping of environment to Cloudformation Stack.**

This means having a separate CloudFormation stack per environment, using a single template file with a dynamically set target stack via the ``--stack-name`` parameter in the ``aws cloudformation deploy`` command.

For example, lets say we have 3 environments (dev, test, and prod).
Each of those would have their own CloudFormation stack — `dev-stack`, `test-stack`, `prod-stack`. Our CI/CD system will deploy to `dev-stack`, `test-stack`, and then `prod-stack` but will be pushing one template through all of these stacks.

This approach limits the 'blast radius' for any given deployment since all resources for each environment are scoped to a different CloudFormation Stack, so we will never be editing production resources on accident.

If we need to bring up separate stacks for different reasons (multiple region deployments, developer/branch stacks) it will be straightforward to do so with this approach since the same template can be used to bring up and manage a new stack independent of any others.

In cases where you need to manage different stages differently this can be done through a combination of Stack Parameters, Conditions, and Fn::If statements.

How to enable API Gateway Logs
------------------------------

Work is underway to make this functionality part of the SAM specification. Until then a suggested workaround is to use the ``aws cli update-stage`` command to enable it.

.. code-block:: console

    aws apigateway update-stage \
      --rest-api-id <api-id> \
      --stage-name <stage-name> \
      --patch-operations \
        op=replace,path=/*/*/logging/dataTrace,value=true \
        op=replace,path=/*/*/logging/loglevel,value=Info \
        op=replace,path=/*/*/metrics/enabled,value=true

The command above can be run as a post deployment CI step or it could be triggered by a `custom resource <https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources.html/>`_ within the same CloudFormation template.

Please note that in either case you will see metric gaps between the time CloudFormation updates API Gateway and the time this command runs.


How to deploy Lambda\@Edge functions with SAM?
----------------------------------------------

At present, SAM doesn't support `Lambda@Edge <https://aws.amazon.com/lambda/edge/>`_ as a native event. However you can follow this example to ease deployment: `Lambda Edge Example <https://github.com/awslabs/serverless-application-model/tree/master/examples/2016-10-31/lambda_edge>`_.
