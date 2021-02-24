from mock import Mock, patch
from unittest import TestCase

from samtranslator.plugins.api.default_definition_body_plugin import DefaultDefinitionBodyPlugin
from samtranslator.public.plugins import BasePlugin

IMPLICIT_API_LOGICAL_ID = "ServerlessRestApi"


class TestDefaultDefinitionBodyPlugin_init(TestCase):
    def setUp(self):
        self.plugin = DefaultDefinitionBodyPlugin()

    def test_plugin_must_setup_correct_name(self):
        # Name is the class name
        expected_name = "DefaultDefinitionBodyPlugin"

        self.assertEqual(self.plugin.name, expected_name)

    def test_plugin_must_be_instance_of_base_plugin_class(self):
        self.assertTrue(isinstance(self.plugin, BasePlugin))


class TestDefaultDefinitionBodyPlugin_on_before_transform_template(TestCase):
    def setUp(self):
        self.plugin = DefaultDefinitionBodyPlugin()

    @patch("samtranslator.plugins.api.default_definition_body_plugin.SamTemplate")
    def test_must_process_functions(self, SamTemplateMock):

        template_dict = {"a": "b"}
        api_resources = [("id1", ApiResource()), ("id2", ApiResource()), ("id3", ApiResource())]

        sam_template = Mock()
        SamTemplateMock.return_value = sam_template
        sam_template.iterate = Mock()
        sam_template.iterate.return_value = api_resources

        self.plugin.on_before_transform_template(template_dict)

        SamTemplateMock.assert_called_with(template_dict)

        # Make sure this is called only for Apis
        sam_template.iterate.assert_any_call({"AWS::Serverless::Api"})
        sam_template.iterate.assert_any_call({"AWS::Serverless::HttpApi"})


class ApiResource(object):
    def __init__(self):
        self.properties = {}
