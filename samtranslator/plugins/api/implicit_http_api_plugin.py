from typing import Any, Dict, Optional, Type, cast

from samtranslator.model.intrinsics import make_conditional
from samtranslator.plugins.api.implicit_api_plugin import ImplicitApiPlugin
from samtranslator.public.open_api import OpenApiEditor
from samtranslator.public.sdk.resource import SamResource, SamResourceType
from samtranslator.sdk.template import SamTemplate
from samtranslator.validator.value_validator import sam_expect


class ImplicitHttpApiPlugin(ImplicitApiPlugin[Type[OpenApiEditor]]):
    """
    This plugin provides Implicit Http API shorthand syntax in the SAM Spec.

    Implicit API syntax is just a syntactic sugar, which will be translated to AWS::Serverless::HttpApi resource.
    This is the only event source implemented as a plugin. Other event sources are not plugins because,
    DynamoDB event source, for example, is not creating the DynamoDB resource. It just adds
    a connection between the resource and Lambda. But with Implicit APIs, it creates and configures the API
    resource in addition to adding the connection. This plugin will simply tackle the resource creation bits
    and delegate the connection work to core translator.

    To sum up, here is the split of responsibilities:
    * This Plugin: Creates AWS::Serverless::HttpApi and generates OpenApi with Methods, Paths, Auth, etc,
                                            essentially anything that configures API Gateway.
    * API Event Source (In Core Translator): ONLY adds the Lambda Integration ARN to appropriate method/path
                                             in OpenApi. Does **not** configure the API by any means.
    """

    API_ID_EVENT_PROPERTY = "ApiId"
    IMPLICIT_API_LOGICAL_ID = "ServerlessHttpApi"
    IMPLICIT_API_CONDITION = "ServerlessHttpApiCondition"
    API_EVENT_TYPE = "HttpApi"
    SERVERLESS_API_RESOURCE_TYPE = SamResourceType.HttpApi.value
    EDITOR_CLASS = OpenApiEditor

    def _process_api_events(  # noqa: PLR0913
        self,
        function: SamResource,
        api_events: Dict[str, Dict[str, Any]],
        template: SamTemplate,
        condition: Optional[str] = None,
        deletion_policy: Optional[str] = None,
        update_replace_policy: Optional[str] = None,
    ) -> None:
        """
        Actually process given HTTP API events. Iteratively adds the APIs to OpenApi JSON in the respective
        AWS::Serverless::HttpApi resource from the template

        :param SamResource function: SAM Function containing the API events to be processed
        :param dict api_events: Http API Events extracted from the function. These events will be processed
        :param SamTemplate template: SAM Template where AWS::Serverless::HttpApi resources can be found
        :param str condition: optional; this is the condition that is on the function with the API event
        """

        for event_id, event in api_events.items():
            # api_events only contains HttpApi events
            event_properties = event.get("Properties", {})

            sam_expect(event_properties, event_id, "", is_sam_event=True).to_be_a_map("Properties should be a map.")
            if not event_properties:
                event["Properties"] = event_properties  # We are updating its Properties

            self._add_tags_to_implicit_api_if_necessary(event_properties, function, template)

            self._add_implicit_api_id_if_necessary(event_properties)  # type: ignore[no-untyped-call]

            path = event_properties.get("Path", "")
            method = event_properties.get("Method", "")
            # If no path and method specified, add the $default path and ANY method
            if not path and not method:
                path = "$default"
                method = "x-amazon-apigateway-any-method"
                event_properties["Path"] = path
                event_properties["Method"] = method

            api_id, path, method = self._validate_api_event(event_id, event_properties)
            self._update_resource_attributes_from_api_event(
                api_id, path, method, condition, deletion_policy, update_replace_policy
            )

            self._add_api_to_swagger(event_id, event_properties, template)  # type: ignore[no-untyped-call]
            if "RouteSettings" in event_properties:
                self._add_route_settings_to_api(event_id, event_properties, template, condition)
            api_events[event_id] = event

        # We could have made changes to the Events structure. Write it back to function
        function.properties["Events"].update(api_events)

    def _generate_implicit_api_resource(self) -> Dict[str, Any]:
        """
        Uses the implicit API in this file to generate an Implicit API resource
        """
        return ImplicitHttpApiResource().to_dict()

    def _get_api_definition_from_editor(self, editor: OpenApiEditor) -> Dict[str, Any]:
        """
        Helper function to return the OAS definition from the editor
        """
        return editor.openapi

    def _add_route_settings_to_api(
        self, event_id: str, event_properties: Dict[str, Any], template: SamTemplate, condition: Optional[str]
    ) -> None:
        """
        Adds the RouteSettings for this path/method from the given event to the RouteSettings configuration
        on the AWS::Serverless::HttpApi that this refers to.

        :param string event_id: LogicalId of the event
        :param dict event_properties: Properties of the event
        :param SamTemplate template: SAM Template to search for Serverless::HttpApi resources
        :param string condition: Condition on this HttpApi event (if any)
        """

        api_id = self._get_api_id(event_properties)
        resource = cast(SamResource, template.get(api_id))  # TODO: make this not an assumption

        path = event_properties["Path"]
        method = event_properties["Method"]

        # Route should be in format "METHOD /path" or just "/path" if the ANY method is used
        route = f"{method.upper()} {path}"
        if method == OpenApiEditor._X_ANY_METHOD:
            route = path

        # Handle Resource-level conditions if necessary
        api_route_settings = resource.properties.get("RouteSettings", {})
        sam_expect(api_route_settings, api_id, "RouteSettings").to_be_a_map()
        event_route_settings = event_properties.get("RouteSettings", {})
        if condition:
            event_route_settings = make_conditional(condition, event_properties.get("RouteSettings", {}))
        sam_expect(event_route_settings, event_id, "RouteSettings", is_sam_event=True).to_be_a_map()

        # Merge event-level and api-level RouteSettings properties
        api_route_settings.setdefault(route, {})
        api_route_settings[route].update(event_route_settings)
        resource.properties["RouteSettings"] = api_route_settings
        template.set(api_id, resource)


class ImplicitHttpApiResource(SamResource):
    """
    Returns a AWS::Serverless::HttpApi resource representing the Implicit APIs. The returned resource
    includes the empty OpenApi along with default values for other properties.
    """

    def __init__(self) -> None:
        open_api = OpenApiEditor.gen_skeleton()

        resource = {
            "Type": SamResourceType.HttpApi.value,
            "Properties": {
                "DefinitionBody": open_api,
                # Internal property that means Event source code can add Events. Used only for implicit APIs, to
                # prevent back compatibility issues for explicit APIs
                "__MANAGE_SWAGGER": True,
            },
        }

        super().__init__(resource)
