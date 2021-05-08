from unittest import TestCase
from mock import patch
import pytest

from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.model import InvalidResourceException
from samtranslator.model.apigatewayv2 import ApiGatewayV2HttpApi
from samtranslator.model.lambda_ import LambdaFunction, LambdaVersion
from samtranslator.model.apigateway import ApiGatewayDeployment, ApiGatewayRestApi
from samtranslator.model.apigateway import ApiGatewayStage
from samtranslator.model.iam import IAMRole
from samtranslator.model.packagetype import IMAGE, ZIP
from samtranslator.model.sam_resources import SamFunction, SamApi, SamHttpApi


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
