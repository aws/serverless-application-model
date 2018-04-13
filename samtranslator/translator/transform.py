from samtranslator.translator.translator import Translator
from samtranslator.parser.parser import Parser


def transform(input_fragment, parameter_values, managed_policy_loader):
    """Translates the SAM manifest provided in the and returns the translation to CloudFormation.

    :param dict input_fragment: the SAM template to transform
    :param dict parameter_values: Parameter values provided by the user
    :returns: the transformed CloudFormation template
    :rtype: dict
    """

    sam_parser = Parser()
    translator = Translator(managed_policy_loader.load(), sam_parser)
    return translator.translate(input_fragment, parameter_values=parameter_values)
