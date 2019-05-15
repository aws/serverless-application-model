from unittest import TestCase
from mock import patch
import pytest

from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.model import InvalidResourceException
from samtranslator.model.lambda_ import LambdaFunction, LambdaVersion
from samtranslator.model.appsync import AppSyncApi, AppSyncApiSchema
from samtranslator.model.sam_resources import SamFunction, SamGraphApi


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

class TestGraphAPISchemaUri(TestCase):
    kwargs = {
        'intrinsics_resolver': IntrinsicsResolver({}),
        'event_resources': [],
        'managed_policy_map': {
            "foo": "bar"
        }
    }

    @patch('boto3.session.Session.region_name', 'ap-southeast-1')
    def test_with_schema_uri(self):
        api = SamGraphApi("foo")
        test_schema = "s3://foobar/foo.gql"

        api.Name = "FooApi"
        api.AuthenticationType = "API_KEY"
        api.LogConfig = {
            'Enabled': True
        }
        api.SchemaDefinitionUri = test_schema
        api.ApiKeys = [None, None]

        cfnResources = api.to_cloudformation(**self.kwargs)
        generatedApiList = [x for x in cfnResources if isinstance(x, AppSyncApi)]
        generatedApiSchema = [x for x in cfnResources if isinstance(x, AppSyncApiSchema)]
        self.assertEqual(generatedApiList.__len__(), 1)
        self.assertEqual(generatedApiSchema[0].DefinitionS3Location, test_schema)
