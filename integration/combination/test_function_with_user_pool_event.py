from integration.helpers.base_test import BaseTest


class TestFunctionWithUserPoolEvent(BaseTest):
    def test_function_with_user_pool_event(self):
        self.create_and_verify_stack("combination/function_with_userpool_event")
        lambda_resources = self.get_stack_resources("AWS::Lambda::Permission")
        my_function_cognito_permission = next(
            (x for x in lambda_resources if x["LogicalResourceId"] == "PreSignupLambdaFunctionCognitoPermission"), None
        )
        self.assertIsNotNone(my_function_cognito_permission)
