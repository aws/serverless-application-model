from unittest import TestCase
from unittest.mock import Mock, patch

from parameterized import parameterized
from samtranslator.model import InvalidResourceException
from samtranslator.model.api.api_generator import ApiGenerator


class TestApiGenerator(TestCase):
    @parameterized.expand([("this should be a dict",), ("123",), ([{}],)])
    @patch("samtranslator.model.api.api_generator.AuthProperties")
    def test_construct_usage_plan_with_invalid_usage_plan_type(self, invalid_usage_plan, AuthProperties_mock):
        AuthProperties_mock.return_value = Mock(UsagePlan=invalid_usage_plan)
        api_generator = ApiGenerator(
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            auth={"some": "value"},
        )
        with self.assertRaises(InvalidResourceException) as cm:
            api_generator._construct_usage_plan()
            self.assertIn("Invalid type", str(cm.exception))

    @patch("samtranslator.model.api.api_generator.AuthProperties")
    def test_construct_usage_plan_with_invalid_usage_plan_fields(self, AuthProperties_mock):
        AuthProperties_mock.return_value = Mock(UsagePlan={"Unknown_field": "123"})
        api_generator = ApiGenerator(
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            auth={"some": "value"},
        )
        with self.assertRaises(InvalidResourceException) as cm:
            api_generator._construct_usage_plan()
            self.assertIn("Invalid property for", str(cm.exception))
