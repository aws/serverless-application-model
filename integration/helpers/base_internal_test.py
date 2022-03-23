from copy import deepcopy

import pytest

from integration.helpers.base_test import BaseTest


class BaseInternalTest(BaseTest):
    """
    Base class for internal only tests. These tests will skip if --internal flag is not provided
    """

    @pytest.fixture(autouse=True)
    def internal(self, check_internal):
        self.pipeline_internal = check_internal

    @pytest.fixture(autouse=True)
    def template_parameter_values(self, parameter_values):
        self.parameter_values = parameter_values

    @pytest.fixture(autouse=True)
    def skip_if_not_internal(self):
        if not self.pipeline_internal:
            pytest.skip("This test is marked as internal but --internal flag is not provided, skipping...")

    def create_and_verify_stack(self, file_path, parameters=None):
        super().create_and_verify_stack(file_path, self._get_merged_parameters(parameters))

    def _get_test_parameters(self):
        test_name = self.id().split(".")[-1]
        raw_test_parameters = deepcopy(self.parameter_values.get(test_name, {}))

        test_parameters = []
        for parameter_key, parameter_value in raw_test_parameters.items():
            test_parameters.append(
                {
                    "ParameterKey": parameter_key,
                    "ParameterValue": parameter_value,
                    "UsePreviousValue": False,
                    "ResolvedValue": "string",
                }
            )

        return test_parameters

    def _get_merged_parameters(self, parameters):
        if parameters:
            return parameters + self._get_test_parameters()
        return self._get_test_parameters()
