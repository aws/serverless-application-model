import os
from pathlib import Path
from unittest.case import TestCase

import boto3
import pytest
import yaml
from samcli.lib.deploy.deployer import Deployer
from tests_integ.helpers.helpers import transform_template, verify_stack_resources, generate_suffix, create_bucket

STACK_NAME_PREFIX = "sam-integ-stack-"
S3_BUCKET_PREFIX = "sam-integ-bucket-"
CODE_KEY_TO_FILE_MAP = {'codeuri': 'code.zip', 'contenturi': 'layer1.zip', 'definitionuri': "swagger1.json"}


class BaseTest(TestCase):

    @classmethod
    def setUpClass(cls):
        BaseTest.tests_integ_dir = Path(__file__).resolve().parents[1]
        BaseTest.template_dir = Path(BaseTest.tests_integ_dir, 'resources', 'templates', 'single')
        BaseTest.output_dir = BaseTest.tests_integ_dir
        BaseTest.expected_dir = Path(BaseTest.tests_integ_dir, 'resources', 'expected', 'single')
        code_dir = Path(BaseTest.tests_integ_dir, 'resources', 'code')

        BaseTest.s3_bucket_name = S3_BUCKET_PREFIX + generate_suffix()
        session = boto3.session.Session()
        my_region = session.region_name
        create_bucket(BaseTest.s3_bucket_name, region=my_region)

        s3_client = boto3.client("s3")
        BaseTest.code_key_to_url = {}

        for key, file_name in CODE_KEY_TO_FILE_MAP.items():
            code_path = str(Path(code_dir, file_name))
            s3_client.upload_file(code_path, BaseTest.s3_bucket_name, file_name)
            code_url = f"s3://{BaseTest.s3_bucket_name}/{file_name}"
            BaseTest.code_key_to_url[key] = code_url

    def setUp(self):
        self.cloudformation_client = boto3.client("cloudformation")
        self.deployer = Deployer(self.cloudformation_client, changeset_prefix="sam-integ-")

    def create_and_verify_stack(self, file_name):
        input_file_path = str(Path(BaseTest.template_dir, file_name + ".yaml"))
        self.output_file_path = str(Path(BaseTest.output_dir, 'cfn_' + file_name + ".yaml"))
        expected_resource_path = str(Path(BaseTest.expected_dir, file_name + ".json"))
        self.stack_name = STACK_NAME_PREFIX + file_name.replace('_', '-') + generate_suffix()

        self.sub_input_file_path = str(Path(BaseTest.output_dir, 'sub_' + file_name + ".yaml"))
        with open(input_file_path, 'r') as f:
            data = f.read()
        for key, s3_url in BaseTest.code_key_to_url.items():
            data = data.replace(f"${{{key}}}", s3_url)
        yaml_doc = yaml.load(data, Loader=yaml.FullLoader)

        with open(self.sub_input_file_path, 'w') as f:
            yaml.dump(yaml_doc, f)

        transform_template(self.sub_input_file_path, self.output_file_path)

        # deploy to cfn
        with open(self.output_file_path, 'r') as cfn_file:
            result, changeset_type = self.deployer.create_and_wait_for_changeset(
                stack_name=self.stack_name,
                cfn_template=cfn_file.read(),
                parameter_values=[],
                capabilities=['CAPABILITY_IAM', 'CAPABILITY_AUTO_EXPAND'],
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

    def tearDown(self):
        self.cloudformation_client.delete_stack(StackName=self.stack_name)
        if os.path.exists(self.output_file_path):
            os.remove(self.output_file_path)
        if os.path.exists(self.sub_input_file_path):
            os.remove(self.sub_input_file_path)

    @classmethod
    def tearDownClass(cls) -> None:
        s3_client = boto3.client("s3")
        response = s3_client.list_objects(Bucket=BaseTest.s3_bucket_name)
        for content in response['Contents']:
            s3_client.delete_object(Key=content['Key'], Bucket=BaseTest.s3_bucket_name)
        s3_client.delete_bucket(Bucket=BaseTest.s3_bucket_name)
