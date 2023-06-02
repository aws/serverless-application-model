from typing import Any, Dict, Optional, Type

from samtranslator.plugins.api.implicit_api_plugin import ImplicitApiPlugin
from samtranslator.public.sdk.resource import SamResource, SamResourceType
from samtranslator.public.swagger import SwaggerEditor
from samtranslator.sdk.template import SamTemplate
from samtranslator.validator.value_validator import sam_expect


class ImplicitRestApiPlugin(ImplicitApiPlugin[Type[SwaggerEditor]]):
    """
    This plugin provides Implicit API shorthand syntax in the SAM Spec.
    https://github.com/awslabs/serverless-application-model/blob/master/versions/2016-10-31.md#api

    Implicit API syntax is just a syntactic sugar, which will be translated to AWS::Serverless::Api resource.
    This is the only event source implemented as a plugin. Other event sources are not plugins because,
    DynamoDB event source, for example, is not creating the DynamoDB resource. It just adds
    a connection between the resource and Lambda. But with Implicit APIs, it creates and configures the API
    resource in addition to adding the connection. This plugin will simply tackle the resource creation
    bits and delegate the connection work to core translator.

    To sum up, here is the split of responsibilities:

    * This Plugin: Creates AWS::Serverless::Api and generates a Swagger with Methods, Paths, CORS, API Keys,
                   Usage Plans etc, essentially anything that configures API Gateway.

    * API Event Source (In Core Translator): ONLY adds the Lambda Integration ARN to appropriate method/path
                                             in Swagger. Does **not** configure the API by any means.
    """

    API_ID_EVENT_PROPERTY = "RestApiId"
    IMPLICIT_API_LOGICAL_ID = "ServerlessRestApi"
    IMPLICIT_API_CONDITION = "ServerlessRestApiCondition"
    API_EVENT_TYPE = "Api"
    SERVERLESS_API_RESOURCE_TYPE = SamResourceType.Api.value
    EDITOR_CLASS = SwaggerEditor

    def _process_api_events(  # noqa: too-many-arguments
        self,
        function: SamResource,
        api_events: Dict[str, Dict[str, Any]],
        template: SamTemplate,
        condition: Optional[str] = None,
        deletion_policy: Optional[str] = None,
        update_replace_policy: Optional[str] = None,
    ) -> None:
        """
        Actually process given API events. Iteratively adds the APIs to Swagger JSON in the respective Serverless::Api
        resource from the template

        :param SamResource function: SAM Function containing the API events to be processed
        :param dict api_events: API Events extracted from the function. These events will be processed
        :param SamTemplate template: SAM Template where Serverless::Api resources can be found
        :param str condition: optional; this is the condition that is on the function with the API event
        """

        for event_id, event in api_events.items():
            event_properties = event.get("Properties", {})
            if not event_properties:
                continue

            sam_expect(event_properties, event_id, "", is_sam_event=True).to_be_a_map("Properties should be a map.")

            self._add_tags_to_implicit_api_if_necessary(event_properties, function, template)

            self._add_implicit_api_id_if_necessary(event_properties)  # type: ignore[no-untyped-call]

            api_id, path, method = self._validate_api_event(event_id, event_properties)
            self._update_resource_attributes_from_api_event(
                api_id, path, method, condition, deletion_policy, update_replace_policy
            )

            self._add_api_to_swagger(event_id, event_properties, template)  # type: ignore[no-untyped-call]

            api_events[event_id] = event

        # We could have made changes to the Events structure. Write it back to function
        function.properties["Events"].update(api_events)

    def _generate_implicit_api_resource(self) -> Dict[str, Any]:
        """
        Uses the implicit API in this file to generate an Implicit API resource
        """
        return ImplicitApiResource().to_dict()

    def _get_api_definition_from_editor(self, editor: SwaggerEditor) -> Dict[str, Any]:
        """
        Helper function to return the OAS definition from the editor
        """
        return editor.swagger


class ImplicitApiResource(SamResource):
    """
    Returns a AWS::Serverless::Api resource representing the Implicit APIs. The returned resource includes
    the empty swagger along with default values for other properties.
    """

    def __init__(self) -> None:
        swagger = SwaggerEditor.gen_skeleton()

        resource = {
            "Type": SamResourceType.Api.value,
            "Properties": {
                # Because we set the StageName to be constant value here, customers cannot override StageName with
                # Globals. This is because, if a property is specified in both Globals and the resource, the resource
                # one takes precedence.
                "StageName": "Prod",
                "DefinitionBody": swagger,
                # Internal property that means Event source code can add Events. Used only for implicit APIs, to
                # prevent back compatibility issues for explicit APIs
                "__MANAGE_SWAGGER": True,
            },
        }

        super().__init__(resource)
