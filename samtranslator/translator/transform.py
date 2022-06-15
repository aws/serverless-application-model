from samtranslator.translator.translator import Translator
from samtranslator.parser.parser import Parser
from samtranslator.utils.py27hash_fix import to_py27_compatible_template, undo_mark_unicode_str_in_template


def transform(input_fragment, parameter_values, managed_policy_loader, feature_toggle=None, passthrough_metadata=False):
    """Translates the SAM manifest provided in the and returns the translation to CloudFormation.

    :param dict input_fragment: the SAM template to transform
    :param dict parameter_values: Parameter values provided by the user
    :returns: the transformed CloudFormation template
    :rtype: dict
    """

    sam_parser = Parser()
    to_py27_compatible_template(input_fragment, parameter_values)
    translator = Translator(managed_policy_loader.load(), sam_parser)
    transformed = translator.translate(
        input_fragment,
        parameter_values=parameter_values,
        feature_toggle=feature_toggle,
        passthrough_metadata=passthrough_metadata,
    )
    transformed = undo_mark_unicode_str_in_template(transformed)
    return transformed
