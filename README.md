# AWS SAM transform

[![Tests](https://github.com/aws/serverless-application-model/actions/workflows/build.yml/badge.svg)](https://github.com/aws/serverless-application-model/actions/workflows/build.yml)
[![PyPI](https://img.shields.io/pypi/v/aws-sam-translator?label=PyPI)](https://pypi.org/project/aws-sam-translator/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aws-sam-translator)](https://pypi.org/project/aws-sam-translator/)

The [AWS Serverless Application Model](https://aws.amazon.com/serverless/sam/) (AWS SAM) transform 

It allows you to write 

This repository hosts the code for the [`AWS::Serverless-2016-10-31` transform](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/transform-aws-serverless.html).

For the `sam` command-line tool, see the [AWS SAM CLI](https://github.com/aws/aws-sam-cli).

## Example

```yaml
Transform: AWS::Serverless-2016-10-31
Resources:
  MyFunction:
    Type: AWS::Serverless::Function
    Properties:
      Runtime: nodejs16.x
      Handler: index.handler
      InlineCode: |
        exports.handler = async (event) => {
          console.log(event);
        }
```

## Getting help

The best way to interact with the team is through GitHub. You can either [create an issue](https://github.com/aws/serverless-application-model/issues/new/choose) or [start a discussion](https://github.com/aws/serverless-application-model/discussions).

Or join the [`#samdev` channel](https://join.slack.com/t/awsdevelopers/shared_invite/zt-yryddays-C9fkWrmguDv0h2EEDzCqvw) on Slack.

## Learn more

## Contributing

### Setting up development environment

Create a [virtual environment](https://docs.python.org/3/library/venv.html):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Set up dependencies:

```bash
make init
```

Run tests:

```bash
make pr
 ```

For more thorough instructions, see [`DEVELOPMENT_GUIDE.md`](DEVELOPMENT_GUIDE.md).

---

- what it is (does it need the whys?)
- example (link to other detailed docs etc)
- getting help (slack etc)
- learn more (docs, tutorials, etc.)
- contributing (setting up env)

Want:
- what it is (mention aws sam cli)
- example
- development
- join slack

---

The [AWS Serverless Application Model](https://aws.amazon.com/serverless/sam/) (AWS SAM) is an open-source framework for building serverless applications.


It provides shorthand syntax to express functions, APIs, databases, and event source mappings.
With just a few lines of configuration, you can define the application you want and model it.

## Recent blogposts and workshops

* **Develop Node projects with SAM CLI using esbuild (Beta)** - And use SAM Accelerate on TypeScript projects. [Read blogpost here](https://s12d.com/5Aa6u0o7).
* **Speed up development with SAM Accelerate (Beta)** - Quickly test your changes in the cloud. [Read blogpost here](https://s12d.com/WeMib4nf).
* **Getting started with CI/CD? SAM pipelines can help you get started** - [This workshop](https://s12d.com/_JQ48d5T) walks you through the basics.
* **Get started with Serverless Application development using SAM CLI** - [This workshop](https://s12d.com/Tq9ZE-Br) walks you through the basics.

https://aws.amazon.com/blogs/compute/building-typescript-projects-with-aws-sam-cli/

https://aws.amazon.com/blogs/compute/accelerating-serverless-development-with-aws-sam-accelerate/?sc_icampaign=launch_sam-accelerate&sc_ichannel=ha&sc_icontent=awssm-9887_launch&sc_iplace=ribbon&trk=ha_awssm-9887_launch

https://cicd.serverlessworkshops.io/

https://catalog.us-east-1.prod.workshops.aws/workshops/d21ec850-bab5-4276-af98-a91664f8b161/en-US/introduction

https://s12d.com/_JQ48d5T

## Get started

To get started with building SAM-based applications, use the [AWS SAM CLI](https://github.com/aws/aws-sam-cli). SAM CLI provides a Lambda-like execution
environment that lets you locally build, test, debug, and deploy applications defined by SAM templates.

* [Install SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* [Build & deploy a "hello world" web app](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-quick-start.html)
* [Install AWS Toolkit](https://aws.amazon.com/getting-started/tools-sdks/#IDE_and_IDE_Toolkits) to use SAM with your favorite IDEs

**Next steps:** Learn to build a more complex serverless application.
* [Extract text from images and store in a database](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-example-s3.html) using Amazon S3 and Amazon Rekognition services.
* [Detect when records are added to a database](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-example-ddb.html) using Amazon DynamoDB database and asynchronous stream processing.
* Watch the [Mastering the AWS Serverless Application Model](https://www.youtube.com/watch?v=QBBewrKR1qg) AWS Online Tech Talk.

**Detailed references:** Explains SAM commands and usage in depth.
* [CLI commands](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-command-reference.html)
* [SAM template specification](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification.html)
* [Policy templates](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-policy-templates.html)

## Why SAM

+ **Single\-deployment configuration**\. SAM makes it easy to organize related components and resources, and operate on a single stack\. You can use SAM to share configuration \(such as memory and timeouts\) between resources, and deploy all related resources together as a single, versioned entity\.

+ **Local debugging and testing**\. Use SAM CLI to locally build, test, and debug SAM applications on a Lambda-like execution environment. It tightens the development loop by helping you find & troubleshoot issues locally that you might otherwise identify only after deploying to the cloud.

+ **Deep integration with development tools**. You can use SAM with a suite of tools you love and use.
    + IDEs: [PyCharm](https://aws.amazon.com/pycharm/), [IntelliJ](https://aws.amazon.com/intellij/), [Visual Studio Code](https://aws.amazon.com/visualstudiocode/), [Visual Studio](https://aws.amazon.com/visualstudio/), [AWS Cloud9](https://aws.amazon.com/cloud9/)
    + Build: [CodeBuild](https://docs.aws.amazon.com/codebuild/latest/userguide/)
    + Deploy: [CodeDeploy](https://docs.aws.amazon.com/codedeploy/latest/userguide/), [Jenkins](https://wiki.jenkins.io/display/JENKINS/AWS+SAM+Plugin)
    + Continuous Delivery Pipelines: [CodePipeline](https://docs.aws.amazon.com/codepipeline/latest/userguide/)
    + Discover Serverless Apps & Patterns: [AWS Serverless Application Repository](https://docs.aws.amazon.com/serverlessrepo/latest/devguide/)

+ **Built\-in best practices**\. You can use SAM to define and deploy your infrastructure as configuration. This makes it possible for you to use and enforce best practices through code reviews. Also, with a few lines of configuration, you can enable safe deployments through CodeDeploy, and can enable tracing using AWS X\-Ray\.

+ **Extension of AWS CloudFormation**\. Because SAM is an extension of AWS CloudFormation, you get the reliable deployment capabilities of AWS CloudFormation\. You can define resources by using CloudFormation in your SAM template\. Also, you can use the full suite of resources, intrinsic functions, and other template features that are available in CloudFormation\.

## Contribute to SAM

**Enhance the SAM specification**

Make pull requests, report bugs, and share ideas to improve the full SAM template specification.
Source code is located on GitHub at [awslabs/serverless-application-model](https://github.com/awslabs/serverless-application-model).
Read the [SAM Specification Contributing Guide](https://github.com/awslabs/serverless-application-model/blob/master/CONTRIBUTING.md)
to get started.

**Strengthen SAM CLI**

Add new commands or enhance existing ones, report bugs, or request new features for the SAM CLI.
Source code is located on GitHub at [awslabs/aws-sam-cli](https://github.com/awslabs/aws-sam-cli). Read the [SAM CLI Contributing Guide](https://github.com/awslabs/aws-sam-cli/blob/develop/CONTRIBUTING.md) to 
get started.

**Update SAM developer guide**

[SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/index.html) provides comprehensive getting started guide and reference documentation.
Source code is located on GitHub at [awsdocs/aws-sam-developer-guide](https://github.com/awsdocs/aws-sam-developer-guide).
Read the [SAM Documentation Contribution Guide](https://github.com/awsdocs/aws-sam-developer-guide/blob/master/CONTRIBUTING.md) to get
started.

