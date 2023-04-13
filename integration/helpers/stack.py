from pathlib import Path

import botocore

from integration.helpers.deployer.deployer import Deployer
from integration.helpers.deployer.exceptions.exceptions import TerminationProtectionUpdateFailedError, ThrottlingError
from integration.helpers.deployer.utils.retry import retry_with_exponential_backoff_and_jitter
from integration.helpers.resource import generate_suffix
from integration.helpers.template import transform_template


class Stack:
    def __init__(self, stack_name, template_path, cfn_client, output_dir):
        self.stack_name = stack_name
        self.template_path = str(template_path)
        self.cfn_client = cfn_client
        self.deployer = Deployer(cfn_client)
        self.output_dir = str(output_dir)
        self.stack_description = None
        self.stack_resources = None

    def create_or_update(self, update):
        output_template_path = self._generate_output_file_path(self.template_path, self.output_dir)
        transform_template(self.template_path, output_template_path)
        self._deploy_stack(output_template_path, update)

    def delete(self):
        self.cfn_client.delete_stack(StackName=self.stack_name)

    def get_stack_outputs(self):
        if not self.stack_description:
            return {}
        output_list = self.stack_description["Stacks"][0]["Outputs"]
        return {output["OutputKey"]: output["OutputValue"] for output in output_list}

    def _deploy_stack(self, output_file_path, update, parameters=None):
        """
        Deploys the current cloud formation stack
        """
        with open(output_file_path) as cfn_file:
            result = self.deployer.create_and_wait_for_changeset(
                stack_name=self.stack_name,
                cfn_template=cfn_file.read(),
                parameter_values=[] if parameters is None else parameters,
                capabilities=["CAPABILITY_IAM", "CAPABILITY_AUTO_EXPAND"],
                role_arn=None,
                notification_arns=[],
                s3_uploader=None,
                tags=[],
                changeset_type="UPDATE" if update else "CREATE",
            )
            if result:
                self.deployer.execute_changeset(result["Id"], self.stack_name)
                self.deployer.wait_for_execute(self.stack_name, "UPDATE" if update else "CREATE")

        self._get_stack_description()
        self._udpate_termination_protection()
        self.stack_resources = self.cfn_client.list_stack_resources(StackName=self.stack_name)

    @retry_with_exponential_backoff_and_jitter(ThrottlingError, 5, 360)
    def _get_stack_description(self):
        try:
            self.stack_description = self.cfn_client.describe_stacks(StackName=self.stack_name)
        except botocore.exceptions.ClientError as ex:
            if "Throttling" in str(ex):
                raise ThrottlingError(stack_name=self.stack_name, msg=str(ex))
            raise

    def _udpate_termination_protection(self, enable=True):
        try:
            self.cfn_client.update_termination_protection(EnableTerminationProtection=enable, StackName=self.stack_name)
        except botocore.exceptions.ClientError as ex:
            raise TerminationProtectionUpdateFailedError(stack_name=self.stack_name, msg=str(ex))

    @staticmethod
    def _generate_output_file_path(file_path, output_dir):
        # add a folder name before file name to avoid possible collisions between
        # files in the single and combination folder
        folder_name = file_path.split("/")[-2]
        file_name = file_path.split("/")[-1].split(".")[0]
        return str(Path(output_dir, "cfn_" + folder_name + "_" + file_name + generate_suffix() + ".yaml"))
