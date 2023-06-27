# AWS SAM transform

[![Tests](https://github.com/aws/serverless-application-model/actions/workflows/build.yml/badge.svg)](https://github.com/aws/serverless-application-model/actions/workflows/build.yml)
[![Update schema](https://github.com/aws/serverless-application-model/actions/workflows/schema.yml/badge.svg)](https://github.com/aws/serverless-application-model/actions/workflows/schema.yml)
[![PyPI](https://img.shields.io/pypi/v/aws-sam-translator?label=PyPI)](https://pypi.org/project/aws-sam-translator/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aws-sam-translator?label=Python)](https://pypi.org/project/aws-sam-translator/)
[![Contribute with Gitpod](https://img.shields.io/badge/Contribute%20with-Gitpod-908a85?logo=gitpod)](https://gitpod.io/#https://github.com/aws/serverless-application-model.git)

The [AWS Serverless Application Model](https://aws.amazon.com/serverless/sam/) (AWS SAM) transform is a [AWS CloudFormation macro](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-macros.html) that transforms [SAM templates](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification-template-anatomy.html) into [CloudFormation templates](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-anatomy.html).

To use the SAM transform, add `AWS::Serverless-2016-10-31` to the [`Transform` section](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/transform-section-structure.html) of your CloudFormation template.

Benefits of using the SAM transform include:

- Built-in best practices and sane defaults.
- Local testing and debugging with the [AWS SAM CLI](https://github.com/aws/aws-sam-cli).
- Extension of the CloudFormation template syntax.

## Getting started

Save the following as `template.yaml`:

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

And deploy it with the [SAM CLI](https://github.com/aws/aws-sam-cli):

```bash
sam sync --stack-name sam-app
```

The [`AWS::Serverless::Function`](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-resource-function.html) resource will create a [AWS Lambda](https://aws.amazon.com/lambda/) function that logs [events](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-concepts.html#gettingstarted-concepts-event) it receives.

Under the hood, the template is transformed into the JSON equivalent of the following CloudFormation template:

```yaml
Resources:
  MyFunction:
    Type: AWS::Lambda::Function
    Properties:
      Code:
        ZipFile: |
          exports.handler = async (event) => {
            console.log(event);
          }
      Handler: index.handler
      Role: !GetAtt MyFunctionRole.Arn
      Runtime: nodejs16.x
      Tags:
        - Key: lambda:createdBy
          Value: SAM
  MyFunctionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Action:
              - sts:AssumeRole
            Effect: Allow
            Principal:
              Service:
                - lambda.amazonaws.com
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Tags:
        - Key: lambda:createdBy
          Value: SAM
```

For a more thorough introduction, see the [this tutorial](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started-hello-world.html) in the [Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html).

## Contributing

### Setting up development environment

You'll need to have Python 3.7+ installed.

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
 
See [`DEVELOPMENT_GUIDE.md`](DEVELOPMENT_GUIDE.md) for further development instructions, and [`CONTRIBUTING.md`](CONTRIBUTING.md) for the contributing guidelines.

## Getting help

The best way to interact with the team is through GitHub. You can either [create an issue](https://github.com/aws/serverless-application-model/issues/new/choose) or [start a discussion](https://github.com/aws/serverless-application-model/discussions).

You can also join the [`#samdev` channel](https://join.slack.com/t/awsdevelopers/shared_invite/zt-yryddays-C9fkWrmguDv0h2EEDzCqvw) on Slack.

## Learn more

### Workshops and tutorials

- [The Complete AWS SAM Workshop](https://catalog.workshops.aws/complete-aws-sam)
- [AWS Serverless Developer Experience Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/9a27e484-7336-4ed0-8f90-f2747e4ac65c/en-US)
- [Deploying a "Hello, World!" application](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started-hello-world.html)
- [Testing in the cloud using the SAM CLI](https://aws.amazon.com/blogs/compute/accelerating-serverless-development-with-aws-sam-accelerate/)

### Documentation

- [SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html)
- [SAM template specification](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification.html)
- [SAM connectors](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/managing-permissions-connectors.html)
- [SAM policy templates](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-policy-templates.html)
