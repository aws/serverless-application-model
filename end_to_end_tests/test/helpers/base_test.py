from .resources import Resources
from unittest import TestCase
from samtranslator.model.exceptions import (
    InvalidTemplateException,
    InvalidDocumentException,
    MultipleResourceFoundException,
    BucketAlreadyExistsException,
    ResourceNotFoundException,
)
from samtranslator.public.translator import ManagedPolicyLoader
from samtranslator.translator.transform import transform
from samtranslator.yaml_helper import yaml_parse

import boto3
import uuid
import json
import functools
import os


class BaseTest(TestCase):
    """
    A base test case contains commonly used methods for running end to end tests

    Attributes
    ----------
    stack_name : str
        A stack name for the end to end test case. The stack name starts with "sam-temp-stack"
    cloud_formation_client : CloudFormation
        cloudformation client for creating, updating and deleting stacks

    Methods
    -------
    :method make_stack(self, template_path, capabilities)
        creates a CloudFormation stack for the given template
    :method get_stack_resources(self)
        returns stack resources for the given template
    :method get_stack_resource_with_resource_type(self, resource_type)
        returns a stack resource based on the resource type
    :method get_stack_resource_with_logical_id(self, resource_logical_id)
        returns a stack resource for the given logical id
    :method make_and_verify_stack(self, template_path, capabilities, expected_resources)
        creates a stack and verifies if the stack has created same resources as expected resources
    :method verify_stack(self, expected_resources)
        verifies if the stack has created same resources as expected resources
    :method get_outputs(self)
        returns the outputs of the stack as a dictionary
    :method delete_stack(self)
        deletes the stack
    :method create_s3_bucket(cls)
        creates s3 bucket for uploading artifacts for integration tests
    :method delete_s3_bucket(cls)
        deletes the s3 bucket created for integration tests
    :method upload_s3_artifacts(cls)
        Uploads all the files present in end_to_end_tests/test_data path for running integration tests
    :method get_transformed_template(template_path)
        returns the template after applying SAM transformation
    """

    def setUp(self):
        """
        creates a stack name and a cloudformation client for an end to end test
        """
        print("in setup of base test")
        self.stack_name = "sam-temp-stack" + str(uuid.uuid4())
        self.cloud_formation_client = boto3.client("cloudformation")

    @classmethod
    def setUpClass(cls):
        """
        creates sam-temp-integration-test-bucket for uploading integration tests artifacts present in end_to_end_tests/test_data
        """
        cls.s3_client = boto3.client("s3")
        cls.bucket_name = "sam-temp-integration-tests-bucket"
        cls.artifacts_path = "end_to_end_tests/test_data"
        cls.create_s3_bucket()
        cls.upload_artifacts()

    @classmethod
    def tearDownClass(cls):
        """
        delete s3 bucket
        """
        cls.delete_s3_bucket()

    def tearDown(self):
        """
        delete stack
        """
        self.delete_stack()

    def make_stack(self, template_path, capabilities):
        """creates a CloudFormation stack for the given template

        :param str template_path: absolute template path for stack creation
        :param list capabilities: required capabilities to create a stack for the given template
        :return: id of the stack created
        :rtype: str
        """
        template_body = BaseTest.get_transformed_template(template_path=template_path)
        stack_id = self.cloud_formation_client.create_stack(
            StackName=self.stack_name, TemplateBody=template_body, Capabilities=capabilities
        )
        waiter = self.cloud_formation_client.get_waiter("stack_create_complete")
        waiter.wait(StackName=self.stack_name)
        return stack_id

    def get_stack_resources(self):
        """returns stack resources for the given template
        :return: returns a dictionary containing all the stack resources
        :rtype: dict
        """
        stack_resources = self.cloud_formation_client.list_stack_resources(StackName=self.stack_name).get(
            "StackResourceSummaries"
        )
        return stack_resources

    def get_stack_resource_with_resource_type(self, resource_type):
        """returns a stack resource based on the resource type.
        This method returns a stack resource only when there is a single resource with the given resource type

        :param ResourceTypes resource_type: type of the resource in ResourceTypes
        :raise: ResourceNotFoundException if there are no resources found with the given resource type
        :raise: MultipleResourceFoundException if more than one resource is found with the given resource type
        :return: stack resource containing "LogicalResourceId", "PhysicalResourceId", "ResourceType", "ResourceStatus   "
        :rtype: dict
        """
        stack_resources = self.get_stack_resources()
        stack_resource = list(filter(lambda d: d["ResourceType"] == resource_type.value, stack_resources))
        if len(stack_resource) == 1:
            return stack_resource[0]
        elif len(stack_resource) == 0:
            raise ResourceNotFoundException("with resource type {}".format(self._resource_type))
        else:
            raise MultipleResourceFoundException(resource_type.value)

    def get_stack_resource_with_logical_id(self, resource_logical_id):
        """returns a stack resource for the given logical id

        :param int resource_logical_id: logical id of the resource
        :return: stack resource containing "LogicalResourceId", "PhysicalResourceId", "ResourceType", "ResourceStatus   "
        :rtype: dict
        """

        stack_resources = self.get_stack_resources()
        stack_resource = list(filter(lambda d: d["LogicalResourceId"] == resource_logical_id, stack_resources))
        # there is only one resource per logical id
        return stack_resource[0]

    def make_and_verify_stack(self, template_path, capabilities, expected_resources):
        """creates a stack and verifies if the stack has same resources as expected resources

        :param str template_path: absolute template path for stack creation
        :param list capabilities: required capabilities to create a stack for the given template
        :param Resources expected_resources: expected resources for the given template
        """

        self.make_stack(template_path, capabilities)
        self.verify_stack(expected_resources)

    def verify_stack(self, expected_resources):
        """verifies if the stack has created same resources as expected resources.

        :param Resources expected_resources: expected resources for the given template
        """

        stack_resources = self.get_stack_resources()
        list_stack_resources = Resources.from_list(resources_list=stack_resources)
        self.assertEqual(list_stack_resources, expected_resources)

    def get_outputs(self):
        """returns the outputs of the stack as a dictionary

        :return: outputs of the stack are present as key and value pairs where key id the "OutputKey" and value is "OutputValue"
        :rtype: dict
        """

        stack_outputs = (
            self.cloud_formation_client.describe_stacks(StackName=self.stack_name).get("Stacks")[0].get("Outputs")
        )
        outputs = dict()
        if stack_outputs is not None:
            for output in stack_outputs:
                outputs[output.get("OutputKey")] = output.get("OutputValue")
            return outputs

    def delete_stack(self):
        """deletes the stack if the stack exists
        """

        self.cloud_formation_client.delete_stack(StackName=self.stack_name)

    @classmethod
    def create_s3_bucket(cls):
        """creates s3 bucket for uploading artifacts for integration tests
        :raise: BucketAlreadyExistsException if the bucket already exists
        """
        print("inside s3 create should be run only once")
        region_name = boto3.session.Session().region_name
        try:
            if region_name == "us-east-1":
                cls.s3_client.create_bucket(Bucket=cls.bucket_name)
            else:
                cls.s3_client.create_bucket(
                    Bucket=cls.bucket_name, CreateBucketConfiguration={"LocationConstraint": region_name}
                )
        except cls.s3_client.exceptions.BucketAlreadyOwnedByYou:
            raise BucketAlreadyExistsException(cls.bucket_name)

    @classmethod
    def delete_s3_bucket(cls):
        """deletes the s3 bucket created for integration tests
        """
        objects_list = cls.s3_client.list_objects(Bucket=cls.bucket_name).get("Contents")
        for s3_object in objects_list:
            cls.s3_client.delete_object(Bucket=cls.bucket_name, Key=s3_object.get("Key"))

        cls.s3_client.delete_bucket(Bucket=cls.bucket_name)

    @classmethod
    def upload_artifacts(cls):
        """
        Uploads all the files present in end_to_end_tests/test_data path for running integration tests
        """
        print("adding artifacts to s3")
        # for file in path upload the file with the key being file name and value being content of the file
        for file in os.listdir(cls.artifacts_path):
            if not file.startswith("."):
                with open(os.path.join(cls.artifacts_path, file), "rb") as zip_data:
                    cls.s3_client.upload_fileobj(zip_data, cls.bucket_name, file)

    @staticmethod
    def get_transformed_template(template_path):
        """returns the template after applying SAM transformation

        :param str template_path: absolute template path for stack creation
        :raise: IOError if the given input path is not valid
        :raise: InvalidTemplateException if the template has any errors
        :raise: InvalidDocumentException if the template is not valid
        :return: transformed template
        :rtype: str
        """

        try:
            with open(template_path, "r") as f:
                sam_template = yaml_parse(f)
        except IOError:
            raise IOError("The input template path: {} is incorrect.".format(template_path))
        else:
            try:
                iam_client = boto3.client("iam")
                cloud_formation_template = json.dumps(
                    transform(sam_template, {}, ManagedPolicyLoader(iam_client)), indent=2
                )
                if len(cloud_formation_template) == 0:
                    raise InvalidTemplateException(" Template path: ".format(template_path))
                return cloud_formation_template
            except InvalidDocumentException as e:
                error_message = functools.reduce(
                    lambda message, error: message + " " + error.message, e.causes, e.message
                )
                errors = map(lambda cause: cause.message, e.causes)
                raise InvalidDocumentException("The template is invalid {} {}".format(errors, error_message))
