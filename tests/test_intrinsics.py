from unittest import TestCase

from parameterized import parameterized
from samtranslator.model.intrinsics import (
    get_logical_id_from_intrinsic,
    is_intrinsic,
    is_intrinsic_if,
    is_intrinsic_no_value,
    make_shorthand,
    validate_intrinsic_if_items,
)


class TestIntrinsics(TestCase):
    @parameterized.expand(["Ref", "Condition", "Fn::foo", "Fn::sub", "Fn::something"])
    def test_is_intrinsic_must_detect_intrinsics(self, intrinsic_name):
        input = {intrinsic_name: ["some value"]}

        self.assertTrue(is_intrinsic(input))

    def test_is_intrinsic_on_empty_input(self):
        self.assertFalse(is_intrinsic(None))

    def test_is_intrinsic_on_non_dict_input(self):
        self.assertFalse(is_intrinsic([1, 2, 3]))

    def test_is_intrinsic_on_intrinsic_like_dict_input(self):
        self.assertFalse(is_intrinsic({"Ref": "foo", "key": "bar"}))

    @parameterized.expand([({"Ref": "foo"}, "${foo}"), ({"Fn::GetAtt": ["foo", "Arn"]}, "${foo.Arn}")])
    def test_make_shorthand_success(self, input, expected):
        self.assertEqual(make_shorthand(input), expected)

    def test_make_short_hand_failure(self):
        input = {"Fn::Sub": "something"}

        with self.assertRaises(NotImplementedError):
            make_shorthand(input)

    def test_is_intrinsic_no_value_must_return_true_for_no_value(self):
        policy = {"Ref": "AWS::NoValue"}

        self.assertTrue(is_intrinsic_no_value(policy))

    def test_is_intrinsic_no_value_must_return_false_for_other_value(self):
        bad_key = {"sRefs": "AWS::NoValue"}
        bad_value = {"Ref": "SWA::NoValue"}
        too_many_keys = {"Ref": "AWS::NoValue", "feR": "SWA::NoValue"}

        self.assertFalse(is_intrinsic_no_value(bad_key))
        self.assertFalse(is_intrinsic_no_value(bad_value))
        self.assertFalse(is_intrinsic_no_value(None))
        self.assertFalse(is_intrinsic_no_value(too_many_keys))

    def test_is_intrinsic_if_must_return_true_for_if(self):
        policy = {"Fn::If": "some value"}

        self.assertTrue(is_intrinsic_if(policy))

    def test_is_intrinsic_if_must_return_false_for_others(self):
        too_many_keys = {"Fn::If": "some value", "Fn::And": "other value"}
        not_if = {"Fn::Or": "some value"}

        self.assertFalse(is_intrinsic_if(too_many_keys))
        self.assertFalse(is_intrinsic_if(not_if))
        self.assertFalse(is_intrinsic_if(None))

    def test_validate_intrinsic_if_items_valid(self):
        validate_intrinsic_if_items(["Condition", "Then", "Else"])

    def test_validate_intrinsic_if_items_invalid(self):
        not_enough_items = ["Then", "Else"]
        is_string = "Then"
        is_integer = 3
        is_boolean = True
        is_dict = {"Fn::If": "some value", "Fn::And": "other value"}

        self.assertRaises(ValueError, validate_intrinsic_if_items, not_enough_items)
        self.assertRaises(ValueError, validate_intrinsic_if_items, is_string)
        self.assertRaises(ValueError, validate_intrinsic_if_items, None)
        self.assertRaises(ValueError, validate_intrinsic_if_items, is_integer)
        self.assertRaises(ValueError, validate_intrinsic_if_items, is_boolean)
        self.assertRaises(ValueError, validate_intrinsic_if_items, is_dict)

    @parameterized.expand(
        [
            ({"Fn::GetAtt": ["Foo", "Bar"]}, "Foo"),
            ({"Fn::GetAtt": "Foo.Bar"}, "Foo"),
            ({"Ref": "Foo"}, "Foo"),
        ]
    )
    def test_get_logical_id_from_intrinsic_success(self, input, expected):
        self.assertEqual(get_logical_id_from_intrinsic(input), expected)

    @parameterized.expand(
        [
            (None,),
            ("Foo",),
            ({"Ref": True}),
            ({"Fn::GetAtt": "Foo"}),
            ({"Fn::GetAtt": ["Foo"]}),
            ({"Fn::GetAtt": [42, "Arn"]}),
            ({"Fn::If": ["Foo", "Bar"]}),
            ({"Fn::GetAtt": "Foo.Bar.WhatEverThisIs"},),
        ]
    )
    def test_get_logical_id_from_intrinsic_error(self, input):
        self.assertIsNone(get_logical_id_from_intrinsic(input))
