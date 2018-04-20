from samtranslator.model.exceptions import InvalidDocumentException, InvalidTemplateException, InvalidResourceException, InvalidEventException, DuplicateLogicalIdException
from samtranslator.validator.validator import SamTemplateValidator
from samtranslator.model import ResourceTypeResolver, sam_resources
from samtranslator.plugins import LifeCycleEvents

class Parser:
    def __init__(self):
        pass

    def parse(self, sam_template, parameter_values, sam_plugins):
        self._validate(sam_template, parameter_values)
        sam_plugins.act(LifeCycleEvents.before_transform_template, sam_template)

    # private methods
    def _validate(self, sam_template, parameter_values):
        """ Validates the template and parameter values and raises exceptions if there's an issue

        :param dict sam_template: SAM template
        :param dict parameter_values: Dictionary of parameter values provided by the user
        """
        if parameter_values is None:
            raise ValueError("`parameter_values` argument is required")

        if "Resources" not in sam_template or not isinstance(sam_template["Resources"], dict) or not sam_template["Resources"]:
            raise InvalidDocumentException(
                [InvalidTemplateException("'Resources' section is required")])

        SamTemplateValidator.validate(sam_template)
