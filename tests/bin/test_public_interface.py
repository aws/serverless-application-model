from unittest import TestCase

from bin.public_interface import _BreakingChanges, _detect_breaking_changes


class TestDetectBreakingChanges(TestCase):
    def test_missing_variables(self):
        self.assertEqual(
            _detect_breaking_changes(
                {},
                ["samtranslator.model.CONST_X", "samtranslator.model.CONST_Y"],
                {},
                ["samtranslator.model.CONST_X", "samtranslator.model.CONST_Z"],
            ),
            _BreakingChanges(
                deleted_variables=["samtranslator.model.CONST_Y"], deleted_routines=[], incompatible_routines=[]
            ),
        )

    def test_missing_routines(self):
        self.assertEqual(
            _detect_breaking_changes(
                {"samtranslator.model.do_something": []},
                [],
                {"samtranslator.model.do_something_2": []},
                [],
            ),
            _BreakingChanges(
                deleted_variables=[], deleted_routines=["samtranslator.model.do_something"], incompatible_routines=[]
            ),
        )

    def test_routines_still_compatible_when_adding_optional_arguments(self):
        self.assertEqual(
            _detect_breaking_changes(
                {"samtranslator.model.do_something": []},
                [],
                {
                    "samtranslator.model.do_something": [
                        {"name": "new_arg", "kind": "POSITIONAL_OR_KEYWORD", "default": False},
                        {"name": "new_arg_2", "kind": "POSITIONAL_OR_KEYWORD", "default": None},
                    ]
                },
                [],
            ),
            _BreakingChanges(deleted_variables=[], deleted_routines=[], incompatible_routines=[]),
        )

    def test_routines_still_compatible_when_optionalize_existing_arguments(self):
        self.assertEqual(
            _detect_breaking_changes(
                {
                    "samtranslator.model.do_something": [
                        {
                            "name": "arg",
                            "kind": "POSITIONAL_OR_KEYWORD",
                        },
                        {
                            "name": "arg_2",
                            "kind": "POSITIONAL_OR_KEYWORD",
                        },
                    ]
                },
                [],
                {
                    "samtranslator.model.do_something": [
                        {"name": "arg", "kind": "POSITIONAL_OR_KEYWORD", "default": False},
                        {"name": "arg_2", "kind": "POSITIONAL_OR_KEYWORD", "default": None},
                    ]
                },
                [],
            ),
            _BreakingChanges(deleted_variables=[], deleted_routines=[], incompatible_routines=[]),
        )

    def test_routines_still_compatible_when_adding_var_arguments(self):
        self.assertEqual(
            _detect_breaking_changes(
                {"samtranslator.model.do_something": []},
                [],
                {
                    "samtranslator.model.do_something": [
                        {"name": "args", "kind": "VAR_POSITIONAL"},
                        {"name": "kwargs", "kind": "VAR_KEYWORD"},
                    ]
                },
                [],
            ),
            _BreakingChanges(deleted_variables=[], deleted_routines=[], incompatible_routines=[]),
        )

    def test_routines_still_compatible_when_converting_from_method_to_staticmethod(self):
        self.assertEqual(
            _detect_breaking_changes(
                {
                    "samtranslator.model.do_something": [
                        {"kind": "POSITIONAL_OR_KEYWORD", "name": "self"},
                        {"name": "some_arg", "kind": "POSITIONAL_OR_KEYWORD"},
                    ]
                },
                [],
                {"samtranslator.model.do_something": [{"name": "some_arg", "kind": "POSITIONAL_OR_KEYWORD"}]},
                [],
            ),
            _BreakingChanges(deleted_variables=[], deleted_routines=[], incompatible_routines=[]),
        )

    def test_routines_still_compatible_when_converting_from_method_to_staticmethod_and_adding_optional_arguments(self):
        self.assertEqual(
            _detect_breaking_changes(
                {
                    "samtranslator.model.do_something": [
                        {"kind": "POSITIONAL_OR_KEYWORD", "name": "self"},
                        {"name": "some_arg", "kind": "POSITIONAL_OR_KEYWORD"},
                    ]
                },
                [],
                {
                    "samtranslator.model.do_something": [
                        {"name": "some_arg", "kind": "POSITIONAL_OR_KEYWORD"},
                        {"name": "new_arg", "kind": "POSITIONAL_OR_KEYWORD", "default": False},
                        {"name": "new_arg_2", "kind": "POSITIONAL_OR_KEYWORD", "default": None},
                    ]
                },
                [],
            ),
            _BreakingChanges(deleted_variables=[], deleted_routines=[], incompatible_routines=[]),
        )

    def test_routines_incompatible_when_changing_default_value(self):
        self.assertEqual(
            _detect_breaking_changes(
                {
                    "samtranslator.model.do_something": [
                        {"kind": "POSITIONAL_OR_KEYWORD", "name": "self"},
                        {"name": "some_arg", "kind": "POSITIONAL_OR_KEYWORD", "default": 0},
                    ]
                },
                [],
                {
                    "samtranslator.model.do_something": [
                        {"kind": "POSITIONAL_OR_KEYWORD", "name": "self"},
                        {"name": "some_arg", "kind": "POSITIONAL_OR_KEYWORD", "default": 1},
                    ]
                },
                [],
            ),
            _BreakingChanges(
                deleted_variables=[], deleted_routines=[], incompatible_routines=["samtranslator.model.do_something"]
            ),
        )

    def test_routines_incompatible_when_add_new_arguments(self):
        self.assertEqual(
            _detect_breaking_changes(
                {
                    "samtranslator.model.do_something": [
                        {"kind": "POSITIONAL_OR_KEYWORD", "name": "self"},
                        {"name": "some_arg", "kind": "POSITIONAL_OR_KEYWORD"},
                    ]
                },
                [],
                {
                    "samtranslator.model.do_something": [
                        {"kind": "POSITIONAL_OR_KEYWORD", "name": "self"},
                        {"name": "some_arg", "kind": "POSITIONAL_OR_KEYWORD"},
                        {"name": "new_arg", "kind": "POSITIONAL_OR_KEYWORD"},
                    ]
                },
                [],
            ),
            _BreakingChanges(
                deleted_variables=[], deleted_routines=[], incompatible_routines=["samtranslator.model.do_something"]
            ),
        )
