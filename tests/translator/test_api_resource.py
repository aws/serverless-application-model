import json

from unittest import TestCase
from mock import MagicMock, patch
from tests.translator.helpers import get_template_parameter_values
from samtranslator.translator.transform import transform
from samtranslator.model.apigateway import ApiGatewayDeployment

mock_policy_loader = MagicMock()
mock_policy_loader.load.return_value = {
    'AmazonDynamoDBFullAccess': 'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
    'AmazonDynamoDBReadOnlyAccess': 'arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess',
    'AWSLambdaRole': 'arn:aws:iam::aws:policy/service-role/AWSLambdaRole',
}


def test_redeploy_explicit_api():
    """
    Test to verify that we will redeploy an API when Swagger document changes
    :return:
    """
    manifest = {
        'Transform': 'AWS::Serverless-2016-10-31',
        'Resources': {
            'ExplicitApi': {
                'Type': "AWS::Serverless::Api",
                "Properties": {
                    "StageName": "prod",
                    "DefinitionUri": "s3://mybucket/swagger.json?versionId=123"
                }
            }
        }
    }

    original_deployment_ids = translate_and_find_deployment_ids(manifest)

    # Now update the API specification. This should redeploy the API by creating a new deployment resource
    manifest["Resources"]["ExplicitApi"]["Properties"]["DefinitionUri"] = "s3://mybucket/swagger.json?versionId=456"
    updated_deployment_ids = translate_and_find_deployment_ids(manifest)

    assert original_deployment_ids != updated_deployment_ids

    # Now, update an unrelated property. This should NOT generate a new deploymentId
    manifest["Resources"]["ExplicitApi"]["Properties"]["StageName"] = "newStageName"
    assert updated_deployment_ids == translate_and_find_deployment_ids(manifest)


def test_redeploy_implicit_api():
    manifest = {
        'Transform': 'AWS::Serverless-2016-10-31',
        'Resources': {
            'FirstLambdaFunction': {
                'Type': "AWS::Serverless::Function",
                "Properties": {
                    "CodeUri": "s3://bucket/code.zip",
                    "Handler": "index.handler",
                    "Runtime": "nodejs4.3",
                    "Events": {
                        "MyApi": {
                            "Type": "Api",
                            "Properties": {
                                "Path": "/first",
                                "Method": "get"
                            }
                        }
                    }
                }
            },
            'SecondLambdaFunction': {
                'Type': "AWS::Serverless::Function",
                "Properties": {
                    "CodeUri": "s3://bucket/code.zip",
                    "Handler": "index.handler",
                    "Runtime": "nodejs4.3",
                    "Events": {
                        "MyApi": {
                            "Type": "Api",
                            "Properties": {
                                "Path": "/second",
                                "Method": "get"
                            }
                        }
                    }
                }
            }
        }
    }

    original_deployment_ids = translate_and_find_deployment_ids(manifest)

    # Update API of one Lambda function should redeploy API
    manifest["Resources"]["FirstLambdaFunction"]["Properties"]["Events"]["MyApi"]["Properties"]["Method"] = "post"
    first_updated_deployment_ids = translate_and_find_deployment_ids(manifest)
    assert original_deployment_ids != first_updated_deployment_ids

    # Update API of second Lambda function should redeploy API
    manifest["Resources"]["SecondLambdaFunction"]["Properties"]["Events"]["MyApi"]["Properties"]["Method"] = "post"
    second_updated_deployment_ids = translate_and_find_deployment_ids(manifest)
    assert first_updated_deployment_ids != second_updated_deployment_ids

    # Now, update an unrelated property. This should NOT generate a new deploymentId
    manifest["Resources"]["SecondLambdaFunction"]["Properties"]["Runtime"] = "java"
    assert second_updated_deployment_ids == translate_and_find_deployment_ids(manifest)


def translate_and_find_deployment_ids(manifest):
    parameter_values = get_template_parameter_values()
    output_fragment = transform(manifest, parameter_values, mock_policy_loader)
    print(json.dumps(output_fragment, indent=2))

    deployment_ids = set()
    for key, value in output_fragment["Resources"].items():
        if value["Type"] == "AWS::ApiGateway::Deployment":
            deployment_ids.add(key)

    return deployment_ids


class TestApiGatewayDeploymentResource(TestCase):

    @patch("samtranslator.translator.logical_id_generator.LogicalIdGenerator")
    def test_make_auto_deployable_with_swagger_dict(self, LogicalIdGeneratorMock):
        prefix = "prefix"
        generator_mock = LogicalIdGeneratorMock.return_value
        stage = MagicMock()
        id_val = "SomeLogicalId"
        full_hash = "127e3fb91142ab1ddc5f5446adb094442581a90d"
        generator_mock.gen.return_value = id_val
        generator_mock.get_hash.return_value = full_hash

        swagger = {"a": "b"}
        deployment = ApiGatewayDeployment(logical_id=prefix)
        deployment.make_auto_deployable(stage, swagger=swagger)

        self.assertEquals(deployment.logical_id, id_val)
        self.assertEquals(deployment.Description, "RestApi deployment id: {}".format(full_hash))

        LogicalIdGeneratorMock.assert_called_once_with(prefix, str(swagger))
        generator_mock.gen.assert_called_once_with()
        generator_mock.get_hash.assert_called_once_with(length=40) # getting full SHA
        stage.update_deployment_ref.assert_called_once_with(id_val)

    @patch("samtranslator.translator.logical_id_generator.LogicalIdGenerator")
    def test_make_auto_deployable_no_swagger(self, LogicalIdGeneratorMock):
        prefix = "prefix"
        stage = MagicMock()
        deployment = ApiGatewayDeployment(logical_id=prefix)
        deployment.make_auto_deployable(stage, swagger=None)

        self.assertEquals(deployment.logical_id, prefix)
        self.assertEquals(deployment.Description, None)

        LogicalIdGeneratorMock.assert_not_called()
        stage.update_deployment_ref.assert_not_called()
