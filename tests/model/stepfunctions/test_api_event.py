from mock import Mock
from unittest import TestCase

from samtranslator.model.stepfunctions.events import Api
from samtranslator.model.exceptions import InvalidResourceException, InvalidEventException


class ApiEventSource(TestCase):
    def setUp(self):
        self.logical_id = "ApiEvent"

        self.api_event_source = Api(self.logical_id)
        self.api_event_source.Path = "/statemachine"
        self.api_event_source.Method = "POST"

        self.state_machine = Mock()
        self.state_machine.logical_id = "MockStateMachine"
        self.state_machine.get_runtime_attr = Mock()
        self.state_machine.get_runtime_attr.return_value = "arn:aws:statemachine:mock"
        self.state_machine.resource_attributes = {}
        self.state_machine.get_passthrough_resource_attributes = Mock()
        self.state_machine.get_passthrough_resource_attributes.return_value = {}

    def test_to_cloudformation_returns_role_resource(self):
        resources = self.api_event_source.to_cloudformation(resource=self.state_machine, explicit_api={})
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].resource_type, "AWS::IAM::Role")

        iam_role = resources[0]
        self.assertEqual(
            iam_role.AssumeRolePolicyDocument,
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": ["sts:AssumeRole"],
                        "Effect": "Allow",
                        "Principal": {"Service": ["apigateway.amazonaws.com"]},
                    }
                ],
            },
        )
        self.assertEqual(
            iam_role.Policies,
            [
                {
                    "PolicyName": "ApiEventRoleStartExecutionPolicy",
                    "PolicyDocument": {
                        "Statement": [
                            {
                                "Action": "states:StartExecution",
                                "Resource": "arn:aws:statemachine:mock",
                                "Effect": "Allow",
                            }
                        ]
                    },
                }
            ],
        )

    def test_resources_to_link_with_explicit_api(self):
        resources = {"MyExplicitApi": {"Type": "AWS::Serverless::Api", "Properties": {"StageName": "Prod"}}}
        self.api_event_source.RestApiId = {"Ref": "MyExplicitApi"}
        resources_to_link = self.api_event_source.resources_to_link(resources)
        self.assertEqual(
            resources_to_link, {"explicit_api": {"StageName": "Prod"}, "explicit_api_stage": {"suffix": "Prod"}}
        )

    def test_resources_to_link_with_undefined_explicit_api(self):
        resources = {}
        self.api_event_source.RestApiId = {"Ref": "MyExplicitApi"}
        with self.assertRaises(InvalidEventException) as error:
            resources_to_link = self.api_event_source.resources_to_link(resources)

    def test_resources_to_link_without_explicit_api(self):
        resources = {}
        resources_to_link = self.api_event_source.resources_to_link(resources)
        self.assertEqual(resources_to_link, {"explicit_api": None, "explicit_api_stage": {"suffix": "AllStages"}})

    def test_to_cloudformation_throws_when_no_resource(self):
        self.assertRaises(TypeError, self.api_event_source.to_cloudformation)

    def test_request_template(self):
        request_template = self.api_event_source._generate_request_template(resource=self.state_machine)
        self.assertEqual(
            request_template,
            {
                "application/json": {
                    "Fn::Sub": '{"input": "$util.escapeJavaScript($input.json(\'$\'))", "stateMachineArn": "${MockStateMachine}"}'
                }
            },
        )
