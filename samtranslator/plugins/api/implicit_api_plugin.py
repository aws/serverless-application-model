import copy
from abc import ABCMeta, abstractmethod
from typing import Any, Dict, Generic, Optional, Tuple, Type, TypeVar, Union

from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.model.eventsources.push import Api
from samtranslator.model.intrinsics import MIN_NUM_CONDITIONS_TO_COMBINE, make_combined_condition
from samtranslator.open_api.open_api import OpenApiEditor
from samtranslator.public.exceptions import InvalidDocumentException, InvalidEventException, InvalidResourceException
from samtranslator.public.plugins import BasePlugin
from samtranslator.public.sdk.resource import SamResource, SamResourceType
from samtranslator.public.sdk.template import SamTemplate
from samtranslator.swagger.swagger import SwaggerEditor
from samtranslator.utils.py27hash_fix import Py27Dict
from samtranslator.validator.value_validator import sam_expect

T = TypeVar("T", bound=Union[Type[OpenApiEditor], Type[SwaggerEditor]])


class ImplicitApiPlugin(BasePlugin, Generic[T], metaclass=ABCMeta):
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

    # Name of the event property name to referring api id in the event source.
    API_ID_EVENT_PROPERTY: str
    # The logical id of the implicit API resource
    IMPLICIT_API_LOGICAL_ID: str
    IMPLICIT_API_CONDITION: str
    API_EVENT_TYPE: str
    SERVERLESS_API_RESOURCE_TYPE: str
    EDITOR_CLASS: T

    def __init__(self) -> None:
        """
        Initialize the plugin.
        """
        super().__init__()

        self.existing_implicit_api_resource: Optional[SamResource] = None
        # dict containing condition (or None) for each resource path+method for all APIs. dict format:
        # {api_id: {path: {method: condition_name_or_None}}}
        self.api_conditions: Dict[str, Any] = {}
        self.api_deletion_policies: Dict[str, Any] = {}
        self.api_update_replace_policies: Dict[str, Any] = {}

    @abstractmethod
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

        :param SamResource function: SAM function containing the API events to be processed
        :param dict api_events: API Events extracted from the function. These events will be processed
        :param SamTemplate template: SAM Template where Serverless::Api resources can be found
        :param str condition: optional; this is the condition that is on the resource with the API event
        """

    @abstractmethod
    def _get_api_definition_from_editor(self, editor):  # type: ignore[no-untyped-def]
        """
        Required function that returns the api body from the respective editor
        """

    @abstractmethod
    def _generate_implicit_api_resource(self) -> Dict[str, Any]:
        """
        Helper function implemented by child classes that create a new implicit API resource
        """

    @cw_timer(prefix="Plugin-ImplicitApi")
    def on_before_transform_template(self, template_dict):  # type: ignore[no-untyped-def]
        """
        Hook method that gets called before the SAM template is processed.
        The template has pass the validation and is guaranteed to contain a non-empty "Resources" section.

        :param dict template_dict: Dictionary of the SAM template
        """

        template = SamTemplate(template_dict)

        # Temporarily add Serverless::Api resource corresponding to Implicit API to the template.
        # This will allow the processing code to work the same way for both Implicit & Explicit APIs
        # If there are no implicit APIs, we will remove from the template later.

        # If the customer has explicitly defined a resource with the id of "ServerlessRestApi",
        # capture it.  If the template ends up not defining any implicit api's, instead of just
        # removing the "ServerlessRestApi" resource, we just restore what the author defined.
        self.existing_implicit_api_resource = copy.deepcopy(template.get(self.IMPLICIT_API_LOGICAL_ID))

        template.set(self.IMPLICIT_API_LOGICAL_ID, self._generate_implicit_api_resource())

        errors = []
        for logicalId, resource in template.iterate(
            {SamResourceType.Function.value, SamResourceType.StateMachine.value}
        ):
            api_events = self._get_api_events(resource)  # type: ignore[no-untyped-call]
            condition = resource.condition
            deletion_policy = resource.deletion_policy
            update_replace_policy = resource.update_replace_policy
            if len(api_events) == 0:
                continue

            try:
                self._process_api_events(
                    resource, api_events, template, condition, deletion_policy, update_replace_policy
                )

            except InvalidEventException as ex:
                errors.append(InvalidResourceException(logicalId, ex.message))

        self._maybe_add_condition_to_implicit_api(template_dict)  # type: ignore[no-untyped-call]
        self._maybe_add_deletion_policy_to_implicit_api(template_dict)  # type: ignore[no-untyped-call]
        self._maybe_add_update_replace_policy_to_implicit_api(template_dict)  # type: ignore[no-untyped-call]
        self._maybe_add_conditions_to_implicit_api_paths(template)  # type: ignore[no-untyped-call]
        self._maybe_remove_implicit_api(template)  # type: ignore[no-untyped-call]

        if len(errors) > 0:
            raise InvalidDocumentException(errors)

    def _add_implicit_api_id_if_necessary(self, event_properties):  # type: ignore[no-untyped-def]
        """
        Events for implicit APIs will *not* have the RestApiId property. Absence of this property means this event
        is associated with the Serverless::Api ImplicitAPI resource. This method solifies this assumption by adding
        RestApiId property to events that don't have them.

        :param dict event_properties: Dictionary of event properties
        """
        if self.API_ID_EVENT_PROPERTY not in event_properties:
            event_properties[self.API_ID_EVENT_PROPERTY] = {"Ref": self.IMPLICIT_API_LOGICAL_ID}

    def _get_api_events(self, resource):  # type: ignore[no-untyped-def]
        """
        Method to return a dictionary of API Events on the resource

        :param SamResource resource: SAM Resource object
        :return dict: Dictionary of API events along with any other configuration passed to it.
            Example: {
                FooEvent: {Path: "/foo", Method: "post", RestApiId: blah, MethodSettings: {<something>},
                            Cors: {<something>}, Auth: {<something>}},
                BarEvent: {Path: "/bar", Method: "any", MethodSettings: {<something>}, Cors: {<something>},
                            Auth: {<something>}}"
            }
        """

        if not (
            resource.valid()
            and isinstance(resource.properties, dict)
            and isinstance(resource.properties.get("Events"), dict)
        ):
            # Resource structure is invalid.
            return Py27Dict()

        api_events = Py27Dict()
        for event_id, event in resource.properties["Events"].items():
            if event and isinstance(event, dict) and event.get("Type") == self.API_EVENT_TYPE:
                api_events[event_id] = event

        return api_events

    def _add_api_to_swagger(self, event_id, event_properties, template):  # type: ignore[no-untyped-def]
        """
        Adds the API path/method from the given event to the Swagger JSON of Serverless::Api resource this event
        refers to.

        :param string event_id: LogicalId of the event
        :param dict event_properties: Properties of the event
        :param SamTemplate template: SAM Template to search for Serverless::Api resources
        """

        # Need to grab the AWS::Serverless::Api resource for this API event and update its Swagger definition
        api_id = self._get_api_id(event_properties)

        # As of right now, this is for backwards compatability. SAM fails if you have an event type "Api" but that
        # references "AWS::Serverless::HttpApi". If you do the opposite, SAM still outputs a valid template. Example of that
        # can be found https://github.com/aws/serverless-application-model/blob/develop/tests/translator/output/api_with_any_method_in_swagger.json.
        # One would argue that, this is unexpected and should actually fail. Instead of suddenly breaking customers in this
        # position, we added a check to make sure the Plugin run (Http or Rest) is referencing an api of the same type.
        is_referencing_http_from_api_event = (
            not template.get(api_id)
            or template.get(api_id).type == "AWS::Serverless::HttpApi"
            and template.get(api_id).type != self.SERVERLESS_API_RESOURCE_TYPE
        )

        # RestApiId is not pointing to a valid API resource
        if isinstance(api_id, dict) or is_referencing_http_from_api_event:
            raise InvalidEventException(
                event_id,
                f"{self.API_ID_EVENT_PROPERTY} must be a valid reference to an '{self.SERVERLESS_API_RESOURCE_TYPE}'"
                " resource in same template.",
            )

        # Make sure Swagger is valid
        resource = template.get(api_id)
        if not (
            resource
            and isinstance(resource.properties, dict)
            and self.EDITOR_CLASS.is_valid(resource.properties.get("DefinitionBody"))
        ):
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
        editor = self.EDITOR_CLASS(swagger)
        editor.add_path(path, method)

        resource.properties["DefinitionBody"] = self._get_api_definition_from_editor(editor)  # type: ignore[no-untyped-call]
        template.set(api_id, resource)

    def _get_api_id(self, event_properties: Dict[str, Any]) -> Any:
        """
        Get API logical id from API event properties.

        Handles case where API id is not specified or is a reference to a logical id.
        """
        api_id = event_properties.get(self.API_ID_EVENT_PROPERTY)
        return Api.get_rest_api_id_string(api_id)

    def _maybe_add_condition_to_implicit_api(self, template_dict):  # type: ignore[no-untyped-def]
        """
        Decides whether to add a condition to the implicit api resource.
        :param dict template_dict: SAM template dictionary
        """
        # Short-circuit if template doesn't have any functions with implicit API events
        if not self.api_conditions.get(self.IMPLICIT_API_LOGICAL_ID, {}):
            return

        # Add a condition to the API resource IFF all of its resource+methods are associated with serverless functions
        # containing conditions.
        implicit_api_conditions = self.api_conditions[self.IMPLICIT_API_LOGICAL_ID]
        all_resource_method_conditions = {
            condition
            for _, method_conditions in implicit_api_conditions.items()
            for _, condition in method_conditions.items()
        }
        at_least_one_resource_method = len(all_resource_method_conditions) > 0
        all_resource_methods_contain_conditions = None not in all_resource_method_conditions
        if at_least_one_resource_method and all_resource_methods_contain_conditions:
            implicit_api_resource = template_dict.get("Resources").get(self.IMPLICIT_API_LOGICAL_ID)
            if len(all_resource_method_conditions) == 1:
                condition = all_resource_method_conditions.pop()
                implicit_api_resource["Condition"] = condition
            else:
                # If multiple functions with multiple different conditions reference the Implicit Api, we need to
                # aggregate those conditions in order to conditionally create the Implicit Api. See RFC:
                # https://github.com/awslabs/serverless-application-model/issues/758
                implicit_api_resource["Condition"] = self.IMPLICIT_API_CONDITION
                self._add_combined_condition_to_template(  # type: ignore[no-untyped-call]
                    template_dict, self.IMPLICIT_API_CONDITION, all_resource_method_conditions
                )

    def _maybe_add_deletion_policy_to_implicit_api(self, template_dict):  # type: ignore[no-untyped-def]
        """
        Decides whether to add a deletion policy to the implicit api resource.
        :param dict template_dict: SAM template dictionary
        """
        # Short-circuit if template doesn't have any functions with implicit API events
        implicit_api_deletion_policies = self.api_deletion_policies.get(self.IMPLICIT_API_LOGICAL_ID)
        if not implicit_api_deletion_policies:
            return

        # Add a deletion policy to the API resource if its resources contains DeletionPolicy.
        at_least_one_resource_method = len(implicit_api_deletion_policies) > 0
        one_resource_method_contains_deletion_policy = False
        contains_retain = False
        contains_delete = False
        # If multiple functions with multiple different policies reference the Implicit Api,
        # we set DeletionPolicy to Retain if Retain is present in one of the functions,
        # else Delete if Delete is present
        for iterated_policy in implicit_api_deletion_policies:
            if iterated_policy:
                one_resource_method_contains_deletion_policy = True
                if iterated_policy == "Retain":
                    contains_retain = True
                if iterated_policy == "Delete":
                    contains_delete = True
        if at_least_one_resource_method and one_resource_method_contains_deletion_policy:
            implicit_api_resource = template_dict.get("Resources").get(self.IMPLICIT_API_LOGICAL_ID)
            if contains_retain:
                implicit_api_resource["DeletionPolicy"] = "Retain"
            elif contains_delete:
                implicit_api_resource["DeletionPolicy"] = "Delete"

    def _maybe_add_update_replace_policy_to_implicit_api(self, template_dict):  # type: ignore[no-untyped-def]
        """
        Decides whether to add an update replace policy to the implicit api resource.
        :param dict template_dict: SAM template dictionary
        """
        # Short-circuit if template doesn't have any functions with implicit API events
        implicit_api_update_replace_policies = self.api_update_replace_policies.get(self.IMPLICIT_API_LOGICAL_ID)
        if not implicit_api_update_replace_policies:
            return

        # Add a update replace policy to the API resource if its resources contains UpdateReplacePolicy.
        at_least_one_resource_method = len(implicit_api_update_replace_policies) > 0
        one_resource_method_contains_update_replace_policy = False
        contains_retain = False
        contains_snapshot = False
        contains_delete = False
        # If multiple functions with multiple different policies reference the Implicit Api,
        # we set UpdateReplacePolicy to Retain if Retain is present in one of the functions,
        # Snapshot if Snapshot is present, else Delete if Delete is present
        for iterated_policy in implicit_api_update_replace_policies:
            if iterated_policy:
                one_resource_method_contains_update_replace_policy = True
                if iterated_policy == "Retain":
                    contains_retain = True
                if iterated_policy == "Snapshot":
                    contains_snapshot = True
                if iterated_policy == "Delete":
                    contains_delete = True
        if at_least_one_resource_method and one_resource_method_contains_update_replace_policy:
            implicit_api_resource = template_dict.get("Resources").get(self.IMPLICIT_API_LOGICAL_ID)
            if contains_retain:
                implicit_api_resource["UpdateReplacePolicy"] = "Retain"
            elif contains_snapshot:
                implicit_api_resource["UpdateReplacePolicy"] = "Snapshot"
            elif contains_delete:
                implicit_api_resource["UpdateReplacePolicy"] = "Delete"

    def _add_combined_condition_to_template(self, template_dict, condition_name, conditions_to_combine):  # type: ignore[no-untyped-def]
        """
        Add top-level template condition that combines the given list of conditions.

        :param dict template_dict: SAM template dictionary
        :param string condition_name: Name of top-level template condition
        :param list conditions_to_combine: List of conditions that should be combined (via OR operator) to form
                                           top-level condition.
        """
        # defensive precondition check
        if not conditions_to_combine or len(conditions_to_combine) < MIN_NUM_CONDITIONS_TO_COMBINE:
            raise ValueError("conditions_to_combine must have at least 2 conditions")

        template_conditions = template_dict.setdefault("Conditions", {})
        new_template_conditions = make_combined_condition(sorted(conditions_to_combine), condition_name)
        # make_combined_condition() won't return None if `conditions_to_combine` has at least 2 elements,
        # which is checked above.
        # TODO: refactor the code to make the length check in one place only.
        for name, definition in new_template_conditions.items():  # type: ignore
            template_conditions[name] = definition

    def _maybe_add_conditions_to_implicit_api_paths(self, template):  # type: ignore[no-untyped-def]
        """
        Add conditions to implicit API paths if necessary.

        Implicit API resource methods are constructed from API events on individual serverless functions within the SAM
        template. Since serverless functions can have conditions on them, it's possible to have a case where all methods
        under a resource path have conditions on them. If all of these conditions evaluate to false, the entire resource
        path should not be defined either. This method checks all resource paths' methods and if all methods under a
        given path contain a condition, a composite condition is added to the overall template Conditions section and
        that composite condition is added to the resource path.
        """

        for api_id, api in template.iterate({self.SERVERLESS_API_RESOURCE_TYPE}):
            if not api.properties.get("__MANAGE_SWAGGER"):
                continue

            swagger = api.properties.get("DefinitionBody")
            editor = self.EDITOR_CLASS(swagger)

            for path in editor.iter_on_path():
                all_method_conditions = {condition for _, condition in self.api_conditions[api_id][path].items()}
                at_least_one_method = len(all_method_conditions) > 0
                all_methods_contain_conditions = None not in all_method_conditions
                if at_least_one_method and all_methods_contain_conditions:
                    if len(all_method_conditions) == 1:
                        editor.make_path_conditional(path, all_method_conditions.pop())
                    else:
                        path_condition_name = self._path_condition_name(api_id, path)  # type: ignore[no-untyped-call]
                        self._add_combined_condition_to_template(  # type: ignore[no-untyped-call]
                            template.template_dict, path_condition_name, all_method_conditions
                        )
                        editor.make_path_conditional(path, path_condition_name)

            api.properties["DefinitionBody"] = self._get_api_definition_from_editor(editor)  # type: ignore[no-untyped-call] # TODO make static method
            template.set(api_id, api)

    def _path_condition_name(self, api_id, path):  # type: ignore[no-untyped-def]
        """
        Generate valid condition logical id from the given API logical id and swagger resource path.
        """
        # only valid characters for CloudFormation logical id are [A-Za-z0-9], but swagger paths can contain
        # slashes and curly braces for templated params, e.g., /foo/{customerId}. So we'll replace
        # non-alphanumeric characters.
        path_logical_id = path.replace("/", "SLASH").replace("{", "OB").replace("}", "CB")
        return f"{api_id}{path_logical_id}PathCondition"

    def _maybe_remove_implicit_api(self, template):  # type: ignore[no-untyped-def]
        """
        Implicit API resource are tentatively added to the template for uniform handling of both Implicit & Explicit
        APIs. They need to removed from the template, if there are *no* API events attached to this resource.
        This method removes the Implicit API if it does not contain any Swagger paths (added in response to API events).

        :param SamTemplate template: SAM Template containing the Implicit API resource
        """

        # Remove Implicit API resource if no paths got added
        implicit_api_resource = template.get(self.IMPLICIT_API_LOGICAL_ID)

        if implicit_api_resource and len(implicit_api_resource.properties["DefinitionBody"]["paths"]) == 0:
            # If there's no implicit api and the author defined a "ServerlessRestApi"
            # resource, restore it
            if self.existing_implicit_api_resource:
                template.set(self.IMPLICIT_API_LOGICAL_ID, self.existing_implicit_api_resource)
            else:
                template.delete(self.IMPLICIT_API_LOGICAL_ID)

    def _validate_api_event(self, event_id: str, event_properties: Dict[str, Any]) -> Tuple[str, str, str]:
        """Validate and return api_id, path, method."""
        api_id = self._get_api_id(event_properties)
        path = event_properties.get("Path")
        method = event_properties.get("Method")

        sam_expect(path, event_id, "Path", is_sam_event=True).to_not_be_none()
        sam_expect(method, event_id, "Method", is_sam_event=True).to_not_be_none()

        return (
            # !Ref is resolved by this time. If it is not a string, we can't parse/use this Api.
            sam_expect(api_id, event_id, self.API_ID_EVENT_PROPERTY, is_sam_event=True).to_be_a_string(),
            sam_expect(path, event_id, "Path", is_sam_event=True).to_be_a_string(),
            sam_expect(method, event_id, "Method", is_sam_event=True).to_be_a_string(),
        )

    def _update_resource_attributes_from_api_event(  # noqa: too-many-arguments
        self,
        api_id: str,
        path: str,
        method: str,
        condition: Optional[str],
        deletion_policy: Optional[str],
        update_replace_policy: Optional[str],
    ) -> None:
        api_dict_condition = self.api_conditions.setdefault(api_id, {})
        method_conditions = api_dict_condition.setdefault(path, {})
        method_conditions[method] = condition

        api_dict_deletion = self.api_deletion_policies.setdefault(api_id, set())
        api_dict_deletion.add(deletion_policy)

        api_dict_update_replace = self.api_update_replace_policies.setdefault(api_id, set())
        api_dict_update_replace.add(update_replace_policy)
