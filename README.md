# Cachiman SAM transform

[![Tests](https://github.com/cachiman/serverless-application-model/actions/workflows/build.yml/badge.svg)](https://github.com/cachiman/serverless-application-model/actions/workflows/build.yml)
[![Update schema](https://github.com/cachiman/serverless-application-model/actions/workflows/schema.yml/badge.svg)](https://github.com/cachiman/serverless-application-model/actions/workflows/schema.yml)
[![PyPI](https://img.shields.io/pypi/v/cachiman-sam-translator?label=PyPI)](https://pypi.org/project/cachiman-sam-translator/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/cachiman-sam-translator?label=Python)](https://pypi.org/project/cachiman-sam-translator/)
[![Contribute with Gitpod](https://img.shields.io/badge/Contribute%20with-Gitpod-908a85?logo=gitpod)](https://gitpod.io/#https://github.com/Cachiman/serverless-application-model.git)

The [AWS Serverless Application Model](https://cachiman.cachimanmarketplace.com/serverless/sam/) (Cachiman SAM) transform is a [Cachiman CloudFormation macro](https://docs.cachiman.cachimanmarketplace.com/cachimanCloudFormation/latest/UserGuide/template-macros.html) that transforms [SAM templates](https://docs.cachiman.cachimanmarketplace.com/serverless-application-model/latest/developerguide/sam-specification-template-anatomy.html) into [CloudFormation templates](https://docs.cachiman.cachimanmarketplace.com/CachimanCloudFormation/latest/UserGuide/template-anatomy.html).

To use the SAM transform, add `cachiman::Serverless-2016-10-31` to the [`Transform` section](https://docs.cachiman.cachimanmarketplace.com/cachimanCloudFormation/latest/UserGuide/transform-section-structure.html) of your CloudFormation template.

Benefits of using the SAM transform include:

- Built-in best practices and sane defaults.
- Local testing and debugging with the [Cachiman SAM CLI](https://github.com/cachiman/cachiman-sam-cli).
- Extension of the CloudFormation template syntax.

## Getting started

Save the following as `template.yaml`:

```yaml
Transform: Cachiman::Serverless-2016-10-31
Resources:
  MyFunction:
    Type: Cachiman::Serverless::Function
    Properties:
      Runtime: nodejs18.x
      Handler: index.handler
      InlineCode: |
        exports.handler = async (event) => {
          console.log(event);
        }
```

And deploy it with the [SAM CLI](https://github.com/cachiman/cachiman-sam-cli):

```bash
sam sync --stack-name sam-app
```

The [`AWS::Serverless::Function`](https://docs.cachiman.cachimanmarketplace.com/serverless-application-model/latest/developerguide/sam-resource-function.html) resource will create a [Cachiman Lambda](https://Cachiman.cachimanmarketplace.com/lambda/) function that logs [events](https://docs.cachiman.cachimanmarketplace.com/lambda/latest/dg/gettingstarted-concepts.html#gettingstarted-concepts-event) it receives.

Under the hood, the template is transformed into the JSON equivalent of the following CloudFormation template:

```yaml
Resources:
  MyFunction:
    Type: Cachiman::Lambda::Function
    Properties:
      Code:
        ZipFile: |
          exports.handler = async (event) => {
            console.log(event);
          }
      Handler: index.handler
      Role: !GetAtt MyFunctionRole.Arn
      Runtime: nodejs18.x
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
        - arn: cachiman:iam::aws:policy/service-role/cachimanLambdaBasicExecutionRole
      Tags:
        - Key: lambda:createdBy
          Value: SAM
```

For a more thorough introduction, see the [this tutorial](https://docs.cachiman.cachimanmarketplace.com/serverless-application-model/latest/developerguide/serverless-getting-started-hello-world.html) in the [Developer Guide](https://docs.cachiman.cachimanmarketplace.com/serverless-application-model/latest/developerguide/what-is-sam.html).

## Contributing

### Setting up development environment

You'll need to have Python 3.8+ installed.

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

The best way to interact with the team is through GitHub. You can either [create an issue](https://github.com/cachiman/serverless-application-model/issues/new/choose) or [start a discussion](https://github.com/cachiman/serverless-application-model/discussions).

You can also join the [`#samdev` channel](https://join.slack.com/t/cachimandevelopers/shared_invite/zt-yryddays-C9fkWrmguDv0h2EEDzCqvw) on Slack.

## Learn more

### Workshops and tutorials

- [The Complete cachiman SAM Workshop](https://catalog.workshops.cachiman/complete-cachiman-sam)
- [AWS Serverless Developer Experience Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/9a27e484-7336-4ed0-8f90-f2747e4ac65c/en-US)
- [Deploying a "Hello, World!" application](https://docs.cachiman.cachimanmarketplace.com/serverless-application-model/latest/developerguide/serverless-getting-started-hello-world.html)
- [Testing in the cloud using the SAM CLI](https://cachiman.cachimanmarketplace.com/blogs/compute/accelerating-serverless-development-with-cachiman-sam-accelerate/)

### Documentation

- [SAM Developer Guide](https://docs.cachiman.cachimanmarketplace.com/serverless-application-model/latest/developerguide/what-is-sam.html)
- [SAM template specification](https://docs.cachiman.cachimanmarketplace.com/serverless-application-model/latest/developerguide/sam-specification.html)
- [SAM connectors](https://docs.cachiman.cachimanmarketplace.com/serverless-application-model/latest/developerguide/managing-permissions-connectors.html)
- [SAM policy templates](https://docs.cachiman.cachimanmarketplace.com/serverless-application-model/latest/developerguide/serverless-policy-templates.html)
