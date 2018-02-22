
FAQ
===

Frequently Asked Questions

.. contents::
  :local:

How to manage multiple environments?
------------------------------------

  *Terminology clarification: Environment and Stage can normally be used interchangeably but since AWS Gateway relies on a concrete concept of Stages we'll use the term Environment here to avoid confusion.*

**We recommend a one-to-one mapping of environment to Cloudformation Stack.**

This means having a separate CloudFormation stack per environment, using a single template file with dynamically set target stack via the ``--stack-name`` parameter in the ``aws deploy`` command.

For example, lets say we have 3 environments (dev, test, and prod).
Each of those would have their own CloudFormation stack — `dev-stack`, `test-stack`, `prod-stack`. Your CI/CD system will deploy to `dev-stack`, `test-stack`, and then `prod-stack` but will be pushing one template through all of these stacks by using the ``aws deploy --stack-name <stack-name>`` command.

This approach limits the 'blast radius' for any given deployment since all resources for each environment are scoped to a different CloudFormation Stack you will never be editing production resources on accident.

If you need to bring up separate stacks for different reasons (multiple region deployments, developer/branch stacks) it will be straightforward to do so with this approach since the same template can be used to bring up and manage a new stack independent of any others.

In cases where you need to manage different stages differently this can be done through a combination of Stack Parameters, Conditions, and Fn::If statements.

How to enable API Gateway Logs
------------------------------

Work is underway to make this functionality part of the SAM specification. Until then the suggested workaround is to use the ``aws cli update-stage`` command to enable this manually after a Clouformation deployment.

.. code-block:: console

    aws apigateway update-stage \
      --rest-api-id <api-id> \
      --stage-name <stage-name> \
      --patch-operations \
        op=replace,path=/*/*/logging/dataTrace,value=true \
        op=replace,path=/*/*/logging/loglevel,value=Info \
        op=replace,path=/*/*/metrics/enabled,value=true
