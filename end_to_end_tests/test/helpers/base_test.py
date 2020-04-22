import unittest
import boto3
import uuid
import os
import subprocess
from .resources import Resources
from samtranslator.model.exceptions import InvalidTemplateException


class BaseTest(unittest.TestCase):
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
    :method get_sam_transformed_template(self, template_path)
        returns the template after applying SAM transformation
    """

    def setUp(self):
        """
        creates a stack name and a cloudformation client for an end to end test
        """
        self.stack_name = "sam-temp-stack" + str(uuid.uuid4())
        self.cloud_formation_client = boto3.client("cloudformation")

    def make_stack(self, template_path, capabilities):
        """creates a CloudFormation stack for the given template

        :param str template_path: absolute template path for stack creation
        :param list capabilities: required capabilities to create a stack for the given template
        :raise: Exception if unable to create stack for the given template
        :return: id of the stack created
        :rtype: str
        """
        template_body = self.get_sam_transformed_template(template_path=template_path)
        try:
            stack_id = self.cloud_formation_client.create_stack(
                StackName=self.stack_name, TemplateBody=template_body, Capabilities=capabilities
            )
            waiter = self.cloud_formation_client.get_waiter("stack_create_complete")
            waiter.wait(StackName=self.stack_name)
            return stack_id
        except Exception as e:
            raise Exception("Unable to create stack for template {}. Exception: ".format(template_path, e))

    def get_stack_resources(self):
        """returns stack resources for the given template
        :raise: Exception if unable to get stack resources fof the given stack
        :return: returns a dictionary containing all the stack resources
        :rtype: dict
        """
        try:
            # stack will be its own data type if needed
            stack_resources = self.cloud_formation_client.list_stack_resources(StackName=self.stack_name).get(
                "StackResourceSummaries"
            )
            return stack_resources
        except Exception as e:
            raise Exception("Unable to list stack resources {}".format(e))

    def get_stack_resource_with_resource_type(self, resource_type):
        """returns a stack resource based on the resource type.
        This method returns a stack resource only when there is a single resource with the given resource type

        :param enum resource_type: type of the resource in ResourceTypes
        :raise: ValueError if there are no resources found with the given resource type
        :raise: ValueError if more than one resource is found with the given resource type
        :return: stack resource containing "LogicalResourceId", "PhysicalResourceId", "ResourceType", "ResourceStatus   "
        :rtype: dict
        """
        # stack will be its own data type if needed
        stack_resources = self.get_stack_resources()
        stack_resource = list(filter(lambda d: d["ResourceType"] == resource_type.value, stack_resources))
        if len(stack_resource) == 1:
            return stack_resource[0]
        elif len(stack_resource) == 0:
            raise ValueError("No resources found with resource type {}".format(resource_type.value))
        else:
            raise ValueError(
                "Mutliple resources found with resource type {}. Please get the resource by using the logical id".format(
                    resource_type.value
                )
            )

    def get_stack_resource_with_logical_id(self, resource_logical_id):
        """returns a stack resource for the given logical id

        :param int resource_logical_id: logical id of the resource
        :raise: ValueError if there is no resource with the given logical id
        :return: stack resource containing "LogicalResourceId", "PhysicalResourceId", "ResourceType", "ResourceStatus   "
        :rtype: dict
        """

        # stack will be its own data type if needed
        stack_resources = self.get_stack_resources()
        try:
            stack_resource = list(filter(lambda d: d["LogicalResourceId"] == resource_logical_id, stack_resources))
            # there is only one resource per logical id
            return stack_resource[0]
        except Exception:
            raise ValueError("There is no resource in the stack with given logical id: {}".format(resource_logical_id))

    def make_and_verify_stack(self, template_path, capabilities, expected_resources):
        """creates a stack and verifies if the stack has same resources as expected resources

        :param str template_path: absolute template path for stack creation
        :param list capabilities: required capabilities to create a stack for the given template
        :param dict expected_resources: expected resources for the given template
        """

        self.make_stack(template_path, capabilities)
        self.verify_stack(expected_resources)

    def verify_stack(self, expected_resources):
        """verifies if the stack has created same resources as expected resources.

        :param dict expected_resources: expected resources for the given template
        """

        stack_resources = self.get_stack_resources()
        list_stack_resources = Resources.from_list(resources_list=stack_resources)
        self.assertEqual(list_stack_resources, expected_resources)

    def get_outputs(self):
        """returns the outputs of the stack as a dictionary

        :raise: Exception if unable to get outputs for the stack
        :return: outputs of the stack are present as key and value pairs where key id the "OutputKey" and value is "OutputValue"
        :rtype: dict
        """

        try:
            stack_outputs = (
                self.cloud_formation_client.describe_stacks(StackName=self.stack_name).get("Stacks")[0].get("Outputs")
            )
        except Exception as e:
            raise Exception("Unable to get the stack outputs {}".format(e))
        else:
            outputs = dict()
            if stack_outputs is not None:
                for output in stack_outputs:
                    outputs[output.get("OutputKey")] = output.get("OutputValue")
                return outputs

    def delete_stack(self):
        """deletes the stack if the stack exists
        """

        self.cloud_formation_client.delete_stack(StackName=self.stack_name)

    def get_sam_transformed_template(self, template_path):
        """returns the template after applying SAM transformation

        :param str template_path: absolute template path for stack creation
        :raise: IOError if the given input path is not valid
        :raise: InvalidTemplateException if the template is not transformed successfully
        :return: transformed template
        :rtype: str
        """

        try:
            output_file = self.stack_name + ".json"
            with open(output_file, "w") as fp:
                pass
            subprocess.call(["python", "bin/sam-translate.py", "--template-file", template_path, "--o", output_file])
        except IOError:
            raise IOError("The input template path: {} is incorrect.".format(template_path))
        else:
            if os.path.exists(self.stack_name + ".json"):
                template_body = open(self.stack_name + ".json").read()
                # delete the temporary file created
                os.remove(self.stack_name + ".json")
            if len(template_body) == 0:
                raise InvalidTemplateException(" Template path: ".format(template_path))
            return template_body
