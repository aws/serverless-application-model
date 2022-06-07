from samtranslator.model.intrinsics import make_conditional
from samtranslator.model.naming import GeneratedLogicalId
from samtranslator.plugins.api.implicit_api_plugin import ImplicitApiPlugin
from samtranslator.public.open_api import OpenApiEditor
from samtranslator.public.exceptions import InvalidEventException
from samtranslator.public.sdk.resource import SamResourceType, SamResource


class ImplicitHttpApiPlugin(ImplicitApiPlugin):
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

    def __init__(self):
        """
        Initializes the plugin
        """
        super(ImplicitHttpApiPlugin, self).__init__(ImplicitHttpApiPlugin.__name__)

    def _setup_api_properties(self):
        """
        Sets up properties that are distinct to this plugin
        """
        self.implicit_api_logical_id = GeneratedLogicalId.implicit_http_api()
        self.implicit_api_condition = "ServerlessHttpApiCondition"
        self.api_event_type = "HttpApi"
        self.api_type = SamResourceType.HttpApi.value
        self.api_id_property = "ApiId"
        self.editor = OpenApiEditor

    def _process_api_events(
        self, function, api_events, template, condition=None, deletion_policy=None, update_replace_policy=None
    ):
        """
        Actually process given HTTP API events. Iteratively adds the APIs to OpenApi JSON in the respective
        AWS::Serverless::HttpApi resource from the template

        :param SamResource function: SAM Function containing the API events to be processed
        :param dict api_events: Http API Events extracted from the function. These events will be processed
        :param SamTemplate template: SAM Template where AWS::Serverless::HttpApi resources can be found
        :param str condition: optional; this is the condition that is on the function with the API event
        """

        for logicalId, event in api_events.items():
            # api_events only contains HttpApi events
            event_properties = event.get("Properties", {})

            if not isinstance(event_properties, dict):
                raise InvalidEventException(
                    logicalId,
                    "Event 'Properties' must be an Object. If you're using YAML, this may be an indentation issue.",
                )

            if not event_properties:
                event["Properties"] = event_properties
            self._add_implicit_api_id_if_necessary(event_properties)

            api_id = self._get_api_id(event_properties)
            path = event_properties.get("Path", "")
            method = event_properties.get("Method", "")
            # If no path and method specified, add the $default path and ANY method
            if not path and not method:
                path = "$default"
                method = "x-amazon-apigateway-any-method"
                event_properties["Path"] = path
                event_properties["Method"] = method
            elif not path or not method:
                key = "Path" if not path else "Method"
                raise InvalidEventException(logicalId, "Event is missing key '{}'.".format(key))

            if not isinstance(path, str) or not isinstance(method, str):
                key = "Path" if not isinstance(path, str) else "Method"
                raise InvalidEventException(logicalId, "Api Event must have a String specified for '{}'.".format(key))

            # !Ref is resolved by this time. If it is not a string, we can't parse/use this Api.
            if api_id and not isinstance(api_id, str):
                raise InvalidEventException(
                    logicalId, "Api Event's ApiId must be a string referencing an Api in the same template."
                )

            api_dict_condition = self.api_conditions.setdefault(api_id, {})
            method_conditions = api_dict_condition.setdefault(path, {})
            method_conditions[method] = condition

            api_dict_deletion = self.api_deletion_policies.setdefault(api_id, set())
            api_dict_deletion.add(deletion_policy)

            api_dict_update_replace = self.api_update_replace_policies.setdefault(api_id, set())
            api_dict_update_replace.add(update_replace_policy)

            self._add_api_to_swagger(logicalId, event_properties, template)
            if "RouteSettings" in event_properties:
                self._add_route_settings_to_api(logicalId, event_properties, template, condition)
            api_events[logicalId] = event

        # We could have made changes to the Events structure. Write it back to function
        function.properties["Events"].update(api_events)

    def _add_implicit_api_id_if_necessary(self, event_properties):
        """
        Events for implicit APIs will *not* have the RestApiId property. Absence of this property means this event
        is associated with the AWS::Serverless::Api ImplicitAPI resource.
        This method solidifies this assumption by adding RestApiId property to events that don't have them.

        :param dict event_properties: Dictionary of event properties
        """
        if "ApiId" not in event_properties:
            event_properties["ApiId"] = {"Ref": self.implicit_api_logical_id}

    def _generate_implicit_api_resource(self):
        """
        Uses the implicit API in this file to generate an Implicit API resource
        """
        return ImplicitHttpApiResource().to_dict()

    def _get_api_definition_from_editor(self, editor):
        """
        Helper function to return the OAS definition from the editor
        """
        return editor.openapi

    def _get_api_resource_type_name(self):
        """
        Returns the type of API resource
        """
        return "AWS::Serverless::HttpApi"

    def _add_route_settings_to_api(self, event_id, event_properties, template, condition):
        """
        Adds the RouteSettings for this path/method from the given event to the RouteSettings configuration
        on the AWS::Serverless::HttpApi that this refers to.

        :param string event_id: LogicalId of the event
        :param dict event_properties: Properties of the event
        :param SamTemplate template: SAM Template to search for Serverless::HttpApi resources
        :param string condition: Condition on this HttpApi event (if any)
        """

        api_id = self._get_api_id(event_properties)
        resource = template.get(api_id)

        path = event_properties["Path"]
        method = event_properties["Method"]

        # Route should be in format "METHOD /path" or just "/path" if the ANY method is used
        route = "{} {}".format(method.upper(), path)
        if method == OpenApiEditor._X_ANY_METHOD:
            route = path

        # Handle Resource-level conditions if necessary
        api_route_settings = resource.properties.get("RouteSettings", {})
        event_route_settings = event_properties.get("RouteSettings", {})
        if condition:
            event_route_settings = make_conditional(condition, event_properties.get("RouteSettings", {}))

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

    def __init__(self):
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

        super(ImplicitHttpApiResource, self).__init__(resource)
