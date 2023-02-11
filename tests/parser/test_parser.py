from unittest import TestCase
from unittest.mock import Mock, call, patch

from samtranslator.model.exceptions import InvalidDocumentException
from samtranslator.parser.parser import Parser
from samtranslator.plugins import LifeCycleEvents


class TestParser(TestCase):
    def test_parse(self):
        parser = Parser()
        parser._validate = Mock()
        sam_plugins_mock = Mock()
        sam_plugins_mock.act = Mock()
        sam_template = {}
        parameter_values = {}

        parser.parse(sam_template, parameter_values, sam_plugins_mock)
        parser._validate.assert_has_calls([call(sam_template, parameter_values)])
        sam_plugins_mock.act.assert_has_calls([call(LifeCycleEvents.before_transform_template, sam_template)])

    @patch("samtranslator.parser.parser.SamTemplateValidator")
    @patch("samtranslator.parser.parser.LOG")
    def test_validate_validator_failure(self, log_mock, sam_template_validator_class_mock):
        exception = Exception()
        sam_template_validator_class_mock.side_effect = exception
        log_mock.exception = Mock()

        sam_template = {
            "Resources": {
                "Function": {},
                "Api": {},
            }
        }
        paramerter_values = {"Param": "value"}
        parser = Parser()
        parser._validate(sam_template, paramerter_values)
        log_mock.exception.assert_has_calls([call("Exception from SamTemplateValidator: %s", exception)])

    def test_validate_parameter_values_is_required(self):
        parser = Parser()
        with self.assertRaises(ValueError):
            parser._validate({}, None)

    def test_validate_template_with_no_resource(self):
        parser = Parser()
        with self.assertRaises(InvalidDocumentException):
            parser._validate({}, {})

    def test_validate_template_with_non_dict_resources(self):
        parser = Parser()
        with self.assertRaises(InvalidDocumentException):
            parser._validate({"Resources": "string"}, {})

    def test_validate_template_with_empty_resources(self):
        parser = Parser()
        with self.assertRaises(InvalidDocumentException):
            parser._validate({"Resources": {}}, {})
