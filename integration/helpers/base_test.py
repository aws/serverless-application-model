import logging
import os
import requests
import shutil

import botocore
import pytest

from integration.config.logger_configurations import LoggingConfiguration
from integration.helpers.client_provider import ClientProvider
from integration.helpers.deployer.exceptions.exceptions import ThrottlingError
from integration.helpers.deployer.utils.retry import retry_with_exponential_backoff_and_jitter
from integration.helpers.exception import StatusCodeError
from integration.helpers.request_utils import RequestUtils
from integration.helpers.resource import generate_suffix, create_bucket, verify_stack_resources
from integration.helpers.s3_uploader import S3Uploader
from integration.helpers.yaml_utils import dump_yaml, load_yaml
from samtranslator.yaml_helper import yaml_parse

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    after_log,
    wait_random,
)

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path
from unittest.case import TestCase

import boto3
from botocore.exceptions import ClientError
from integration.helpers.deployer.deployer import Deployer
from integration.helpers.template import transform_template

from integration.helpers.file_resources import FILE_TO_S3_URI_MAP, CODE_KEY_TO_FILE_MAP

LOG = logging.getLogger(__name__)

REQUEST_LOGGER = logging.getLogger(f"{__name__}.requests")
LoggingConfiguration.configure_request_logger(REQUEST_LOGGER)

STACK_NAME_PREFIX = "sam-integ-stack-"
S3_BUCKET_PREFIX = "sam-integ-bucket-"


