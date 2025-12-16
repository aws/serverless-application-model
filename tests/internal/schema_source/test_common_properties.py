"""
Property-based tests for Pydantic v2 migration in common.py module.

These tests verify the correctness properties defined in the design document
for the pydantic-v2-upgrade feature.
"""

from typing import Any, Dict, Optional

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError
from samtranslator.internal.schema_source.any_cfn_resource import Resource
from samtranslator.internal.schema_source.common import BaseModel, PassThroughProp

# Strategy for generating PassThrough values (Any type)
passthrough_values = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False),
    st.text(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
)


class TestPassThroughPropProperties:
    """
    **Feature: pydantic-v2-upgrade, Property 4: RootModel value access**
    **Validates: Requirements 4.2**

    Property 4: RootModel value access
    *For any* PassThroughProp instance wrapping a value, accessing `.root`
    should return the original wrapped value unchanged.
    """

    @settings(max_examples=100)
    @given(value=passthrough_values)
    def test_rootmodel_value_access(self, value):
        """
        **Feature: pydantic-v2-upgrade, Property 4: RootModel value access**
        **Validates: Requirements 4.2**
        """
        # Create PassThroughProp with the value
        prop = PassThroughProp(value)

        # Access via .root should return the original value
        assert prop.root == value


class TestBaseModelExtraFieldsProperties:
    """
    **Feature: pydantic-v2-upgrade, Property 5: Extra fields rejected**
    **Validates: Requirements 5.1**

    Property 5: Extra fields rejected
    *For any* input dictionary containing fields not defined in the model,
    validation should raise ValidationError when `extra='forbid'` is configured.
    """

    @settings(max_examples=100)
    @given(
        name=st.text(min_size=1),
        extra_field_name=st.text(min_size=1).filter(lambda x: x not in ("name", "value")),
        extra_field_value=st.one_of(st.text(), st.integers(), st.booleans()),
    )
    def test_extra_fields_rejected(self, name, extra_field_name, extra_field_value):
        """
        **Feature: pydantic-v2-upgrade, Property 5: Extra fields rejected**
        **Validates: Requirements 5.1**
        """

        # Define a test model that inherits from BaseModel (which has extra='forbid')
        class TestModel(BaseModel):
            name: str
            value: Optional[PassThroughProp] = None

        # Attempt to create model with extra field should raise ValidationError
        with pytest.raises(ValidationError):
            TestModel(name=name, **{extra_field_name: extra_field_value})


class TestPatternValidationProperties:
    """
    **Feature: pydantic-v2-upgrade, Property 6: Pattern validation works**
    **Validates: Requirements 5.2**

    Property 6: Pattern validation works
    *For any* string that does not match the defined pattern constraint,
    validation should raise ValidationError.
    """

    # Strategy for generating valid non-serverless AWS resource types
    valid_resource_types = st.from_regex(r"^(?!AWS::Serverless::)[A-Za-z0-9:]+$", fullmatch=True).filter(
        lambda x: len(x) > 0
    )

    # Strategy for generating invalid AWS::Serverless:: resource types
    invalid_serverless_types = st.from_regex(r"^AWS::Serverless::[A-Za-z]+$", fullmatch=True)

    @settings(max_examples=100)
    @given(resource_type=valid_resource_types)
    def test_valid_non_serverless_types_accepted(self, resource_type):
        """
        **Feature: pydantic-v2-upgrade, Property 6: Pattern validation works**
        **Validates: Requirements 5.2**

        Valid resource types that don't start with AWS::Serverless:: should be accepted.
        """
        # Should not raise - valid types are accepted
        resource = Resource(Type=resource_type)
        assert resource.Type == resource_type

    @settings(max_examples=100)
    @given(resource_type=invalid_serverless_types)
    def test_serverless_types_rejected(self, resource_type):
        """
        **Feature: pydantic-v2-upgrade, Property 6: Pattern validation works**
        **Validates: Requirements 5.2**

        Resource types starting with AWS::Serverless:: should be rejected
        by the pattern constraint.
        """
        # Should raise ValidationError - serverless types are rejected
        with pytest.raises(ValidationError):
            Resource(Type=resource_type)


