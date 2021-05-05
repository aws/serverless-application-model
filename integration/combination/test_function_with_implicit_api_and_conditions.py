from integration.helpers.base_test import BaseTest


class TestFunctionWithImplicitApiAndCondition(BaseTest):
    def test_function_with_implicit_api_and_conditions(self):
        self.create_and_verify_stack("combination/function_with_implicit_api_and_conditions")