class BaseTest(TestCase):
    @pytest.fixture(autouse=True)
    def prefix(self, get_prefix):
        self.pipeline_prefix = get_prefix

    @pytest.fixture(autouse=True)
    def stage(self, get_stage):
        self.pipeline_stage = get_stage

    @classmethod
    @pytest.mark.usefixtures("get_prefix", "get_stage", "check_internal", "parameter_values")
    def setUpClass(cls):
        cls.FUNCTION_OUTPUT = "hello"
        cls.tests_integ_dir = Path(__file__).resolve().parents[1]
        cls.resources_dir = Path(cls.tests_integ_dir, "resources")
        cls.template_dir = Path(cls.resources_dir, "templates")
        cls.output_dir = Path(cls.tests_integ_dir, "tmp" + "-" + generate_suffix())
        cls.expected_dir = Path(cls.resources_dir, "expected")
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
        shutil.rmtree(cls.output_dir)

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
        self.s3_uploader = S3Uploader(self.client_provider.s3_client, self.s3_bucket_name)

    def tearDown(self):
        if self.stack_name:
            self.client_provider.cfn_client.delete_stack(StackName=self.stack_name)
        if self.output_file_path and os.path.exists(self.output_file_path):
            os.remove(self.output_file_path)
        if self.sub_input_file_path and os.path.exists(self.sub_input_file_path):
            os.remove(self.sub_input_file_path)

    def create_stack(self, file_path, parameters=None, s3_uploader=None):
        """
        Creates the Cloud Formation stack and verifies it against the expected
        result

        Parameters
        ----------
        file_path : string
            Template file name, format "folder_name/file_name"
        parameters : list
            List of parameters
        s3_uploader: S3Uploader object
            Object for uploading files to s3
        """
        folder, file_name = file_path.split("/")
        self.generate_out_put_file_path(folder, file_name)
        self.stack_name = (
            self.pipeline_prefix + STACK_NAME_PREFIX + file_name.replace("_", "-") + "-" + generate_suffix()
        )

        self._fill_template(folder, file_name)
        self.transform_template()
        self._create_stack(parameters, s3_uploader)

    def create_and_verify_stack(self, file_path, parameters=None, s3_uploader=None):
        """
        Creates the Cloud Formation stack and verifies it against the expected
        result

        Parameters
        ----------
        file_path : string
            Template file name, format "folder_name/file_name"
        parameters : list
            List of parameters
        s3_uploader: S3Uploader object
            Object for uploading files to s3
        """
        folder, file_name = file_path.split("/")

        # If template is too large, calling the method with self.s3_uploader to send the template to s3 then deploy
        self.create_stack(file_path, parameters, s3_uploader)
        self.expected_resource_path = str(Path(self.expected_dir, folder, file_name + ".json"))
        self.verify_stack()

    def update_stack(self, parameters=None, file_path=None):
        """
        Updates the Cloud Formation stack

        Parameters
        ----------
        parameters : list
            List of parameters
        file_path : string
            Template file name, format "folder_name/file_name"
        """
        if not self.stack_name:
            raise Exception("Stack not created.")

        if file_path:
            if os.path.exists(self.output_file_path):
                os.remove(self.output_file_path)
            if os.path.exists(self.sub_input_file_path):
                os.remove(self.sub_input_file_path)

            folder, file_name = file_path.split("/")
            self.generate_out_put_file_path(folder, file_name)

            self._fill_template(folder, file_name)

        self.transform_template()
        self._update_stack(parameters)

    def update_and_verify_stack(self, parameters=None, file_path=None):
        """
        Updates the Cloud Formation stack with new template and verifies it against the expected
        result

        Parameters
        ----------
        parameters : list
            List of parameters
        file_path : string
            Template file name, format "folder_name/file_name"
        """
        self.update_stack(file_path=file_path, parameters=parameters)

        folder, file_name = file_path.split("/")
        self.generate_out_put_file_path(folder, file_name)
        self.expected_resource_path = str(Path(self.expected_dir, folder, file_name + ".json"))
        self.verify_stack(end_state="UPDATE_COMPLETE")

    def generate_out_put_file_path(self, folder_name, file_name):
        # add a folder name before file name to avoid possible collisions between
        # files in the single and combination folder
        self.output_file_path = str(
            Path(self.output_dir, "cfn_" + folder_name + "_" + file_name + generate_suffix() + ".yaml")
        )

    def transform_template(self):
        if not self.pipeline_stage:
            transform_template(self.sub_input_file_path, self.output_file_path)
        else:
            transform_name = "AWS::Serverless-2016-10-31"
            if self.pipeline_stage == "beta":
                transform_name = "AWS::Serverless-2016-10-31-Beta"
            elif self.pipeline_stage == "gamma":
                transform_name = "AWS::Serverless-2016-10-31-Gamma"
            elif self.pipeline_stage == "test":
                transform_name = "AWS::Serverless-2016-10-31-test"
            template = load_yaml(self.sub_input_file_path)
            template["AWSTemplateFormatVersion"] = "2010-09-09"
            template["Transform"] = transform_name

            dump_yaml(self.output_file_path, template)
            print("Wrote transformed CloudFormation template to: " + self.output_file_path)

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

    def _fill_template(self, folder, file_name):
        """
        Replaces the template variables with their value

        Parameters
        ----------
        folder : string
            The combination/single folder which contains the template
        file_name : string
            Template file name
        """
        input_file_path = str(Path(self.template_dir, folder, file_name + ".yaml"))
        # add a folder name before file name to avoid possible collisions between
        # files in the single and combination folder
        updated_template_path = self.output_file_path.split(".yaml")[0] + "_sub" + ".yaml"
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

    def remove_template_resource_property(self, resource_name, property_name):
        """
        remove a resource property of the current SAM template

        Parameters
        ----------
        resource_name: string
            resource name
        property_name: string
            property name
        """
        yaml_doc = load_yaml(self.sub_input_file_path)
        del yaml_doc["Resources"][resource_name]["Properties"][property_name]
        dump_yaml(self.sub_input_file_path, yaml_doc)

    def get_template_resource_property(self, resource_name, property_name):
        yaml_doc = load_yaml(self.sub_input_file_path)
        return yaml_doc["Resources"][resource_name]["Properties"][property_name]

    def _create_stack(self, parameters=None, s3_uploader=None):
        self._create_and_execute_changeset_with_type("CREATE", parameters, s3_uploader)

    def _update_stack(self, parameters=None):
        self._create_and_execute_changeset_with_type("UPDATE", parameters)

    def _create_and_execute_changeset_with_type(self, changeset_type, parameters=None, s3_uploader=None):
        with open(self.output_file_path) as cfn_file:
            result = self.deployer.create_and_wait_for_changeset(
                stack_name=self.stack_name,
                cfn_template=cfn_file.read(),
                parameter_values=[] if parameters is None else parameters,
                capabilities=["CAPABILITY_IAM", "CAPABILITY_AUTO_EXPAND"],
                role_arn=None,
                notification_arns=[],
                s3_uploader=s3_uploader,
                tags=[],
                changeset_type=changeset_type,
            )
            self.deployer.execute_changeset(result["Id"], self.stack_name)
            self.deployer.wait_for_execute(self.stack_name, changeset_type)

        self._get_stack_description()
        self.stack_resources = self.client_provider.cfn_client.list_stack_resources(StackName=self.stack_name)

    @retry_with_exponential_backoff_and_jitter(ThrottlingError, 5, 360)
    def _get_stack_description(self):
        try:
            self.stack_description = self.client_provider.cfn_client.describe_stacks(StackName=self.stack_name)
        except botocore.exceptions.ClientError as ex:
            if "Throttling" in str(ex):
                raise ThrottlingError(stack_name=self.stack_name, msg=str(ex))
            raise

    def verify_stack(self, end_state="CREATE_COMPLETE"):
        """
        Gets and compares the Cloud Formation stack against the expect result file
        """
        # verify if the stack was successfully created
        self.assertEqual(self.stack_description["Stacks"][0]["StackStatus"], end_state)
        assert self.stack_description["Stacks"][0]["StackStatus"] == end_state
        # verify if the stack contains the expected resources
        error = verify_stack_resources(self.expected_resource_path, self.stack_resources)
        if error:
            self.fail(error)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10) + wait_random(0, 1),
        retry=retry_if_exception_type(StatusCodeError),
        after=after_log(LOG, logging.WARNING),
        reraise=True,
    )
    def verify_get_request_response(self, url, expected_status_code, headers=None):
        """
        Verify if the get request to a certain url return the expected status code

        Parameters
        ----------
        url : string
            the url for the get request
        expected_status_code : int
            the expected status code
        headers : dict
            headers to use in request
        """
        response = BaseTest.do_get_request_with_logging(url, headers)
        if response.status_code != expected_status_code:
            raise StatusCodeError(
                "Request to {} failed with status: {}, expected status: {}".format(
                    url, response.status_code, expected_status_code
                )
            )
        return response

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10) + wait_random(0, 1),
        retry=retry_if_exception_type(StatusCodeError),
        after=after_log(LOG, logging.WARNING),
        reraise=True,
    )
    def verify_options_request(self, url, expected_status_code, headers=None):
        """
        Verify if the option request to a certain url return the expected status code

        Parameters
        ----------
        url : string
            the url for the get request
        expected_status_code : int
            the expected status code
        headers : dict
            headers to use in request
        """
        response = BaseTest.do_options_request_with_logging(url, headers)
        if response.status_code != expected_status_code:
            raise StatusCodeError(
                "Request to {} failed with status: {}, expected status: {}".format(
                    url, response.status_code, expected_status_code
                )
            )
        return response

    def get_default_test_template_parameters(self):
        """
        get the default template parameters
        """
        parameters = [
            {
                "ParameterKey": "Bucket",
                "ParameterValue": self.s3_bucket_name,
                "UsePreviousValue": False,
                "ResolvedValue": "string",
            },
            {
                "ParameterKey": "CodeKey",
                "ParameterValue": "code.zip",
                "UsePreviousValue": False,
                "ResolvedValue": "string",
            },
            {
                "ParameterKey": "SwaggerKey",
                "ParameterValue": "swagger1.json",
                "UsePreviousValue": False,
                "ResolvedValue": "string",
            },
        ]
        return parameters

    @staticmethod
    def generate_parameter(key, value, previous_value=False, resolved_value="string"):
        parameter = {
            "ParameterKey": key,
            "ParameterValue": value,
            "UsePreviousValue": previous_value,
            "ResolvedValue": resolved_value,
        }
        return parameter

    @staticmethod
    def do_get_request_with_logging(url, headers=None):
        """
        Perform a get request to an APIGW endpoint and log relevant info
        Parameters
        ----------
        url : string
            the url for the get request
        headers : dict
            headers to use in request
        """
        response = requests.get(url, headers=headers) if headers else requests.get(url)
        amazon_headers = RequestUtils(response).get_amazon_headers()
        REQUEST_LOGGER.info("Request made to " + url, extra={"status": response.status_code, "headers": amazon_headers})
        return response

    @staticmethod
    def do_options_request_with_logging(url, headers=None):
        """
        Perform a options request to an APIGW endpoint and log relevant info
        Parameters
        ----------
        url : string
            the url for the get request
        headers : dict
            headers to use in request
        """
        response = requests.options(url, headers=headers) if headers else requests.get(url)
        amazon_headers = RequestUtils(response).get_amazon_headers()
        REQUEST_LOGGER.info("Request made to " + url, extra={"status": response.status_code, "headers": amazon_headers})
        return response
