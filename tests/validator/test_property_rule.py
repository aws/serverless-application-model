from typing import Optional
from unittest import TestCase

from samtranslator.internal.schema_source.common import BaseModel
from samtranslator.validator.property_rule import PropertyRules, RuleType


class PropertyRulesTestSchema(BaseModel):
    """Shared test schema for all property rule tests"""

    ImageUri: Optional[str] = None
    CodeUri: Optional[str] = None
    InlineCode: Optional[str] = None
    DeploymentPreference: Optional[str] = None
    AutoPublishAlias: Optional[str] = None
    Runtime: Optional[str] = None
    PackageType: Optional[str] = None
    ImageConfig: Optional[dict] = None
    Handler: Optional[str] = None
    Layers: Optional[list] = None
    VpcConfig: Optional[dict] = None
    SecurityGroupIds: Optional[list] = None
    SubnetIds: Optional[list] = None


class TestPropertyRulesCreation(TestCase):
    """Test PropertyRules creation and rule building API"""

    def test_create_property_rule(self):
        """Test PropertyRules creation"""
        rule = PropertyRules()
        self.assertIsInstance(rule, PropertyRules)
        self.assertEqual(len(rule._rules), 0)

    def test_add_mutually_exclusive_rule(self):
        """Test adding mutually exclusive validation rule"""
        rule = PropertyRules().addMutuallyExclusive("ImageUri", "CodeUri", "InlineCode")
        self.assertEqual(len(rule._rules), 1)
        self.assertEqual(rule._rules[0][0], RuleType.MUTUALLY_EXCLUSIVE)

    def test_add_conditional_exclusive_rule(self):
        """Test adding conditional exclusive validation rule"""
        rule = PropertyRules().addConditionalExclusive("Runtime", ["ImageUri"])
        self.assertEqual(len(rule._rules), 1)
        self.assertEqual(rule._rules[0][0], RuleType.CONDITIONAL_EXCLUSIVE)

    def test_add_mutually_inclusive_rule(self):
        """Test adding mutually inclusive validation rule"""
        rule = PropertyRules().addMutuallyInclusive("VpcConfig", "SecurityGroupIds", "SubnetIds")
        self.assertEqual(len(rule._rules), 1)
        self.assertEqual(rule._rules[0][0], RuleType.MUTUALLY_INCLUSIVE)

    def test_add_conditional_inclusive_rule(self):
        """Test adding conditional inclusive validation rule"""
        rule = PropertyRules().addConditionalInclusive("VpcConfig", ["SecurityGroupIds", "SubnetIds"])
        self.assertEqual(len(rule._rules), 1)
        self.assertEqual(rule._rules[0][0], RuleType.CONDITIONAL_INCLUSIVE)

    def test_fluent_chaining(self):
        """Test fluent API chaining with all rule types"""
        rule = (
            PropertyRules()
            .addMutuallyExclusive("ImageUri", "CodeUri", "InlineCode")
            .addConditionalExclusive("Runtime", ["ImageUri"])
            .addMutuallyInclusive("VpcConfig", "SecurityGroupIds", "SubnetIds")
            .addConditionalInclusive("VpcConfig", ["SecurityGroupIds", "SubnetIds"])
        )
        self.assertEqual(len(rule._rules), 4)


class TestPropertyRulesValidation(TestCase):
    """Test PropertyRules validation logic with different rule types"""

    def test_validate_property_names_valid(self):
        """Test validation with valid property names"""
        PropertyRules().addMutuallyExclusive("ImageUri", "CodeUri")

    def test_validate_property_names_invalid(self):
        """Test validation with invalid property names"""
        rules = PropertyRules().addMutuallyExclusive("InvalidProperty", "CodeUri")
        validated_model = PropertyRulesTestSchema()
        errors = rules.validate_all(validated_model)
        self.assertTrue(any("InvalidProperty" in error for error in errors))


