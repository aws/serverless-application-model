Policy Templates
================

When you define a Serverless Function, SAM automatically creates the IAM Role required to run the function. Let's say
your function needs to access couple of DynamoDB tables, you need to give your function explicit permissions to access
the tables. You can do this by adding AWS Managed Policies to Serverless Function resource definition in your SAM 
template.

For Example:

.. code:: yaml

  MyFunction:
    Type: AWS::Serverless::Function
    Properties:
      ...
      Policies:
        # Give DynamoDB Full Access to your Lambda Function
        - AmazonDynamoDBFullAccess
      ...

  MyTable:
    Type: AWS::Serverless::SimpleTable


Behind the scenes, ``AmazonDynamoDBFullAccess`` will give your function access to **all** DynamoDB APIs against **all**
DynamoDB tables in **all** regions. This is excessively permissive when all that your function does is Read & Write
values from the ``MyTable`` created in the stack.

SAM provides a tighter and more secure version of AWS Managed Policies called **Policy Templates**. This are a set of 
readily availbale policies that can be scoped to a specific resource in the same region where your stack exists. 
Let's modify the above example to use a policy template called ``DynamoDBCrudPolicy``:

.. code:: yaml

  MyFunction:
    Type: AWS::Serverless::Function
    Properties:
      ...
      Policies:

        # Give just CRUD permissions to one table
        - DynamoDBCrudPolicy:
            TableName: !Ref MyTable

      ...

  MyTable:
    Type: AWS::Serverless::SimpleTable


How to Use
----------

Policy Templates are specified in ``Policies`` property of AWS::Serverless::Function resource. You can mix policy 
templates with AWS Managed Policies, custom managed policies or inline policy statements. Behind the scenes
SAM will expand the policy template to a inline policy statement based on the definition listed in 
`policy_templates.json`_ file.

Every policy template requires zero or more parameters, which are the resource that this policy is scoped to. 
Your template will fail to deploy if the value for a required parameter is not specified. You can consult the 
`policy_templates.json`_ file for name of the policy templates, parameter names as well as the actual policy statement
it represents. 

If you want a quick reference of all policies, checkout the `all_policy_templates.yaml`_ SAM template in examples 
folder. 

  NOTE: If a policy template does not require a parameter, you should still specify the value to be an empty dictionary
  like this:
  
  .. code: yaml
  
    Policies:
      - CloudWatchPutMetricPolicy: {}      

.. _policy_templates.json: policy_templates_data/policy_templates.json
.. _all_policy_templates.yaml: ../examples/2016-10-31/policy_templates/all_policy_templates.yaml
