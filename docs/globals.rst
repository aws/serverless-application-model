Globals Section
===============

.. contents::

Lambda functions within a SAM template tend to have shared configuration such as Runtime, Memory, 
VPC Settings, Environment Variables etc. Instead of duplicating this information in every function, you can 
write them once in the  ``Globals`` section and let all Functions inhert it. 

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
timeout and index.handler Handler. ``HelloWorldFunction`` adds MESSAGE environnment variable in addition to the 
inherited TABLE_NAME. ``ThumbnailFunction`` inherits all the Globals properties and adds an API Event source.

Supported Resources
-------------------
Properties of ``AWS::Serverless::Function`` are only supported in Globals section presently. 

.. code:: yaml

  Globals:
    Function:
      # Properties of AWS::Serverless::Function

Following properties of ``AWS::Serverless::Function`` are **not** supported in Globals section. We made the explicitly
call to not support them because it either made the template hard to understand or opens scope for potential security 
issues.

* Role
* Policies
* FunctionName
* Events

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
*Also called as dictionaries, or key/value pairs*

Map value in the resource will be **merged** with the map value from Global. 

Example:

Environment variables of ``MyFunction`` will be set to ``{ TABLE_NAME: "resource-table", "NEW_VAR": "hello" }``

.. code:: yaml

  Globals:
    Function:
      Environment: 
        Variables:
          TABLE_NAME: global-table

  Resources:
    MyFunction:
      Type: AWS::Serverless::Function
      Properties:
        Environment: 
          Variables:
            TABLE_NAME: resource-table
            NEW_VAR: hello

Lists are additivie
~~~~~~~~~~~~~~~~~~
*Also called as arrays*

List values in the resource will be **appended** with the map value from Global. 

Example:

SecurityGroupIds of VpcConfig will be set to ``["sg-first", "sg-123", "sg-456"]``

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
 




