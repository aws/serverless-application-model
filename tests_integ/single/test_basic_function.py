import os
from pathlib import Path
from unittest.case import TestCase

import boto3
import pytest
from parameterized import parameterized
from samcli.lib.deploy.deployer import Deployer
from tests_integ.helpers.helpers import transform_template, verify_stack_resources

STACK_NAME_PREFIX = "sam-integ-test-"


class TestBasicFunction(TestCase):
    # set up before every tests run:
    def setUp(self):
        tests_integ_dir = Path(__file__).resolve().parents[1]
        self.template_dir = Path(tests_integ_dir, 'resources', 'templates', 'single')
        self.output_dir = tests_integ_dir
        self.expected_dir = Path(tests_integ_dir, 'resources', 'expected', 'single')

        self.cloudformation_client = boto3.client("cloudformation")
        self.deployer = Deployer(self.cloudformation_client, changeset_prefix="sam-integ-")

    @parameterized.expand([("basic_function.yaml", "cfn_basic_function.yaml", "basic_function.json")])
    @pytest.mark.flaky(reruns=1) # why we need this one?
    def test_basic_function(self, input_file_name, out_put_file_name, expected_name):
        input_file_path = str(Path(self.template_dir, input_file_name))
        self.output_file_path = str(Path(self.output_dir, out_put_file_name))
        expected_resource_path = str(Path(self.expected_dir, expected_name))
        self.stack_name = STACK_NAME_PREFIX + input_file_name.split('.')[0].replace('_', '-')

        transform_template(input_file_path, self.output_file_path)

        # deploy to cfn
        with open(self.output_file_path, 'r') as cfn_file:
            result, changeset_type = self.deployer.create_and_wait_for_changeset(
                stack_name=self.stack_name,
                cfn_template=cfn_file.read(),
                parameter_values=[],
                capabilities=['CAPABILITY_IAM'],
                role_arn=None,
                notification_arns=[],
                s3_uploader=None,
                tags=[],
            )
            self.deployer.execute_changeset(result["Id"], self.stack_name)
            self.deployer.wait_for_execute(self.stack_name, changeset_type)

            # verify
            stacks_description = self.cloudformation_client.describe_stacks(StackName=self.stack_name)
            stack_resources = self.cloudformation_client.list_stack_resources(StackName=self.stack_name)
            # verify if the stack is create successfully or not
            self.assertEqual(stacks_description['Stacks'][0]['StackStatus'], 'CREATE_COMPLETE')
            # verify if the stack contain the expected resources
            self.assertTrue(verify_stack_resources(expected_resource_path, stack_resources))

    # clean up
    # delete stack and delete translated cfn template
    def tearDown(self):
        self.cloudformation_client.delete_stack(StackName=self.stack_name)
        os.remove(self.output_file_path)
