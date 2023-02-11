from unittest.case import skipIf

from botocore.exceptions import ClientError

from integration.config.service_names import SERVERLESS_REPO
from integration.helpers.base_test import BaseTest
from integration.helpers.deployer.exceptions.exceptions import ThrottlingError
from integration.helpers.deployer.utils.retry import retry_with_exponential_backoff_and_jitter
from integration.helpers.resource import current_region_does_not_support


class TestFunctionWithApplication(BaseTest):
    @skipIf(
        current_region_does_not_support([SERVERLESS_REPO]), "ServerlessRepo is not supported in this testing region"
    )
    def test_function_referencing_outputs_from_application(self):
        self.create_and_verify_stack("combination/function_with_application")

        lambda_function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        nested_stack_name = self.get_physical_id_by_type("AWS::CloudFormation::Stack")
        lambda_client = self.client_provider.lambda_client
        cfn_client = self.client_provider.cfn_client

        function_config = lambda_client.get_function_configuration(FunctionName=lambda_function_name)
        stack_result = self._describe_stacks(cfn_client, nested_stack_name)
        expected = stack_result["Stacks"][0]["Outputs"][0]["OutputValue"]

        self.assertEqual(function_config["Environment"]["Variables"]["TABLE_NAME"], expected)

    @retry_with_exponential_backoff_and_jitter(ThrottlingError, 5, 360)
    def _describe_stacks(self, cfn_client, stack_name):
        try:
            stack_result = cfn_client.describe_stacks(StackName=stack_name)
        except ClientError as ex:
            if "Throttling" in str(ex):
                raise ThrottlingError(stack_name=stack_name, msg=str(ex))
            raise ex

        return stack_result
