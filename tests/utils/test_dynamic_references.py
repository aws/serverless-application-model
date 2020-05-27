from parameterized import parameterized
from unittest import TestCase

from samtranslator.utils.cfn_dynamic_references import is_dynamic_reference


class TestDynamicReferences(TestCase):
    valid_dynamic_references = [
        "{{resolve:ssm:S3AccessControl:2}}",
        "{{resolve:ssm-secure:IAMUserPassword:10}}",
        "{{resolve:secretsmanager:MyRDSSecret:SecretString:password}}",
        "{{resolve:secretsmanager:MyRDSSecret:SecretString}}",
    ]

    @parameterized.expand(valid_dynamic_references)
    def test_is_dynamic_reference_must_detect_dynamic_reference(self, dynamic_reference):
        self.assertTrue(is_dynamic_reference(dynamic_reference))

    invalid_dynamic_references = [
        "{{resolve}}",
        "{{resolve::}}",
        "{{invalid:ssm:S3AccessControl:2}}",
        "{{invalid:ssm:S3AccessControl}}",
    ]

    @parameterized.expand(invalid_dynamic_references)
    def test_is_intrinsic_on_invalid_input(self, invalid_dynamic_reference):
        self.assertFalse(is_dynamic_reference(invalid_dynamic_reference))
