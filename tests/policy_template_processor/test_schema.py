from samtranslator.policy_template_processor.processor import PolicyTemplatesProcessor

from parameterized import parameterized
from unittest import TestCase


class TestTemplates(object):
    """
    Write your test cases here as different variables that store the entire template file. Start the variable with
    "succeed" if you want to test success case, "fail" if you want to test failure cases. The test runner will know
    to test for the right expectations

    Just trying out a BDDish test runner
    """

    succeed_with_no_template = {"Version": "1.2.3", "Templates": {}}

    succeed_with_single_statement = {
        "Version": "1.0.0",
        "Templates": {
            "ManagedPolicy1Policy": {
                "Description": "Very first managed policy",
                "Parameters": {"Param1": {"Description": "some desc"}, "Param2": {"Description": "some desc"}},
                "Definition": {"Statement": [{"key": "value"}]},
            }
        },
    }

    succeed_with_multiple_templates = {
        "Version": "1.0.0",
        "Templates": {
            "ManagedPolicy1Policy": {
                "Description": "Very first managed policy",
                "Parameters": {"Param1": {"Description": "some desc"}, "Param2": {"Description": "some desc"}},
                "Definition": {"Statement": [{"key": "value"}, {"otherkey": "othervalue"}]},
            },
            "ManagedPolicy2Policy": {
                "Description": "Second managed policy",
                "Parameters": {"1stParam": {"Description": "some desc"}},
                "Definition": {"Statement": [{"key": "value"}]},
            },
        },
    }

    fail_for_template_with_no_version = {"Templates": {}}

    fail_without_template = {"Version": "1.2.3"}

    fail_with_non_semantic_version = {"Version": "version1", "Templates": {}}

    fail_without_all_three_parts_of_semver = {
        # Yes! you need all three parts
        "Version": "1.0",
        "Templates": {},
    }

    fail_with_additional_properties = {"Version": "1.2.3", "Templates": {}, "Something": "value"}

    fail_for_bad_template_name = {
        "Version": "1.0.0",
        "Templates": {
            # Names must have the suffix "Policy"
            "ThisNameDoesNotHaveTheSuffix": {"Parameters": {}, "Definition": {"Statement": [{"key": "value"}]}}
        },
    }

    fail_for_template_without_parameters = {
        "Version": "1.0.0",
        "Templates": {"MyTemplate": {"Definition": {"Statement": [{"key": "value"}]}}},
    }

    fail_for_template_without_definition = {"Version": "1.0.0", "Templates": {"MyTemplate": {"Parameters": {}}}}

    fail_for_template_with_empty_definition = {
        "Version": "1.0.0",
        "Templates": {"MyTemplate": {"Parameters": {}, "Definition": {}}},
    }

    fail_for_parameter_with_no_description = {
        "Version": "1.0.0",
        "Templates": {"MyTemplate": {"Parameters": {"Param1": {}}, "Definition": {"Statement": [{"key": "value"}]}}},
    }

    fail_for_parameter_name_with_underscores = {
        "Version": "1.0.0",
        "Templates": {
            "MyTemplate": {
                "Parameters": {
                    # Underscores are not allowed. Following CFN naming convention here
                    "invalid_name": {"Description": "value"}
                },
                "Definition": {"Statement": [{"key": "value"}]},
            }
        },
    }

    fail_for_definition_is_an_array = {
        "Version": "1.0.0",
        "Templates": {
            "MyTemplate": {
                "Parameters": {"Param1": {"Description": "value"}},
                # Definition must be a direct statement object. This is not allowed
                "Definition": [{"Statement": [{"key": "value"}]}],
            }
        },
    }


class TestPolicyTemplateSchema(TestCase):
    """
    Some basic test cases to validate that the JSON Schema representing policy templates actually work as intended
    """

    # Grab all variables of the class TestTemplates
    @parameterized.expand([d for d in dir(TestTemplates) if not d.startswith("__")])
    def test_schema(self, case):

        failure_case = case.startswith("fail")
        template = getattr(TestTemplates, case)

        if failure_case:

            with self.assertRaises(ValueError):
                PolicyTemplatesProcessor._is_valid_templates_dict(template)

        else:
            # Success case
            self.assertTrue(PolicyTemplatesProcessor._is_valid_templates_dict(template))
