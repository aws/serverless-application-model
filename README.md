[![Build Status](https://travis-ci.org/awslabs/serverless-application-model.svg?branch=develop)](https://travis-ci.org/awslabs/serverless-application-model)
[![PyPI version](https://badge.fury.io/py/aws-sam-translator.svg)](https://badge.fury.io/py/aws-sam-translator)

![Logo](aws_sam_introduction.png)

# AWS Serverless Application Model (AWS SAM)
You can use SAM to define serverless applications in simple and clean syntax.

This GitHub project is the starting point for AWS SAM. It contains the SAM specification, the code that translates SAM templates into AWS CloudFormation stacks, general information about the model, and examples of common applications.

The SAM specification and implementation are open sourced under the Apache 2.0 license. The current version of the SAM specification is available at [AWS SAM 2016-10-31](versions/2016-10-31.md).


## Creating a serverless application using SAM
To create a serverless application using SAM, first, you create a SAM template: a JSON or YAML configuration file that describes your Lambda functions, API endpoints and the other resources in your application. Then, you test, upload, and deploy your application using the [SAM Local CLI](https://github.com/awslabs/aws-sam-local). During deployment, SAM automatically translates your application’s specification into CloudFormation syntax, filling in default values for any unspecified properties and determining the appropriate mappings and invocation permissions to setup for any Lambda functions.

[Read the How-To Guide](HOWTO.md) and see [examples](examples/) to learn how to define & deploy serverless applications using SAM.


## Contributing new features and enhancements to SAM
You can build serverless applications faster and further simplify your development of serverless applications by defining new event sources, new resource types, and new parameters within SAM. Additionally, you can modify SAM to integrate it with other frameworks and deployment providers from the community for building serverless applications.

[Read the Development Guide](DEVELOPMENT_GUIDE.rst) for in-depth information on how to start making changes.

[Join the SAM developers channel (#samdev) on Slack](https://awssamopensource.splashthat.com/) to collaborate with fellow community members and the AWS SAM team.
