from unittest import TestCase
from mock import patch
import pytest

from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.model import InvalidResourceException
from samtranslator.model.lambda_ import LambdaFunction, LambdaVersion
from samtranslator.model.apigateway import ApiGatewayRestApi
from samtranslator.model.apigateway import ApiGatewayDeployment
from samtranslator.model.sam_resources import SamFunction
from samtranslator.model.sam_resources import SamApi


class TestCodeUri(TestCase):
    kwargs = {
        'intrinsics_resolver': IntrinsicsResolver({}),
        'event_resources': [],
        'managed_policy_map': {
            "foo": "bar"
        }
    }

    @patch('boto3.session.Session.region_name', 'ap-southeast-1')
    def test_with_code_uri(self):
        function = SamFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"


        cfnResources = function.to_cloudformation(**self.kwargs)
        generatedFunctionList = [x for x in cfnResources if isinstance(x, LambdaFunction)]
        self.assertEqual(generatedFunctionList.__len__(), 1)
        self.assertEqual(generatedFunctionList[0].Code, {
            "S3Key": "foo.zip",
            "S3Bucket": "foobar",
        })


    @patch('boto3.session.Session.region_name', 'ap-southeast-1')
    def test_with_zip_file(self):
        function = SamFunction("foo")
        function.InlineCode = "hello world"

        cfnResources = function.to_cloudformation(**self.kwargs)
        generatedFunctionList = [x for x in cfnResources if isinstance(x, LambdaFunction)]
        self.assertEqual(generatedFunctionList.__len__(), 1)
        self.assertEqual(generatedFunctionList[0].Code, {
            "ZipFile": "hello world"
        })

    def test_with_no_code_uri_or_zipfile(self):
        function = SamFunction("foo")
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

class TestVersionDescription(TestCase):
    kwargs = {
        'intrinsics_resolver': IntrinsicsResolver({}),
        'event_resources': [],
        'managed_policy_map': {
            "foo": "bar"
        }
    }

    @patch('boto3.session.Session.region_name', 'ap-southeast-1')
    def test_with_version_description(self):
        function = SamFunction("foo")
        test_description = "foobar"

        function.CodeUri = "s3://foobar/foo.zip"
        function.VersionDescription = test_description
        function.AutoPublishAlias = "live"

        cfnResources = function.to_cloudformation(**self.kwargs)
        generateFunctionVersion = [x for x in cfnResources if isinstance(x, LambdaVersion)]
        self.assertEqual(generateFunctionVersion[0].Description, test_description)

class TestOpenApi(TestCase):
    kwargs = {
        'intrinsics_resolver': IntrinsicsResolver({}),
        'event_resources': [],
        'managed_policy_map': {
            "foo": "bar"
        }
    }

    @patch('boto3.session.Session.region_name', 'ap-southeast-1')
    def test_with_open_api_3_no_stage(self):
        api = SamApi("foo")
        api.OpenApiVersion = "3.0"

        resources = api.to_cloudformation(**self.kwargs)
        deployment = [x for x in resources if isinstance(x, ApiGatewayDeployment)]

        self.assertEqual(deployment.__len__(), 1)
        self.assertEqual(deployment[0].StageName, None)

    @patch('boto3.session.Session.region_name', 'ap-southeast-1')
    def test_with_open_api_2_no_stage(self):
        api = SamApi("foo")
        api.OpenApiVersion = "3.0"

        resources = api.to_cloudformation(**self.kwargs)
        deployment = [x for x in resources if isinstance(x, ApiGatewayDeployment)]

        self.assertEqual(deployment.__len__(), 1)
        self.assertEqual(deployment[0].StageName, None)

    @patch('boto3.session.Session.region_name', 'ap-southeast-1')
    def test_with_open_api_bad_value(self):
        api = SamApi("foo")
        api.OpenApiVersion = "5.0"
        with pytest.raises(InvalidResourceException):
            api.to_cloudformation(**self.kwargs)

    @patch('boto3.session.Session.region_name', 'ap-southeast-1')
    def test_with_swagger_no_stage(self):
        api = SamApi("foo")

        resources = api.to_cloudformation(**self.kwargs)
        deployment = [x for x in resources if isinstance(x, ApiGatewayDeployment)]

        self.assertEqual(deployment.__len__(), 1)
        self.assertEqual(deployment[0].StageName, "Stage")
