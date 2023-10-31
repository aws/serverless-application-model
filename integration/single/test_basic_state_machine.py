from unittest.case import skipIf

from integration.config.service_names import STATE_MACHINE_INLINE_DEFINITION, XRAY
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


class TestBasicLayerVersion(BaseTest):
    """
    Basic AWS::Serverless::StateMachine tests
    """

    @skipIf(
        current_region_does_not_support([STATE_MACHINE_INLINE_DEFINITION]),
        "StateMachine with inline definition is not supported in this testing region",
    )
    def test_basic_state_machine_inline_definition(self):
        """
        Creates a State Machine from inline definition
        """
        self.create_and_verify_stack("single/basic_state_machine_inline_definition")

    @skipIf(current_region_does_not_support([XRAY]), "XRay is not supported in this testing region")
    def test_basic_state_machine_with_tags(self):
        """
        Creates a State Machine with tags
        """
        self.create_and_verify_stack("single/basic_state_machine_with_tags")

        tags = self.get_stack_tags("MyStateMachineArn")

        self.assertIsNotNone(tags)
        self._verify_tag_presence(tags, "stateMachine:createdBy", "SAM")
        self._verify_tag_presence(tags, "TagOne", "ValueOne")
        self._verify_tag_presence(tags, "TagTwo", "ValueTwo")

    @skipIf(
        current_region_does_not_support([STATE_MACHINE_INLINE_DEFINITION]),
        "StateMachine with inline definition is not supported in this testing region",
    )
    def test_state_machine_with_role_path(self):
        """
        Creates a State machine with a Role Path
        """
        self.create_and_verify_stack("single/state_machine_with_role_path")

        role_name = self.get_physical_id_by_type("AWS::IAM::Role")
        iam_client = self.client_provider.iam_client
        response = iam_client.get_role(RoleName=role_name)

        self.assertEqual(response["Role"]["Path"], "/foo/bar/")

    def _verify_tag_presence(self, tags, key, value):
        """
        Verifies the presence of a tag and its value

        Parameters
        ----------
        tags : List of dict
            List of tag objects
        key : string
            Tag key
        value : string
            Tag value
        """
        tag = next(tag for tag in tags if tag["key"] == key)
        self.assertIsNotNone(tag)
        self.assertEqual(tag["value"], value)
