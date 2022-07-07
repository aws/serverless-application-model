from unittest.case import skipIf

from integration.config.service_names import EFS
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


class TestFunctionWithFileSystemConfig(BaseTest):
    @skipIf(current_region_does_not_support([EFS]), "EFS is not supported in this testing region")
    def test_function_with_efs_integration(self):
        self.create_and_verify_stack("combination/function_with_file_system_config")
