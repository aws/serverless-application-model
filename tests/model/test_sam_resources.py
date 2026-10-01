from unittest import TestCase
from unittest.mock import patch

import pytest
from parameterized import parameterized
from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.model import InvalidResourceException, ResourceResolver
from samtranslator.model.apigateway import ApiGatewayDeployment, ApiGatewayRestApi, ApiGatewayStage
from samtranslator.model.apigatewayv2 import ApiGatewayV2HttpApi
from samtranslator.model.iam import IAMRole
from samtranslator.model.lambda_ import (
    LambdaFunction,
    LambdaLayerVersion,
    LambdaPermission,
    LambdaUrl,
    LambdaVersion,
    LambdaWebFunction,
    LambdaWebFunctionEndpoint,
    LambdaWebFunctionRevision,
)
from samtranslator.model.packagetype import IMAGE, ZIP
from samtranslator.model.sam_resources import (
    SamApi,
    SamCapacityProvider,
    SamConnector,
    SamFunction,
    SamGraphQLApi,
    SamHttpApi,
    SamLayerVersion,
    SamWebFunction,
)


class TestArchitecture(TestCase):
    kwargs = {
        "intrinsics_resolver": IntrinsicsResolver({}),
        "event_resources": [],
        "managed_policy_map": {"foo": "bar"},
        "resource_resolver": ResourceResolver({}),
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
        "resource_resolver": ResourceResolver({}),
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
        "resource_resolver": ResourceResolver({}),
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
        "resource_resolver": ResourceResolver({}),
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

        function.Runtime = "foobar"
        function.Handler = "bar"
        function.CodeUri = "s3://foobar/foo.zip"
        function.AutoPublishAlias = "live"
        function.AutoPublishCodeSha256 = "08240bdc52933ca4f88d5f75fc88cd3228a48feffa9920c735602433b94767ad"

        # confirm no exception thrown
        function.to_cloudformation(**self.kwargs)


class TestWebFunctionBuildConfig(TestCase):
    kwargs = {
        "intrinsics_resolver": IntrinsicsResolver({}),
        "event_resources": [],
        "managed_policy_map": {"foo": "bar"},
        "resource_resolver": ResourceResolver({}),
    }

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_code_uri(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        cfnResources = function.to_cloudformation(**self.kwargs)
        revisions = [x for x in cfnResources if isinstance(x, LambdaWebFunctionRevision)]
        self.assertEqual(len(revisions), 1)
        self.assertEqual(revisions[0].BuildConfig["CodeConfig"]["S3Object"], {"Key": "foo.zip", "Bucket": "foobar"})

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_no_code_uri_or_no_inline(self):
        function = SamWebFunction("foo")
        function.Runtime = "foobar"
        function.AuthType = "IamAuth"
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_both_code_uri_and_inline(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.InlineCode = "hello world"
        function.AuthType = "IamAuth"
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_no_runtime(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.AuthType = "IamAuth"
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)


class TestWebFunctionRegions(TestCase):
    kwargs = {
        "intrinsics_resolver": IntrinsicsResolver({}),
        "event_resources": [],
        "managed_policy_map": {"foo": "bar"},
        "resource_resolver": ResourceResolver({}),
    }

    def test_with_regions_flatlist(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.ReplicaRegions = ["us-east-1", "us-east-1", "eu-west-1"]
        cfnResources = function.to_cloudformation(**self.kwargs)
        endpoints = [x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint)]
        self.assertEqual(len(endpoints), 1)
        self.assertCountEqual(endpoints[0].Regions, ["us-east-1", "eu-west-1"])

    def test_with_flatlist_enum(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.ReplicaRegions = ["US"]
        cfnResources = function.to_cloudformation(**self.kwargs)
        endpoints = [x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint)]
        self.assertEqual(len(endpoints), 1)
        self.assertCountEqual(endpoints[0].Regions, ["us-east-1", "us-east-2", "us-west-1", "us-west-2"])

    def test_with_include_exclude_regions(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.ReplicaRegions = {"IncludeRegions": ["US"], "ExcludeRegions": ["us-east-1"]}
        cfnResources = function.to_cloudformation(**self.kwargs)
        endpoints = [x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint)]
        self.assertEqual(len(endpoints), 1)
        self.assertCountEqual(endpoints[0].Regions, ["us-east-2", "us-west-1", "us-west-2"])

    def test_with_all_standard(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.ReplicaRegions = ["ALL_STANDARD"]
        cfnResources = function.to_cloudformation(**self.kwargs)
        endpoints = [x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint)]
        self.assertEqual(len(endpoints), 1)
        self.assertCountEqual(
            endpoints[0].Regions,
            [
                "us-east-1",
                "us-east-2",
                "us-west-1",
                "us-west-2",
                "ap-south-1",
                "ap-northeast-1",
                "ap-northeast-2",
                "ap-northeast-3",
                "ap-southeast-1",
                "ap-southeast-2",
                "ca-central-1",
                "eu-west-1",
                "eu-west-2",
                "eu-west-3",
                "eu-central-1",
                "eu-north-1",
                "sa-east-1",
            ],
        )

    def test_with_lowercase_enum(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.ReplicaRegions = {"IncludeRegions": ["us"]}
        cfnResources = function.to_cloudformation(**self.kwargs)
        endpoints = [x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint)]
        self.assertEqual(len(endpoints), 1)
        self.assertCountEqual(endpoints[0].Regions, ["us-east-1", "us-east-2", "us-west-1", "us-west-2"])

    def test_with_enum_and_individual(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.ReplicaRegions = {"IncludeRegions": ["ALL_STANDARD", "af-south-1"]}
        cfnResources = function.to_cloudformation(**self.kwargs)
        endpoints = [x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint)]
        self.assertEqual(len(endpoints), 1)
        self.assertCountEqual(
            endpoints[0].Regions,
            [
                "us-east-1",
                "us-east-2",
                "us-west-1",
                "us-west-2",
                "ap-south-1",
                "ap-northeast-1",
                "ap-northeast-2",
                "ap-northeast-3",
                "ap-southeast-1",
                "ap-southeast-2",
                "ca-central-1",
                "eu-west-1",
                "eu-west-2",
                "eu-west-3",
                "eu-central-1",
                "eu-north-1",
                "sa-east-1",
                "af-south-1",
            ],
        )

    def test_with_invalid_region(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.ReplicaRegions = ["USA"]
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    def test_with_only_exclude_regions_raises(self):
        # ExcludeRegions without IncludeRegions would silently yield an empty region list; require both.
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.ReplicaRegions = {"ExcludeRegions": ["US"]}
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    def test_replica_regions_top_level_intrinsic_passthrough(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.ReplicaRegions = {"Ref": "RegionList"}
        cfnResources = function.to_cloudformation(**self.kwargs)
        endpoints = [x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint)]
        self.assertEqual(endpoints[0].Regions, {"Ref": "RegionList"})

    def test_flatlist_with_intrinsic_entry(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.ReplicaRegions = ["us-east-1", {"Ref": "ExtraRegion"}]
        cfnResources = function.to_cloudformation(**self.kwargs)
        endpoints = [x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint)]
        self.assertEqual(endpoints[0].Regions, ["us-east-1", {"Ref": "ExtraRegion"}])

    def test_include_regions_with_intrinsic_entry(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.ReplicaRegions = {"IncludeRegions": ["us-east-1", {"Ref": "ExtraRegion"}]}
        cfnResources = function.to_cloudformation(**self.kwargs)
        endpoints = [x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint)]
        self.assertEqual(endpoints[0].Regions, ["us-east-1", {"Ref": "ExtraRegion"}])

    def test_include_regions_top_level_intrinsic_raises(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.ReplicaRegions = {"IncludeRegions": {"Ref": "Regions"}}
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    def test_exclude_regions_intrinsic_entry_raises(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.ReplicaRegions = {"IncludeRegions": ["US"], "ExcludeRegions": [{"Ref": "Skip"}]}
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    def test_exclude_with_only_intrinsic_include_raises(self):
        # Exclusions cannot be applied to an intrinsic include at transform time.
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.ReplicaRegions = {"IncludeRegions": [{"Ref": "RegionParam"}], "ExcludeRegions": ["us-west-2"]}
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    def test_exclude_with_mixed_string_and_intrinsic_include_raises(self):
        # Even with a string include present, the intrinsic include portion cannot honor the exclusion.
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.ReplicaRegions = {
            "IncludeRegions": ["US", {"Ref": "RegionParam"}],
            "ExcludeRegions": ["us-west-2"],
        }
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    def test_replica_regions_unknown_key_raises(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.ReplicaRegions = {"IncludeRegionz": ["US"]}
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)


class TestWebFunctionConfigs(TestCase):
    kwargs = {
        "intrinsics_resolver": IntrinsicsResolver({}),
        "event_resources": [],
        "managed_policy_map": {"foo": "bar"},
        "resource_resolver": ResourceResolver({}),
    }

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_produces_four_resources(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        cfnResources = function.to_cloudformation(**self.kwargs)
        self.assertEqual(len([x for x in cfnResources if isinstance(x, IAMRole)]), 1)
        self.assertEqual(len([x for x in cfnResources if isinstance(x, LambdaWebFunction)]), 1)
        self.assertEqual(len([x for x in cfnResources if isinstance(x, LambdaWebFunctionRevision)]), 1)
        self.assertEqual(len([x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint)]), 1)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_generated_function_name_uses_logical_id_and_stack_guid(self):
        function = SamWebFunction("MyWebFunction")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        cfnResources = function.to_cloudformation(**self.kwargs)
        fn = next(x for x in cfnResources if isinstance(x, LambdaWebFunction))
        self.assertEqual(fn.FunctionName["Fn::Sub"][0], "MyWebFunction-${StackIdSuffix}")

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_generated_function_name_bounds_long_logical_id(self):
        # FunctionName limit is 64; the 8-char stack GUID suffix plus a separator leave a 55-char budget for
        # the logical ID, so the resolved name can never exceed the limit (55 + 1 + 8 = 64).
        logical_id = "A" * 200
        function = SamWebFunction(logical_id)
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        cfnResources = function.to_cloudformation(**self.kwargs)
        fn = next(x for x in cfnResources if isinstance(x, LambdaWebFunction))
        template = fn.FunctionName["Fn::Sub"][0]
        self.assertEqual(template, "A" * 55 + "-${StackIdSuffix}")
        # Worst-case resolved length stays within the 64-char FunctionName limit
        self.assertLessEqual(55 + 1 + 8, 64)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_generated_function_name_shared_by_all_resources(self):
        # Ref on AWS::Lambda::WebFunction returns the ARN, so the revision and endpoint must reuse the same
        # generated name value as the function rather than Ref it.
        function = SamWebFunction("MyWebFunction")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        cfnResources = function.to_cloudformation(**self.kwargs)
        fn = next(x for x in cfnResources if isinstance(x, LambdaWebFunction))
        revision = next(x for x in cfnResources if isinstance(x, LambdaWebFunctionRevision))
        endpoint = next(x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint))
        self.assertEqual(revision.FunctionName, fn.FunctionName)
        self.assertEqual(endpoint.FunctionName, fn.FunctionName)
        # And specifically NOT a bare Ref (which resolves to the ARN)
        self.assertNotEqual(revision.FunctionName, {"Ref": "MyWebFunction"})
        self.assertNotEqual(endpoint.FunctionName, {"Ref": "MyWebFunction"})

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_webfunction_name_runtime_attr_is_not_ref(self):
        # Ref resolves to the ARN, so get_runtime_attr("name") must return the FunctionName value, not a Ref.
        function = SamWebFunction("MyWebFunction")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        cfnResources = function.to_cloudformation(**self.kwargs)
        fn = next(x for x in cfnResources if isinstance(x, LambdaWebFunction))
        self.assertEqual(fn.get_runtime_attr("name"), fn.FunctionName)
        self.assertNotEqual(fn.get_runtime_attr("name"), {"Ref": "MyWebFunction"})

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_explicit_function_name_shared_by_all_resources(self):
        function = SamWebFunction("MyWebFunction")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.FunctionName = "my-explicit-name"
        cfnResources = function.to_cloudformation(**self.kwargs)
        fn = next(x for x in cfnResources if isinstance(x, LambdaWebFunction))
        revision = next(x for x in cfnResources if isinstance(x, LambdaWebFunctionRevision))
        endpoint = next(x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint))
        self.assertEqual(fn.FunctionName, "my-explicit-name")
        self.assertEqual(revision.FunctionName, "my-explicit-name")
        self.assertEqual(endpoint.FunctionName, "my-explicit-name")

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_default_service_config(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        cfnResources = function.to_cloudformation(**self.kwargs)
        revisions = [x for x in cfnResources if isinstance(x, LambdaWebFunctionRevision)]
        self.assertEqual(revisions[0].ServiceConfig["TimeoutSeconds"], 30)
        self.assertIn("ExecutionRoleArn", revisions[0].ServiceConfig)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_custom_timeout(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.Timeout = 120
        cfnResources = function.to_cloudformation(**self.kwargs)
        revisions = [x for x in cfnResources if isinstance(x, LambdaWebFunctionRevision)]
        self.assertEqual(revisions[0].ServiceConfig["TimeoutSeconds"], 120)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_service_config(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.ExecutionRoleArn = "arn:aws:iam::123456789012:role/execution_role"
        function.EntryPoint = "app.js"
        cfnResources = function.to_cloudformation(**self.kwargs)
        revisions = [x for x in cfnResources if isinstance(x, LambdaWebFunctionRevision)]
        self.assertEqual(revisions[0].ServiceConfig["EnvironmentVariables"], {"AWS_LAMBDA_NODEJS_ENTRYPOINT": "app.js"})
        self.assertEqual(
            revisions[0].ServiceConfig["ExecutionRoleArn"], "arn:aws:iam::123456789012:role/execution_role"
        )

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_max_concurrency_per_environment_passthrough(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.MaxConcurrencyPerEnvironment = 100
        cfnResources = function.to_cloudformation(**self.kwargs)
        revisions = [x for x in cfnResources if isinstance(x, LambdaWebFunctionRevision)]
        self.assertEqual(revisions[0].ServiceConfig["MaxConcurrencyPerEnvironment"], 100)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_endpoint_scaling_throttle_and_description_passthrough(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.EndpointDescription = "prod endpoint"
        function.ScalingConfig = {"MaxEnvironments": 50}
        function.ThrottleConfig = {"RateLimit": 5000}
        cfnResources = function.to_cloudformation(**self.kwargs)
        endpoints = [x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint)]
        self.assertEqual(endpoints[0].Description, "prod endpoint")
        self.assertEqual(endpoints[0].ScalingConfig, {"MaxEnvironments": 50})
        self.assertEqual(endpoints[0].ThrottleConfig, {"RateLimit": 5000})

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_endpoint_defaults(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        cfnResources = function.to_cloudformation(**self.kwargs)
        endpoints = [x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint)]
        self.assertEqual(endpoints[0].EndpointName, "prod")
        self.assertEqual(endpoints[0].EndpointType, "HomeRegion")
        self.assertEqual(endpoints[0].AuthType, "IamAuth")

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_endpoint_custom_values(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.EndpointName = "staging"
        function.EndpointType = "MultiRegion"
        function.AuthType = "IamAuth"
        function.AutoDeploymentMode = "Disabled"
        function.RevisionWeights = {"rev-abc": 100}
        cfnResources = function.to_cloudformation(**self.kwargs)
        endpoints = [x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint)]
        self.assertEqual(endpoints[0].EndpointName, "staging")
        self.assertEqual(endpoints[0].EndpointType, "MultiRegion")
        self.assertEqual(endpoints[0].AuthType, "IamAuth")

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_validation_latest_revision_with_routing(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.AutoDeploymentMode = "LatestRevision"
        function.RevisionWeights = {"rev-123": 100}
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_validation_multiregion_with_latest_revision(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.EndpointType = "MultiRegion"
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_validation_disabled_without_revision_weights(self):
        # HomeRegion 'Disabled' with no RevisionWeights would be identical to 'LatestRevision' — reject it.
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.AutoDeploymentMode = "Disabled"
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_multiregion_disabled_without_revision_weights_uses_initial_revision(self):
        # MultiRegion mandates 'Disabled' but may omit RevisionWeights; the endpoint then pins 100% to the
        # revision created in this same stack (via GetAtt), enabling a single-shot MultiRegion create.
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.EndpointType = "MultiRegion"
        function.AutoDeploymentMode = "Disabled"
        cfnResources = function.to_cloudformation(**self.kwargs)
        endpoint = next(x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint))
        self.assertEqual(endpoint.EndpointType, "MultiRegion")
        self.assertEqual(
            endpoint.RevisionWeights,
            [{"RevisionId": {"Fn::GetAtt": ["fooRevision", "RevisionId"]}, "Weight": 100}],
        )

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_validation_perregion_with_latest_revision(self):
        # PerRegion shares MultiRegion's rules: it mandates 'Disabled', so 'LatestRevision' (the default) fails.
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.EndpointType = "PerRegion"
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_perregion_disabled_without_revision_weights_uses_initial_revision(self):
        # PerRegion mandates 'Disabled' but may omit RevisionWeights; like MultiRegion the endpoint then pins
        # 100% to the revision created in this same stack and emits the replica Regions as per-Region endpoints.
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.EndpointType = "PerRegion"
        function.AutoDeploymentMode = "Disabled"
        function.ReplicaRegions = {"IncludeRegions": ["us-west-2", "us-east-1"]}
        cfnResources = function.to_cloudformation(**self.kwargs)
        endpoint = next(x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint))
        self.assertEqual(endpoint.EndpointType, "PerRegion")
        self.assertEqual(
            endpoint.RevisionWeights,
            [{"RevisionId": {"Fn::GetAtt": ["fooRevision", "RevisionId"]}, "Weight": 100}],
        )
        self.assertEqual(endpoint.Regions, ["us-east-1", "us-west-2"])

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_manual_revision_routing(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.AutoDeploymentMode = "Disabled"
        function.RevisionWeights = {"rev-abc": 80, "rev-def": 20}
        cfnResources = function.to_cloudformation(**self.kwargs)
        endpoints = [x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint)]
        self.assertCountEqual(
            endpoints[0].RevisionWeights,
            [{"RevisionId": "rev-abc", "Weight": 80}, {"RevisionId": "rev-def", "Weight": 20}],
        )

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_revision_weights_with_intrinsic_value(self):
        # Individual weight values may be intrinsics; the map is still converted to the list shape.
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.AutoDeploymentMode = "Disabled"
        function.RevisionWeights = {"rev-abc": {"Ref": "WeightA"}, "rev-def": {"Ref": "WeightB"}}
        cfnResources = function.to_cloudformation(**self.kwargs)
        endpoints = [x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint)]
        self.assertCountEqual(
            endpoints[0].RevisionWeights,
            [
                {"RevisionId": "rev-abc", "Weight": {"Ref": "WeightA"}},
                {"RevisionId": "rev-def", "Weight": {"Ref": "WeightB"}},
            ],
        )

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_revision_weights_top_level_intrinsic_raises(self):
        # A top-level intrinsic map (e.g. Fn::If) cannot be converted to the endpoint's list shape.
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.AutoDeploymentMode = "Disabled"
        function.RevisionWeights = {"Fn::If": ["Cond", {"rev-a": 100}, {"rev-b": 100}]}
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_revision_weight_zero_raises(self):
        # A 0 weight sums to 100 but violates the service's [1, 100] range; reject at transform time.
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.AutoDeploymentMode = "Disabled"
        function.RevisionWeights = {"rev-a": 0, "rev-b": 100}
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_revision_weight_out_of_range_raises(self):
        # Sums to 100 but individual weights fall outside [1, 100].
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.AutoDeploymentMode = "Disabled"
        function.RevisionWeights = {"rev-a": 120, "rev-b": -20}
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_auto_deployment_mode_resolved_intrinsic(self):
        # A Ref that resolves to a concrete mode is honored: "Disabled" allows RevisionWeights.
        kwargs = dict(self.kwargs)
        kwargs["intrinsics_resolver"] = IntrinsicsResolver({"Mode": "Disabled"})
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.AutoDeploymentMode = {"Ref": "Mode"}
        function.RevisionWeights = {"rev-abc": 100}
        cfnResources = function.to_cloudformation(**kwargs)
        endpoints = [x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint)]
        self.assertEqual(endpoints[0].RevisionWeights, [{"RevisionId": "rev-abc", "Weight": 100}])

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_auto_deployment_mode_resolved_intrinsic_conflicts_with_weights(self):
        # Resolves to "LatestRevision", which forbids RevisionWeights.
        kwargs = dict(self.kwargs)
        kwargs["intrinsics_resolver"] = IntrinsicsResolver({"Mode": "LatestRevision"})
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.AutoDeploymentMode = {"Ref": "Mode"}
        function.RevisionWeights = {"rev-abc": 100}
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_auto_deployment_mode_unresolved_intrinsic_raises(self):
        # AutoDeploymentMode is SAM-only and never reaches CFN; an unresolved Ref must be rejected.
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.AutoDeploymentMode = {"Ref": "Unknown"}
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_auto_deployment_mode_resolved_to_invalid_raises(self):
        kwargs = dict(self.kwargs)
        kwargs["intrinsics_resolver"] = IntrinsicsResolver({"Mode": "Nonsense"})
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.AutoDeploymentMode = {"Ref": "Mode"}
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_endpoint_type_unresolved_intrinsic_passthrough(self):
        # EndpointType IS a CFN property, so an unresolved intrinsic is passed through and the
        # MultiRegion constraint is not enforced.
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.EndpointType = {"Ref": "EpType"}
        cfnResources = function.to_cloudformation(**self.kwargs)
        endpoints = [x for x in cfnResources if isinstance(x, LambdaWebFunctionEndpoint)]
        self.assertEqual(endpoints[0].EndpointType, {"Ref": "EpType"})

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_endpoint_type_resolved_multiregion_requires_disabled(self):
        kwargs = dict(self.kwargs)
        kwargs["intrinsics_resolver"] = IntrinsicsResolver({"EpType": "MultiRegion"})
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.EndpointType = {"Ref": "EpType"}
        # AutoDeploymentMode defaults to LatestRevision, which is invalid for MultiRegion.
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_timeout_below_minimum_raises(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.Timeout = 1
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_timeout_above_maximum_raises(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.Timeout = 901
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_invalid_env_var_key_raises(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.EnvironmentVariables = {"1BAD": "value"}
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_leading_underscore_env_var_key_raises(self):
        # The service key pattern requires a leading letter (no leading underscore); reject it here so it
        # fails at transform time rather than at stack creation.
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.EnvironmentVariables = {"_FOO": "value"}
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_empty_env_var_value_raises(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.EnvironmentVariables = {"MY_VAR": ""}
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_env_var_value_too_long_raises(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.EnvironmentVariables = {"MY_VAR": "x" * 4097}
        with pytest.raises(InvalidResourceException):
            function.to_cloudformation(**self.kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_intrinsic_env_vars_with_entrypoint_raises(self):
        function = SamWebFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "bar"
        function.AuthType = "IamAuth"
        function.EnvironmentVariables = {"Fn::If": ["Cond", {"A": "1"}, {"B": "2"}]}
        function.EntryPoint = "app.js"
        with pytest.raises(InvalidResourceException):
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
        "resource_resolver": ResourceResolver({}),
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
        self.assertEqual(generatedUrlList.__len__(), 2)
        for permission in generatedUrlList:
            self.assertEqual(permission.FunctionName, {"Ref": "foo"})
            self.assertEqual(permission.Principal, "*")
            self.assertTrue(permission.Action in ["lambda:InvokeFunctionUrl", "lambda:InvokeFunction"])
            if permission.Action == "lambda:InvokeFunctionUrl":
                self.assertEqual(permission.FunctionUrlAuthType, "NONE")
            if permission.Action == "lambda:InvokeFunction":
                self.assertEqual(permission.InvokedViaFunctionUrl, True)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_with_aws_iam_function_url_config_with_lambda_permission(self):
        function = SamFunction("foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"
        # When create FURL with AWS_IAM
        function.FunctionUrlConfig = {"AuthType": "AWS_IAM"}

        cfnResources = function.to_cloudformation(**self.kwargs)
        generatedUrlList = [x for x in cfnResources if isinstance(x, LambdaPermission)]
        # Then no permisssion should be auto created
        self.assertEqual(generatedUrlList.__len__(), 0)

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


def test_function_datasource_set_with_none():
    api = SamGraphQLApi("MyApi")
    none_datasource = api._construct_none_datasource("foo")
    assert none_datasource


class TestSamFunctionRoleResolver(TestCase):
    """
    Tests for resolving IAM role property values in SamFunction
    """

    def setUp(self):
        self.function = SamFunction("foo")
        self.function.CodeUri = "s3://foobar/foo.zip"
        self.function.Runtime = "foo"
        self.function.Handler = "bar"
        self.kwargs = {
            "intrinsics_resolver": IntrinsicsResolver({}),
            "event_resources": [],
            "managed_policy_map": {},
            "resource_resolver": ResourceResolver({}),
            "conditions": {"Conditions": {}},
        }

    def test_role_none_creates_execution_role(self):
        self.function.Role = None
        cfn_resources = self.function.to_cloudformation(**self.kwargs)
        generated_roles = [x for x in cfn_resources if isinstance(x, IAMRole)]

        self.assertEqual(len(generated_roles), 1)  # Should create execution role

    def test_role_explicit_arn_no_execution_role(self):
        test_role = "arn:aws:iam::123456789012:role/existing-role"
        self.function.Role = test_role

        cfn_resources = self.function.to_cloudformation(**self.kwargs)
        generated_roles = [x for x in cfn_resources if isinstance(x, IAMRole)]
        lambda_function = next(r for r in cfn_resources if r.resource_type == "AWS::Lambda::Function")

        self.assertEqual(len(generated_roles), 0)  # Should not create execution role
        self.assertEqual(lambda_function.Role, test_role)

    def test_role_fn_if_no_aws_no_value_keeps_original(self):
        role_conditional = {
            "Fn::If": ["Condition", "arn:aws:iam::123456789012:role/existing-role", {"Ref": "iamRoleArn"}]
        }
        self.function.Role = role_conditional

        kwargs = dict(self.kwargs)
        kwargs["conditions"] = {"Condition": True}

        cfn_resources = self.function.to_cloudformation(**self.kwargs)
        generated_roles = [x for x in cfn_resources if isinstance(x, IAMRole)]
        lambda_function = next(r for r in cfn_resources if r.resource_type == "AWS::Lambda::Function")

        # Should not create a role if a role is passed in for both cases
        self.assertEqual(len(generated_roles), 0)
        self.assertEqual(lambda_function.Role, role_conditional)

    def test_role_fn_if_both_no_value_creates_execution_role(self):
        role_conditional = {"Fn::If": ["Condition", {"Ref": "AWS::NoValue"}, {"Ref": "AWS::NoValue"}]}
        self.function.Role = role_conditional

        kwargs = dict(self.kwargs)
        kwargs["conditions"] = {"Condition": True}

        cfn_resources = self.function.to_cloudformation(**self.kwargs)
        generated_roles = [x for x in cfn_resources if isinstance(x, IAMRole)]

        self.assertEqual(len(generated_roles), 1)

    def test_role_fn_if_first_no_value_creates_conditional_role(self):
        role_conditional = {"Fn::If": ["Condition", {"Ref": "AWS::NoValue"}, {"Ref": "iamRoleArn"}]}
        self.function.Role = role_conditional

        kwargs = dict(self.kwargs)
        kwargs["conditions"] = {"Condition": True}

        cfn_resources = self.function.to_cloudformation(**self.kwargs)
        generated_roles = [x for x in cfn_resources if isinstance(x, IAMRole)]
        lambda_function = next(r for r in cfn_resources if r.resource_type == "AWS::Lambda::Function")

        self.assertEqual(len(generated_roles), 1)
        self.assertEqual(
            lambda_function.Role, {"Fn::If": ["Condition", {"Fn::GetAtt": ["fooRole", "Arn"]}, {"Ref": "iamRoleArn"}]}
        )

    def test_role_fn_if_second_no_value_creates_conditional_role(self):
        role_conditional = {"Fn::If": ["Condition", {"Ref": "iamRoleArn"}, {"Ref": "AWS::NoValue"}]}
        self.function.Role = role_conditional

        kwargs = dict(self.kwargs)
        kwargs["conditions"] = {"Condition": True}

        cfn_resources = self.function.to_cloudformation(**self.kwargs)
        generated_roles = [x for x in cfn_resources if isinstance(x, IAMRole)]
        lambda_function = next(r for r in cfn_resources if r.resource_type == "AWS::Lambda::Function")

        self.assertEqual(len(generated_roles), 1)
        self.assertEqual(
            lambda_function.Role, {"Fn::If": ["Condition", {"Ref": "iamRoleArn"}, {"Fn::GetAtt": ["fooRole", "Arn"]}]}
        )

    def test_role_get_att_no_execution_role(self):
        role_get_att = {"Fn::GetAtt": ["MyCustomRole", "Arn"]}
        self.function.Role = role_get_att

        cfn_resources = self.function.to_cloudformation(**self.kwargs)
        lambda_function = next(r for r in cfn_resources if r.resource_type == "AWS::Lambda::Function")

        self.assertEqual(lambda_function.Role, role_get_att)

    @parameterized.expand(
        [
            # 2-arg Fn::If (missing false value)
            ({"Fn::If": ["Condition", "arn:aws:iam::123456789012:role/existing-role"]},),
            # 4-arg Fn::If (extra value)
            ({"Fn::If": ["Condition", "role_a", "role_b", "role_c"]},),
        ]
    )
    def test_role_fn_if_invalid_arity_raises_invalid_resource_exception(self, malformed_role):
        """Fn::If must have exactly 3 items: [Condition, TrueValue, FalseValue].
        Any other arity used to crash SAM-T with a raw ValueError/IndexError,
        which CloudFormation surfaced as "Internal transform failure".
        It must now raise a user-facing InvalidResourceException instead.
        """
        self.function.Role = malformed_role

        with pytest.raises(InvalidResourceException) as excinfo:
            self.function.to_cloudformation(**self.kwargs)

        msg = str(excinfo.value)
        self.assertIn("foo", msg)  # logical id
        self.assertIn("Role", msg)
        self.assertIn("Fn::If", msg)

    @parameterized.expand(
        [
            # 2-arg Fn::If (missing false value)
            ({"Fn::If": ["SomeCondition", "queue-arn"]},),
            # 4-arg Fn::If (extra value)
            ({"Fn::If": ["SomeCondition", "a", "b", "c"]},),
        ]
    )
    def test_destination_fn_if_invalid_arity_raises_invalid_resource_exception(self, malformed):
        """EventInvokeConfig.DestinationConfig.{OnSuccess,OnFailure}.Destination
        also supports Fn::If. Any list arity other than 3 previously crashed the
        transform with IndexError in _get_or_make_condition.
        """
        with pytest.raises(InvalidResourceException) as excinfo:
            self.function._get_or_make_condition(malformed, "DestLogicalId", {})

        msg = str(excinfo.value)
        self.assertIn("DestLogicalId", msg)
        self.assertIn("Destination", msg)
        self.assertIn("Fn::If", msg)


class TestSamCapacityProvider(TestCase):
    """Tests for SamCapacityProvider"""

    def setUp(self):
        self.intrinsics_resolver = IntrinsicsResolver({})
        self.kwargs = {
            "intrinsics_resolver": self.intrinsics_resolver,
            "resource_resolver": ResourceResolver({}),
        }

    def test_basic_capacity_provider_without_propagate_tags(self):
        """Test that tags are correctly set on the capacity provider"""
        capacity_provider = SamCapacityProvider("MyCapacityProvider")
        capacity_provider.VpcConfig = {"SubnetIds": ["subnet-123", "subnet-456"], "SecurityGroupIds": ["sg-123"]}
        capacity_provider.Tags = {"Environment": "Production", "Project": "ServerlessApp"}

        resources = capacity_provider.to_cloudformation(**self.kwargs)

        # Verify the capacity provider has the expected tags
        lambda_capacity_providers = [
            r for r in resources if hasattr(r, "resource_type") and r.resource_type == "AWS::Lambda::CapacityProvider"
        ]
        self.assertEqual(len(lambda_capacity_providers), 1)

        # Check that the tags are present in the capacity provider
        tags = lambda_capacity_providers[0].Tags
        if not tags:
            self.fail("CapacityProvider resource generated with missing tags.")
        self.assertEqual(sorted([tag["Key"] for tag in tags]), ["Environment", "Project", "lambda:createdBy"])
        self.assertEqual(sorted([tag["Value"] for tag in tags]), ["Production", "SAM", "ServerlessApp"])

        # Verify that IAM resources don't have user tags by default
        iam_resources = [
            r for r in resources if hasattr(r, "resource_type") and r.resource_type.startswith("AWS::IAM::")
        ]
        for resource in iam_resources:
            if hasattr(resource, "Tags") and resource.Tags:
                tags = resource.Tags
                self.assertEqual([tag["Key"] for tag in tags], ["lambda:createdBy"])
                self.assertEqual([tag["Value"] for tag in tags], ["SAM"])

    def test_capacity_provider_with_propagate_tags(self):
        """Test that tags are propagated to all resources when PropagateTags is True"""
        capacity_provider = SamCapacityProvider("MyCapacityProvider")
        capacity_provider.VpcConfig = {"SubnetIds": ["subnet-123", "subnet-456"], "SecurityGroupIds": ["sg-123"]}
        capacity_provider.Tags = {"Environment": "Production", "Project": "ServerlessApp"}
        capacity_provider.PropagateTags = True

        resources = capacity_provider.to_cloudformation(**self.kwargs)

        # Check that tags are propagated to all resources
        for resource in resources:
            if hasattr(resource, "Tags") and resource.Tags:
                tags = resource.Tags
                self.assertEqual(sorted([tag["Key"] for tag in tags]), ["Environment", "Project", "lambda:createdBy"])
                self.assertEqual(sorted([tag["Value"] for tag in tags]), ["Production", "SAM", "ServerlessApp"])


class TestFunctionPolicy(TestCase):
    kwargs = {
        "intrinsics_resolver": IntrinsicsResolver({}),
        "event_resources": [],
        "managed_policy_map": {"foo": "bar"},
        "resource_resolver": ResourceResolver({}),
    }

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_managed_policy_name(self):
        function = SamFunction("Foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"
        managedPolicyName = "foo"
        function.Policies = [managedPolicyName]

        cfnResources = function.to_cloudformation(**self.kwargs)
        iamRoles = [x for x in cfnResources if isinstance(x, IAMRole)]
        self.assertEqual(iamRoles[0].ManagedPolicyArns[1], self.kwargs["managed_policy_map"][managedPolicyName])

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_unknown_policy_name(self):
        function = SamFunction("Foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"
        unknownPolicyName = "bar"
        function.Policies = [unknownPolicyName]

        cfnResources = function.to_cloudformation(**self.kwargs)
        iamRoles = [x for x in cfnResources if isinstance(x, IAMRole)]
        self.assertEqual(iamRoles[0].ManagedPolicyArns[1], unknownPolicyName)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_managed_policy_name_within_intrinsic_if_then(self):
        function = SamFunction("Foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"
        managedPolicyName = "foo"
        function.Policies = [{"Fn::If": ["Condition", managedPolicyName, {"Fn::Ref": "AWS::NoValue"}]}]

        cfnResources = function.to_cloudformation(**self.kwargs)
        iamRoles = [x for x in cfnResources if isinstance(x, IAMRole)]

        self.assertIn("Fn::If", iamRoles[0].ManagedPolicyArns[1])
        self.assertEqual(iamRoles[0].ManagedPolicyArns[1]["Fn::If"][0], "Condition")
        self.assertEqual(
            iamRoles[0].ManagedPolicyArns[1]["Fn::If"][1], self.kwargs["managed_policy_map"][managedPolicyName]
        )
        self.assertDictEqual(iamRoles[0].ManagedPolicyArns[1]["Fn::If"][2], {"Fn::Ref": "AWS::NoValue"})

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_managed_policy_name_within_intrinsic_if_else(self):
        function = SamFunction("Foo")
        function.CodeUri = "s3://foobar/foo.zip"
        function.Runtime = "foo"
        function.Handler = "bar"
        managedPolicyName = "foo"
        function.Policies = [{"Fn::If": ["Condition", {"Fn::Ref": "AWS::NoValue"}, managedPolicyName]}]

        cfnResources = function.to_cloudformation(**self.kwargs)
        iamRoles = [x for x in cfnResources if isinstance(x, IAMRole)]

        self.assertIn("Fn::If", iamRoles[0].ManagedPolicyArns[1])
        self.assertEqual(iamRoles[0].ManagedPolicyArns[1]["Fn::If"][0], "Condition")
        self.assertDictEqual(iamRoles[0].ManagedPolicyArns[1]["Fn::If"][1], {"Fn::Ref": "AWS::NoValue"})
        self.assertEqual(
            iamRoles[0].ManagedPolicyArns[1]["Fn::If"][2], self.kwargs["managed_policy_map"][managedPolicyName]
        )
