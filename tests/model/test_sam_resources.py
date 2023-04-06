from unittest import TestCase
from unittest.mock import patch

import pytest
from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.model import InvalidResourceException, ResourceResolver
from samtranslator.model.apigateway import ApiGatewayDeployment, ApiGatewayRestApi, ApiGatewayStage
from samtranslator.model.apigatewayv2 import ApiGatewayV2HttpApi
from samtranslator.model.iam import IAMRole
from samtranslator.model.lambda_ import LambdaFunction, LambdaLayerVersion, LambdaPermission, LambdaUrl, LambdaVersion
from samtranslator.model.packagetype import IMAGE, ZIP
from samtranslator.model.sam_resources import (
    SamApi,
    SamConnector,
    SamFunction,
    SamHttpApi,
    SamLayerVersion,
)


class TestArchitecture(TestCase):
    kwargs = {
        "intrinsics_resolver": IntrinsicsResolver({}),
        "event_resources": [],
        "managed_policy_map": {"foo": "bar"},
    }

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_validate_architecture_with_intrinsic(self):
        function = SamFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"
        function.Architectures = {"Ref": "MyRef"}

        cfnResources = function.to_cloudformation(**self.kwargs)
        generatedFunctionList = [x for x in cfnResources if isinstance(x, LambdaFunction)]
        self.assertEqual(generatedFunctionList.__len__(), 1)
        self.assertEqual(generatedFunctionList[0].Architectures, {"Ref": "MyRef"})

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_valid_architectures(self):
        function = SamFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"
        valid_architectures = (["arm64"], ["x86_64"])

        for architecture in valid_architectures:
            function.Architectures = architecture
            cfnResources = function.to_cloudformation(**self.kwargs)
            generatedFunctionList = [x for x in cfnResources if isinstance(x, LambdaFunction)]
            self.assertEqual(generatedFunctionList.__len__(), 1)
            self.assertEqual(generatedFunctionList[0].Architectures, architecture)


class TestCodeUriandImageUri(TestCase):
    kwargs = {
        "intrinsics_resolver": IntrinsicsResolver({}),
        "event_resources": [],
        "managed_policy_map": {"foo": "bar"},
    }

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_code_uri(self):
        function = SamFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"

        cfnResources = function.to_cloudformation(**self.kwargs)
        generatedFunctionList = [x for x in cfnResources if isinstance(x, LambdaFunction)]
        self.assertEqual(generatedFunctionList.__len__(), 1)
        self.assertEqual(generatedFunctionList[0].Code, {"S3Key": "foo.zip", "S3Bucket": "foobar"})

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_zip_file(self):
        function = SamFunction("foo")
        function.InlineCode = "hello world"
        function.Runtime = "foo"
        function.Handler = "bar"

        cfnResources = function.to_cloudformation(**self.kwargs)
        generatedFunctionList = [x for x in cfnResources if isinstance(x, LambdaFunction)]
        self.assertEqual(generatedFunctionList.__len__(), 1)
        self.assertEqual(generatedFunctionList[0].Code, {"ZipFile": "hello world"})

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_no_code_uri_or_zipfile_or_no_image_uri(self):
        function = SamFunction("foo")
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_image_uri(self):
        function = SamFunction("foo")
        function.ImageUri = "123456789.dkr.ecr.us-east-1.amazonaws.com/myimage:latest"
        function.PackageType = IMAGE
        cfnResources = function.to_cloudformation(**self.kwargs)
        generatedFunctionList = [x for x in cfnResources if isinstance(x, LambdaFunction)]
        self.assertEqual(generatedFunctionList.__len__(), 1)
        self.assertEqual(generatedFunctionList[0].Code, {"ImageUri": function.ImageUri})

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_image_uri_layers_runtime_handler(self):
        function = SamFunction("foo")
        function.ImageUri = "123456789.dkr.ecr.us-east-1.amazonaws.com/myimage:latest"
        function.Layers = ["Layer1"]
        function.Runtime = "foo"
        function.Handler = "bar"
        function.PackageType = IMAGE
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_image_uri_package_type_zip(self):
        function = SamFunction("foo")
        function.ImageUri = "123456789.dkr.ecr.us-east-1.amazonaws.com/myimage:latest"
        function.PackageType = ZIP
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_image_uri_invalid_package_type(self):
        function = SamFunction("foo")
        function.ImageUri = "123456789.dkr.ecr.us-east-1.amazonaws.com/myimage:latest"
        function.PackageType = "fake"
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_image_uri_and_code_uri(self):
        function = SamFunction("foo")
        function.ImageUri = "123456789.dkr.ecr.us-east-1.amazonaws.com/myimage:latest"
        function.CodeUri = "s3://foobar/foo.zip"
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)


