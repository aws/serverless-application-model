import logging
from typing import Any, Dict

from samtranslator.model.exceptions import (
    InvalidDocumentException,
    InvalidResourceAttributeTypeException,
    InvalidTemplateException,
)
from samtranslator.plugins import LifeCycleEvents
from samtranslator.plugins.sam_plugins import SamPlugins
from samtranslator.public.sdk.template import SamTemplate
from samtranslator.validator.value_validator import sam_expect

LOG = logging.getLogger(__name__)


class Parser:
    def __init__(self) -> None:
        pass

    def parse(self, sam_template: Dict[str, Any], parameter_values: Dict[str, Any], sam_plugins: SamPlugins) -> None:
        self._validate(sam_template, parameter_values)  # type: ignore[no-untyped-call]
        sam_plugins.act(LifeCycleEvents.before_transform_template, sam_template)

    @staticmethod
    def validate_datatypes(sam_template):  # type: ignore[no-untyped-def]
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
                        "All 'Resources' must be Objects. If you're using YAML, this may be an indentation issue."
                    )
                ]
            )

        sam_template_instance = SamTemplate(sam_template)

        for resource_logical_id, sam_resource in sam_template_instance.iterate():
            # NOTE: Properties isn't required for SimpleTable, so we can't check
            # `not isinstance(sam_resources.get("Properties"), dict)` as this would be a breaking change.
            # sam_resource.properties defaults to {} in SamTemplate init
            try:
                sam_expect(
                    sam_resource.properties, resource_logical_id, "Properties", is_resource_attribute=True
                ).to_be_a_map()
            except InvalidResourceAttributeTypeException as e:
                raise InvalidDocumentException([e]) from e

    # private methods
    def _validate(self, sam_template, parameter_values):  # type: ignore[no-untyped-def]
        """Validates the template and parameter values and raises exceptions if there's an issue

        :param dict sam_template: SAM template
        :param dict parameter_values: Dictionary of parameter values provided by the user
        """
        if parameter_values is None:
            raise ValueError("`parameter_values` argument is required")

        Parser.validate_datatypes(sam_template)  # type: ignore[no-untyped-call]