class TestValidationErrorPropertyPath:
    """
    **Feature: pydantic-v2-upgrade, Property 2: Validation error contains property path**
    **Validates: Requirements 2.3**

    Property 2: Validation error contains property path
    *For any* invalid input dictionary with a type error at a nested path,
    the ValidationError should contain that property path in its errors.
    """

    @settings(max_examples=100)
    @given(
        outer_field=st.text(min_size=1, alphabet=st.characters(whitelist_categories=("L", "N"))),
        inner_field=st.text(min_size=1, alphabet=st.characters(whitelist_categories=("L", "N"))),
    )
    def test_validation_error_contains_property_path(self, outer_field, inner_field):
        """
        **Feature: pydantic-v2-upgrade, Property 2: Validation error contains property path**
        **Validates: Requirements 2.3**

        When validation fails at a nested path, the error should contain
        the full property path in its location.
        """

        # Define nested models to test property path in errors
        class InnerModel(BaseModel):
            required_int: int

        class OuterModel(BaseModel):
            nested: InnerModel

        # Create invalid input with wrong type at nested path
        invalid_input = {"nested": {"required_int": "not_an_int"}}

        try:
            OuterModel.model_validate(invalid_input)
            # Should not reach here
            assert False, "Expected ValidationError"
        except ValidationError as e:
            errors = e.errors()
            # Verify at least one error exists
            assert len(errors) > 0

            # Verify the error contains the property path
            error_locs = [error["loc"] for error in errors]
            # The path should include 'nested' and 'required_int'
            found_nested_path = any("nested" in str(loc) and "required_int" in str(loc) for loc in error_locs)
            assert found_nested_path, f"Expected nested path in errors, got: {error_locs}"

    @settings(max_examples=100)
    @given(
        field_name=st.text(min_size=1, alphabet=st.characters(whitelist_categories=("L", "N"))),
    )
    def test_validation_error_path_for_missing_required_field(self, field_name):
        """
        **Feature: pydantic-v2-upgrade, Property 2: Validation error contains property path**
        **Validates: Requirements 2.3**

        When a required field is missing, the error should contain
        the field name in its location.
        """

        # Define a model with a required field
        class RequiredFieldModel(BaseModel):
            required_field: str

        # Create invalid input missing the required field
        invalid_input = {}

        try:
            RequiredFieldModel.model_validate(invalid_input)
            # Should not reach here
            assert False, "Expected ValidationError"
        except ValidationError as e:
            errors = e.errors()
            # Verify at least one error exists
            assert len(errors) > 0

            # Verify the error contains the field name in the path
            error_locs = [error["loc"] for error in errors]
            found_field_path = any("required_field" in str(loc) for loc in error_locs)
            assert found_field_path, f"Expected 'required_field' in error path, got: {error_locs}"


