from unittest import TestCase

from parameterized import parameterized
from samtranslator.model.api.api_generator import SharedApiUsagePlan
from samtranslator.model.exceptions import InvalidTemplateException


class TestSharedApiUsagePlan(TestCase):
    def setUp(self):
        self.shared_usage_plan = SharedApiUsagePlan()

    def test_values_should_be_propagated(self):
        conditions = {}
        actual_attributes = self.shared_usage_plan.get_combined_resource_attributes(
            {
                "Condition": "C1",
                "DeletionPolicy": "Delete",
                "UpdateReplacePolicy": "Delete",
            },
            conditions,
        )

        self.assertEqual(
            {
                "Condition": SharedApiUsagePlan.SHARED_USAGE_PLAN_CONDITION_NAME,
                "DeletionPolicy": "Delete",
                "UpdateReplacePolicy": "Delete",
            },
            actual_attributes,
        )

        self.assertEqual(conditions, {"SharedUsagePlanCondition": "C1"})

    @parameterized.expand(
        [
            ([None],),
            ([None, "C1"],),
            (["C1", None],),
            (["C1", "C2"],),
            (["C1", "C2", "C3"],),
        ]
    )
    def test_multiple_apis_with_conditions(self, api_conditions):
        template_conditions = dict()
        result = {}
        for api_condition in api_conditions:
            result = self.shared_usage_plan.get_combined_resource_attributes(
                {"Condition": api_condition}, template_conditions
            )
            print(f"Calling with {api_condition} result {result}")

        if None in api_conditions:
            self.assertEqual({}, result)
            self.assertEqual({}, template_conditions)
        else:
            print(template_conditions)
            self.assertTrue("SharedUsagePlanCondition" in template_conditions)
            self.assertEqual({"Condition": "SharedUsagePlanCondition"}, result)
            combined_conditions = [
                condition.get("Condition")
                for condition in template_conditions.get("SharedUsagePlanCondition", {}).get("Fn::Or")
            ]
            for combined_condition in combined_conditions:
                self.assertTrue(combined_condition in api_conditions)

    def test_should_raise_invalid_template_when_no_conditions_section(self):
        with self.assertRaises(InvalidTemplateException):
            self.shared_usage_plan.get_combined_resource_attributes({"Condition": "C1"}, None)

    def test_deletion_policy_priority(self):
        # first api sets it to delete
        actual_attributes = self.shared_usage_plan.get_combined_resource_attributes({"DeletionPolicy": "Delete"}, {})
        self.assertEqual(actual_attributes["DeletionPolicy"], "Delete")

        # then second api sets it to Retain
        actual_attributes = self.shared_usage_plan.get_combined_resource_attributes({"DeletionPolicy": "Retain"}, {})
        self.assertEqual(actual_attributes["DeletionPolicy"], "Retain")

        # if third api sets it to delete, it should keep retain value
        actual_attributes = self.shared_usage_plan.get_combined_resource_attributes({"DeletionPolicy": "Delete"}, {})
        self.assertEqual(actual_attributes["DeletionPolicy"], "Retain")

    def test_update_replace_policy_priority(self):
        # first api sets it to delete
        actual_attributes = self.shared_usage_plan.get_combined_resource_attributes(
            {"UpdateReplacePolicy": "Delete"}, {}
        )
        self.assertEqual(actual_attributes["UpdateReplacePolicy"], "Delete")

        # then second api sets it to Retain
        actual_attributes = self.shared_usage_plan.get_combined_resource_attributes(
            {"UpdateReplacePolicy": "Snapshot"}, {}
        )
        self.assertEqual(actual_attributes["UpdateReplacePolicy"], "Snapshot")

        # if third api sets it to delete, it should keep retain value
        actual_attributes = self.shared_usage_plan.get_combined_resource_attributes(
            {"UpdateReplacePolicy": "Delete"}, {}
        )
        self.assertEqual(actual_attributes["UpdateReplacePolicy"], "Snapshot")

        # if third api sets it to delete, it should keep retain value
        actual_attributes = self.shared_usage_plan.get_combined_resource_attributes(
            {"UpdateReplacePolicy": "Retain"}, {}
        )
        self.assertEqual(actual_attributes["UpdateReplacePolicy"], "Retain")

        # if third api sets it to delete, it should keep retain value
        actual_attributes = self.shared_usage_plan.get_combined_resource_attributes(
            {"UpdateReplacePolicy": "Snapshot"}, {}
        )
        self.assertEqual(actual_attributes["UpdateReplacePolicy"], "Retain")

        # if third api sets it to delete, it should keep retain value
        actual_attributes = self.shared_usage_plan.get_combined_resource_attributes(
            {"UpdateReplacePolicy": "Delete"}, {}
        )
        self.assertEqual(actual_attributes["UpdateReplacePolicy"], "Retain")
