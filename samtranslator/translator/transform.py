from samtranslator.parser.parser import Parser
from samtranslator.translator.translator import Translator
from samtranslator.utils.py27hash_fix import to_py27_compatible_template, undo_mark_unicode_str_in_template


def transform(  # type: ignore[no-untyped-def]
    input_fragment,
    parameter_values,
    managed_policy_loader,
    feature_toggle=None,
    passthrough_metadata=False,
    get_managed_policy_map=None,
):
    """Translates the SAM manifest provided in the and returns the translation to CloudFormation.

    :param dict input_fragment: the SAM template to transform
    :param dict parameter_values: Parameter values provided by the user
    :returns: the transformed CloudFormation template
    :rtype: dict
    """

    sam_parser = Parser()
    to_py27_compatible_template(input_fragment, parameter_values)  # type: ignore[no-untyped-call]
    managed_policy_map = managed_policy_loader.load() if managed_policy_loader else None
    translator = Translator(managed_policy_map, sam_parser)  # type: ignore[no-untyped-call]
    transformed = translator.translate(
        input_fragment,
        parameter_values=parameter_values,
        feature_toggle=feature_toggle,
        passthrough_metadata=passthrough_metadata,
        get_managed_policy_map=get_managed_policy_map,
    )
    return undo_mark_unicode_str_in_template(transformed)  # type: ignore[no-untyped-call]