class TestValidationRoundTripConsistency:
    """
    **Feature: pydantic-v2-upgrade, Property 1: Validation round-trip consistency**
    **Validates: Requirements 2.1, 3.1, 3.3**

    Property 1: Validation round-trip consistency
    *For any* valid SAM resource properties dictionary, validating with `model_validate()`
    and converting back with `model_dump()` should preserve all non-None values.
    """

    @settings(max_examples=100)
    @given(
        subnet_id=st.text(min_size=1, alphabet=st.characters(whitelist_categories=("L", "N"))),
        security_group_id=st.text(min_size=1, alphabet=st.characters(whitelist_categories=("L", "N"))),
    )
    def test_vpc_config_round_trip(self, subnet_id, security_group_id):
        """
        **Feature: pydantic-v2-upgrade, Property 1: Validation round-trip consistency**
        **Validates: Requirements 2.1, 3.1, 3.3**

        VpcConfig model should preserve all values through validate/dump round-trip.
        """
        from samtranslator.internal.schema_source.aws_serverless_capacity_provider import VpcConfig

        # Create input dictionary
        input_dict = {
            "SubnetIds": [subnet_id],
            "SecurityGroupIds": [security_group_id],
        }

        # Validate and dump
        model = VpcConfig.model_validate(input_dict)
        output_dict = model.model_dump()

        # Verify round-trip preserves values
        assert output_dict["SubnetIds"] == input_dict["SubnetIds"]
        assert output_dict["SecurityGroupIds"] == input_dict["SecurityGroupIds"]

    @settings(max_examples=100)
    @given(
        max_vcpu=st.integers(min_value=1, max_value=10000),
        avg_cpu=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    )
    def test_scaling_config_round_trip(self, max_vcpu, avg_cpu):
        """
        **Feature: pydantic-v2-upgrade, Property 1: Validation round-trip consistency**
        **Validates: Requirements 2.1, 3.1, 3.3**

        ScalingConfig model should preserve all values through validate/dump round-trip.
        """
        from samtranslator.internal.schema_source.aws_serverless_capacity_provider import ScalingConfig

        # Create input dictionary
        input_dict = {
            "MaxVCpuCount": max_vcpu,
            "AverageCPUUtilization": avg_cpu,
        }

        # Validate and dump
        model = ScalingConfig.model_validate(input_dict)
        output_dict = model.model_dump()

        # Verify round-trip preserves values
        assert output_dict["MaxVCpuCount"] == input_dict["MaxVCpuCount"]
        assert output_dict["AverageCPUUtilization"] == input_dict["AverageCPUUtilization"]

    @settings(max_examples=100)
    @given(
        arch=st.sampled_from(["x86_64", "arm64"]),
        allowed_type=st.text(min_size=1, alphabet=st.characters(whitelist_categories=("L", "N"))),
    )
    def test_instance_requirements_round_trip(self, arch, allowed_type):
        """
        **Feature: pydantic-v2-upgrade, Property 1: Validation round-trip consistency**
        **Validates: Requirements 2.1, 3.1, 3.3**

        InstanceRequirements model should preserve all values through validate/dump round-trip.
        """
        from samtranslator.internal.schema_source.aws_serverless_capacity_provider import InstanceRequirements

        # Create input dictionary
        input_dict = {
            "Architectures": [arch],
            "AllowedTypes": [allowed_type],
        }

        # Validate and dump
        model = InstanceRequirements.model_validate(input_dict)
        output_dict = model.model_dump()

        # Verify round-trip preserves values
        assert output_dict["Architectures"] == input_dict["Architectures"]
        assert output_dict["AllowedTypes"] == input_dict["AllowedTypes"]

    @settings(max_examples=100)
    @given(
        auth_type=st.sampled_from(["API_KEY", "AWS_IAM", "AWS_LAMBDA", "OPENID_CONNECT", "AMAZON_COGNITO_USER_POOLS"]),
    )
    def test_authorizer_round_trip(self, auth_type):
        """
        **Feature: pydantic-v2-upgrade, Property 1: Validation round-trip consistency**
        **Validates: Requirements 2.1, 3.1, 3.3**

        GraphQL Authorizer model should preserve Type through validate/dump round-trip.
        """
        from samtranslator.internal.schema_source.aws_serverless_graphqlapi import Authorizer

        # Create input dictionary with just Type (minimal valid input)
        input_dict = {"Type": auth_type}

        # Validate and dump
        model = Authorizer.model_validate(input_dict)
        output_dict = model.model_dump()

        # Verify round-trip preserves the Type value
        assert output_dict["Type"] == input_dict["Type"]