class TestMutuallyExclusiveRules(TestCase):
    """Test mutually exclusive validation rules"""

    def test_mutually_exclusive_success(self):
        """Test mutually exclusive rule validation - success case"""
        rules = PropertyRules().addMutuallyExclusive("ImageUri", "CodeUri", "InlineCode")
        validated_model = PropertyRulesTestSchema(ImageUri="some-image", CodeUri=None, InlineCode=None)
        errors = rules.validate_all(validated_model)
        self.assertEqual(errors, [])

    def test_mutually_exclusive_failure(self):
        """Test mutually exclusive rule validation - failure case"""
        rules = PropertyRules().addMutuallyExclusive("ImageUri", "CodeUri", "InlineCode")
        validated_model = PropertyRulesTestSchema(ImageUri="some-image", CodeUri="some-code", InlineCode=None)
        errors = rules.validate_all(validated_model)
        self.assertEqual(len(errors), 1)
        self.assertIn("Cannot specify", errors[0])


class TestConditionalExclusiveRules(TestCase):
    """Test conditional exclusive validation rules"""

    def test_conditional_exclusive_success(self):
        """Test conditional exclusive rule validation - success case"""
        rules = PropertyRules().addConditionalExclusive("Runtime", ["ImageUri"])
        validated_model = PropertyRulesTestSchema(Runtime="python3.9", ImageUri=None)
        errors = rules.validate_all(validated_model)
        self.assertEqual(errors, [])

    def test_conditional_exclusive_failure(self):
        """Test conditional exclusive rule validation - failure case"""
        rules = PropertyRules().addConditionalExclusive("Runtime", ["ImageUri"])
        validated_model = PropertyRulesTestSchema(Runtime="python3.9", ImageUri="some-image")
        errors = rules.validate_all(validated_model)
        self.assertEqual(len(errors), 1)
        self.assertIn("'Runtime' cannot be used with 'ImageUri'", errors[0])


class TestMutuallyInclusiveRules(TestCase):
    """Test mutually inclusive validation rules"""

    def test_mutually_inclusive_success_all_present(self):
        """Test mutually inclusive rule validation - all present"""
        rules = PropertyRules().addMutuallyInclusive("VpcConfig", "SecurityGroupIds", "SubnetIds")
        validated_model = PropertyRulesTestSchema(
            VpcConfig={"some": "config"}, SecurityGroupIds=["sg-123"], SubnetIds=["subnet-123"]
        )
        errors = rules.validate_all(validated_model)
        self.assertEqual(errors, [])

    def test_mutually_inclusive_success_none_present(self):
        """Test mutually inclusive rule validation - none present"""
        rules = PropertyRules().addMutuallyInclusive("VpcConfig", "SecurityGroupIds", "SubnetIds")
        validated_model = PropertyRulesTestSchema(VpcConfig=None, SecurityGroupIds=None, SubnetIds=None)
        errors = rules.validate_all(validated_model)
        self.assertEqual(errors, [])

    def test_mutually_inclusive_failure(self):
        """Test mutually inclusive rule validation - partial present"""
        rules = PropertyRules().addMutuallyInclusive("VpcConfig", "SecurityGroupIds", "SubnetIds")
        validated_model = PropertyRulesTestSchema(VpcConfig={"some": "config"}, SecurityGroupIds=None, SubnetIds=None)
        errors = rules.validate_all(validated_model)
        self.assertEqual(len(errors), 1)
        self.assertIn("When using 'VpcConfig', you must also specify", errors[0])


class TestConditionalInclusiveRules(TestCase):
    """Test conditional inclusive validation rules"""

    def test_conditional_inclusive_success(self):
        """Test conditional inclusive rule validation - success case"""
        rules = PropertyRules().addConditionalInclusive("VpcConfig", ["SecurityGroupIds", "SubnetIds"])
        validated_model = PropertyRulesTestSchema(
            VpcConfig={"some": "config"}, SecurityGroupIds=["sg-123"], SubnetIds=["subnet-123"]
        )
        errors = rules.validate_all(validated_model)
        self.assertEqual(errors, [])

    def test_conditional_inclusive_failure(self):
        """Test conditional inclusive rule validation - failure case"""
        rules = PropertyRules().addConditionalInclusive("VpcConfig", ["SecurityGroupIds", "SubnetIds"])
        validated_model = PropertyRulesTestSchema(VpcConfig={"some": "config"}, SecurityGroupIds=None, SubnetIds=None)
        errors = rules.validate_all(validated_model)
        self.assertEqual(len(errors), 1)
        self.assertIn("'VpcConfig' requires all of:", errors[0])
