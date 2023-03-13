from unittest import TestCase
from unittest.mock import patch

from parameterized import parameterized
from samtranslator.model.preferences.deployment_preference_collection import DeploymentPreferenceCollection


class TestDeploymentPreferenceCollection(TestCase):
    @parameterized.expand(
        [
            ["aws-iso"],
            ["aws-iso-b"],
        ]
    )
    def test_codedeploy_iam_role_contains_AWSCodeDeployRoleForLambdaLimited_managedpolicy(self, partition):
        with patch(
            "samtranslator.translator.arn_generator.ArnGenerator.get_partition_name"
        ) as get_partition_name_patch:
            get_partition_name_patch.return_value = partition

            iam_role = DeploymentPreferenceCollection().get_codedeploy_iam_role()

            self.assertIn(
                f"arn:{partition}:iam::aws:policy/service-role/AWSCodeDeployRoleForLambdaLimited",
                iam_role.ManagedPolicyArns,
            )

    @parameterized.expand(
        [
            ["aws"],
            ["aws-cn"],
            ["aws-us-gov"],
        ]
    )
    def test_codedeploy_iam_role_contains_AWSCodeDeployRoleForLambda_managedpolicy(self, partition):
        with patch(
            "samtranslator.translator.arn_generator.ArnGenerator.get_partition_name"
        ) as get_partition_name_patch:
            get_partition_name_patch.return_value = partition

            iam_role = DeploymentPreferenceCollection().get_codedeploy_iam_role()

            self.assertIn(
                f"arn:{partition}:iam::aws:policy/service-role/AWSCodeDeployRoleForLambda",
                iam_role.ManagedPolicyArns,
            )
