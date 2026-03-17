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
