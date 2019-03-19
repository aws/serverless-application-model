import copy
import six

from samtranslator.model.naming import GeneratedLogicalId
from samtranslator.model.intrinsics import make_combined_condition
from samtranslator.public.plugins import BasePlugin
from samtranslator.public.swagger import SwaggerEditor
from samtranslator.public.exceptions import InvalidDocumentException, InvalidResourceException, InvalidEventException
from samtranslator.public.sdk.resource import SamResourceType, SamResource
from samtranslator.public.sdk.template import SamTemplate


class ImplicitApiPlugin(BasePlugin):
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
        super(ImplicitApiPlugin, self).__init__(ImplicitApiPlugin.__name__)

        self.implicit_api_logical_id = GeneratedLogicalId.implicit_api()
        self.existing_implicit_api_resource = None
        # dict containing condition (or None) for each resource path+method for all APIs. dict format:
        # {api_id: {path: {method: condition_name_or_None}}}
        self.api_conditions = {}
        self.implicit_api_condition = 'ServerlessRestApiCondition'

    def on_before_transform_template(self, template_dict):
        """
        Hook method that gets called before the SAM template is processed.
        The template has pass the validation and is guaranteed to contain a non-empty "Resources" section.

        :param dict template_dict: Dictionary of the SAM template
        :return: Nothing
        """

        template = SamTemplate(template_dict)

        # Temporarily add Serverless::Api resource corresponding to Implicit API to the template.
        # This will allow the processing code to work the same way for both Implicit & Explicit APIs
        # If there are no implicit APIs, we will remove from the template later.

        # If the customer has explicitly defined a resource with the id of "ServerlessRestApi",
        # capture it.  If the template ends up not defining any implicit api's, instead of just
        # removing the "ServerlessRestApi" resource, we just restore what the author defined.
        self.existing_implicit_api_resource = copy.deepcopy(template.get(self.implicit_api_logical_id))

        template.set(self.implicit_api_logical_id, ImplicitApiResource().to_dict())

        errors = []
        for logicalId, function in template.iterate(SamResourceType.Function.value):

            api_events = self._get_api_events(function)
            condition = function.condition
            if len(api_events) == 0:
                continue

            try:
                self._process_api_events(function, api_events, template, condition)

            except InvalidEventException as ex:
                errors.append(InvalidResourceException(logicalId, ex.message))

        self._maybe_add_condition_to_implicit_api(template_dict)
        self._maybe_add_conditions_to_implicit_api_paths(template)
        self._maybe_remove_implicit_api(template)

        if len(errors) > 0:
            raise InvalidDocumentException(errors)

    def _get_api_events(self, function):
        """
        Method to return a dictionary of API Events on the function

        :param SamResource function: Function Resource object
        :return dict: Dictionary of API events along with any other configuration passed to it.
            Example: {
                FooEvent: {Path: "/foo", Method: "post", RestApiId: blah, MethodSettings: {<something>},
                            Cors: {<something>}, Auth: {<something>}},
                BarEvent: {Path: "/bar", Method: "any", MethodSettings: {<something>}, Cors: {<something>},
                            Auth: {<something>}}"
            }
        """

        if not (function.valid() and
                isinstance(function.properties, dict) and
                isinstance(function.properties.get("Events"), dict)
                ):
            # Function resource structure is invalid.
            return {}

        api_events = {}
        for event_id, event in function.properties["Events"].items():

            if event and isinstance(event, dict) and event.get("Type") == "Api":
                api_events[event_id] = event

        return api_events

    def _process_api_events(self, function, api_events, template, condition=None):
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

            self._add_implicit_api_id_if_necessary(event_properties)

            api_id = self._get_api_id(event_properties)
            try:
                path = event_properties["Path"]
                method = event_properties["Method"]
            except KeyError as e:
                raise InvalidEventException(logicalId, "Event is missing key {}.".format(e))

            if (not isinstance(path, six.string_types)):
                raise InvalidEventException(logicalId,
                                            "Api Event must have a String specified for 'Path'.")
            if (not isinstance(method, six.string_types)):
                raise InvalidEventException(logicalId,
                                            "Api Event must have a String specified for 'Method'.")

            api_dict = self.api_conditions.setdefault(api_id, {})
            method_conditions = api_dict.setdefault(path, {})
            method_conditions[method] = condition

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

    def _add_api_to_swagger(self, event_id, event_properties, template):
        """
        Adds the API path/method from the given event to the Swagger JSON of Serverless::Api resource this event
        refers to.

        :param string event_id: LogicalId of the event
        :param dict event_properties: Properties of the event
        :param SamTemplate template: SAM Template to search for Serverless::Api resources
        """

        # Need to grab the AWS::Serverless::Api resource for this API event and update its Swagger definition
        api_id = self._get_api_id(event_properties)

        # RestApiId is not pointing to a valid  API resource
        if isinstance(api_id, dict) or not template.get(api_id):
            raise InvalidEventException(event_id,
                                        "RestApiId must be a valid reference to an 'AWS::Serverless::Api' resource "
                                        "in same template")

        # Make sure Swagger is valid
        resource = template.get(api_id)
        if not (resource and
                isinstance(resource.properties, dict) and
                SwaggerEditor.is_valid(resource.properties.get("DefinitionBody"))):
            # This does not have an inline Swagger. Nothing can be done about it.
            return

        if not resource.properties.get("__MANAGE_SWAGGER"):
            # Do not add the api to Swagger, if the resource is not actively managed by SAM.
            # ie. Implicit API resources are created & managed by SAM on behalf of customers.
            # But for explicit API resources, customers write their own Swagger and manage it.
            # If a path is present in Events section but *not* present in the Explicit API Swagger, then it is
            # customer's responsibility to add to Swagger. We will not modify the Swagger here.
            #
            # In the future, we will might expose a flag that will allow SAM to manage explicit API Swagger as well.
            # Until then, we will not modify explicit explicit APIs.
            return

        swagger = resource.properties.get("DefinitionBody")

        path = event_properties["Path"]
        method = event_properties["Method"]
        editor = SwaggerEditor(swagger)
        editor.add_path(path, method)

        resource.properties["DefinitionBody"] = editor.swagger
        template.set(api_id, resource)

    def _get_api_id(self, event_properties):
        """
        Get API logical id from API event properties.

        Handles case where API id is not specified or is a reference to a logical id.
        """
        api_id = event_properties.get("RestApiId")
        if isinstance(api_id, dict) and "Ref" in api_id:
            api_id = api_id["Ref"]
        return api_id

    def _maybe_add_condition_to_implicit_api(self, template_dict):
        """
        Decides whether to add a condition to the implicit api resource.
        :param dict template_dict: SAM template dictionary
        """
        # Short-circuit if template doesn't have any functions with implicit API events
        if not self.api_conditions.get(self.implicit_api_logical_id, {}):
            return

        # Add a condition to the API resource IFF all of its resource+methods are associated with serverless functions
        # containing conditions.
        implicit_api_conditions = self.api_conditions[self.implicit_api_logical_id]
        all_resource_method_conditions = set([condition
                                              for path, method_conditions in implicit_api_conditions.items()
                                              for method, condition in method_conditions.items()])
        at_least_one_resource_method = len(all_resource_method_conditions) > 0
        all_resource_methods_contain_conditions = None not in all_resource_method_conditions
        if at_least_one_resource_method and all_resource_methods_contain_conditions:
            implicit_api_resource = template_dict.get('Resources').get(self.implicit_api_logical_id)
            if len(all_resource_method_conditions) == 1:
                condition = all_resource_method_conditions.pop()
                implicit_api_resource['Condition'] = condition
            else:
                # If multiple functions with multiple different conditions reference the Implicit Api, we need to
                # aggregate those conditions in order to conditionally create the Implicit Api. See RFC:
                # https://github.com/awslabs/serverless-application-model/issues/758
                implicit_api_resource['Condition'] = self.implicit_api_condition
                self._add_combined_condition_to_template(
                    template_dict, self.implicit_api_condition, all_resource_method_conditions)

    def _add_combined_condition_to_template(self, template_dict, condition_name, conditions_to_combine):
        """
        Add top-level template condition that combines the given list of conditions.

        :param dict template_dict: SAM template dictionary
        :param string condition_name: Name of top-level template condition
        :param list conditions_to_combine: List of conditions that should be combined (via OR operator) to form
                                           top-level condition.
        """
        # defensive precondition check
        if not conditions_to_combine or len(conditions_to_combine) < 2:
            raise ValueError('conditions_to_combine must have at least 2 conditions')

        template_conditions = template_dict.setdefault('Conditions', {})
        new_template_conditions = make_combined_condition(sorted(list(conditions_to_combine)), condition_name)
        for name, definition in new_template_conditions.items():
            template_conditions[name] = definition

    def _maybe_add_conditions_to_implicit_api_paths(self, template):
        """
        Add conditions to implicit API paths if necessary.

        Implicit API resource methods are constructed from API events on individual serverless functions within the SAM
        template. Since serverless functions can have conditions on them, it's possible to have a case where all methods
        under a resource path have conditions on them. If all of these conditions evaluate to false, the entire resource
        path should not be defined either. This method checks all resource paths' methods and if all methods under a
        given path contain a condition, a composite condition is added to the overall template Conditions section and
        that composite condition is added to the resource path.
        """

        for api_id, api in template.iterate(SamResourceType.Api.value):
            if not api.properties.get('__MANAGE_SWAGGER'):
                continue

            swagger = api.properties.get("DefinitionBody")
            editor = SwaggerEditor(swagger)

            for path in editor.iter_on_path():
                all_method_conditions = set(
                    [condition for method, condition in self.api_conditions[api_id][path].items()]
                )
                at_least_one_method = len(all_method_conditions) > 0
                all_methods_contain_conditions = None not in all_method_conditions
                if at_least_one_method and all_methods_contain_conditions:
                    if len(all_method_conditions) == 1:
                        editor.make_path_conditional(path, all_method_conditions.pop())
                    else:
                        path_condition_name = self._path_condition_name(api_id, path)
                        self._add_combined_condition_to_template(
                            template.template_dict, path_condition_name, all_method_conditions)
                        editor.make_path_conditional(path, path_condition_name)

            api.properties["DefinitionBody"] = editor.swagger
            template.set(api_id, api)

    def _path_condition_name(self, api_id, path):
        """
        Generate valid condition logical id from the given API logical id and swagger resource path.
        """
        # only valid characters for CloudFormation logical id are [A-Za-z0-9], but swagger paths can contain
        # slashes and curly braces for templated params, e.g., /foo/{customerId}. So we'll replace
        # non-alphanumeric characters.
        path_logical_id = path.replace('/', 'SLASH').replace('{', 'OB').replace('}', 'CB')
        return '{}{}PathCondition'.format(api_id, path_logical_id)

    def _maybe_remove_implicit_api(self, template):
        """
        Implicit API resource are tentatively added to the template for uniform handling of both Implicit & Explicit
        APIs. They need to removed from the template, if there are *no* API events attached to this resource.
        This method removes the Implicit API if it does not contain any Swagger paths (added in response to API events).

        :param SamTemplate template: SAM Template containing the Implicit API resource
        """

        # Remove Implicit API resource if no paths got added
        implicit_api_resource = template.get(self.implicit_api_logical_id)

        if implicit_api_resource and len(implicit_api_resource.properties["DefinitionBody"]["paths"]) == 0:
            # If there's no implicit api and the author defined a "ServerlessRestApi"
            # resource, restore it
            if self.existing_implicit_api_resource:
                template.set(self.implicit_api_logical_id, self.existing_implicit_api_resource)
            else:
                template.delete(self.implicit_api_logical_id)


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
                "__MANAGE_SWAGGER": True
            }
        }

        super(ImplicitApiResource, self).__init__(resource)