class TestAssumeRolePolicyDocument(TestCase):
    kwargs = {
        "intrinsics_resolver": IntrinsicsResolver({}),
        "event_resources": [],
        "managed_policy_map": {"foo": "bar"},
    }

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_assume_role_policy_document(self):
        function = SamFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"

        assume_role_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": ["sts:AssumeRole"],
                    "Effect": "Allow",
                    "Principal": {"Service": ["lambda.amazonaws.com", "edgelambda.amazonaws.com"]},
                }
            ],
        }

        function.AssumeRolePolicyDocument = assume_role_policy_document

        cfnResources = function.to_cloudformation(**self.kwargs)
        generateFunctionVersion = [x for x in cfnResources if isinstance(x, IAMRole)]
        self.assertEqual(generateFunctionVersion[0].AssumeRolePolicyDocument, assume_role_policy_document)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_without_assume_role_policy_document(self):
        function = SamFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"

        assume_role_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {"Action": ["sts:AssumeRole"], "Effect": "Allow", "Principal": {"Service": ["lambda.amazonaws.com"]}}
            ],
        }

        cfnResources = function.to_cloudformation(**self.kwargs)
        generateFunctionVersion = [x for x in cfnResources if isinstance(x, IAMRole)]
        self.assertEqual(generateFunctionVersion[0].AssumeRolePolicyDocument, assume_role_policy_document)


class TestVersionDescription(TestCase):
    kwargs = {
        "intrinsics_resolver": IntrinsicsResolver({}),
        "event_resources": [],
        "managed_policy_map": {"foo": "bar"},
    }

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_version_description(self):
        function = SamFunction("foo")
        test_description = "foobar"

        function.Runtime = "foo"
        function.Handler = "bar"
        function.CodeUri = "s3://foobar/foo.zip"
        function.VersionDescription = test_description
        function.AutoPublishAlias = "live"

        cfnResources = function.to_cloudformation(**self.kwargs)
        generateFunctionVersion = [x for x in cfnResources if isinstance(x, LambdaVersion)]
        self.assertEqual(generateFunctionVersion[0].Description, test_description)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_autopublish_bad_hash(self):
        function = SamFunction("foo")

        function.Runtime = "foo"
        function.Handler = "bar"
        function.CodeUri = "s3://foobar/foo.zip"
        function.AutoPublishAlias = "live"
        function.AutoPublishCodeSha256 = {"Fn::Sub": "${parameter1}"}

        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_autopublish_good_hash(self):
        function = SamFunction("foo")

        function.Runtime = "foo"
        function.Handler = "bar"
        function.CodeUri = "s3://foobar/foo.zip"
        function.AutoPublishAlias = "live"
        function.AutoPublishCodeSha256 = "08240bdc52933ca4f88d5f75fc88cd3228a48feffa9920c735602433b94767ad"

        # confirm no exception thrown
        function.to_cloudformation(**self.kwargs)


class TestOpenApi(TestCase):
    kwargs = {
        "intrinsics_resolver": IntrinsicsResolver({}),
        "event_resources": [],
        "managed_policy_map": {"foo": "bar"},
    }

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_open_api_3_no_stage(self):
        api = SamApi("foo")
        api.OpenApiVersion = "3.0"

        resources = api.to_cloudformation(**self.kwargs)
        deployment = [x for x in resources if isinstance(x, ApiGatewayDeployment)]

        self.assertEqual(deployment.__len__(), 1)
        self.assertEqual(deployment[0].StageName, None)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_open_api_2_no_stage(self):
        api = SamApi("foo")
        api.OpenApiVersion = "3.0"

        resources = api.to_cloudformation(**self.kwargs)
        deployment = [x for x in resources if isinstance(x, ApiGatewayDeployment)]

        self.assertEqual(deployment.__len__(), 1)
        self.assertEqual(deployment[0].StageName, None)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_open_api_bad_value(self):
        api = SamApi("foo")
        api.OpenApiVersion = "5.0"
        with pytest.raises(InvalidResourceException):
            api.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_swagger_no_stage(self):
        api = SamApi("foo")

        resources = api.to_cloudformation(**self.kwargs)
        deployment = [x for x in resources if isinstance(x, ApiGatewayDeployment)]

        self.assertEqual(deployment.__len__(), 1)
        self.assertEqual(deployment[0].StageName, "Stage")


