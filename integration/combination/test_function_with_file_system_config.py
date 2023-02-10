from unittest.case import skipIf

import pytest

from integration.config.service_names import EFS
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


class TestFunctionWithFileSystemConfig(BaseTest):
    @pytest.fixture(autouse=True)
    def companion_stack_outputs(self, get_companion_stack_outputs):
        self.companion_stack_outputs = get_companion_stack_outputs

    @skipIf(current_region_does_not_support([EFS]), "EFS is not supported in this testing region")
    def test_function_with_efs_integration(self):
        parameters = self.get_parameters(self.companion_stack_outputs)
        self.create_and_verify_stack("combination/function_with_file_system_config", parameters)

    def get_parameters(self, dictionary):
        parameters = []
        parameters.append(self.generate_parameter("PreCreatedSubnetOne", dictionary["PreCreatedSubnetOne"]))
        parameters.append(self.generate_parameter("PreCreatedVpc", dictionary["PreCreatedVpc"]))
        return parameters
