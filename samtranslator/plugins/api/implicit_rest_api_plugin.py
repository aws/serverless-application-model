from samtranslator.model.naming import GeneratedLogicalId
from samtranslator.plugins.api.implicit_api_plugin import ImplicitApiPlugin
from samtranslator.public.swagger import SwaggerEditor
from samtranslator.public.exceptions import InvalidEventException
from samtranslator.public.sdk.resource import SamResourceType, SamResource


class ImplicitRestApiPlugin(ImplicitApiPlugin):
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

    def __init__(self):
        """
        Initialize the plugin
        """
        super(ImplicitRestApiPlugin, self).__init__(ImplicitRestApiPlugin.__name__)

    def _setup_api_properties(self):
        """
        Sets up properties that are distinct to this plugin
        """
        self.implicit_api_logical_id = GeneratedLogicalId.implicit_api()
        self.implicit_api_condition = "ServerlessRestApiCondition"
        self.api_event_type = "Api"
        self.api_type = SamResourceType.Api.value
        self.api_id_property = "RestApiId"
        self.editor = SwaggerEditor

    def _process_api_events(
        self, function, api_events, template, condition=None, deletion_policy=None, update_replace_policy=None
    ):
        """
        Actually process given API events. Iteratively adds the APIs to Swagger JSON in the respective Serverless::Api
        resource from the template

        :param SamResource function: SAM Function containing the API events to be processed
        :param dict api_events: API Events extracted from the function. These events will be processed
        :param SamTemplate template: SAM Template where Serverless::Api resources can be found
        :param str condition: optional; this is the condition that is on the function with the API event
        """

        for logicalId, event in api_events.items():

            event_properties = event.get("Properties", {})
            if not event_properties:
                continue

            if not isinstance(event_properties, dict):
                raise InvalidEventException(
                    logicalId,
                    "Event 'Properties' must be an Object. If you're using YAML, this may be an indentation issue.",
                )

            self._add_implicit_api_id_if_necessary(event_properties)

            api_id = self._get_api_id(event_properties)
            try:
                path = event_properties["Path"]
                method = event_properties["Method"]
            except KeyError as e:
                raise InvalidEventException(logicalId, "Event is missing key {}.".format(e))

            if not isinstance(path, str):
                raise InvalidEventException(logicalId, "Api Event must have a String specified for 'Path'.")
            if not isinstance(method, str):
                raise InvalidEventException(logicalId, "Api Event must have a String specified for 'Method'.")

            # !Ref is resolved by this time. If it is not a string, we can't parse/use this Api.
            if api_id and not isinstance(api_id, str):
                raise InvalidEventException(
                    logicalId, "Api Event's RestApiId must be a string referencing an Api in the same template."
                )

            api_dict_condition = self.api_conditions.setdefault(api_id, {})
            method_conditions = api_dict_condition.setdefault(path, {})
            method_conditions[method] = condition

            api_dict_deletion = self.api_deletion_policies.setdefault(api_id, set())
            api_dict_deletion.add(deletion_policy)

            api_dict_update_replace = self.api_update_replace_policies.setdefault(api_id, set())
            api_dict_update_replace.add(update_replace_policy)

            self._add_api_to_swagger(logicalId, event_properties, template)

            api_events[logicalId] = event

        # We could have made changes to the Events structure. Write it back to function
        function.properties["Events"].update(api_events)

    def _add_implicit_api_id_if_necessary(self, event_properties):
        """
        Events for implicit APIs will *not* have the RestApiId property. Absence of this property means this event
        is associated with the Serverless::Api ImplicitAPI resource. This method solifies this assumption by adding
        RestApiId property to events that don't have them.

        :param dict event_properties: Dictionary of event properties
        """
        if "RestApiId" not in event_properties:
            event_properties["RestApiId"] = {"Ref": self.implicit_api_logical_id}

    def _generate_implicit_api_resource(self):
        """
        Uses the implicit API in this file to generate an Implicit API resource
        """
        return ImplicitApiResource().to_dict()

    def _get_api_definition_from_editor(self, editor):
        """
        Helper function to return the OAS definition from the editor
        """
        return editor.swagger

    def _get_api_resource_type_name(self):
        """
        Returns the type of API resource
        """
        return "AWS::Serverless::Api"


class ImplicitApiResource(SamResource):
    """
    Returns a AWS::Serverless::Api resource representing the Implicit APIs. The returned resource includes
    the empty swagger along with default values for other properties.
    """

    def __init__(self):
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

        super(ImplicitApiResource, self).__init__(resource)
