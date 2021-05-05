from integration.helpers.base_test import BaseTest


class TestDependsOn(BaseTest):
    def test_depends_on(self):
        # Stack template is setup such that it will fail stack creation if DependsOn doesn't work.
        # Simply creating the stack is enough verification
        self.create_and_verify_stack("combination/depends_on")