class TestApiTags(TestCase):
    kwargs = {
        "intrinsics_resolver": IntrinsicsResolver({}),
        "event_resources": [],
        "managed_policy_map": {"foo": "bar"},
    }

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_no_tags(self):
        api = SamApi("foo")
        api.Tags = {}

        resources = api.to_cloudformation(**self.kwargs)
        deployment = [x for x in resources if isinstance(x, ApiGatewayStage)]

        self.assertEqual(deployment.__len__(), 1)
        self.assertEqual(deployment[0].Tags, [])

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_tags(self):
        api = SamApi("foo")
        api.Tags = {"MyKey": "MyValue"}

        resources = api.to_cloudformation(**self.kwargs)
        deployment = [x for x in resources if isinstance(x, ApiGatewayStage)]

        self.assertEqual(deployment.__len__(), 1)
        self.assertEqual(deployment[0].Tags, [{"Key": "MyKey", "Value": "MyValue"}])


class TestApiDescription(TestCase):
    kwargs = {
        "intrinsics_resolver": IntrinsicsResolver({}),
        "event_resources": [],
        "managed_policy_map": {"foo": "bar"},
    }

    @patch("boto3.session.Session.region_name", "eu-central-1")
    def test_with_no_description(self):
        sam_api = SamApi("foo")

        resources = sam_api.to_cloudformation(**self.kwargs)
        rest_api = [x for x in resources if isinstance(x, ApiGatewayRestApi)]
        self.assertEqual(rest_api[0].Description, None)

    @patch("boto3.session.Session.region_name", "eu-central-1")
    def test_with_description(self):
        sam_api = SamApi("foo")
        sam_api.Description = "my description"

        resources = sam_api.to_cloudformation(**self.kwargs)
        rest_api = [x for x in resources if isinstance(x, ApiGatewayRestApi)]
        self.assertEqual(rest_api[0].Description, "my description")


class TestHttpApiDescription(TestCase):
    kwargs = {
        "intrinsics_resolver": IntrinsicsResolver({}),
        "event_resources": [],
        "managed_policy_map": {"foo": "bar"},
    }

    @patch("boto3.session.Session.region_name", "eu-central-1")
    def test_with_no_description(self):
        sam_http_api = SamHttpApi("foo")
        sam_http_api.DefinitionBody = {
            "openapi": "3.0.1",
            "paths": {"/foo": {}, "/bar": {}},
            "info": {"description": "existing description"},
        }

        resources = sam_http_api.to_cloudformation(**self.kwargs)
        http_api = [x for x in resources if isinstance(x, ApiGatewayV2HttpApi)]
        self.assertEqual(http_api[0].Body.get("info", {}).get("description"), "existing description")

    @patch("boto3.session.Session.region_name", "eu-central-1")
    def test_with_no_definition_body(self):
        sam_http_api = SamHttpApi("foo")
        sam_http_api.Description = "my description"

        with self.assertRaises(InvalidResourceException) as context:
            sam_http_api.to_cloudformation(**self.kwargs)
        self.assertEqual(
            context.exception.message,
            "Resource with id [foo] is invalid. "
            "Description works only with inline OpenApi specified in the 'DefinitionBody' property.",
        )

    @patch("boto3.session.Session.region_name", "eu-central-1")
    def test_with_description_defined_in_definition_body(self):
        sam_http_api = SamHttpApi("foo")
        sam_http_api.DefinitionBody = {
            "openapi": "3.0.1",
            "paths": {"/foo": {}, "/bar": {}},
            "info": {"description": "existing description"},
        }
        sam_http_api.Description = "new description"

        with self.assertRaises(InvalidResourceException) as context:
            sam_http_api.to_cloudformation(**self.kwargs)
        self.assertEqual(
            context.exception.message,
            "Resource with id [foo] is invalid. "
            "Unable to set Description because it is already defined within inline OpenAPI specified in the "
            "'DefinitionBody' property.",
        )

    @patch("boto3.session.Session.region_name", "eu-central-1")
    def test_with_description_not_defined_in_definition_body(self):
        sam_http_api = SamHttpApi("foo")
        sam_http_api.DefinitionBody = {"openapi": "3.0.1", "paths": {"/foo": {}}, "info": {}}
        sam_http_api.Description = "new description"

        resources = sam_http_api.to_cloudformation(**self.kwargs)
        http_api = [x for x in resources if isinstance(x, ApiGatewayV2HttpApi)]
        self.assertEqual(http_api[0].Body.get("info", {}).get("description"), "new description")


