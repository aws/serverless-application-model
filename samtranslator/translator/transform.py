import copy
from functools import cache
from typing import Any

from samtranslator.feature_toggle.feature_toggle import FeatureToggle
from samtranslator.parser.parser import Parser
from samtranslator.translator.managed_policy_translator import ManagedPolicyLoader
from samtranslator.translator.translator import Translator
from samtranslator.utils.py27hash_fix import to_py27_compatible_template, undo_mark_unicode_str_in_template


def transform(
    input_fragment: dict[str, Any],
    parameter_values: dict[str, Any],
    managed_policy_loader: ManagedPolicyLoader,
    feature_toggle: FeatureToggle | None = None,
    passthrough_metadata: bool | None = False,
) -> dict[str, Any]:
    """Translates the SAM manifest provided in the and returns the translation to CloudFormation.

    :param dict input_fragment: the SAM template to transform
    :param dict parameter_values: Parameter values provided by the user
    :returns: the transformed CloudFormation template
    :rtype: dict
    """

    # Work on our own copies: the parser and plugins mutate the template in place --
    # Globals are merged into resource properties and the Globals section itself is
    # removed -- and to_py27_compatible_template() below mutates parameter_values in
    # place, replacing its values with Py27UniStr/Py27Dict/Py27LongInt wrappers.
    # Callers hand us objects they may still need afterwards, or may transform more
    # than once.
    #
    # Both copies are taken before to_py27_compatible_template() so that only plain
    # dicts and strings are copied. The Py27Dict/Py27UniStr wrappers that function
    # installs carry hash-ordering state that logical ID generation depends on, and
    # deep-copying them does not preserve it.
    input_fragment = copy.deepcopy(input_fragment)
    parameter_values = copy.deepcopy(parameter_values)

    sam_parser = Parser()
    to_py27_compatible_template(input_fragment, parameter_values)
    translator = Translator(
        None,
        sam_parser,
    )

    @cache
    def get_managed_policy_map() -> dict[str, str]:
        return managed_policy_loader.load()

    transformed = translator.translate(
        input_fragment,
        parameter_values=parameter_values,
        feature_toggle=feature_toggle,
        passthrough_metadata=passthrough_metadata,
        get_managed_policy_map=get_managed_policy_map,
    )
    return undo_mark_unicode_str_in_template(transformed)
