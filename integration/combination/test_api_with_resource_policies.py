import json
from unittest.case import skipIf

from integration.config.service_names import REST_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([REST_API]), "Rest API is not supported in this testing region")
class TestApiWithResourcePolicies(BaseTest):
    def test_api_resource_policies(self):
        self.create_and_verify_stack("combination/api_with_resource_policies")

        stack_outputs = self.get_stack_outputs()
        region = stack_outputs["Region"]
        accountId = stack_outputs["AccountId"]
        partition = stack_outputs["Partition"]
        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        apigw_client = self.client_provider.api_client

        rest_api_response = apigw_client.get_rest_api(restApiId=rest_api_id)
        policy_str = rest_api_response["policy"]

        expected_policy_str = (
            '{"Version":"2012-10-17",'
            + '"Statement":[{"Effect":"Allow",'
            + '"Principal":"*",'
            + '"Action":"execute-api:Invoke",'
            + '"Resource":"arn:'
            + partition
            + ":execute-api:"
            + region
            + ":"
            + accountId
            + ":"
            + rest_api_id
            + '\\/Prod\\/*\\/apione"},'
            + '{"Effect":"Deny",'
            + '"Principal":"*",'
            + '"Action":"execute-api:Invoke",'
            + '"Resource":"arn:'
            + partition
            + ":execute-api:"
            + region
            + ":"
            + accountId
            + ":"
            + rest_api_id
            + '\\/Prod\\/*\\/apione",'
            + '"Condition":{"NotIpAddress":'
            + '{"aws:SourceIp":"1.2.3.4"}}},'
            + '{"Effect":"Deny",'
            + '"Principal":"*",'
            + '"Action":"execute-api:Invoke",'
            + '"Resource":"arn:'
            + partition
            + ":execute-api:"
            + region
            + ":"
            + accountId
            + ":"
            + rest_api_id
            + '\\/Prod\\/*\\/apione",'
            + '"Condition":{"StringNotEquals":'
            + '{"aws:SourceVpc":"vpc-1234"}}},'
            + '{"Effect":"Deny",'
            + '"Principal":"*",'
            + '"Action":"execute-api:Invoke",'
            + '"Resource":"arn:'
            + partition
            + ":execute-api:"
            + region
            + ":"
            + accountId
            + ":"
            + rest_api_id
            + '\\/Prod\\/*\\/apione",'
            + '"Condition":{"StringEquals":'
            + '{"aws:SourceVpce":"vpce-5678"}}},'
            + '{"Effect":"Allow",'
            + '"Principal":"*",'
            + '"Action":"execute-api:Invoke",'
            + '"Resource":"arn:'
            + partition
            + ":execute-api:"
            + region
            + ":"
            + accountId
            + ":"
            + rest_api_id
            + '\\/Prod\\/GET\\/apitwo"},'
            + '{"Effect":"Deny",'
            + '"Principal":"*",'
            + '"Action":"execute-api:Invoke",'
            + '"Resource":"arn:'
            + partition
            + ":execute-api:"
            + region
            + ":"
            + accountId
            + ":"
            + rest_api_id
            + '\\/Prod\\/GET\\/apitwo",'
            + '"Condition":{"NotIpAddress":'
            + '{"aws:SourceIp":"1.2.3.4"}}},'
            + '{"Effect":"Deny",'
            + '"Principal":"*",'
            + '"Action":"execute-api:Invoke",'
            + '"Resource":"arn:'
            + partition
            + ":execute-api:"
            + region
            + ":"
            + accountId
            + ":"
            + rest_api_id
            + '\\/Prod\\/GET\\/apitwo",'
            + '"Condition":{"StringNotEquals":'
            + '{"aws:SourceVpc":"vpc-1234"}}},'
            + '{"Effect":"Deny",'
            + '"Principal":"*",'
            + '"Action":"execute-api:Invoke",'
            + '"Resource":"arn:'
            + partition
            + ":execute-api:"
            + region
            + ":"
            + accountId
            + ":"
            + rest_api_id
            + '\\/Prod\\/GET\\/apitwo",'
            + '"Condition":{"StringEquals":'
            + '{"aws:SourceVpce":"vpce-5678"}}},'
            + '{"Effect":"Allow",'
            + '"Principal":"*",'
            + '"Action":"execute-api:Invoke",'
            + '"Resource":"execute-api:*\\/*\\/*"}]}'
        )

        expected_policy = json.loads(expected_policy_str)
        policy = json.loads(policy_str.encode().decode("unicode_escape"))

        self.assertTrue(self.compare_two_policies_object(policy, expected_policy))

    def test_api_resource_policies_aws_account(self):
        self.create_and_verify_stack("combination/api_with_resource_policies_aws_account")

        stack_outputs = self.get_stack_outputs()
        region = stack_outputs["Region"]
        accountId = stack_outputs["AccountId"]
        partition = stack_outputs["Partition"]
        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        apigw_client = self.client_provider.api_client

        rest_api_response = apigw_client.get_rest_api(restApiId=rest_api_id)
        policy_str = rest_api_response["policy"]

        expected_policy_str = (
            '{\\"Version\\":\\"2012-10-17\\",'
            + '\\"Statement\\":[{'
            + '\\"Effect\\":\\"Allow\\",'
            + '\\"Principal\\":{\\"AWS\\":\\"arn:'
            + partition
            + ":iam::"
            + accountId
            + ':root\\"},'
            + '\\"Action\\":\\"execute-api:Invoke\\",'
            + '\\"Resource\\":\\"arn:'
            + partition
            + ":execute-api:"
            + region
            + ":"
            + accountId
            + ":"
            + rest_api_id
            + '\\/Prod\\/GET\\/get\\"}]}'
        )

        self.assertEqual(policy_str, expected_policy_str)

    @staticmethod
    def compare_two_policies_object(policy_a, policy_b):
        if len(policy_a) != len(policy_b):
            return False

        if policy_a["Version"] != policy_b["Version"]:
            return False

        statement_a = policy_a["Statement"]
        statement_b = policy_b["Statement"]

        if len(statement_a) != len(statement_b):
            return False

        try:
            for item in statement_a:
                statement_b.remove(item)
        except ValueError:
            return False
        return not statement_b
