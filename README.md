# AWS SAM transform

[![Tests](https://github.com/aws/serverless-application-model/actions/workflows/build.yml/badge.svg)](https://github.com/aws/serverless-application-model/actions/workflows/build.yml)
[![PyPI](https://img.shields.io/pypi/v/aws-sam-translator?label=PyPI)](https://pypi.org/project/aws-sam-translator/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aws-sam-translator?label=Python)](https://pypi.org/project/aws-sam-translator/)

The [AWS Serverless Application Model](https://aws.amazon.com/serverless/sam/) (AWS SAM) transform is a [AWS CloudFormation macro](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-macros.html) that transforms [SAM templates](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification-template-anatomy.html) into [CloudFormation templates](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-anatomy.html).

The SAM transform is used in templates with `AWS::Serverless-2016-10-31` in their [`Transform` section](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/transform-section-structure.html).

For the `sam` command-line tool, see the [AWS SAM CLI](https://github.com/aws/aws-sam-cli).

## Example

Deploying the following template creates a [AWS Lambda](https://aws.amazon.com/lambda/) function that prints out any [events](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-concepts.html#gettingstarted-concepts-event) it receives:

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
  <summary>Transformed CloudFormation template</summary>

```json
{
  "Resources": {
    "MyFunction": {
      "Type": "AWS::Lambda::Function",
      "Properties": {
        "Code": {
          "ZipFile": "exports.handler = async (event) => {\n  console.log(event);\n}\n"
        },
        "Handler": "index.handler",
        "Role": {
          "Fn::GetAtt": [
            "MyFunctionRole",
            "Arn"
          ]
        },
        "Runtime": "nodejs16.x",
        "Tags": [
          {
            "Key": "lambda:createdBy",
            "Value": "SAM"
          }
        ]
      }
    },
    "MyFunctionRole": {
      "Type": "AWS::IAM::Role",
      "Properties": {
        "AssumeRolePolicyDocument": {
          "Version": "2012-10-17",
          "Statement": [
            {
              "Action": [
                "sts:AssumeRole"
              ],
              "Effect": "Allow",
              "Principal": {
                "Service": [
                  "lambda.amazonaws.com"
                ]
              }
            }
          ]
        },
        "ManagedPolicyArns": [
          "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        ],
        "Tags": [
          {
            "Key": "lambda:createdBy",
            "Value": "SAM"
          }
        ]
      }
    }
  }
}
```

</details>

## Contributing

### Setting up development environment

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

- [Deploying a "Hello, World!" application](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started-hello-world.html)
- [SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html)
- [SAM template specification](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification.html)
- [SAM connectors](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/managing-permissions-connectors.html)
- [SAM policy templates](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-policy-templates.html)
