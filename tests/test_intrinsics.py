from parameterized import parameterized
from unittest import TestCase

from samtranslator.model.intrinsics import is_intrinsic, make_shorthand


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
