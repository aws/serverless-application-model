from typing import Any, Dict

from pydantic import field_validator

from samtranslator.internal.schema_source.common import LenientBaseModel


# Anything goes if has string Type but is not AWS::Serverless::*
class Resource(LenientBaseModel):
    Type: str

    # Use model_json_schema_extra to add the pattern to JSON Schema
    # Pydantic's Rust regex doesn't support lookahead, but JSON Schema validators do
    model_config = {
        "json_schema_extra": lambda schema, _: _add_type_pattern(schema),
    }

    @field_validator("Type")
    @classmethod
    def type_must_not_be_serverless(cls, v: str) -> str:
        """Validate that Type does not start with AWS::Serverless::"""
        if v.startswith("AWS::Serverless::"):
            raise ValueError("Type must not start with 'AWS::Serverless::'")
        return v


def _add_type_pattern(schema: Dict[str, Any]) -> None:
    """Add pattern constraint to Type field in JSON Schema."""
    if "properties" in schema and "Type" in schema["properties"]:
        schema["properties"]["Type"]["pattern"] = r"^(?!AWS::Serverless::).+$"
