from unittest import TestCase
from mock import patch

from samtranslator.public.exceptions import InvalidDocumentException
from samtranslator.public.plugins import BasePlugin
from samtranslator.plugins.globals.globals_plugin import GlobalsPlugin
from samtranslator.plugins.globals.globals import InvalidGlobalsSectionException


class TestGlobalsPlugin(TestCase):
    """
    Unit testing Globals Plugin
    """

    def setUp(self):
        self.plugin = GlobalsPlugin()

    def test_plugin_must_setup_correct_name(self):
        # Name is the class name
        expected_name = "GlobalsPlugin"

        self.assertEqual(self.plugin.name, expected_name)

    def test_plugin_must_be_instance_of_base_plugin_class(self):
        self.assertTrue(isinstance(self.plugin, BasePlugin))

    @patch("samtranslator.plugins.globals.globals_plugin.Globals")
    def test_on_before_transform_template_must_raise_on_invalid_globals_section(self, GlobalsMock):

        id = "id"
        msg = "msg"
        template = {"foo": "bar"}
        globals_ex = InvalidGlobalsSectionException(id, msg)

        GlobalsMock.side_effect = globals_ex

        with self.assertRaises(InvalidDocumentException) as context:
            self.plugin.on_before_transform_template(template)

        ex = context.exception
        self.assertEqual(1, len(ex.causes))
        self.assertEqual(ex.causes[0], globals_ex)

    # Skipping test for the happy case because the end-to-end unit tests capture a lot of the Globals Plugin's logic.
