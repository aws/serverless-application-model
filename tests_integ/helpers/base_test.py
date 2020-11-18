import logging
import os
from pathlib import Path
from unittest.case import TestCase

import boto3
import pytest
import yaml
from botocore.exceptions import ClientError
from samcli.lib.deploy.deployer import Deployer
from tests_integ.helpers.helpers import transform_template, verify_stack_resources, generate_suffix, create_bucket

LOG = logging.getLogger(__name__)
STACK_NAME_PREFIX = "sam-integ-stack-"
S3_BUCKET_PREFIX = "sam-integ-bucket-"
CODE_KEY_TO_FILE_MAP = {"codeuri": "code.zip", "contenturi": "layer1.zip", "definitionuri": "swagger1.json"}


class BaseTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tests_integ_dir = Path(__file__).resolve().parents[1]
        cls.resources_dir = Path(cls.tests_integ_dir, "resources")
        cls.template_dir = Path(cls.resources_dir, "templates", "single")
        cls.output_dir = cls.tests_integ_dir
        cls.expected_dir = Path(cls.resources_dir, "expected", "single")
        cls.code_dir = Path(cls.resources_dir, "code")
        cls.s3_bucket_name = S3_BUCKET_PREFIX + generate_suffix()
        cls.session = boto3.session.Session()
        cls.my_region = cls.session.region_name
        cls.s3_client = boto3.client("s3")

        cls._upload_resources()

    @classmethod
    def tearDownClass(cls):
        cls._clean_bucket()

    @classmethod
    def _clean_bucket(cls):
        """
        Empties and deletes the bucket used for the tests
        """
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(cls.s3_bucket_name)
        object_summary_iterator = bucket.objects.all()

        for object_summary in object_summary_iterator:
            cls.s3_client.delete_object(Key=object_summary.key, Bucket=cls.s3_bucket_name)
        cls.s3_client.delete_bucket(Bucket=cls.s3_bucket_name)

    @classmethod
    def _upload_resources(cls):
        """
        Creates the bucket and uploads the files used by the tests to it
        """
        create_bucket(cls.s3_bucket_name, region=cls.my_region)
        code_key_to_url = {}

        try:
            for key, file_name in CODE_KEY_TO_FILE_MAP.items():
                code_path = str(Path(cls.code_dir, file_name))
                LOG.debug(f"Uploading file {file_name} to s3 bucket {cls.s3_bucket_name}.")
                cls.s3_client.upload_file(code_path, cls.s3_bucket_name, file_name)
                LOG.debug(f"{file_name} uploaded successfully.")
                code_url = f"s3://{cls.s3_bucket_name}/{file_name}"
                code_key_to_url[key] = code_url
        except ClientError as error:
            LOG.error('upload failed')
            LOG.error('Error code: ' + error.response['Error']['Code'])
            cls._clean_bucket()
            raise error

        cls.code_key_to_url = code_key_to_url

    def setUp(self):
        self.cloudformation_client = boto3.client("cloudformation")
        self.deployer = Deployer(self.cloudformation_client, changeset_prefix="sam-integ-")

    def tearDown(self):
        self.cloudformation_client.delete_stack(StackName=self.stack_name)
        if os.path.exists(self.output_file_path):
            os.remove(self.output_file_path)
        if os.path.exists(self.sub_input_file_path):
            os.remove(self.sub_input_file_path)

    def create_and_verify_stack(self, file_name):
        """
        Creates the Cloud Formation stack and verifies it against the expected
        result

        Parameters
        ----------
        file_name : string
            Template file name
        """
        self.output_file_path = str(Path(self.output_dir, "cfn_" + file_name + ".yaml"))
        expected_resource_path = str(Path(self.expected_dir, file_name + ".json"))
        self.stack_name = STACK_NAME_PREFIX + file_name.replace("_", "-") + generate_suffix()

        self._update_template(file_name)
        transform_template(self.sub_input_file_path, self.output_file_path)
        self._deploy_stack()
        self._verify_stack(expected_resource_path)

    def _update_template(self, file_name):
        """
        Updates a template before converting it to a cloud formation template
        and saves it to sub_input_file_path

        Parameters
        ----------
        file_name : string
            Template file name
        """
        input_file_path = str(Path(self.template_dir, file_name + ".yaml"))
        updated_template_path = str(Path(self.output_dir, "sub_" + file_name + ".yaml"))
        with open(input_file_path, "r") as f:
            data = f.read()
        for key, s3_url in self.code_key_to_url.items():
            data = data.replace(f"${{{key}}}", s3_url)
        yaml_doc = yaml.load(data, Loader=yaml.FullLoader)

        with open(updated_template_path, "w") as f:
            yaml.dump(yaml_doc, f)

        self.sub_input_file_path = updated_template_path

    def _deploy_stack(self):
        """
        Deploys the current cloud formation stack
        """
        with open(self.output_file_path, "r") as cfn_file:
            result, changeset_type = self.deployer.create_and_wait_for_changeset(
                stack_name=self.stack_name,
                cfn_template=cfn_file.read(),
                parameter_values=[],
                capabilities=["CAPABILITY_IAM", "CAPABILITY_AUTO_EXPAND"],
                role_arn=None,
                notification_arns=[],
                s3_uploader=None,
                tags=[],
            )
            self.deployer.execute_changeset(result["Id"], self.stack_name)
            self.deployer.wait_for_execute(self.stack_name, changeset_type)

    def _verify_stack(self, expected_resource_path):
        """
        Gets and compares the Cloud Formation stack against the expect result file

        Parameters:
        ----------
        expected_resource_path: string
            Absolute path to the expected result file
        """
        stacks_description = self.cloudformation_client.describe_stacks(StackName=self.stack_name)
        stack_resources = self.cloudformation_client.list_stack_resources(StackName=self.stack_name)
        # verify if the stack was successfully created
        self.assertEqual(stacks_description["Stacks"][0]["StackStatus"], "CREATE_COMPLETE")
        # verify if the stack contains the expected resources
        self.assertTrue(verify_stack_resources(expected_resource_path, stack_resources))
