from unittest import TestCase
from mock import patch, Mock
import os
from samtranslator.model.sam_resources import SamFunction
from samtranslator.model.lambda_ import LambdaAlias, LambdaVersion, LambdaFunction
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.update_policy import UpdatePolicy
from samtranslator.model.preferences.deployment_preference import DeploymentPreference


class TestVersionsAndAliases(TestCase):
    def setUp(self):

        self.intrinsics_resolver_mock = Mock()
        self.intrinsics_resolver_mock.resolve = Mock()
        self.mappings_resolver_mock = Mock()
        self.mappings_resolver_mock.resolve = Mock()

        self.code_uri = "s3://bucket/key?versionId=version"
        self.func_dict = {
            "Type": "AWS::Serverless::Function",
            "Properties": {"CodeUri": self.code_uri, "Runtime": "nodejs12.x", "Handler": "index.handler"},
        }
        self.sam_func = SamFunction.from_dict(logical_id="foo", resource_dict=self.func_dict)
        self.lambda_func = self._make_lambda_function(self.sam_func.logical_id)
        self.lambda_version = self._make_lambda_version("VersionLogicalId", self.sam_func)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch.object(SamFunction, "_get_resolved_alias_name")
    def test_sam_function_with_alias(self, get_resolved_alias_name_mock):
        alias_name = "AliasName"
        func = {
            "Type": "AWS::Serverless::Function",
            "Properties": {
                "CodeUri": self.code_uri,
                "Runtime": "nodejs12.x",
                "Handler": "index.handler",
                "AutoPublishAlias": alias_name,
            },
        }

        sam_func = SamFunction.from_dict(logical_id="foo", resource_dict=func)

        kwargs = {}
        kwargs["managed_policy_map"] = {"a": "b"}
        kwargs["event_resources"] = []
        kwargs["intrinsics_resolver"] = self.intrinsics_resolver_mock
        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = {
            "S3Bucket": "bucket",
            "S3Key": "key",
            "S3ObjectVersion": "version",
        }
        get_resolved_alias_name_mock.return_value = alias_name

        resources = sam_func.to_cloudformation(**kwargs)

        # Function, Version, Alias, IAM Role
        self.assertEqual(len(resources), 4)

        aliases = [r.to_dict() for r in resources if r.resource_type == LambdaAlias.resource_type]
        versions = [r.to_dict() for r in resources if r.resource_type == LambdaVersion.resource_type]
        self.assertEqual(len(aliases), 1)
        self.assertEqual(len(versions), 1)

        alias = list(aliases[0].values())[0]["Properties"]
        self.assertEqual(alias["Name"], alias_name)
        # We don't need to do any deeper validation here because there is a separate SAM template -> CFN template conversion test
        # that will care of validating all properties & connections

        sam_func._get_resolved_alias_name.assert_called_once_with(
            "AutoPublishAlias", alias_name, self.intrinsics_resolver_mock
        )

    def test_sam_function_with_alias_cannot_be_list(self):

        # Alias cannot be a list
        with self.assertRaises(InvalidResourceException):
            self.func_dict["Properties"]["AutoPublishAlias"] = ["a", "b"]
            SamFunction.from_dict(logical_id="foo", resource_dict=self.func_dict)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch.object(SamFunction, "_get_resolved_alias_name")
    def test_sam_function_with_deployment_preference(self, get_resolved_alias_name_mock):
        deploy_preference_dict = {"Type": "LINEAR"}
        alias_name = "AliasName"
        func = {
            "Type": "AWS::Serverless::Function",
            "Properties": {
                "CodeUri": self.code_uri,
                "Runtime": "nodejs12.x",
                "Handler": "index.handler",
                "AutoPublishAlias": alias_name,
                "DeploymentPreference": deploy_preference_dict,
            },
        }

        sam_func = SamFunction.from_dict(logical_id="foo", resource_dict=func)

        kwargs = dict()
        kwargs["managed_policy_map"] = {"a": "b"}
        kwargs["event_resources"] = []
        kwargs["intrinsics_resolver"] = self.intrinsics_resolver_mock
        kwargs["mappings_resolver"] = self.mappings_resolver_mock
        deployment_preference_collection = self._make_deployment_preference_collection()
        kwargs["deployment_preference_collection"] = deployment_preference_collection
        get_resolved_alias_name_mock.return_value = alias_name

        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = {
            "S3Bucket": "bucket",
            "S3Key": "key",
            "S3ObjectVersion": "version",
        }
        resources = sam_func.to_cloudformation(**kwargs)

        deployment_preference_collection.update_policy.assert_called_once_with(self.sam_func.logical_id)
        deployment_preference_collection.add.assert_called_once_with(self.sam_func.logical_id, deploy_preference_dict)

        aliases = [r.to_dict() for r in resources if r.resource_type == LambdaAlias.resource_type]

        self.assertTrue("UpdatePolicy" in list(aliases[0].values())[0])
        self.assertEqual(list(aliases[0].values())[0]["UpdatePolicy"], self.update_policy().to_dict())

    @patch.object(SamFunction, "_get_resolved_alias_name")
    def test_sam_function_with_deployment_preference_missing_collection_raises_error(
        self, get_resolved_alias_name_mock
    ):
        alias_name = "AliasName"
        deploy_preference_dict = {"Type": "LINEAR"}
        func = {
            "Type": "AWS::Serverless::Function",
            "Properties": {
                "CodeUri": self.code_uri,
                "Runtime": "nodejs12.x",
                "Handler": "index.handler",
                "AutoPublishAlias": alias_name,
                "DeploymentPreference": deploy_preference_dict,
            },
        }

        sam_func = SamFunction.from_dict(logical_id="foo", resource_dict=func)

        kwargs = dict()
        kwargs["managed_policy_map"] = {"a": "b"}
        kwargs["event_resources"] = []
        kwargs["intrinsics_resolver"] = self.intrinsics_resolver_mock
        kwargs["mappings_resolver"] = self.mappings_resolver_mock
        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = {
            "S3Bucket": "bucket",
            "S3Key": "key",
            "S3ObjectVersion": "version",
        }
        get_resolved_alias_name_mock.return_value = alias_name

        with self.assertRaises(ValueError):
            sam_func.to_cloudformation(**kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch.object(SamFunction, "_get_resolved_alias_name")
    def test_sam_function_with_disabled_deployment_preference_does_not_add_update_policy(
        self, get_resolved_alias_name_mock
    ):
        alias_name = "AliasName"
        enabled = False
        deploy_preference_dict = {"Enabled": enabled}
        func = {
            "Type": "AWS::Serverless::Function",
            "Properties": {
                "CodeUri": self.code_uri,
                "Runtime": "nodejs12.x",
                "Handler": "index.handler",
                "AutoPublishAlias": alias_name,
                "DeploymentPreference": deploy_preference_dict,
            },
        }

        sam_func = SamFunction.from_dict(logical_id="foo", resource_dict=func)

        kwargs = dict()
        kwargs["managed_policy_map"] = {"a": "b"}
        kwargs["event_resources"] = []
        kwargs["intrinsics_resolver"] = self.intrinsics_resolver_mock
        kwargs["mappings_resolver"] = self.mappings_resolver_mock
        preference_collection = self._make_deployment_preference_collection()
        preference_collection.get.return_value = DeploymentPreference.from_dict(
            sam_func.logical_id, deploy_preference_dict
        )

        kwargs["deployment_preference_collection"] = preference_collection
        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = enabled
        get_resolved_alias_name_mock.return_value = alias_name

        resources = sam_func.to_cloudformation(**kwargs)

        preference_collection.add.assert_called_once_with(sam_func.logical_id, deploy_preference_dict)
        preference_collection.get.assert_called_once_with(sam_func.logical_id)
        self.intrinsics_resolver_mock.resolve_parameter_refs.assert_called_with(enabled)
        aliases = [r.to_dict() for r in resources if r.resource_type == LambdaAlias.resource_type]

        self.assertTrue("UpdatePolicy" not in list(aliases[0].values())[0])

    def test_sam_function_cannot_be_with_deployment_preference_without_alias(self):
        with self.assertRaises(InvalidResourceException):
            func = {
                "Type": "AWS::Serverless::Function",
                "Properties": {
                    "CodeUri": self.code_uri,
                    "Runtime": "nodejs12.x",
                    "Handler": "index.handler",
                    "DeploymentPreference": {"Type": "LINEAR"},
                },
            }

            sam_func = SamFunction.from_dict(logical_id="foo", resource_dict=func)

            kwargs = dict()
            kwargs["intrinsics_resolver"] = self.intrinsics_resolver_mock
            kwargs["mappings_resolver"] = self.mappings_resolver_mock
            kwargs["deployment_preference_collection"] = self._make_deployment_preference_collection()
            sam_func.to_cloudformation(**kwargs)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_sam_function_without_alias_allows_disabled_deployment_preference(self):
        enabled = False
        deploy_preference_dict = {"Enabled": enabled}
        func = {
            "Type": "AWS::Serverless::Function",
            "Properties": {
                "CodeUri": self.code_uri,
                "Runtime": "nodejs12.x",
                "Handler": "index.handler",
                "DeploymentPreference": deploy_preference_dict,
            },
        }

        sam_func = SamFunction.from_dict(logical_id="foo", resource_dict=func)

        kwargs = dict()
        kwargs["managed_policy_map"] = {"a": "b"}
        kwargs["event_resources"] = []
        kwargs["intrinsics_resolver"] = self.intrinsics_resolver_mock
        kwargs["mappings_resolver"] = self.mappings_resolver_mock

        preference_collection = self._make_deployment_preference_collection()
        preference_collection.get.return_value = DeploymentPreference.from_dict(
            sam_func.logical_id, deploy_preference_dict
        )

        kwargs["deployment_preference_collection"] = preference_collection
        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = enabled
        resources = sam_func.to_cloudformation(**kwargs)

        self.intrinsics_resolver_mock.resolve_parameter_refs.assert_called_with(enabled)
        # Function, IAM Role
        self.assertEqual(len(resources), 2)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch.object(SamFunction, "_get_resolved_alias_name")
    def test_sam_function_with_deployment_preference_intrinsic_ref_enabled_boolean_parameter(
        self, get_resolved_alias_name_mock
    ):
        alias_name = "AliasName"
        enabled = {"Ref": "MyEnabledFlag"}
        deploy_preference_dict = {"Type": "LINEAR", "Enabled": enabled}
        func = {
            "Type": "AWS::Serverless::Function",
            "Properties": {
                "CodeUri": self.code_uri,
                "Runtime": "nodejs12.x",
                "Handler": "index.handler",
                "AutoPublishAlias": alias_name,
                "DeploymentPreference": deploy_preference_dict,
            },
        }

        sam = SamFunction.from_dict(logical_id="foo", resource_dict=func)

        kwargs = dict()
        kwargs["managed_policy_map"] = {"a": "b"}
        kwargs["event_resources"] = []
        kwargs["intrinsics_resolver"] = self.intrinsics_resolver_mock
        kwargs["mappings_resolver"] = self.mappings_resolver_mock
        deployment_preference_collection = self._make_deployment_preference_collection()
        kwargs["deployment_preference_collection"] = deployment_preference_collection
        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = True
        get_resolved_alias_name_mock.return_value = alias_name

        resources = sam.to_cloudformation(**kwargs)

        deployment_preference_collection.update_policy.assert_called_once_with(self.sam_func.logical_id)
        deployment_preference_collection.add.assert_called_once_with(self.sam_func.logical_id, deploy_preference_dict)
        self.intrinsics_resolver_mock.resolve_parameter_refs.assert_any_call(enabled)

        aliases = [r.to_dict() for r in resources if r.resource_type == LambdaAlias.resource_type]

        self.assertTrue("UpdatePolicy" in list(aliases[0].values())[0])
        self.assertEqual(list(aliases[0].values())[0]["UpdatePolicy"], self.update_policy().to_dict())

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch.object(SamFunction, "_get_resolved_alias_name")
    def test_sam_function_with_deployment_preference_intrinsic_ref_enabled_dict_parameter(
        self, get_resolved_alias_name_mock
    ):
        alias_name = "AliasName"
        enabled = {"Ref": "MyEnabledFlag"}
        deploy_preference_dict = {"Type": "LINEAR", "Enabled": enabled}
        func = {
            "Type": "AWS::Serverless::Function",
            "Properties": {
                "CodeUri": self.code_uri,
                "Runtime": "nodejs12.x",
                "Handler": "index.handler",
                "AutoPublishAlias": alias_name,
                "DeploymentPreference": deploy_preference_dict,
            },
        }

        sam_func = SamFunction.from_dict(logical_id="foo", resource_dict=func)

        kwargs = dict()
        kwargs["managed_policy_map"] = {"a": "b"}
        kwargs["event_resources"] = []
        kwargs["intrinsics_resolver"] = self.intrinsics_resolver_mock
        kwargs["mappings_resolver"] = self.mappings_resolver_mock
        deployment_preference_collection = self._make_deployment_preference_collection()
        kwargs["deployment_preference_collection"] = deployment_preference_collection
        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = {"MyEnabledFlag": True}
        get_resolved_alias_name_mock.return_value = alias_name

        sam_func.to_cloudformation(**kwargs)
        self.assertTrue(sam_func.DeploymentPreference["Enabled"])

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch.object(SamFunction, "_get_resolved_alias_name")
    def test_sam_function_with_deployment_preference_intrinsic_findinmap_enabled_dict_parameter(
        self, get_resolved_alias_name_mock
    ):
        alias_name = "AliasName"
        enabled = {"Fn::FindInMap": ["FooMap", "FooKey", "Enabled"]}
        deploy_preference_dict = {"Type": "LINEAR", "Enabled": enabled}
        func = {
            "Type": "AWS::Serverless::Function",
            "Properties": {
                "CodeUri": self.code_uri,
                "Runtime": "nodejs12.x",
                "Handler": "index.handler",
                "AutoPublishAlias": alias_name,
                "DeploymentPreference": deploy_preference_dict,
            },
        }

        sam_func = SamFunction.from_dict(logical_id="foo", resource_dict=func)

        kwargs = dict()
        kwargs["managed_policy_map"] = {"a": "b"}
        kwargs["event_resources"] = []
        kwargs["intrinsics_resolver"] = self.intrinsics_resolver_mock
        kwargs["mappings_resolver"] = self.mappings_resolver_mock
        deployment_preference_collection = self._make_deployment_preference_collection()
        kwargs["deployment_preference_collection"] = deployment_preference_collection
        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = {"MyEnabledFlag": True}
        self.mappings_resolver_mock.resolve_parameter_refs.return_value = True
        get_resolved_alias_name_mock.return_value = alias_name

        sam_func.to_cloudformation(**kwargs)
        self.assertTrue(sam_func.DeploymentPreference["Enabled"])

    @patch("samtranslator.translator.logical_id_generator.LogicalIdGenerator")
    def test_version_creation(self, LogicalIdGeneratorMock):
        generator_mock = LogicalIdGeneratorMock.return_value
        id_val = "SomeLogicalId"
        generator_mock.gen.return_value = id_val

        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = self.lambda_func.Code
        version = self.sam_func._construct_version(self.lambda_func, self.intrinsics_resolver_mock)

        self.assertEqual(version.logical_id, id_val)
        self.assertEqual(version.Description, None)
        self.assertEqual(version.FunctionName, {"Ref": self.lambda_func.logical_id})
        self.assertEqual(version.get_resource_attribute("DeletionPolicy"), "Retain")

        expected_prefix = self.sam_func.logical_id + "Version"
        LogicalIdGeneratorMock.assert_called_once_with(expected_prefix, self.lambda_func.Code, None)
        generator_mock.gen.assert_called_once_with()
        self.intrinsics_resolver_mock.resolve_parameter_refs.assert_called_once_with(self.lambda_func.Code)

    @patch("samtranslator.translator.logical_id_generator.LogicalIdGenerator")
    def test_version_creation_with_code_sha(self, LogicalIdGeneratorMock):
        generator_mock = LogicalIdGeneratorMock.return_value
        prefix = "SomeLogicalId"
        hash_code = "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b"
        id_val = "{}{}".format(prefix, hash_code[:10])
        generator_mock.gen.return_value = id_val

        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = self.lambda_func.Code
        self.sam_func.AutoPublishCodeSha256 = hash_code
        version = self.sam_func._construct_version(self.lambda_func, self.intrinsics_resolver_mock, hash_code)

        self.assertEqual(version.logical_id, id_val)
        self.assertEqual(version.Description, None)
        self.assertEqual(version.FunctionName, {"Ref": self.lambda_func.logical_id})
        self.assertEqual(version.get_resource_attribute("DeletionPolicy"), "Retain")

        expected_prefix = self.sam_func.logical_id + "Version"
        LogicalIdGeneratorMock.assert_called_once_with(expected_prefix, self.lambda_func.Code, hash_code)
        generator_mock.gen.assert_called_once_with()
        self.intrinsics_resolver_mock.resolve_parameter_refs.assert_called_once_with(self.lambda_func.Code)

    # Test without S3 object version
    @patch("samtranslator.translator.logical_id_generator.LogicalIdGenerator")
    def test_version_creation_without_s3_object_version(self, LogicalIdGeneratorMock):
        generator_mock = LogicalIdGeneratorMock.return_value
        id_val = "SomeLogicalId"
        generator_mock.gen.return_value = id_val

        del self.lambda_func.Code["S3ObjectVersion"]
        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = self.lambda_func.Code
        version = self.sam_func._construct_version(self.lambda_func, self.intrinsics_resolver_mock)

        self.assertEqual(version.logical_id, id_val)

        expected_prefix = self.sam_func.logical_id + "Version"
        LogicalIdGeneratorMock.assert_called_once_with(expected_prefix, self.lambda_func.Code, None)
        generator_mock.gen.assert_called_once_with()
        self.intrinsics_resolver_mock.resolve_parameter_refs.assert_called_once_with(self.lambda_func.Code)

    def test_version_creation_error(self):
        # Empty code dictionary
        self.lambda_func.Code = {}
        with self.assertRaises(ValueError):
            self.sam_func._construct_version(self.lambda_func, self.intrinsics_resolver_mock)

    @patch("samtranslator.translator.logical_id_generator.LogicalIdGenerator")
    def test_version_creation_intrinsic_function_in_code_s3key(self, LogicalIdGeneratorMock):
        # One of the properties of Code dictionary is an intrinsic function
        generator_mock = LogicalIdGeneratorMock.return_value
        id_val = "SomeLogicalId"
        generator_mock.gen.return_value = id_val

        self.lambda_func.Code = {"S3Bucket": "bucket", "S3Key": {"Ref": "keyparameter"}, "S3ObjectVersion": "version"}
        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = self.lambda_func.Code

        version = self.sam_func._construct_version(self.lambda_func, self.intrinsics_resolver_mock)
        self.assertEqual(version.logical_id, id_val)

        expected_prefix = self.sam_func.logical_id + "Version"
        LogicalIdGeneratorMock.assert_called_once_with(expected_prefix, self.lambda_func.Code, None)
        self.intrinsics_resolver_mock.resolve_parameter_refs.assert_called_once_with(self.lambda_func.Code)

    @patch("samtranslator.translator.logical_id_generator.LogicalIdGenerator")
    def test_version_creation_intrinsic_function_in_code_s3bucket(self, LogicalIdGeneratorMock):
        generator_mock = LogicalIdGeneratorMock.return_value
        id_val = "SomeLogicalId"
        generator_mock.gen.return_value = id_val

        self.lambda_func.Code = {"S3Bucket": {"Ref": "bucketparameter"}, "S3Key": "key", "S3ObjectVersion": "version"}
        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = self.lambda_func.Code

        version = self.sam_func._construct_version(self.lambda_func, self.intrinsics_resolver_mock)
        self.assertEqual(version.logical_id, id_val)

        expected_prefix = self.sam_func.logical_id + "Version"
        LogicalIdGeneratorMock.assert_called_once_with(expected_prefix, self.lambda_func.Code, None)
        self.intrinsics_resolver_mock.resolve_parameter_refs.assert_called_once_with(self.lambda_func.Code)

    @patch("samtranslator.translator.logical_id_generator.LogicalIdGenerator")
    def test_version_creation_intrinsic_function_in_code_s3version(self, LogicalIdGeneratorMock):
        generator_mock = LogicalIdGeneratorMock.return_value
        id_val = "SomeLogicalId"
        generator_mock.gen.return_value = id_val

        self.lambda_func.Code = {"S3Bucket": "bucket", "S3Key": "key", "S3ObjectVersion": {"Ref": "versionparameter"}}
        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = self.lambda_func.Code

        version = self.sam_func._construct_version(self.lambda_func, self.intrinsics_resolver_mock)
        self.assertEqual(version.logical_id, id_val)

        expected_prefix = self.sam_func.logical_id + "Version"
        LogicalIdGeneratorMock.assert_called_once_with(expected_prefix, self.lambda_func.Code, None)
        self.intrinsics_resolver_mock.resolve_parameter_refs.assert_called_once_with(self.lambda_func.Code)

    @patch("samtranslator.translator.logical_id_generator.LogicalIdGenerator")
    def test_version_logical_id_changes(self, LogicalIdGeneratorMock):
        generator_mock = LogicalIdGeneratorMock.return_value
        id_val = "SomeLogicalId"
        generator_mock.gen.return_value = id_val
        prefix = self.sam_func.logical_id + "Version"

        # Test that logicalId changes with changes to CodeSha
        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = self.lambda_func.Code
        self.sam_func._construct_version(self.lambda_func, self.intrinsics_resolver_mock)

        LogicalIdGeneratorMock.assert_called_once_with(prefix, self.lambda_func.Code, None)
        self.intrinsics_resolver_mock.resolve_parameter_refs.assert_called_with(self.lambda_func.Code)

        # Modify Code of the lambda function
        self.lambda_func.Code["S3ObjectVersion"] = "new object version"
        new_code = self.lambda_func.Code.copy()
        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = new_code
        self.sam_func._construct_version(self.lambda_func, self.intrinsics_resolver_mock)
        LogicalIdGeneratorMock.assert_called_with(prefix, new_code, None)
        self.intrinsics_resolver_mock.resolve_parameter_refs.assert_called_with(new_code)

    @patch("samtranslator.translator.logical_id_generator.LogicalIdGenerator")
    def test_version_logical_id_changes_with_intrinsic_functions(self, LogicalIdGeneratorMock):
        generator_mock = LogicalIdGeneratorMock.return_value
        id_val = "SomeLogicalId"
        generator_mock.gen.return_value = id_val
        prefix = self.sam_func.logical_id + "Version"

        self.lambda_func.Code = {"S3Bucket": "bucket", "S3Key": {"Ref": "someparam"}}

        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = self.lambda_func.Code
        self.sam_func._construct_version(self.lambda_func, self.intrinsics_resolver_mock)

        LogicalIdGeneratorMock.assert_called_once_with(prefix, self.lambda_func.Code, None)
        self.intrinsics_resolver_mock.resolve_parameter_refs.assert_called_with(self.lambda_func.Code)

        # Now, just let the intrinsics resolver return a different value. Let's make sure the new value gets wired up properly
        new_code = {"S3Bucket": "bucket", "S3Key": "some new value"}
        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = new_code
        self.sam_func._construct_version(self.lambda_func, self.intrinsics_resolver_mock)
        LogicalIdGeneratorMock.assert_called_with(prefix, new_code, None)
        self.intrinsics_resolver_mock.resolve_parameter_refs.assert_called_with(self.lambda_func.Code)

    def test_alias_creation(self):
        name = "aliasname"

        alias = self.sam_func._construct_alias(name, self.lambda_func, self.lambda_version)

        expected_logical_id = "%sAlias%s" % (self.lambda_func.logical_id, name)
        self.assertEqual(alias.logical_id, expected_logical_id)
        self.assertEqual(alias.Name, name)
        self.assertEqual(alias.FunctionName, {"Ref": self.lambda_func.logical_id})
        self.assertEqual(alias.FunctionVersion, {"Fn::GetAtt": [self.lambda_version.logical_id, "Version"]})

    def test_alias_creation_error(self):
        with self.assertRaises(InvalidResourceException):
            self.sam_func._construct_alias(None, self.lambda_func, self.lambda_version)

    def test_get_resolved_alias_name_must_work(self):

        property_name = "something"
        alias_value = {"Ref": "param1"}
        alias_name = "AliasName"
        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = alias_name

        result = self.sam_func._get_resolved_alias_name(property_name, alias_value, self.intrinsics_resolver_mock)
        self.assertEqual(alias_name, result)

    def test_get_resolved_alias_name_must_error_if_intrinsics_are_not_resolved(self):

        property_name = "something"
        expected_exception_msg = "Resource with id [{}] is invalid. '{}' must be a string or a Ref to a template parameter".format(
            self.sam_func.logical_id, property_name
        )

        alias_value = {"Ref": "param1"}
        # Unresolved
        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = {"Ref": "param1"}

        with self.assertRaises(InvalidResourceException) as raises_assert:
            self.sam_func._get_resolved_alias_name(property_name, alias_value, self.intrinsics_resolver_mock)

        ex = raises_assert.exception
        self.assertEqual(expected_exception_msg, ex.message)

    def test_get_resolved_alias_name_must_error_if_intrinsics_are_not_resolved_with_list(self):

        property_name = "something"
        expected_exception_msg = "Resource with id [{}] is invalid. '{}' must be a string or a Ref to a template parameter".format(
            self.sam_func.logical_id, property_name
        )

        alias_value = ["Ref", "param1"]
        # Unresolved
        self.intrinsics_resolver_mock.resolve_parameter_refs.return_value = ["Ref", "param1"]

        with self.assertRaises(InvalidResourceException) as raises_assert:
            self.sam_func._get_resolved_alias_name(property_name, alias_value, self.intrinsics_resolver_mock)

        ex = raises_assert.exception
        self.assertEqual(expected_exception_msg, ex.message)

    def _make_lambda_function(self, logical_id):
        func = LambdaFunction(logical_id)
        func.Code = {"S3Bucket": "bucket", "S3Key": "key", "S3ObjectVersion": "version"}
        return func

    def _make_lambda_version(self, logical_id, func):
        version = LambdaVersion(logical_id)
        version.FunctionName = {"Ref": func.logical_id}
        return version

    def update_policy(self):
        return UpdatePolicy("app_name", "deploy_group_name", None, None)

    def _make_deployment_preference_collection(self):
        deployment_preference_collection = Mock()
        deployment_preference_collection.update_policy.return_value = self.update_policy()

        return deployment_preference_collection


class TestSupportedResourceReferences(TestCase):
    def test_must_not_break_support(self):

        func = SamFunction("LogicalId")
        self.assertEqual(4, len(func.referable_properties))
        self.assertEqual(func.referable_properties["Alias"], "AWS::Lambda::Alias")
        self.assertEqual(func.referable_properties["Version"], "AWS::Lambda::Version")
        self.assertEqual(func.referable_properties["DestinationTopic"], "AWS::SNS::Topic")
        self.assertEqual(func.referable_properties["DestinationQueue"], "AWS::SQS::Queue")