class TestExcludeNoneBehavior:
    """
    **Feature: pydantic-v2-upgrade, Property 3: exclude_none removes all None values**
    **Validates: Requirements 3.2**

    Property 3: exclude_none removes all None values
    *For any* Pydantic model with some fields set to None, `model_dump(exclude_none=True)`
    should return a dict with no None values at any nesting level.
    """

    @settings(max_examples=100)
    @given(
        max_vcpu=st.one_of(st.none(), st.integers(min_value=1, max_value=10000)),
        avg_cpu=st.one_of(st.none(), st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)),
    )
    def test_scaling_config_exclude_none(self, max_vcpu, avg_cpu):
        """
        **Feature: pydantic-v2-upgrade, Property 3: exclude_none removes all None values**
        **Validates: Requirements 3.2**

        ScalingConfig.model_dump(exclude_none=True) should not contain any None values.
        """
        from samtranslator.internal.schema_source.aws_serverless_capacity_provider import ScalingConfig

        # Create input dictionary (may have None values)
        input_dict: Dict[str, Any] = {}
        if max_vcpu is not None:
            input_dict["MaxVCpuCount"] = max_vcpu
        if avg_cpu is not None:
            input_dict["AverageCPUUtilization"] = avg_cpu

        # Validate and dump with exclude_none
        model = ScalingConfig.model_validate(input_dict)
        output_dict = model.model_dump(exclude_none=True)

        # Verify no None values in output
        assert None not in output_dict.values(), f"Found None in output: {output_dict}"

        # Verify only non-None values are present
        if max_vcpu is not None:
            assert output_dict.get("MaxVCpuCount") == max_vcpu
        else:
            assert "MaxVCpuCount" not in output_dict

        if avg_cpu is not None:
            assert output_dict.get("AverageCPUUtilization") == avg_cpu
        else:
            assert "AverageCPUUtilization" not in output_dict

    @settings(max_examples=100)
    @given(
        arch=st.one_of(st.none(), st.lists(st.sampled_from(["x86_64", "arm64"]), min_size=1, max_size=2)),
        allowed=st.one_of(
            st.none(),
            st.lists(
                st.text(min_size=1, alphabet=st.characters(whitelist_categories=("L", "N"))), min_size=1, max_size=2
            ),
        ),
        excluded=st.one_of(
            st.none(),
            st.lists(
                st.text(min_size=1, alphabet=st.characters(whitelist_categories=("L", "N"))), min_size=1, max_size=2
            ),
        ),
    )
    def test_instance_requirements_exclude_none(self, arch, allowed, excluded):
        """
        **Feature: pydantic-v2-upgrade, Property 3: exclude_none removes all None values**
        **Validates: Requirements 3.2**

        InstanceRequirements.model_dump(exclude_none=True) should not contain any None values.
        """
        from samtranslator.internal.schema_source.aws_serverless_capacity_provider import InstanceRequirements

        # Create input dictionary (may have None values)
        input_dict: Dict[str, Any] = {}
        if arch is not None:
            input_dict["Architectures"] = arch
        if allowed is not None:
            input_dict["AllowedTypes"] = allowed
        if excluded is not None:
            input_dict["ExcludedTypes"] = excluded

        # Validate and dump with exclude_none
        model = InstanceRequirements.model_validate(input_dict)
        output_dict = model.model_dump(exclude_none=True)

        # Verify no None values in output
        assert None not in output_dict.values(), f"Found None in output: {output_dict}"

    def _check_no_none_recursive(self, d: Dict[str, Any]) -> bool:
        """Helper to recursively check for None values in nested dicts."""
        for value in d.values():
            if value is None:
                return False
            if isinstance(value, dict):
                if not self._check_no_none_recursive(value):
                    return False
        return True

    @settings(max_examples=100)
    @given(
        ttl=st.integers(min_value=0, max_value=3600),  # Ttl is required, always provide it
        caching_keys=st.one_of(st.none(), st.lists(st.text(min_size=1), min_size=1, max_size=3)),
    )
    def test_caching_config_exclude_none(self, ttl, caching_keys):
        """
        **Feature: pydantic-v2-upgrade, Property 3: exclude_none removes all None values**
        **Validates: Requirements 3.2**

        Caching config model_dump(exclude_none=True) should not contain any None values.
        """
        from samtranslator.internal.schema_source.aws_serverless_graphqlapi import Caching

        # Create input dictionary (Ttl is required, CachingKeys is optional)
        input_dict: Dict[str, Any] = {"Ttl": ttl}
        if caching_keys is not None:
            input_dict["CachingKeys"] = caching_keys

        # Validate and dump with exclude_none
        model = Caching.model_validate(input_dict)
        output_dict = model.model_dump(exclude_none=True)

        # Verify no None values in output (including nested)
        assert self._check_no_none_recursive(output_dict), f"Found None in output: {output_dict}"
