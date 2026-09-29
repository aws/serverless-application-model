from unittest import TestCase

from samtranslator.model.apigateway import ApiGatewayUsagePlan
from samtranslator.model.iam import IAMRole
from samtranslator.translator.verify_logical_id import GeneratedLogicalIdTracker


class TestGeneratedLogicalIdTracker(TestCase):
    def test_returns_conflicting_source_for_role_generated_by_different_resource(self):
        tracker = GeneratedLogicalIdTracker()

        self.assertIsNone(tracker.record(IAMRole("NetOperatorRole"), "NetOperator"))
        self.assertEqual(tracker.record(IAMRole("NetOperatorRole"), "Net"), "NetOperator")

    def test_allows_same_resource_to_generate_role_again(self):
        tracker = GeneratedLogicalIdTracker()

        self.assertIsNone(tracker.record(IAMRole("MyFunctionRole"), "MyFunction"))
        self.assertIsNone(tracker.record(IAMRole("MyFunctionRole"), "MyFunction"))

    def test_keeps_first_source_after_conflict(self):
        tracker = GeneratedLogicalIdTracker()

        tracker.record(IAMRole("NetOperatorRole"), "NetOperator")
        tracker.record(IAMRole("NetOperatorRole"), "Net")

        self.assertEqual(tracker.record(IAMRole("NetOperatorRole"), "Other"), "NetOperator")

    def test_ignores_non_role_resources_by_default(self):
        tracker = GeneratedLogicalIdTracker()

        self.assertIsNone(tracker.record(ApiGatewayUsagePlan("ServerlessUsagePlan"), "ApiA"))
        self.assertIsNone(tracker.record(ApiGatewayUsagePlan("ServerlessUsagePlan"), "ApiB"))

    def test_scope_can_be_widened(self):
        tracker = GeneratedLogicalIdTracker(should_check=lambda resource: True)

        tracker.record(ApiGatewayUsagePlan("ServerlessUsagePlan"), "ApiA")

        self.assertEqual(tracker.record(ApiGatewayUsagePlan("ServerlessUsagePlan"), "ApiB"), "ApiA")
