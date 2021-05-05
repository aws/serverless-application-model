from integration.helpers.base_test import BaseTest


class TestFunctionWithFileSystemConfig(BaseTest):
    def test_function_with_efs_integration(self):
        self.create_and_verify_stack("combination/function_with_file_system_config")
