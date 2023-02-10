from unittest.case import skipIf

from integration.config.service_names import COGNITO
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([COGNITO]), "Cognito is not supported in this testing region")
class TestFunctionWithUserPoolEvent(BaseTest):
    def test_function_with_user_pool_event(self):
        self.create_and_verify_stack("combination/function_with_userpool_event")
        lambda_resources = self.get_stack_resources("AWS::Lambda::Permission")
        my_function_cognito_permission = next(
            (x for x in lambda_resources if x["LogicalResourceId"] == "PreSignupLambdaFunctionCognitoPermission"), None
        )
        self.assertIsNotNone(my_function_cognito_permission)
