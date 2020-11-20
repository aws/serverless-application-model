from parameterized import parameterized
from tests_integ.helpers.base_test import BaseTest


class TestBasicLayerVersion(BaseTest):
    def test_basic_state_machine_inline_definition(self):
        self.create_and_verify_stack("basic_state_machine_inline_definition")

    def test_basic_state_machine_with_tags(self):
        self.create_and_verify_stack("basic_state_machine_with_tags")

        tags = self.get_stack_tags("MyStateMachineArn")

        self.assertIsNotNone(tags)
        self._verify_tag_presence(tags, "stateMachine:createdBy", "SAM")
        self._verify_tag_presence(tags, "TagOne", "ValueOne")
        self._verify_tag_presence(tags, "TagTwo", "ValueTwo")

    def _verify_tag_presence(self, tags, key, value):
        tag = next(tag for tag in tags if tag["key"] == key)
        self.assertIsNotNone(tag)
        self.assertEqual(tag["value"], value)
