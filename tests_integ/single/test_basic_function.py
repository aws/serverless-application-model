import json
import logging
import os
import sys
from functools import reduce
from unittest.case import TestCase

import boto3
from samcli.lib.deploy.deployer import Deployer
from samtranslator.model.exceptions import InvalidDocumentException
from samtranslator.translator.managed_policy_translator import ManagedPolicyLoader
from samtranslator.translator.transform import transform
from samtranslator.yaml_helper import yaml_parse

LOG = logging.getLogger(__name__)
iam_client = boto3.client("iam")
my_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, my_path + "/..")

STACK_NAME = "foss-integ-test"
INPUT_TEMPLATE = "basic_function.yaml"
TRANSLATED_CFN_TEMPLATE = "cfn_basic_function.yaml"
EXPECTED_JSON_FILE = "expected_basic_function.json"


# can we import this from sam-translate.py?
def transform_template(input_file_path, output_file_path):
    with open(input_file_path, "r") as f:
        sam_template = yaml_parse(f)

    try:
        cloud_formation_template = transform(sam_template, {}, ManagedPolicyLoader(iam_client))
        cloud_formation_template_prettified = json.dumps(cloud_formation_template, indent=2)

        with open(output_file_path, "w") as f:
            f.write(cloud_formation_template_prettified)

        print("Wrote transformed CloudFormation template to: " + output_file_path)
    except InvalidDocumentException as e:
        errorMessage = reduce(lambda message, error: message + " " + error.message, e.causes, e.message)
        LOG.error(errorMessage)
        errors = map(lambda cause: cause.message, e.causes)
        LOG.error(errors)


def verify_stack_resources(expected_file_path, stack_resources):
    with open(expected_file_path, 'r') as expected_data:
        expected_resources = json.load(expected_data)
        parsed_resources = _parse_stack_resources(stack_resources)
    return expected_resources == parsed_resources


def _parse_stack_resources(stack_resources):
    logic_id_to_resource_type = {}
    for resource in stack_resources['StackResourceSummaries']:
        logic_id_to_resource_type[resource['LogicalResourceId']] = resource['ResourceType']
    return logic_id_to_resource_type


class TestBasicFunction(TestCase):
    # set up before every tests run:
    # upload test code to s3
    # replace the template's codeuri with s3 location

    # move client set up to here and create template folder to store translated cfn template, or upload template to s3?
    # def setUp(self):
    #     pass

    def test_basic_function(self):
        # make stack
        # transform sam template to cfn template
        cwd = os.getcwd()
        input_file_path = os.path.join(cwd, 'resources', 'templates', 'single', INPUT_TEMPLATE)
        output_file_path = os.path.join(cwd, TRANSLATED_CFN_TEMPLATE)
        expected_resource_path = os.path.join(cwd, EXPECTED_JSON_FILE)
        transform_template(input_file_path, output_file_path)

        # cfn part
        cloudformation_client = boto3.client("cloudformation")
        deployer = Deployer(cloudformation_client, changeset_prefix="foss-integ")

        # deploy to cfn
        with open(output_file_path, 'r') as cfn_file:
            result, changeset_type = deployer.create_and_wait_for_changeset(
                stack_name=STACK_NAME,
                cfn_template=cfn_file.read(),
                parameter_values=[],
                capabilities=['CAPABILITY_IAM'],
                role_arn=None,
                notification_arns=[],
                s3_uploader=None,
                tags=[],
            )
            deployer.execute_changeset(result["Id"], STACK_NAME)
            deployer.wait_for_execute(STACK_NAME, changeset_type)

            # verify
            stacks_description = cloudformation_client.describe_stacks(StackName=STACK_NAME)
            stack_resources = cloudformation_client.list_stack_resources(StackName=STACK_NAME)
            # verify if the stack is create successfully or not
            self.assertEqual(stacks_description['Stacks'][0]['StackStatus'], 'CREATE_COMPLETE')
            # verify if the stack contain the expected resources
            self.assertTrue(verify_stack_resources(expected_resource_path, stack_resources))

    # clean up
    # delete stack and delete translated cfn template
    # def tearDown(self):
    #     pass
