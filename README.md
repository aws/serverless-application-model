# AWS SAM transform

[![Tests](https://github.com/aws/serverless-application-model/actions/workflows/build.yml/badge.svg)](https://github.com/aws/serverless-application-model/actions/workflows/build.yml)
[![PyPI](https://img.shields.io/pypi/v/aws-sam-translator?label=PyPI)](https://pypi.org/project/aws-sam-translator/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aws-sam-translator?label=Python)](https://pypi.org/project/aws-sam-translator/)

The [AWS Serverless Application Model](https://aws.amazon.com/serverless/sam/) (AWS SAM) transform is a [AWS CloudFormation macro](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-macros.html) that transforms [SAM templates](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification-template-anatomy.html) into [CloudFormation templates](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-anatomy.html).

A SAM template has [`AWS::Serverless-2016-10-31`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/transform-aws-serverless.html) in its `Transform` section.

For the `sam` command-line tool, see the [AWS SAM CLI](https://github.com/aws/aws-sam-cli).

## Example

The following example specifies a AWS Lambda function.

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

<details>
  <summary>Transformed AWS CloudFormation template</summary>
  
  ### Heading
  1. Foo
  2. Bar
     * Baz
     * Qux

  ### Some Code
  ```js
  function logSomething(something) {
    console.log('Something', something);
  }
  ```
</details>

## Setting up development environment

Make sure you have Python 3.7+ installed.

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

For further instructions, see [`DEVELOPMENT_GUIDE.md`](DEVELOPMENT_GUIDE.md).

## Getting help

The best way to interact with the team is through GitHub. You can either [create an issue](https://github.com/aws/serverless-application-model/issues/new/choose) or [start a discussion](https://github.com/aws/serverless-application-model/discussions).

You can also join the [`#samdev` channel](https://join.slack.com/t/awsdevelopers/shared_invite/zt-yryddays-C9fkWrmguDv0h2EEDzCqvw) on Slack.

## Learn more


---

1. what it is
2. example
3. contributing
4. getting help
5. learn more

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