class TestPassthroughResourceAttributes(TestCase):
    def test_with_passthrough_resource_attributes(self):
        expected = {"DeletionPolicy": "Delete", "UpdateReplacePolicy": "Retain", "Condition": "C1"}
        function = SamFunction("foo", attributes=expected)
        attributes = function.get_passthrough_resource_attributes()
        self.assertEqual(attributes, expected)


class TestLayers(TestCase):
    kwargs = {
        "intrinsics_resolver": IntrinsicsResolver({}),
        "event_resources": [],
        "managed_policy_map": {"foo": "bar"},
    }

    def test_basic_layer(self):
        layer = SamLayerVersion("foo")
        layer.ContentUri = "s3://foobar/foo.zip"
        cfnResources = layer.to_cloudformation(**self.kwargs)
        [x for x in cfnResources if isinstance(x, LambdaLayerVersion)]
        self.assertEqual(cfnResources.__len__(), 1)
        self.assertTrue(isinstance(cfnResources[0], LambdaLayerVersion))
        self.assertEqual(cfnResources[0].Content, {"S3Key": "foo.zip", "S3Bucket": "foobar"})

    def test_invalid_compatible_architectures(self):
        layer = SamLayerVersion("foo")
        layer.ContentUri = "s3://foobar/foo.zip"
        invalid_architectures = [["arm"], [1], "arm", 1, True]
        for architecturea in invalid_architectures:
            layer.CompatibleArchitectures = architecturea
            with pytest.raises(InvalidResourceException):
                layer.to_cloudformation(**self.kwargs)


