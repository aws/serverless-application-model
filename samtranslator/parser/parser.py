import logging

from samtranslator.model.exceptions import InvalidDocumentException, InvalidTemplateException, InvalidResourceException
from samtranslator.validator.validator import SamTemplateValidator
from samtranslator.plugins import LifeCycleEvents
from samtranslator.public.sdk.template import SamTemplate

LOG = logging.getLogger(__name__)


class Parser:
    def __init__(self):
        pass

    def parse(self, sam_template, parameter_values, sam_plugins):
        self._validate(sam_template, parameter_values)
        sam_plugins.act(LifeCycleEvents.before_transform_template, sam_template)

    @staticmethod
    def validate_datatypes(sam_template):
        """Validates the datatype within the template"""
        if (
            "Resources" not in sam_template
            or not isinstance(sam_template["Resources"], dict)
            or not sam_template["Resources"]
        ):
            raise InvalidDocumentException([InvalidTemplateException("'Resources' section is required")])

        if not all(isinstance(sam_resource, dict) for sam_resource in sam_template["Resources"].values()):
            raise InvalidDocumentException(
                [
                    InvalidTemplateException(
                        "All 'Resources' must be Objects. If you're using YAML, this may be an " "indentation issue."
                    )
                ]
            )

        sam_template_instance = SamTemplate(sam_template)

        for resource_logical_id, sam_resource in sam_template_instance.iterate():
            # NOTE: Properties isn't required for SimpleTable, so we can't check
            # `not isinstance(sam_resources.get("Properties"), dict)` as this would be a breaking change.
            # sam_resource.properties defaults to {} in SamTemplate init
            if not isinstance(sam_resource.properties, dict):
                raise InvalidDocumentException(
                    [
                        InvalidResourceException(
                            resource_logical_id,
                            "All 'Resources' must be Objects and have a 'Properties' Object. If "
                            "you're using YAML, this may be an indentation issue.",
                        )
                    ]
                )

    # private methods
    def _validate(self, sam_template, parameter_values):
        """Validates the template and parameter values and raises exceptions if there's an issue

        :param dict sam_template: SAM template
        :param dict parameter_values: Dictionary of parameter values provided by the user
        """
        if parameter_values is None:
            raise ValueError("`parameter_values` argument is required")

        Parser.validate_datatypes(sam_template)

        try:
            validator = SamTemplateValidator()
            validation_errors = validator.validate(sam_template)
            if validation_errors:
                LOG.warning("Template schema validation reported the following errors: %s", validation_errors)
        except Exception as e:
            # Catching any exception and not re-raising to make sure any validation process won't break transform
            LOG.exception("Exception from SamTemplateValidator: %s", e)
