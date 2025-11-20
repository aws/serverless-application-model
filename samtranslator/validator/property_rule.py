from enum import Enum
from typing import Any, List, Optional, Tuple, TypeVar

RT = TypeVar("RT")


class RuleType(Enum):
    MUTUALLY_EXCLUSIVE = "mutually_exclusive"
    CONDITIONAL_EXCLUSIVE = "conditional_exclusive"
    MUTUALLY_INCLUSIVE = "mutually_inclusive"
    CONDITIONAL_INCLUSIVE = "conditional_inclusive"


class PropertyRules:
    def __init__(self) -> None:
        self._rules: List[Tuple[RuleType, List[str], List[str]]] = []

    def addMutuallyExclusive(self, *props: str) -> "PropertyRules":
        self._rules.append((RuleType.MUTUALLY_EXCLUSIVE, list(props), []))
        return self

    def addConditionalExclusive(self, source_prop: str, target_props: List[str]) -> "PropertyRules":
        self._rules.append((RuleType.CONDITIONAL_EXCLUSIVE, [source_prop], target_props))
        return self

    def addMutuallyInclusive(self, *props: str) -> "PropertyRules":
        self._rules.append((RuleType.MUTUALLY_INCLUSIVE, list(props), []))
        return self

    def addConditionalInclusive(self, source_prop: str, target_props: List[str]) -> "PropertyRules":
        self._rules.append((RuleType.CONDITIONAL_INCLUSIVE, [source_prop], target_props))
        return self

    def validate_all(self, validated_model: Optional[RT]) -> List[str]:
        if validated_model is None:
            return []

        errors = []
        for rule_type, source_props, target_props in self._rules:
            # Validate property names during validation
            all_props = source_props + target_props
            for prop in all_props:
                # Skip validation for value-based conditions (PropertyName=Value)
                if "=" in prop:
                    prop_name = prop.split("=", 1)[0]
                    if "." not in prop_name and not hasattr(validated_model, prop_name):
                        errors.append(f"Property '{prop_name}' does not exist in the schema")
                        continue
                elif "." not in prop and not hasattr(validated_model, prop):
                    errors.append(f"Property '{prop}' does not exist in the schema")
                    continue

            error = self._validate_rule(validated_model, rule_type, source_props, target_props)
            if error:
                errors.append(error)
        return errors

    def _validate_rule(
        self, validated_model: RT, rule_type: RuleType, source_props: List[str], target_props: List[str]
    ) -> Optional[str]:
        if rule_type == RuleType.MUTUALLY_EXCLUSIVE:
            return self._validate_mutually_exclusive(validated_model, source_props)
        if rule_type == RuleType.CONDITIONAL_EXCLUSIVE:
            return self._validate_conditional_exclusive(validated_model, source_props, target_props)
        if rule_type == RuleType.MUTUALLY_INCLUSIVE:
            return self._validate_mutually_inclusive(validated_model, source_props)
        if rule_type == RuleType.CONDITIONAL_INCLUSIVE:
            return self._validate_conditional_inclusive(validated_model, source_props, target_props)
        return None

    def _validate_mutually_exclusive(self, validated_model: RT, source_props: List[str]) -> Optional[str]:
        present = [prop for prop in source_props if self._get_property_value(validated_model, prop) is not None]
        if len(present) > 1:
            present_props = " and ".join(f"'{p}'" for p in present)
            return f"Cannot specify {present_props} together."
        return None

    def _validate_conditional_exclusive(
        self, validated_model: RT, source_props: List[str], target_props: List[str]
    ) -> Optional[str]:
        source_present = any(self._check_property_condition(validated_model, prop) for prop in source_props)
        if source_present:
            conflicting = [prop for prop in target_props if self._check_property_condition(validated_model, prop)]
            if conflicting:
                conflicting_props = ", ".join(f"'{p}'" for p in conflicting)
                return f"'{source_props[0]}' cannot be used with {conflicting_props}."
        return None

    def _validate_mutually_inclusive(self, validated_model: RT, source_props: List[str]) -> Optional[str]:
        present = [prop for prop in source_props if self._get_property_value(validated_model, prop) is not None]
        if 0 < len(present) < len(source_props):
            missing = [prop for prop in source_props if prop not in present]
            missing_props = ", ".join(f"'{p}'" for p in missing)
            present_props = ", ".join(f"'{p}'" for p in present)
            return f"When using {present_props}, you must also specify {missing_props}."
        return None

    def _validate_conditional_inclusive(
        self, validated_model: RT, source_props: List[str], target_props: List[str]
    ) -> Optional[str]:
        source_present = any(self._check_property_condition(validated_model, prop) for prop in source_props)
        if source_present:
            missing = [prop for prop in target_props if not self._check_property_condition(validated_model, prop)]
            if missing:
                missing_props = ", ".join(f"'{p}'" for p in missing)
                return f"'{source_props[0]}' requires all of: {missing_props}."
        return None

    def _get_property_value(self, validated_model: RT, prop: str) -> Any:
        if "." not in prop:
            return getattr(validated_model, prop, None)

        # Handle nested properties recursively
        try:
            first_part, rest = prop.split(".", 1)

            # Get the first level value
            if hasattr(validated_model, first_part):
                value = getattr(validated_model, first_part)
            elif isinstance(validated_model, dict) and first_part in validated_model:
                value = validated_model[first_part]
            else:
                return None

            # If value is None, return None
            if value is None:
                return None

            # Recursively get the rest of the property path
            return self._get_property_value(value, rest)
        except Exception:
            return None

    def _check_property_condition(self, validated_model: RT, prop: str) -> bool:
        """Check if property condition is met. Supports 'PropertyName=Value' syntax."""
        if "=" in prop:
            prop_name, expected_value = prop.split("=", 1)
            actual_value = self._get_property_value(validated_model, prop_name)
            return actual_value is not None and str(actual_value) == expected_value
        return self._get_property_value(validated_model, prop) is not None