class TestFunctionUrlConfig(TestCase):
    kwargs = {
        "intrinsics_resolver": IntrinsicsResolver({}),
        "event_resources": [],
        "managed_policy_map": {"foo": "bar"},
    }

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_function_url_config_with_no_authorization_type(self):
        function = SamFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"
        function.FunctionUrlConfig = {"Cors": {"AllowOrigins": ["example1.com"]}}
        with pytest.raises(InvalidResourceException) as e:
            function.to_cloudformation(**self.kwargs)
        self.assertEqual(
            str(e.value.message),
            "Resource with id [foo] is invalid. AuthType is required to configure"
            + " function property `FunctionUrlConfig`. Please provide either AWS_IAM or NONE.",
        )

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_function_url_config_with_no_cors_config(self):
        function = SamFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"
        function.FunctionUrlConfig = {"AuthType": "AWS_IAM"}
        cfnResources = function.to_cloudformation(**self.kwargs)
        generatedUrlList = [x for x in cfnResources if isinstance(x, LambdaUrl)]
        self.assertEqual(generatedUrlList.__len__(), 1)
        self.assertEqual(generatedUrlList[0].AuthType, "AWS_IAM")

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_validate_function_url_config_properties_with_intrinsic(self):
        function = SamFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"
        function.FunctionUrlConfig = {
            "AuthType": {"Ref": "AWS_IAM"},
            "Cors": {"Ref": "MyCorConfigRef"},
            "InvokeMode": {"Ref": "MyInvokeMode"},
        }

        cfnResources = function.to_cloudformation(**self.kwargs)
        generatedUrlList = [x for x in cfnResources if isinstance(x, LambdaUrl)]
        self.assertEqual(generatedUrlList.__len__(), 1)
        generatedUrlList = [x for x in cfnResources if isinstance(x, LambdaUrl)]
        self.assertEqual(generatedUrlList.__len__(), 1)
        self.assertEqual(generatedUrlList[0].AuthType, {"Ref": "AWS_IAM"})
        self.assertEqual(generatedUrlList[0].Cors, {"Ref": "MyCorConfigRef"})
        self.assertEqual(generatedUrlList[0].InvokeMode, {"Ref": "MyInvokeMode"})

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_valid_function_url_config(self):
        cors = {
            "AllowOrigins": ["example1.com", "example2.com", "example2.com"],
            "AllowMethods": ["GET"],
            "AllowCredentials": True,
            "AllowHeaders": ["X-Custom-Header"],
            "ExposeHeaders": ["x-amzn-header"],
            "MaxAge": 10,
        }
        function = SamFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"
        function.FunctionUrlConfig = {"AuthType": "NONE", "Cors": cors}

        cfnResources = function.to_cloudformation(**self.kwargs)
        generatedUrlList = [x for x in cfnResources if isinstance(x, LambdaUrl)]
        self.assertEqual(generatedUrlList.__len__(), 1)
        self.assertEqual(generatedUrlList[0].TargetFunctionArn, {"Ref": "foo"})
        self.assertEqual(generatedUrlList[0].AuthType, "NONE")
        self.assertEqual(generatedUrlList[0].Cors, cors)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_valid_function_url_config_with_Intrinsics(self):
        function = SamFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"
        function.FunctionUrlConfig = {"Ref": "MyFunctionUrlConfig"}

        cfnResources = function.to_cloudformation(**self.kwargs)
        generatedUrlList = [x for x in cfnResources if isinstance(x, LambdaUrl)]
        self.assertEqual(generatedUrlList.__len__(), 1)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_function_url_config_with_invalid_cors_parameter(self):
        function = SamFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"
        function.FunctionUrlConfig = {"AuthType": "NONE", "Cors": {"AllowOrigin": ["example1.com"]}}
        with pytest.raises(InvalidResourceException) as e:
            function.to_cloudformation(**self.kwargs)
        self.assertEqual(
            str(e.value.message),
            "Resource with id [foo] is invalid. AllowOrigin is not a valid property for configuring Cors.",
        )

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_function_url_config_with_invalid_cors_parameter_data_type(self):
        function = SamFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"
        function.FunctionUrlConfig = {"AuthType": "NONE", "Cors": {"AllowOrigins": "example1.com"}}
        with pytest.raises(InvalidResourceException) as e:
            function.to_cloudformation(**self.kwargs)
        self.assertEqual(
            str(e.value.message),
            "Resource with id [foo] is invalid. AllowOrigins must be of type list.",
        )

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_valid_function_url_config_with(self):
        function = SamFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"
        function.FunctionUrlConfig = {"AuthType": "NONE", "Cors": {"AllowOrigins": ["example1.com"]}}

        cfnResources = function.to_cloudformation(**self.kwargs)
        generatedUrlList = [x for x in cfnResources if isinstance(x, LambdaUrl)]
        self.assertEqual(generatedUrlList.__len__(), 1)
        expected_url_logicalid = {"Ref": "foo"}
        self.assertEqual(generatedUrlList[0].TargetFunctionArn, expected_url_logicalid)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_valid_function_url_config_with_lambda_permission(self):
        function = SamFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"
        function.FunctionUrlConfig = {"AuthType": "NONE", "Cors": {"AllowOrigins": ["example1.com"]}}

        cfnResources = function.to_cloudformation(**self.kwargs)
        generatedUrlList = [x for x in cfnResources if isinstance(x, LambdaPermission)]
        self.assertEqual(generatedUrlList.__len__(), 1)
        self.assertEqual(generatedUrlList[0].Action, "lambda:InvokeFunctionUrl")
        self.assertEqual(generatedUrlList[0].FunctionName, {"Ref": "foo"})
        self.assertEqual(generatedUrlList[0].Principal, "*")
        self.assertEqual(generatedUrlList[0].FunctionUrlAuthType, "NONE")

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_invalid_function_url_config_with_authorization_type_value_as_None(self):
        function = SamFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"
        function.FunctionUrlConfig = {"AuthType": None}

        with pytest.raises(InvalidResourceException) as e:
            function.to_cloudformation(**self.kwargs)
        self.assertEqual(
            str(e.value.message),
            "Resource with id [foo] is invalid. AuthType is required to configure function property "
            + "`FunctionUrlConfig`. Please provide either AWS_IAM or NONE.",
        )

    def test_with_function_url_config_with_invoke_mode(self):
        function = SamFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"
        function.FunctionUrlConfig = {"AuthType": "AWS_IAM", "InvokeMode": "RESPONSE_STREAM"}
        cfnResources = function.to_cloudformation(**self.kwargs)
        generatedUrlList = [x for x in cfnResources if isinstance(x, LambdaUrl)]
        self.assertEqual(generatedUrlList.__len__(), 1)
        self.assertEqual(generatedUrlList[0].AuthType, "AWS_IAM")
        self.assertEqual(generatedUrlList[0].InvokeMode, "RESPONSE_STREAM")


