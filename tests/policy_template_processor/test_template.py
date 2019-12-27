from unittest import TestCase
from mock import Mock, patch, ANY

from samtranslator.policy_template_processor.template import Template
from samtranslator.policy_template_processor.exceptions import InvalidParameterValues, InsufficientParameterValues


class TestTemplateObject(TestCase):
    @patch.object(Template, "check_parameters_exist")
    def test_init_must_check_for_existence_of_all_parameters(self, check_parameters_exist_mock):

        template_name = "template_name"
        parameters = {}
        template_definition = {"key": "value"}

        template = Template(template_name, parameters, template_definition)

        self.assertEqual(template.name, template_name)
        self.assertEqual(template.parameters, parameters)
        self.assertEqual(template.definition, template_definition)
        check_parameters_exist_mock.assert_called_once_with(parameters, template_definition)

    @patch.object(Template, "check_parameters_exist")
    def test_from_dict_must_return_object(self, check_parameters_exist_mock):
        template_name = "template_name"
        parameters = {"A": "B"}
        template_definition = {"key": "value"}

        template_dict = {"Parameters": parameters, "Definition": template_definition}

        template = Template.from_dict(template_name, template_dict)

        self.assertTrue(isinstance(template, Template))
        self.assertEqual(template.name, template_name)
        self.assertEqual(template.parameters, parameters)
        self.assertEqual(template.definition, template_definition)

    @patch.object(Template, "check_parameters_exist")
    def test_from_dict_must_work_when_parameters_is_absent(self, check_parameters_exist_mock):
        template_name = "template_name"
        template_definition = {"key": "value"}

        template_dict = {"Definition": template_definition}

        template = Template.from_dict(template_name, template_dict)

        self.assertEqual(template.parameters, {})  # Defaults to {}
        self.assertEqual(template.definition, template_definition)

    @patch.object(Template, "check_parameters_exist")
    def test_from_dict_must_work_when_template_definition_is_absent(self, check_parameters_exist_mock):
        template_name = "template_name"
        parameters = {"key": "value"}

        template_dict = {"Parameters": parameters}

        template = Template.from_dict(template_name, template_dict)

        self.assertEqual(template.parameters, parameters)
        self.assertEqual(template.definition, {})  # Defaults to {}

    def test_missing_parameter_values_must_work_when_input_has_less_keys(self):
        template_parameters = {"param1": {"Description": "foo"}, "param2": {"Description": "bar"}}
        parameter_values = {"param1": "value1"}
        expected = ["param2"]

        template = Template("name", template_parameters, {})
        result = template.missing_parameter_values(parameter_values)

        self.assertEqual(expected, result)

    def test_missing_parameter_values_must_work_when_input_has_all_keys(self):
        template_parameters = {"param1": {"Description": "foo"}, "param2": {"Description": "bar"}}
        parameter_values = {"param1": "value1", "param2": "value3"}
        expected = []

        template = Template("name", template_parameters, {})
        result = template.missing_parameter_values(parameter_values)

        self.assertEqual(expected, result)

    def test_missing_parameter_values_must_work_when_input_has_more_keys(self):
        template_parameters = {"param1": {"Description": "foo"}, "param2": {"Description": "bar"}}
        parameter_values = {"param1": "value1", "param2": "value2", "newparam": "new value"}
        expected = []  # We do a set-difference. So new keys won't make it here

        template = Template("name", template_parameters, {})
        result = template.missing_parameter_values(parameter_values)

        self.assertEqual(expected, result)

    def test_missing_parameter_values_must_raise_on_invalid_input(self):
        template_parameters = {"param1": {"Description": "foo"}, "param2": {"Description": "bar"}}
        parameter_values = [1, 2, 3]

        template = Template("name", template_parameters, {})

        with self.assertRaises(InvalidParameterValues):
            template.missing_parameter_values(parameter_values)

    def test_is_valid_parameter_values_must_work(self):

        parameter_values = {"a": "b"}
        self.assertTrue(Template._is_valid_parameter_values(parameter_values))

    def test_is_valid_parameter_values_must_fail_for_none_value(self):

        parameter_values = None
        self.assertFalse(Template._is_valid_parameter_values(parameter_values))

    def test_is_valid_parameter_values_must_fail_for_non_dict(self):

        parameter_values = [1, 2, 3]
        self.assertFalse(Template._is_valid_parameter_values(parameter_values))

    @patch("samtranslator.policy_template_processor.template.IntrinsicsResolver")
    def test_to_statement_must_work_with_valid_inputs(self, intrinsics_resolver_mock):
        parameter_values = {"param1": "b"}
        template_parameters = {"param1": {"Description": "something"}}
        template_definition = {"Statement": {"key": "value"}}
        expected = "some result"

        resolver_instance_mock = Mock()
        intrinsics_resolver_mock.return_value = resolver_instance_mock
        resolver_instance_mock.resolve_parameter_refs.return_value = expected

        template = Template("name", template_parameters, template_definition)
        result = template.to_statement(parameter_values)

        self.assertEqual(expected, result)
        intrinsics_resolver_mock.assert_called_once_with(parameter_values, {"Ref": ANY})
        resolver_instance_mock.resolve_parameter_refs.assert_called_once_with({"Statement": {"key": "value"}})

    @patch("samtranslator.policy_template_processor.template.IntrinsicsResolver")
    def test_to_statement_must_exclude_extra_parameter_values(self, intrinsics_resolver_mock):
        parameter_values = {"param1": "b", "key1": "value1", "key2": "value2"}
        template_parameters = {"param1": {"Description": "something"}}
        template_definition = {"Statement": {"key": "value"}}

        resolver_instance_mock = Mock()
        intrinsics_resolver_mock.return_value = resolver_instance_mock
        resolver_instance_mock.resolve_parameter_refs.return_value = "some result"

        template = Template("name", template_parameters, template_definition)
        template.to_statement(parameter_values)

        # Intrinsics resolver must be called only with the parameters declared in the template
        expected_parameter_values = {"param1": "b"}
        intrinsics_resolver_mock.assert_called_once_with(expected_parameter_values, ANY)

    @patch("samtranslator.policy_template_processor.template.IntrinsicsResolver")
    def test_to_statement_must_raise_with_missing_parameters(self, intrinsics_resolver_mock):
        parameter_values = {"key1": "value1", "key2": "value2"}
        template_parameters = {"param1": {"Description": "something"}}
        template_definition = {"Statement": {"key": "value"}}

        template = Template("name", template_parameters, template_definition)
        with self.assertRaises(InsufficientParameterValues):
            template.to_statement(parameter_values)

    @patch("samtranslator.policy_template_processor.template.IntrinsicsResolver")
    def test_to_statement_must_fail_for_invalid_parameter_values(self, intrinsics_resolver_mock):
        parameter_values = None

        template = Template("name", {}, {})

        with self.assertRaises(InvalidParameterValues):
            template.to_statement(parameter_values)
