from parameterized import parameterized, param

import pytest
from unittest import TestCase
from samtranslator.sdk.parameter import SamParameterValues
from mock import patch


class TestSAMParameterValues(TestCase):
    def test_add_default_parameter_values_must_merge(self):
        parameter_values = {"Param1": "value1"}

        sam_template = {"Parameters": {"Param2": {"Type": "String", "Default": "template default"}}}

        expected = {"Param1": "value1", "Param2": "template default"}

        sam_parameter_values = SamParameterValues(parameter_values)
        sam_parameter_values.add_default_parameter_values(sam_template)
        self.assertEqual(expected, sam_parameter_values.parameter_values)

    def test_add_default_parameter_values_must_override_user_specified_values(self):
        parameter_values = {"Param1": "value1"}

        sam_template = {"Parameters": {"Param1": {"Type": "String", "Default": "template default"}}}

        expected = {"Param1": "value1"}

        sam_parameter_values = SamParameterValues(parameter_values)
        sam_parameter_values.add_default_parameter_values(sam_template)
        self.assertEqual(expected, sam_parameter_values.parameter_values)

    def test_add_default_parameter_values_must_skip_params_without_defaults(self):
        parameter_values = {"Param1": "value1"}

        sam_template = {"Parameters": {"Param1": {"Type": "String"}, "Param2": {"Type": "String"}}}

        expected = {"Param1": "value1"}

        sam_parameter_values = SamParameterValues(parameter_values)
        sam_parameter_values.add_default_parameter_values(sam_template)
        self.assertEqual(expected, sam_parameter_values.parameter_values)

    @parameterized.expand(
        [
            # Array
            param(["1", "2"]),
            # String
            param("something"),
            # Some other non-parameter looking dictionary
            param({"Param1": {"Foo": "Bar"}}),
            param(None),
        ]
    )
    def test_add_default_parameter_values_must_ignore_invalid_template_parameters(self, template_parameters):
        parameter_values = {"Param1": "value1"}

        expected = {"Param1": "value1"}

        sam_template = {"Parameters": template_parameters}

        sam_parameter_values = SamParameterValues(parameter_values)
        sam_parameter_values.add_default_parameter_values(sam_template)
        self.assertEqual(expected, sam_parameter_values.parameter_values)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_add_pseudo_parameter_values_aws_region(self):
        parameter_values = {"Param1": "value1"}

        expected = {"Param1": "value1", "AWS::Region": "ap-southeast-1", "AWS::Partition": "aws"}

        sam_parameter_values = SamParameterValues(parameter_values)
        sam_parameter_values.add_pseudo_parameter_values()
        self.assertEqual(expected, sam_parameter_values.parameter_values)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_add_pseudo_parameter_values_aws_region_not_override(self):
        parameter_values = {"AWS::Region": "value1"}

        expected = {"AWS::Region": "value1", "AWS::Partition": "aws"}

        sam_parameter_values = SamParameterValues(parameter_values)
        sam_parameter_values.add_pseudo_parameter_values()
        self.assertEqual(expected, sam_parameter_values.parameter_values)

    @patch("boto3.session.Session.region_name", "us-gov-west-1")
    def test_add_pseudo_parameter_values_aws_partition(self):
        parameter_values = {"Param1": "value1"}

        expected = {"Param1": "value1", "AWS::Region": "us-gov-west-1", "AWS::Partition": "aws-us-gov"}

        sam_parameter_values = SamParameterValues(parameter_values)
        sam_parameter_values.add_pseudo_parameter_values()
        self.assertEqual(expected, sam_parameter_values.parameter_values)

    @patch("boto3.session.Session.region_name", "us-gov-west-1")
    def test_add_pseudo_parameter_values_aws_partition_not_override(self):
        parameter_values = {"AWS::Partition": "aws"}

        expected = {"AWS::Partition": "aws", "AWS::Region": "us-gov-west-1"}

        sam_parameter_values = SamParameterValues(parameter_values)
        sam_parameter_values.add_pseudo_parameter_values()
        self.assertEqual(expected, sam_parameter_values.parameter_values)