class TestInvalidSamConnectors(TestCase):
    kwargs = {
        "resource_resolver": ResourceResolver(
            {
                "notype": {"Properties": {}},
                "func": {},
                "func2": {
                    "Type": "AWS::Lambda::Function",
                    "Properties": {},
                },
                "func3": {
                    "Type": "AWS::Lambda::Function",
                    "Properties": {
                        "Role": "arn:aws:iam:123456789012:role/roleName",
                    },
                },
                "table": {
                    "Type": "AWS::DynamoDB::Table",
                },
                "sqs": {
                    "Type": "AWS::SQS::Queue",
                },
                "sns": {
                    "Type": "AWS::SNS::Topic",
                    "Properties": {
                        "Subscription": [
                            {
                                "Protocol": "lambda",
                                "Endpoint": {
                                    "Fn::GetAtt": ["sqs", "Arn"],
                                },
                            }
                        ]
                    },
                },
            }
        ),
        "original_template": {},
    }

    def test_invalid_source_without_id_connector(self):
        connector = SamConnector("foo")
        connector.Source = {"1": "2"}
        connector.Destination = {"1": "2"}
        connector.Permissions = ["Read"]
        with self.assertRaisesRegex(InvalidResourceException, ".+'Type' is missing or not a string."):
            connector.to_cloudformation(**self.kwargs)[0]

    def test_unknown_type_connector(self):
        connector = SamConnector("foo")
        connector.Source = {"Id": "notype"}
        connector.Destination = {"Id": "table"}
        connector.Permissions = ["Read"]
        with self.assertRaisesRegex(InvalidResourceException, ".+'Type' is missing or not a string."):
            connector.to_cloudformation(**self.kwargs)[0]

    def test_unknown_rolename_connector(self):
        connector = SamConnector("foo")
        connector.Source = {"Id": "func2"}
        connector.Destination = {"Id": "table"}
        connector.Permissions = ["Read"]
        with self.assertRaisesRegex(InvalidResourceException, ".+Unable to get IAM role name from 'Source' resource.+"):
            connector.to_cloudformation(**self.kwargs)[0]

    def test_unsupported_permissions_connector(self):
        connector = SamConnector("foo")
        connector.Source = {"Id": "func2"}
        connector.Destination = {"Id": "table"}
        connector.Permissions = ["INVOKE"]
        with self.assertRaisesRegex(
            InvalidResourceException,
            ".+Unsupported 'Permissions' provided for connector from AWS::Lambda::Function to AWS::DynamoDB::Table; valid values are: Read, Write.",
        ):
            connector.to_cloudformation(**self.kwargs)[0]

    def test_unsupported_permissions_connector_with_one_supported_permission(self):
        connector = SamConnector("foo")
        connector.Source = {"Id": "table"}
        connector.Destination = {"Id": "func2"}
        connector.Permissions = ["INVOKE"]
        with self.assertRaisesRegex(
            InvalidResourceException,
            ".+Unsupported 'Permissions' provided for connector from AWS::DynamoDB::Table to AWS::Lambda::Function; valid values are: Read.",
        ):
            connector.to_cloudformation(**self.kwargs)[0]

    def test_unsupported_permissions_combination(self):
        connector = SamConnector("foo")
        connector.Source = {"Id": "sqs"}
        connector.Destination = {"Id": "func2"}
        connector.Permissions = ["Read"]
        with self.assertRaisesRegex(
            InvalidResourceException,
            "Unsupported 'Permissions' provided for connector from AWS::SQS::Queue to AWS::Lambda::Function; valid combinations are: Read \\+ Write.",
        ):
            connector.to_cloudformation(**self.kwargs)[0]
