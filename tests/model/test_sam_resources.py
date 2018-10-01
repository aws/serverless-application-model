from unittest import TestCase
from mock import patch
import pytest

from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.model import InvalidResourceException
from samtranslator.model.lambda_ import LambdaFunction
from samtranslator.model.sam_resources import SamFunction


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
