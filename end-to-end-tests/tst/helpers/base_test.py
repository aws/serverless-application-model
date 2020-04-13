import unittest
import boto3
import random
import os
import subprocess
from resources import Resources


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.stack_name = "sam-temp-stack" + str(random.randint(0, 10000))
        self.cloud_formation_client = boto3.client("cloudformation")

    def make_stack(self, capabilties, template_path):
        template_body = self.get_sam_transformed_template(template_path=template_path)
        stack_id = self.cloud_formation_client.create_stack(
            StackName=self.stack_name, TemplateBody=template_body, Capabilities=capabilties
        )
        waiter = self.cloud_formation_client.get_waiter("stack_create_complete")
        waiter.wait(StackName=self.stack_name)
        return stack_id

    def get_stack_resources(self):
        # stack will be its own data type if needed
        stack_resources = self.cloud_formation_client.list_stack_resources(StackName=self.stack_name).get(
            "StackResourceSummaries"
        )
        return stack_resources

    def get_stack_resource_with_resource_type(self, resource_type):
        # stack will be its own data type if needed
        stack_resources = self.get_stack_resources()
        stack_resource = list(filter(lambda d: d['ResourceType'] == resource_type.value, stack_resources))
        if len(stack_resource) == 1:
            return stack_resource[0]
        elif len(stack_resource) == 0:
            raise ValueError("No resources found with resource type {}".format(resource_type.value))
        else:
            raise ValueError("Mutliple resources found with resource type {}. Please get the resource by using the logical id".format(resource_type.value))

    def get_stack_resource_with_logical_id(self, resource_logical_id):
        # stack will be its own data type if needed
        stack_resources = self.get_stack_resources()
        try:
            stack_resource = list(filter(lambda d: d['LogicalResourceId'] == resource_logical_id, stack_resources))
            # one resource per logical id
            return stack_resource[0]
        except:
            raise ValueError("There is no resource in the stack with given logical id: {}".format(resource_logical_id))

    # add expected_resources instead of count
    def make_and_verify_stack(self, template_path, capabilities, expected_resources):
        self.make_stack(capabilities, template_path)
        stack_resources = self.get_stack_resources()
        list_stack_resources = Resources().from_list(resources_list=stack_resources)
        self.assertEquals(list_stack_resources, expected_resources)
        # return stack
        return self.stack_name

    def get_outputs(self):
        stack_outputs = (
            self.cloud_formation_client.describe_stacks(StackName=self.stack_name).get("Stacks")[0].get("Outputs")
        )
        outputs = dict()
        if stack_outputs is not None:
            for output in stack_outputs:
                outputs[output.get("OutputKey")] = output.get("OutputValue")
            return outputs

    def delete_stack(self):
        self.cloud_formation_client.delete_stack(StackName=self.stack_name)

    def get_sam_transformed_template(self, template_path):
        try:
            # template_body = open(template_path).read()
            subprocess.call(["bin/sam-translate.py", "--template-file", template_path, "--o", self.stack_name+".json"])
            template_body = open(self.stack_name+".json").read()
            # delete the file directly
            if os.path.exists(self.stack_name+".json"):
                os.remove(self.stack_name+".json")
            return template_body
        except IOError:
            raise IOError("The input template path: {} is not correct.".format(template_path))
