from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.plugins import BasePlugin
from samtranslator.swagger.swagger import SwaggerEditor
from samtranslator.open_api.open_api import OpenApiEditor
from samtranslator.public.sdk.resource import SamResourceType
from samtranslator.public.sdk.template import SamTemplate


class DefaultDefinitionBodyPlugin(BasePlugin):
    """
    If the user does not provide a DefinitionBody or DefinitionUri
    on an AWS::Serverless::Api resource, the Swagger constructed by
    SAM is used. It accomplishes this by simply setting DefinitionBody
    to a minimum Swagger definition and sets `__MANAGE_SWAGGER: true`.
    """

    def __init__(self):
        """
        Initialize the plugin.
        """

        super(DefaultDefinitionBodyPlugin, self).__init__(DefaultDefinitionBodyPlugin.__name__)

    @cw_timer(prefix="Plugin-DefaultDefinitionBody")
    def on_before_transform_template(self, template_dict):
        """
        Hook method that gets called before the SAM template is processed.
        The template has passed the validation and is guaranteed to contain a non-empty "Resources" section.

        :param dict template_dict: Dictionary of the SAM template
        :return: Nothing
        """
        template = SamTemplate(template_dict)

        for api_type in [SamResourceType.Api.value, SamResourceType.HttpApi.value]:
            for logicalId, api in template.iterate({api_type}):
                if api.properties.get("DefinitionBody") or api.properties.get("DefinitionUri"):
                    continue

                if api_type is SamResourceType.HttpApi.value:
                    # If "Properties" is not set in the template, set them here
                    if not api.properties:
                        template.set(logicalId, api)
                    api.properties["DefinitionBody"] = OpenApiEditor.gen_skeleton()

                if api_type is SamResourceType.Api.value:
                    api.properties["DefinitionBody"] = SwaggerEditor.gen_skeleton()

                api.properties["__MANAGE_SWAGGER"] = True
