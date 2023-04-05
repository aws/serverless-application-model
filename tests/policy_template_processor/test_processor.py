import json
from unittest import TestCase
from unittest.mock import Mock, mock_open, patch

import jsonschema
from jsonschema.exceptions import ValidationError
from samtranslator.policy_template_processor.exceptions import TemplateNotFoundException
from samtranslator.policy_template_processor.processor import PolicyTemplatesProcessor
from samtranslator.policy_template_processor.template import Template


class TestPolicyTemplateProcessor(TestCase):
    @patch.object(PolicyTemplatesProcessor, "_is_valid_templates_dict")
    def test_init_must_validate_against_default_schema(self, is_valid_templates_dict_mock):
        policy_templates_dict = {"Templates": {}}

        is_valid_templates_dict_mock.return_value = True

        PolicyTemplatesProcessor(policy_templates_dict)
        is_valid_templates_dict_mock.assert_called_once_with(policy_templates_dict, None)

    @patch.object(PolicyTemplatesProcessor, "_is_valid_templates_dict")
    def test_init_must_validate_against_input_schema(self, is_valid_templates_dict_mock):
        policy_templates_dict = {"Templates": {}}
        schema = "something"

        is_valid_templates_dict_mock.return_value = True

        PolicyTemplatesProcessor(policy_templates_dict, schema)
        is_valid_templates_dict_mock.assert_called_once_with(policy_templates_dict, schema)

    @patch.object(PolicyTemplatesProcessor, "_is_valid_templates_dict")
    def test_init_must_raise_on_invalid_template(self, is_valid_templates_dict_mock):
        policy_templates_dict = {"Templates": {}}
        is_valid_templates_dict_mock.side_effect = ValueError()

        with self.assertRaises(ValueError):
            PolicyTemplatesProcessor(policy_templates_dict)

    @patch.object(PolicyTemplatesProcessor, "_is_valid_templates_dict")
    @patch.object(Template, "from_dict")
    def test_init_must_convert_template_value_dict_to_object(
        self, template_from_dict_mock, is_valid_templates_dict_mock
    ):
        policy_templates_dict = {"Templates": {"key1": "value1", "key2": "value2"}}

        is_valid_templates_dict_mock.return_value = True
        template_from_dict_mock.return_value = "Something"

        processor = PolicyTemplatesProcessor(policy_templates_dict)

        self.assertEqual(2, len(processor.policy_templates))
        self.assertEqual(set(["key1", "key2"]), set(processor.policy_templates.keys()))

        # Template.from_dict must be called only once for each template entry
        self.assertEqual(2, template_from_dict_mock.call_count)
        template_from_dict_mock.assert_any_call("key1", "value1")
        template_from_dict_mock.assert_any_call("key2", "value2")

    @patch.object(PolicyTemplatesProcessor, "_is_valid_templates_dict")
    @patch.object(Template, "from_dict")
    def test_has_method_must_work_for_known_template_names(self, template_from_dict_mock, is_valid_templates_dict_mock):
        policy_templates_dict = {"Templates": {"key1": "value1", "key2": "value2"}}

        processor = PolicyTemplatesProcessor(policy_templates_dict)

        self.assertTrue(processor.has("key1"))
        self.assertTrue(processor.has("key2"))

    @patch.object(PolicyTemplatesProcessor, "_is_valid_templates_dict")
    @patch.object(Template, "from_dict")
    def test_has_method_must_work_for_not_known_template_names(self, template_from_dict_mock, is_valid_templates_dict):
        policy_templates_dict = {"Templates": {"key1": "value1", "key2": "value2"}}

        processor = PolicyTemplatesProcessor(policy_templates_dict)

        self.assertFalse(processor.has("someotherkey"))

    @patch.object(PolicyTemplatesProcessor, "_is_valid_templates_dict")
    @patch.object(Template, "from_dict")
    def test_get_method_must_return_template_object_for_known_template_names(
        self, template_from_dict_mock, is_valid_templates_dict
    ):
        policy_templates_dict = {"Templates": {"key1": "value1"}}

        template_obj = "some value"
        template_from_dict_mock.return_value = template_obj

        processor = PolicyTemplatesProcessor(policy_templates_dict)

        self.assertEqual(processor.get("key1"), template_obj)

    @patch.object(PolicyTemplatesProcessor, "_is_valid_templates_dict")
    @patch.object(Template, "from_dict")
    def test_get_method_must_return_none_for_unknown_template_names(
        self, template_from_dict_mock, is_valid_templates_dict
    ):
        policy_templates_dict = {"Templates": {"key1": "value1"}}

        template_obj = "some value"
        template_from_dict_mock.return_value = template_obj

        processor = PolicyTemplatesProcessor(policy_templates_dict)

        self.assertEqual(processor.get("key2"), None)

    @patch.object(PolicyTemplatesProcessor, "_is_valid_templates_dict")
    @patch.object(Template, "from_dict")
    def test_convert_must_work_for_known_template_names(self, template_from_dict_mock, is_valid_templates_dict):
        policy_templates_dict = {"Templates": {"key1": "value1"}}
        parameter_values = {"a": "b"}

        template_obj_mock = Mock()
        template_from_dict_mock.return_value = template_obj_mock

        expected = {"stmt": "result"}
        template_obj_mock.to_statement.return_value = expected

        processor = PolicyTemplatesProcessor(policy_templates_dict)
        result = processor.convert("key1", parameter_values)

        self.assertEqual(result, expected)
        template_obj_mock.to_statement.assert_called_once_with(parameter_values)

    @patch.object(PolicyTemplatesProcessor, "_is_valid_templates_dict")
    @patch.object(Template, "from_dict")
    def test_convert_must_raise_if_template_name_not_found(self, template_from_dict_mock, is_valid_templates_dict):
        policy_templates_dict = {"Templates": {"key1": "value1"}}
        parameter_values = {"a": "b"}

        processor = PolicyTemplatesProcessor(policy_templates_dict)

        with self.assertRaises(TemplateNotFoundException):
            processor.convert("key2", parameter_values)

    @patch.object(PolicyTemplatesProcessor, "_is_valid_templates_dict")
    @patch.object(Template, "from_dict")
    def test_convert_must_bubble_exceptions(self, template_from_dict_mock, is_valid_templates_dict):
        policy_templates_dict = {"Templates": {"key1": "value1"}}
        parameter_values = {"a": "b"}

        template_obj_mock = Mock()
        template_from_dict_mock.return_value = template_obj_mock

        template_obj_mock.to_statement.side_effect = TypeError

        processor = PolicyTemplatesProcessor(policy_templates_dict)

        with self.assertRaises(TypeError):
            processor.convert("key1", parameter_values)

    @patch.object(jsonschema, "validate")
    @patch.object(PolicyTemplatesProcessor, "_read_schema")
    def test_is_valid_templates_dict_must_use_default_schema(self, read_schema_mock, jsonschema_validate_mock):
        policy_templates_dict = {"key": "value"}

        schema = "some schema"
        read_schema_mock.return_value = schema
        jsonschema_validate_mock.return_value = True

        result = PolicyTemplatesProcessor._is_valid_templates_dict(policy_templates_dict)
        self.assertTrue(result)

        jsonschema_validate_mock.assert_called_once_with(policy_templates_dict, schema)
        read_schema_mock.assert_called_once_with()

    @patch.object(jsonschema, "validate")
    @patch.object(PolicyTemplatesProcessor, "_read_schema")
    def test_is_valid_templates_dict_must_use_input_schema(self, read_schema_mock, jsonschema_validate_mock):
        policy_templates_dict = {"key": "value"}

        schema = "some schema"
        jsonschema_validate_mock.return_value = True

        result = PolicyTemplatesProcessor._is_valid_templates_dict(policy_templates_dict, schema)
        self.assertTrue(result)

        jsonschema_validate_mock.assert_called_once_with(policy_templates_dict, schema)
        read_schema_mock.assert_not_called()  # must not read schema if one is given

    @patch.object(jsonschema, "validate")
    @patch.object(PolicyTemplatesProcessor, "_read_schema")
    def test_is_valid_templates_dict_must_raise_for_invalid_input(self, read_schema_mock, jsonschema_validate_mock):
        policy_templates_dict = {"key": "value"}

        schema = "some schema"
        exception_msg = "exception"

        read_schema_mock.return_value = schema
        jsonschema_validate_mock.side_effect = ValidationError(exception_msg)

        with self.assertRaises(ValueError) as cm:
            PolicyTemplatesProcessor._is_valid_templates_dict(policy_templates_dict)

        ex = cm.exception
        self.assertEqual(str(ex), exception_msg)

    @patch.object(jsonschema, "validate")
    @patch.object(PolicyTemplatesProcessor, "_read_schema")
    def test_is_valid_templates_dict_must_bubble_unhandled_exceptions(self, read_schema_mock, jsonschema_validate_mock):
        policy_templates_dict = {"key": "value"}

        schema = "some schema"
        exception_msg = "exception"

        read_schema_mock.return_value = schema
        jsonschema_validate_mock.side_effect = TypeError(exception_msg)

        with self.assertRaises(TypeError):
            PolicyTemplatesProcessor._is_valid_templates_dict(policy_templates_dict)

    @patch.object(json, "loads")
    def test_read_json_must_read_from_file(self, json_loads_mock):
        filepath = Mock()

        json_return = "something"
        json_loads_mock.return_value = json_return

        open_mock = filepath.open = mock_open()
        result = PolicyTemplatesProcessor._read_json(filepath)
        self.assertEqual(result, json_return)

        open_mock.assert_called_once_with(encoding="utf-8")
        self.assertEqual(1, json_loads_mock.call_count)

    @patch.object(PolicyTemplatesProcessor, "_read_json")
    def test_read_schema_must_use_default_schema_location(self, _read_file_mock):
        expected = "something"
        _read_file_mock.return_value = expected

        result = PolicyTemplatesProcessor._read_schema()
        self.assertEqual(result, expected)
        _read_file_mock.assert_called_once_with(PolicyTemplatesProcessor.SCHEMA_LOCATION)

    @patch.object(PolicyTemplatesProcessor, "_read_json")
    def test_get_default_policy_template_json_must_work(self, _read_file_mock):
        expected = "something"
        _read_file_mock.return_value = expected

        result = PolicyTemplatesProcessor.get_default_policy_templates_json()
        self.assertEqual(result, expected)
        _read_file_mock.assert_called_once_with(PolicyTemplatesProcessor.DEFAULT_POLICY_TEMPLATES_FILE)
