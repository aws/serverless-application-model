import logging
import os

from integration.helpers.client_provider import ClientProvider
from integration.helpers.resource import generate_suffix, create_bucket, verify_stack_resources
from integration.helpers.yaml_utils import dump_yaml, load_yaml
from samtranslator.yaml_helper import yaml_parse

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path
from unittest.case import TestCase

import boto3
import pytest
import yaml
from botocore.exceptions import ClientError
from botocore.config import Config
from integration.helpers.deployer.deployer import Deployer
from integration.helpers.template import transform_template

from integration.helpers.file_resources import FILE_TO_S3_URI_MAP, CODE_KEY_TO_FILE_MAP

LOG = logging.getLogger(__name__)
STACK_NAME_PREFIX = "sam-integ-stack-"
S3_BUCKET_PREFIX = "sam-integ-bucket-"


class BaseTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.FUNCTION_OUTPUT = "hello"
        cls.tests_integ_dir = Path(__file__).resolve().parents[1]
        cls.resources_dir = Path(cls.tests_integ_dir, "resources")
        cls.template_dir = Path(cls.resources_dir, "templates", "single")
        cls.output_dir = Path(cls.tests_integ_dir, "tmp")
        cls.expected_dir = Path(cls.resources_dir, "expected", "single")
        cls.code_dir = Path(cls.resources_dir, "code")
        cls.s3_bucket_name = S3_BUCKET_PREFIX + generate_suffix()
        cls.session = boto3.session.Session()
        cls.my_region = cls.session.region_name
        cls.client_provider = ClientProvider()
        cls.file_to_s3_uri_map = FILE_TO_S3_URI_MAP
        cls.code_key_to_file = CODE_KEY_TO_FILE_MAP

        if not cls.output_dir.exists():
            os.mkdir(str(cls.output_dir))

        cls._upload_resources(FILE_TO_S3_URI_MAP)

    @classmethod
    def tearDownClass(cls):
        cls._clean_bucket()

    @classmethod
    def _clean_bucket(cls):
        """
        Empties and deletes the bucket used for the tests
        """
        s3 = boto3.resource("s3")
        bucket = s3.Bucket(cls.s3_bucket_name)
        object_summary_iterator = bucket.objects.all()

        for object_summary in object_summary_iterator:
            try:
                cls.client_provider.s3_client.delete_object(Key=object_summary.key, Bucket=cls.s3_bucket_name)
            except ClientError as e:
                LOG.error(
                    "Unable to delete object %s from bucket %s", object_summary.key, cls.s3_bucket_name, exc_info=e
                )
        try:
            cls.client_provider.s3_client.delete_bucket(Bucket=cls.s3_bucket_name)
        except ClientError as e:
            LOG.error("Unable to delete bucket %s", cls.s3_bucket_name, exc_info=e)

    @classmethod
    def _upload_resources(cls, file_to_s3_uri_map):
        """
        Creates the bucket and uploads the files used by the tests to it
        """
        if not file_to_s3_uri_map or not file_to_s3_uri_map.items():
            LOG.debug("No resources to upload")
            return

        create_bucket(cls.s3_bucket_name, region=cls.my_region)

        current_file_name = ""

        try:
            for file_name, file_info in file_to_s3_uri_map.items():
                current_file_name = file_name
                code_path = str(Path(cls.code_dir, file_name))
                LOG.debug("Uploading file %s to bucket %s", file_name, cls.s3_bucket_name)
                s3_client = cls.client_provider.s3_client
                s3_client.upload_file(code_path, cls.s3_bucket_name, file_name)
                LOG.debug("File %s uploaded successfully to bucket %s", file_name, cls.s3_bucket_name)
                file_info["uri"] = cls._get_s3_uri(file_name, file_info["type"])
        except ClientError as error:
            LOG.error("Upload of file %s to bucket %s failed", current_file_name, cls.s3_bucket_name, exc_info=error)
            cls._clean_bucket()
            raise error

    @classmethod
    def _get_s3_uri(cls, file_name, uri_type):
        if uri_type == "s3":
            return "s3://{}/{}".format(cls.s3_bucket_name, file_name)

        if cls.my_region == "us-east-1":
            return "https://s3.amazonaws.com/{}/{}".format(cls.s3_bucket_name, file_name)
        if cls.my_region == "us-iso-east-1":
            return "https://s3.us-iso-east-1.c2s.ic.gov/{}/{}".format(cls.s3_bucket_name, file_name)
        if cls.my_region == "us-isob-east-1":
            return "https://s3.us-isob-east-1.sc2s.sgov.gov/{}/{}".format(cls.s3_bucket_name, file_name)

        return "https://s3-{}.amazonaws.com/{}/{}".format(cls.my_region, cls.s3_bucket_name, file_name)

    def setUp(self):
        self.deployer = Deployer(self.client_provider.cfn_client)

    def tearDown(self):
        self.client_provider.cfn_client.delete_stack(StackName=self.stack_name)
        if os.path.exists(self.output_file_path):
            os.remove(self.output_file_path)
        if os.path.exists(self.sub_input_file_path):
            os.remove(self.sub_input_file_path)

    def create_and_verify_stack(self, file_name, parameters=None):
        """
        Creates the Cloud Formation stack and verifies it against the expected
        result

        Parameters
        ----------
        file_name : string
            Template file name
        parameters : list
            List of parameters
        """
        self.output_file_path = str(Path(self.output_dir, "cfn_" + file_name + ".yaml"))
        self.expected_resource_path = str(Path(self.expected_dir, file_name + ".json"))
        self.stack_name = STACK_NAME_PREFIX + file_name.replace("_", "-") + "-" + generate_suffix()

        self._fill_template(file_name)
        self.transform_template()
        self.deploy_stack(parameters)
        self.verify_stack()

    def transform_template(self):
        transform_template(self.sub_input_file_path, self.output_file_path)

    def get_region(self):
        return self.my_region

    def get_s3_uri(self, file_name):
        """
        Returns the S3 URI of a resource file

        Parameters
        ----------
        file_name : string
            Resource file name
        """
        return self.file_to_s3_uri_map[file_name]["uri"]

    def get_code_key_s3_uri(self, code_key):
        """
        Returns the S3 URI of a code key for template replacement

        Parameters
        ----------
        code_key : string
            Template code key
        """
        return self.file_to_s3_uri_map[self.code_key_to_file[code_key]]["uri"]

    def get_stack_resources(self, resource_type, stack_resources=None):
        if not stack_resources:
            stack_resources = self.stack_resources

        resources = []
        for res in stack_resources["StackResourceSummaries"]:
            if res["ResourceType"] == resource_type:
                resources.append(res)

        return resources

    def get_stack_output(self, output_key):
        for output in self.stack_description["Stacks"][0]["Outputs"]:
            if output["OutputKey"] == output_key:
                return output
        return None

    def get_stack_tags(self, output_name):
        resource_arn = self.get_stack_output(output_name)["OutputValue"]
        return self.client_provider.sfn_client.list_tags_for_resource(resourceArn=resource_arn)["tags"]

    def get_stack_deployment_ids(self):
        resources = self.get_stack_resources("AWS::ApiGateway::Deployment")
        ids = []
        for res in resources:
            ids.append(res["LogicalResourceId"])

        return ids

    def get_api_stack_stages(self):
        resources = self.get_stack_resources("AWS::ApiGateway::RestApi")

        if not resources:
            return []

        return self.client_provider.api_client.get_stages(restApiId=resources[0]["PhysicalResourceId"])["item"]

    def get_api_v2_stack_stages(self):
        resources = self.get_stack_resources("AWS::ApiGatewayV2::Api")

        if not resources:
            return []

        return self.client_provider.api_v2_client.get_stages(ApiId=resources[0]["PhysicalResourceId"])["Items"]

    def get_api_v2_endpoint(self, logical_id):
        api_id = self.get_physical_id_by_logical_id(logical_id)
        api = self.client_provider.api_v2_client.get_api(ApiId=api_id)
        return api["ApiEndpoint"]

    def get_stack_nested_stack_resources(self):
        resources = self.get_stack_resources("AWS::CloudFormation::Stack")

        if not resources:
            return None

        return self.client_provider.cfn_client.list_stack_resources(StackName=resources[0]["PhysicalResourceId"])

    def get_stack_outputs(self):
        if not self.stack_description:
            return {}
        output_list = self.stack_description["Stacks"][0]["Outputs"]
        return {output["OutputKey"]: output["OutputValue"] for output in output_list}

    def get_resource_status_by_logical_id(self, logical_id):
        if not self.stack_resources:
            return None

        for res in self.stack_resources["StackResourceSummaries"]:
            if res["LogicalResourceId"] == logical_id:
                return res["ResourceStatus"]

        return None

    def get_physical_id_by_type(self, resource_type):
        if not self.stack_resources:
            return None

        for res in self.stack_resources["StackResourceSummaries"]:
            if res["ResourceType"] == resource_type:
                return res["PhysicalResourceId"]

        return None

    def get_logical_id_by_type(self, resource_type):
        if not self.stack_resources:
            return None

        for res in self.stack_resources["StackResourceSummaries"]:
            if res["ResourceType"] == resource_type:
                return res["LogicalResourceId"]

        return None

    def get_physical_id_by_logical_id(self, logical_id):
        if not self.stack_resources:
            return None

        for res in self.stack_resources["StackResourceSummaries"]:
            if res["LogicalResourceId"] == logical_id:
                return res["PhysicalResourceId"]

        return None

    def _fill_template(self, file_name):
        """
        Replaces the template variables with their value

        Parameters
        ----------
        file_name : string
            Template file name
        """
        input_file_path = str(Path(self.template_dir, file_name + ".yaml"))
        updated_template_path = str(Path(self.output_dir, "sub_" + file_name + ".yaml"))
        with open(input_file_path) as f:
            data = f.read()
        for key, _ in self.code_key_to_file.items():
            # We must double the {} to escape them so they will survive a round of unescape
            data = data.replace("${{{}}}".format(key), self.get_code_key_s3_uri(key))
        yaml_doc = yaml_parse(data)

        dump_yaml(updated_template_path, yaml_doc)

        self.sub_input_file_path = updated_template_path

    def set_template_resource_property(self, resource_name, property_name, value):
        """
        Updates a resource property of the current SAM template

        Parameters
        ----------
        resource_name: string
            resource name
        property_name: string
            property name
        value
            value
        """
        yaml_doc = load_yaml(self.sub_input_file_path)
        yaml_doc["Resources"][resource_name]["Properties"][property_name] = value
        dump_yaml(self.sub_input_file_path, yaml_doc)

    def get_template_resource_property(self, resource_name, property_name):
        yaml_doc = load_yaml(self.sub_input_file_path)
        return yaml_doc["Resources"][resource_name]["Properties"][property_name]

    def deploy_stack(self, parameters=None):
        """
        Deploys the current cloud formation stack
        """
        with open(self.output_file_path) as cfn_file:
            result, changeset_type = self.deployer.create_and_wait_for_changeset(
                stack_name=self.stack_name,
                cfn_template=cfn_file.read(),
                parameter_values=[] if parameters is None else parameters,
                capabilities=["CAPABILITY_IAM", "CAPABILITY_AUTO_EXPAND"],
                role_arn=None,
                notification_arns=[],
                s3_uploader=None,
                tags=[],
            )
            self.deployer.execute_changeset(result["Id"], self.stack_name)
            self.deployer.wait_for_execute(self.stack_name, changeset_type)

        self.stack_description = self.client_provider.cfn_client.describe_stacks(StackName=self.stack_name)
        self.stack_resources = self.client_provider.cfn_client.list_stack_resources(StackName=self.stack_name)

    def verify_stack(self):
        """
        Gets and compares the Cloud Formation stack against the expect result file
        """
        # verify if the stack was successfully created
        self.assertEqual(self.stack_description["Stacks"][0]["StackStatus"], "CREATE_COMPLETE")
        # verify if the stack contains the expected resources
        error = verify_stack_resources(self.expected_resource_path, self.stack_resources)
        if error:
            self.fail(error)
