from mock import Mock
from unittest import TestCase

from samtranslator.model import ResourceTypeResolver
from samtranslator.model.exceptions import InvalidResourceException, InvalidEventException
from samtranslator.model.stepfunctions import StateMachineGenerator
from samtranslator.model.stepfunctions.events import CloudWatchEvent


class StepFunctionsStateMachine(TestCase):
    def setUp(self):
        self.kwargs = {
            "logical_id": "StateMachineId",
            "depends_on": None,
            "managed_policy_map": None,
            "intrinsics_resolver": None,
            "definition": None,
            "definition_uri": None,
            "logging": None,
            "name": None,
            "policies": None,
            "definition_substitutions": None,
            "role": None,
            "state_machine_type": None,
            "events": None,
            "event_resources": None,
            "event_resolver": None,
            "tags": None,
            "resource_attributes": None,
            "passthrough_resource_attributes": None,
        }

    def test_state_machine_no_definition_source(self):
        self.kwargs["definition"] = None
        self.kwargs["definition_uri"] = None
        with self.assertRaises(InvalidResourceException) as error:
            StateMachineGenerator(**self.kwargs).to_cloudformation()
        self.assertEqual(
            error.exception.message,
            "Resource with id [StateMachineId] is invalid. Either 'Definition' or 'DefinitionUri' property must be specified.",
        )

    def test_state_machine_multiple_definition_sources(self):
        self.kwargs["definition"] = {"StartAt": "StateOne", "States": {"StateOne": {"Type": "Pass", "End": True}}}
        self.kwargs["definition_uri"] = "s3://my-sam-bucket/definition.asl.json"
        with self.assertRaises(InvalidResourceException) as error:
            StateMachineGenerator(**self.kwargs).to_cloudformation()
        self.assertEqual(
            error.exception.message,
            "Resource with id [StateMachineId] is invalid. Specify either 'Definition' or 'DefinitionUri' property and not both.",
        )

    def test_state_machine_no_role_or_policies(self):
        self.kwargs["definition_uri"] = "s3://my-demo-bucket/my_asl_file.asl.json"
        self.kwargs["role"] = None
        self.kwargs["policies"] = None
        with self.assertRaises(InvalidResourceException) as error:
            StateMachineGenerator(**self.kwargs).to_cloudformation()
        self.assertEqual(
            error.exception.message,
            "Resource with id [StateMachineId] is invalid. Either 'Role' or 'Policies' property must be specified.",
        )

    def test_state_machine_both_role_and_policies(self):
        self.kwargs["definition_uri"] = "s3://my-demo-bucket/my_asl_file.asl.json"
        self.kwargs["role"] = "arn:my-sample-role"
        self.kwargs["policies"] = {
            "Policies": [{"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Action": "*", "Resource": "*"}]}]
        }
        with self.assertRaises(InvalidResourceException) as error:
            StateMachineGenerator(**self.kwargs).to_cloudformation()
        self.assertEqual(
            error.exception.message,
            "Resource with id [StateMachineId] is invalid. Specify either 'Role' or 'Policies' property and not both.",
        )

    def test_state_machine_invalid_definition_uri_string(self):
        self.kwargs["definition"] = None
        self.kwargs["definition_uri"] = "invalid_uri"
        with self.assertRaises(InvalidResourceException) as error:
            StateMachineGenerator(**self.kwargs).to_cloudformation()
        self.assertEqual(
            error.exception.message,
            "Resource with id [StateMachineId] is invalid. 'DefinitionUri' is not a valid S3 Uri of the form 's3://bucket/key' with optional versionId query parameter.",
        )

    def test_state_machine_invalid_definition_uri_object(self):
        self.kwargs["definition"] = None
        self.kwargs["definition_uri"] = {"Bucket": "only-bucket-name"}
        with self.assertRaises(InvalidResourceException) as error:
            StateMachineGenerator(**self.kwargs).to_cloudformation()
        self.assertEqual(
            error.exception.message,
            "Resource with id [StateMachineId] is invalid. 'DefinitionUri' requires Bucket and Key properties to be specified.",
        )

    def test_state_machine_no_tags_provided(self):
        self.kwargs["definition_uri"] = "s3://mybucket/myASLfile"
        self.kwargs["role"] = "my-test-role-arn"
        self.kwargs["tags"] = None
        expected_tags = [{"Key": StateMachineGenerator._SAM_KEY, "Value": StateMachineGenerator._SAM_VALUE}]
        generated_tags = StateMachineGenerator(**self.kwargs)._construct_tag_list()
        self.assertEqual(generated_tags, expected_tags)

    def test_state_machine_with_tags_provided(self):
        self.kwargs["definition_uri"] = "s3://mybucket/myASLfile"
        self.kwargs["role"] = "my-test-role-arn"
        self.kwargs["tags"] = {"Key01": "Value01", "Key02": "Value02"}
        expected_tags = [
            {"Key": StateMachineGenerator._SAM_KEY, "Value": StateMachineGenerator._SAM_VALUE},
            {"Key": "Key01", "Value": "Value01"},
            {"Key": "Key02", "Value": "Value02"},
        ]
        generated_tags = StateMachineGenerator(**self.kwargs)._construct_tag_list()
        self.assertEqual(generated_tags, expected_tags)

    def test_state_machine_with_supported_event_source(self):
        self.kwargs["definition_uri"] = "s3://mybucket/myASLfile"
        self.kwargs["role"] = "my-test-role-arn"
        event_resolver = Mock()
        event_resolver.resolve_resource_type = Mock(return_value=CloudWatchEvent)
        self.kwargs["event_resolver"] = event_resolver
        self.kwargs["events"] = {
            "CWEEvent": {"Type": "CloudWatchEvent", "Properties": {"Pattern": {"detail": {"state": ["terminated"]}}}}
        }
        self.kwargs["event_resources"] = {"CWEEvent": {}}
        generated_event_resources = StateMachineGenerator(**self.kwargs)._generate_event_resources()
        self.assertEqual(generated_event_resources[0].resource_type, "AWS::Events::Rule")

    def test_state_machine_with_unsupported_event_source(self):
        self.kwargs["definition_uri"] = "s3://mybucket/myASLfile"
        self.kwargs["role"] = "my-test-role-arn"
        event_resolver = Mock()
        event_resolver.resolve_resource_type = Mock(return_value=None)
        self.kwargs["event_resolver"] = event_resolver
        self.kwargs["events"] = {
            "KinesesEvent": {
                "Type": "Kineses",
                "Properties": {
                    "Stream": "arn:aws:kinesis:us-east-1:123456789012:stream/my-stream",
                    "StartingPosition": "TRIM_HORIZON",
                    "BatchSize": 10,
                    "Enabled": False,
                },
            }
        }
        self.kwargs["event_resources"] = {"KinesesEvent": {}}
        with self.assertRaises(InvalidEventException) as error:
            StateMachineGenerator(**self.kwargs).to_cloudformation()
