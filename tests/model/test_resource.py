from unittest import TestCase

from samtranslator.model import Property, SamResourceMacro
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.types import IS_STR


class DummyResourceWithValidation(SamResourceMacro):
    # validate_setattr is set to True in Resource class by default
    resource_type = "AWS::Serverless:DummyResource"
    property_types = {"SomeProperty": Property(False, IS_STR), "AnotherProperty": Property(False, IS_STR)}

    def to_cloudformation(self, **kwargs):
        return []


class DummyResourceNoValidation(SamResourceMacro):
    resource_type = "AWS::Serverless:DummyResource"
    property_types = {"SomeProperty": Property(False, IS_STR), "AnotherProperty": Property(False, IS_STR)}

    validate_setattr = False

    def to_cloudformation(self, **kwargs):
        return []


class TestResource(TestCase):
    def test_create_instance_variable_when_validate_setattr_is_true(self):
        resource = DummyResourceWithValidation("foo")
        with self.assertRaises(InvalidResourceException):
            resource.SomeExtraValue = "foo"

    def test_create_instance_variable_when_validate_setattr_is_false(self):
        resource = DummyResourceNoValidation("foo")

        resource.SomeExtraValue = "foo"
        resource.AnotherValue = "bar"
        resource.RandomValue = "baz"
