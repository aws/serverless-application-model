from integration.helpers.base_test import BaseTest


class TestDependsOn(BaseTest):
    def test_depends_on(self):
        self.create_and_verify_stack("combination/function_with_signing_profile")
