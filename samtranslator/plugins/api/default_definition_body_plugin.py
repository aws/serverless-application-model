from samtranslator.plugins import BasePlugin
from samtranslator.swagger.swagger import SwaggerEditor
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

    def on_before_transform_template(self, template_dict):
        """
        Hook method that gets called before the SAM template is processed.
        The template has passed the validation and is guaranteed to contain a non-empty "Resources" section.

        :param dict template_dict: Dictionary of the SAM template
        :return: Nothing
        """
        template = SamTemplate(template_dict)

        for logicalId, api in template.iterate(SamResourceType.Api.value):
            if api.properties.get('DefinitionBody') or api.properties.get('DefinitionUri'):
                continue

            api.properties['DefinitionBody'] = SwaggerEditor.gen_skeleton()
            api.properties['__MANAGE_SWAGGER'] = True
