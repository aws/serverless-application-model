"""
Tests for Pydantic v2 schema generation.

These tests verify that the schema generation produces valid JSON Schema
and handles the Pydantic v2 anyOf null pattern for optional fields.
"""

from typing import Any, Dict, List, Optional, Union
from unittest import TestCase

from jsonschema.validators import Draft4Validator
from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, RootModel


class TestSchemaGeneration(TestCase):
    """Test schema generation with Pydantic v2."""

    def test_model_json_schema_produces_valid_json_schema(self):
        """Verify that model_json_schema() produces valid JSON Schema."""

        class TestModel(PydanticBaseModel):
            model_config = ConfigDict(extra="forbid")
            Name: str
            Description: Optional[str] = None

        schema = TestModel.model_json_schema()
        schema["$schema"] = "http://json-schema.org/draft-04/schema#"

        # Normalize $defs to definitions for Draft4 compatibility
        if "$defs" in schema:
            schema["definitions"] = schema.pop("$defs")

        # Validate the schema is valid JSON Schema
        Draft4Validator.check_schema(schema)

    def test_anyof_null_pattern_for_optional_fields(self):
        """Verify that optional fields use anyOf null pattern in Pydantic v2."""

        class TestModel(PydanticBaseModel):
            RequiredField: str
            OptionalField: Optional[str] = None

        schema = TestModel.model_json_schema()

        # Required field should not have anyOf pattern
        required_prop = schema["properties"]["RequiredField"]
        self.assertEqual(required_prop.get("type"), "string")
        self.assertNotIn("anyOf", required_prop)

        # Optional field should have anyOf pattern with null
        optional_prop = schema["properties"]["OptionalField"]
        self.assertIn("anyOf", optional_prop)

        # Verify the anyOf contains string and null types
        any_of_types = [item.get("type") for item in optional_prop["anyOf"]]
        self.assertIn("string", any_of_types)
        self.assertIn("null", any_of_types)

    def test_defs_key_in_pydantic_v2(self):
        """Verify that Pydantic v2 uses $defs instead of definitions."""

        class NestedModel(PydanticBaseModel):
            Value: str

        class TestModel(PydanticBaseModel):
            Nested: NestedModel

        schema = TestModel.model_json_schema()

        # Pydantic v2 uses $defs
        self.assertIn("$defs", schema)
        self.assertNotIn("definitions", schema)

    def test_rootmodel_schema_generation(self):
        """Verify that RootModel generates correct schema."""
        PassThrough = Union[Dict[str, Any], List[Any], str, int, float, bool, None]

        class PassThroughProp(RootModel[PassThrough]):
            pass

        class TestModel(PydanticBaseModel):
            Prop: Optional[PassThroughProp] = None

        schema = TestModel.model_json_schema()

        # Should have $defs with PassThroughProp
        self.assertIn("$defs", schema)
        self.assertIn("PassThroughProp", schema["$defs"])

        # PassThroughProp should have anyOf with multiple types
        passthrough_schema = schema["$defs"]["PassThroughProp"]
        self.assertIn("anyOf", passthrough_schema)

        # Verify it includes object, array, string, integer, number, boolean, null
        any_of_types = []
        for item in passthrough_schema["anyOf"]:
            if "type" in item:
                any_of_types.append(item["type"])
        self.assertIn("object", any_of_types)
        self.assertIn("array", any_of_types)
        self.assertIn("string", any_of_types)
        self.assertIn("integer", any_of_types)
        self.assertIn("number", any_of_types)
        self.assertIn("boolean", any_of_types)
        self.assertIn("null", any_of_types)

    def test_ref_paths_use_defs(self):
        """Verify that $ref paths use $defs in Pydantic v2."""

        class NestedModel(PydanticBaseModel):
            Value: str

        class TestModel(PydanticBaseModel):
            Nested: NestedModel

        schema = TestModel.model_json_schema()

        # The $ref should point to $defs
        nested_ref = schema["properties"]["Nested"]["$ref"]
        self.assertTrue(nested_ref.startswith("#/$defs/"))


def _normalize_refs(obj: Any) -> Any:
    """
    Recursively update $ref paths from Pydantic v2 format (#/$defs/) to v1 format (#/definitions/).
    This is a copy of the function from schema.py for testing purposes.
    """
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if k == "$ref" and isinstance(v, str) and v.startswith("#/$defs/"):
                result[k] = v.replace("#/$defs/", "#/definitions/")
            else:
                result[k] = _normalize_refs(v)
        return result
    elif isinstance(obj, list):
        return [_normalize_refs(item) for item in obj]
    return obj


class TestSchemaNormalization(TestCase):
    """Test schema normalization functions."""

    def test_normalize_refs_converts_defs_to_definitions(self):
        """Test that _normalize_refs converts $defs refs to definitions refs."""
        input_schema = {
            "properties": {
                "Nested": {"$ref": "#/$defs/NestedModel"},
                "List": {"items": {"$ref": "#/$defs/ItemModel"}},
            },
            "$defs": {
                "NestedModel": {"type": "object"},
                "ItemModel": {"type": "string"},
            },
        }

        result = _normalize_refs(input_schema)

        # $ref paths should be converted
        self.assertEqual(result["properties"]["Nested"]["$ref"], "#/definitions/NestedModel")
        self.assertEqual(result["properties"]["List"]["items"]["$ref"], "#/definitions/ItemModel")

        # $defs key should remain unchanged (it's renamed separately in get_schema)
        self.assertIn("$defs", result)

    def test_normalize_refs_handles_nested_structures(self):
        """Test that _normalize_refs handles deeply nested structures."""
        input_schema = {
            "anyOf": [
                {"$ref": "#/$defs/TypeA"},
                {"type": "object", "properties": {"nested": {"$ref": "#/$defs/TypeB"}}},
            ]
        }

        result = _normalize_refs(input_schema)

        self.assertEqual(result["anyOf"][0]["$ref"], "#/definitions/TypeA")
        self.assertEqual(result["anyOf"][1]["properties"]["nested"]["$ref"], "#/definitions/TypeB")

    def test_normalize_refs_preserves_non_ref_values(self):
        """Test that _normalize_refs preserves non-$ref values."""
        input_schema = {
            "type": "object",
            "title": "TestModel",
            "properties": {
                "name": {"type": "string"},
                "count": {"type": "integer"},
            },
        }

        result = _normalize_refs(input_schema)

        self.assertEqual(result["type"], "object")
        self.assertEqual(result["title"], "TestModel")
        self.assertEqual(result["properties"]["name"]["type"], "string")
        self.assertEqual(result["properties"]["count"]["type"], "integer")
