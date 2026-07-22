"""Tests for MUTUALLY_EXCLUSIVE validation rule with =Value conditional presence syntax.

Parametrized across:
- Path depth: top-level properties vs nested (dot-notation) properties
- Value types: =True, =False, =StringValue, no = (plain presence check)
- Combinations: condition met, condition not met, property absent
"""

from unittest import TestCase

from parameterized import parameterized
from samtranslator.internal.schema_source.common import BaseModel
from samtranslator.model import PropertyType, SamResourceMacro, ValidationRule
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.types import IS_BOOL, IS_DICT, IS_STR

# --- Schema fixtures ---


class NestedProps(BaseModel):
    Flag: bool | None = None
    Mode: str | None = None
    Tags: dict | None = None


class SchemaFixture(BaseModel):
    TopBool: bool | None = None
    TopStr: str | None = None
    Nested: NestedProps | None = None


class ResourceFixture(SamResourceMacro):
    resource_type = "Test::Resource"
    property_types = {
        "TopBool": PropertyType(False, IS_BOOL),
        "TopStr": PropertyType(False, IS_STR),
        "Nested": PropertyType(False, IS_DICT),
    }

    def to_cloudformation(self, **kwargs):
        return []


def _make_resource(rules):
    class Resource(ResourceFixture):
        __validation_rules__ = rules

    return Resource("TestId")


class TestValidationRuleValueSyntax(TestCase):
    """Tests for =Value conditional presence syntax in MUTUALLY_EXCLUSIVE rules."""

    @parameterized.expand(
        [
            # Top-level: bool =True
            (
                ["TopBool=True", "TopStr"],
                {"TopBool": True, "TopStr": "val"},
                "top-level bool=True + top-level str",
            ),
            # Nested: bool =True
            (
                ["Nested.Flag=True", "Nested.Tags"],
                {"Nested": {"Flag": True, "Tags": {"k": "v"}}},
                "nested bool=True + nested dict",
            ),
            # Nested: string =Value
            (
                ["Nested.Mode=Explicit", "Nested.Tags"],
                {"Nested": {"Mode": "Explicit", "Tags": {"k": "v"}}},
                "nested str=Explicit + nested dict",
            ),
            # Top-level: bool =False
            (
                ["TopBool=False", "TopStr"],
                {"TopBool": False, "TopStr": "val"},
                "top-level bool=False + top-level str",
            ),
            # Plain (no =): both non-None triggers error
            (
                ["Nested.Flag", "Nested.Tags"],
                {"Nested": {"Flag": False, "Tags": {"k": "v"}}},
                "plain nested props, both non-None (backward compat)",
            ),
            # Mixed: one with =Value, one plain
            (
                ["Nested.Mode=Propagate", "TopStr"],
                {"Nested": {"Mode": "Propagate"}, "TopStr": "val"},
                "nested str=Value + top-level plain",
            ),
            # String value with spaces (split on first = only)
            (
                ["Nested.Mode=Hello World", "Nested.Tags"],
                {"Nested": {"Mode": "Hello World", "Tags": {"k": "v"}}},
                "string value with spaces",
            ),
        ]
    )
    def test_raises_when_condition_met(self, rule_props, props, description):
        """Validation should raise when =Value condition is met and target is present."""
        resource = _make_resource([(ValidationRule.MUTUALLY_EXCLUSIVE, rule_props)])
        for key, val in props.items():
            setattr(resource, key, val)

        with self.assertRaises(InvalidResourceException):
            resource.validate_before_transform(SchemaFixture)

    @parameterized.expand(
        [
            # =True condition not met (value is False)
            (
                ["TopBool=True", "TopStr"],
                {"TopBool": False, "TopStr": "val"},
                "top-level bool=True rule, actual=False -> valid",
            ),
            (
                ["Nested.Flag=True", "Nested.Tags"],
                {"Nested": {"Flag": False, "Tags": {"k": "v"}}},
                "nested bool=True rule, actual=False -> valid",
            ),
            # =False condition not met (value is True)
            (
                ["TopBool=False", "TopStr"],
                {"TopBool": True, "TopStr": "val"},
                "top-level bool=False rule, actual=True -> valid",
            ),
            # String =Value not matching
            (
                ["Nested.Mode=Explicit", "Nested.Tags"],
                {"Nested": {"Mode": "None", "Tags": {"k": "v"}}},
                "nested str=Explicit rule, actual=None -> valid",
            ),
            # Only condition property present (no target)
            (
                ["Nested.Flag=True", "Nested.Tags"],
                {"Nested": {"Flag": True}},
                "condition met but target absent -> valid",
            ),
            # Only target present (no condition property)
            (
                ["Nested.Flag=True", "Nested.Tags"],
                {"Nested": {"Tags": {"k": "v"}}},
                "target present but condition absent -> valid",
            ),
            # Both absent
            (
                ["Nested.Flag=True", "Nested.Tags"],
                {"Nested": {}},
                "both absent -> valid",
            ),
            # Parent property not set at all
            (
                ["Nested.Flag=True", "Nested.Tags"],
                {},
                "parent property None -> valid",
            ),
            # Condition value is None (not set)
            (
                ["TopBool=True", "TopStr"],
                {"TopStr": "val"},
                "condition property None, target present -> valid",
            ),
            # Top-level + nested mix, condition not met
            (
                ["Nested.Mode=Propagate", "TopStr"],
                {"Nested": {"Mode": "Explicit"}, "TopStr": "val"},
                "nested str=Propagate rule, actual=Explicit -> valid",
            ),
            # String value with spaces - not matching
            (
                ["Nested.Mode=Hello World", "Nested.Tags"],
                {"Nested": {"Mode": "Other Value", "Tags": {"k": "v"}}},
                "string with spaces, value mismatch -> valid",
            ),
        ]
    )
    def test_valid_when_condition_not_met(self, rule_props, props, description):
        """Validation should pass when =Value condition is not met."""
        resource = _make_resource([(ValidationRule.MUTUALLY_EXCLUSIVE, rule_props)])
        for key, val in props.items():
            setattr(resource, key, val)

        resource.validate_before_transform(SchemaFixture)  # Should not raise

    def test_error_message_includes_value_syntax(self):
        """Error message should show the full 'Property=Value' in the output."""
        resource = _make_resource(
            [
                (ValidationRule.MUTUALLY_EXCLUSIVE, ["Nested.Flag=True", "Nested.Tags"]),
            ]
        )
        resource.Nested = {"Flag": True, "Tags": {"k": "v"}}

        with self.assertRaises(InvalidResourceException) as ctx:
            resource.validate_before_transform(SchemaFixture)

        self.assertIn("'Nested.Flag=True'", ctx.exception.message)
        self.assertIn("'Nested.Tags'", ctx.exception.message)
        self.assertIn("together", ctx.exception.message)
