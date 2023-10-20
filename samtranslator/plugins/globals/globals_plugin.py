from typing import Any, Dict

from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.model.exceptions import InvalidResourceAttributeTypeException
from samtranslator.plugins.globals.globals import Globals, InvalidGlobalsSectionException
from samtranslator.public.exceptions import InvalidDocumentException
from samtranslator.public.plugins import BasePlugin
from samtranslator.public.sdk.template import SamTemplate

_API_RESOURCE = "AWS::Serverless::Api"


class GlobalsPlugin(BasePlugin):
    """
    Plugin to process Globals section of a SAM template before the template is translated to CloudFormation.
    """

    @cw_timer(prefix="Plugin-Globals")
    def on_before_transform_template(self, template_dict: Dict[str, Any]) -> None:
        """
        Hook method that runs before a template gets transformed. In this method, we parse and process Globals section
        from the template (if present).

        :param dict template_dict: SAM template as a dictionary
        """
        try:
            global_section = Globals(template_dict)
        except InvalidGlobalsSectionException as ex:
            raise InvalidDocumentException([ex]) from ex

        # For each resource in template, try and merge with Globals if necessary
        template = SamTemplate(template_dict)
        for logicalId, resource in template.iterate():
            try:
                resource.properties = global_section.merge(
                    str(resource.type), resource.properties, logicalId, resource.ignore_globals
                )
            except InvalidResourceAttributeTypeException as ex:
                raise InvalidDocumentException([ex]) from ex
            template.set(logicalId, resource)

        # Remove the Globals section from template if necessary
        Globals.del_section(template_dict)

        # If there was a global openApiVersion flag, check and convert swagger
        # to the right version
        Globals.fix_openapi_definitions(template_dict)
