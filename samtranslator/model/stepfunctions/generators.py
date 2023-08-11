import json
from copy import deepcopy
from typing import Any, Dict, List, Tuple

from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.model.exceptions import InvalidEventException, InvalidResourceException
from samtranslator.model.iam import IAMRole, IAMRolePolicies
from samtranslator.model.intrinsics import fnJoin, is_intrinsic
from samtranslator.model.resource_policies import ResourcePolicies
from samtranslator.model.role_utils import construct_role_for_resource
from samtranslator.model.s3_utils.uri_parser import parse_s3_uri
from samtranslator.model.stepfunctions.resources import (
    StepFunctionsStateMachine,
    StepFunctionsStateMachineAlias,
    StepFunctionsStateMachineVersion,
)
from samtranslator.model.tags.resource_tagging import get_tag_list
from samtranslator.model.xray_utils import get_xray_managed_policy_name
from samtranslator.utils.cfn_dynamic_references import is_dynamic_reference


class StateMachineGenerator:
    _SAM_KEY = "stateMachine:createdBy"
    _SAM_VALUE = "SAM"
    _SUBSTITUTION_NAME_TEMPLATE = "definition_substitution_%s"
    _SUBSTITUTION_KEY_TEMPLATE = "${definition_substitution_%s}"
    SFN_INVALID_PROPERTY_BOTH_ROLE_POLICY = (
        "Specify either 'Role' or 'Policies' (but not both at the same time) or neither of them"
    )

    def __init__(  # type: ignore[no-untyped-def] # noqa: PLR0913
        self,
        logical_id,
        depends_on,
        managed_policy_map,
        intrinsics_resolver,
        definition,
        definition_uri,
        logging,
        name,
        policies,
        permissions_boundary,
        definition_substitutions,
        role,
        state_machine_type,
        tracing,
        events,
        event_resources,
        event_resolver,
        role_path=None,
        tags=None,
        resource_attributes=None,
        passthrough_resource_attributes=None,
        get_managed_policy_map=None,
        auto_publish_alias=None,
        deployment_preference=None,
    ):
        """
        Constructs an State Machine Generator class that generates a State Machine resource

        :param logical_id: Logical id of the SAM State Machine Resource
        :param depends_on: Any resources that need to be depended on
        :param managed_policy_map: Map of managed policy names to the ARNs
        :param intrinsics_resolver: Instance of the resolver that knows how to resolve parameter references
        :param definition: State Machine definition
        :param definition_uri: URI to State Machine definition
        :param logging: Logging configuration for the State Machine
        :param name: Name of the State Machine resource
        :param policies: Policies attached to the execution role
        :param permissions_boundary: The ARN of the policy used to set the permissions boundary for the role
        :param definition_substitutions: Variable-to-value mappings to be replaced in the State Machine definition
        :param role: Role ARN to use for the execution role
        :param role_path: The file path of the execution role
        :param state_machine_type: Type of the State Machine
        :param tracing: Tracing configuration for the State Machine
        :param events: List of event sources for the State Machine
        :param event_resources: Event resources to link
        :param event_resolver: Resolver that maps Event types to Event classes
        :param tags: Tags to be associated with the State Machine resource
        :param resource_attributes: Resource attributes to add to the State Machine resource
        :param passthrough_resource_attributes: Attributes such as `Condition` that are added to derived resources
        :param auto_publish_alias: Name of the state machine alias to automatically create and update
        :deployment_preference: Settings to enable gradual state machine deployments
        """
        self.logical_id = logical_id
        self.depends_on = depends_on
        self.managed_policy_map = managed_policy_map
        self.intrinsics_resolver = intrinsics_resolver
        self.passthrough_resource_attributes = passthrough_resource_attributes
        self.resource_attributes = resource_attributes
        self.definition = definition
        self.definition_uri = definition_uri
        self.name = name
        self.logging = logging
        self.policies = policies
        self.permissions_boundary = permissions_boundary
        self.definition_substitutions = definition_substitutions
        self.role = role
        self.role_path = role_path
        self.type = state_machine_type
        self.tracing = tracing
        self.events = events
        self.event_resources = event_resources
        self.event_resolver = event_resolver
        self.tags = tags
        self.state_machine = StepFunctionsStateMachine(
            logical_id, depends_on=depends_on, attributes=resource_attributes
        )
        self.substitution_counter = 1
        self.get_managed_policy_map = get_managed_policy_map
        self.auto_publish_alias = auto_publish_alias
        self.deployment_preference = deployment_preference

    @cw_timer(prefix="Generator", name="StateMachine")
    def to_cloudformation(self):  # type: ignore[no-untyped-def]
        """
        Constructs and returns the State Machine resource and any additional resources associated with it.

        :returns: a list of resources including the State Machine resource.
        :rtype: list
        """
        resources: List[Any] = [self.state_machine]

        # Defaulting to {} will add the DefinitionSubstitutions field on the transform output even when it is not relevant
        if self.definition_substitutions:
            self.state_machine.DefinitionSubstitutions = self.definition_substitutions

        if self.definition and self.definition_uri:
            raise InvalidResourceException(
                self.logical_id, "Specify either 'Definition' or 'DefinitionUri' property and not both."
            )
        if self.definition:
            processed_definition = deepcopy(self.definition)
            substitutions = self._replace_dynamic_values_with_substitutions(processed_definition)  # type: ignore[no-untyped-call]
            if len(substitutions) > 0:
                if self.state_machine.DefinitionSubstitutions:
                    self.state_machine.DefinitionSubstitutions.update(substitutions)
                else:
                    self.state_machine.DefinitionSubstitutions = substitutions
            self.state_machine.DefinitionString = self._build_definition_string(processed_definition)  # type: ignore[no-untyped-call]
        elif self.definition_uri:
            self.state_machine.DefinitionS3Location = self._construct_definition_uri()
        else:
            raise InvalidResourceException(
                self.logical_id, "Either 'Definition' or 'DefinitionUri' property must be specified."
            )

        if self.role and self.policies:
            raise InvalidResourceException(self.logical_id, self.SFN_INVALID_PROPERTY_BOTH_ROLE_POLICY)
        if self.role:
            self.state_machine.RoleArn = self.role
        else:
            if not self.policies:
                self.policies = []
            execution_role = self._construct_role()
            self.state_machine.RoleArn = execution_role.get_runtime_attr("arn")
            resources.append(execution_role)

        self.state_machine.StateMachineName = self.name
        self.state_machine.StateMachineType = self.type
        self.state_machine.LoggingConfiguration = self.logging
        self.state_machine.TracingConfiguration = self.tracing
        self.state_machine.Tags = self._construct_tag_list()

        managed_traffic_shifting_resources = self._generate_managed_traffic_shifting_resources()
        resources.extend(managed_traffic_shifting_resources)

        event_resources = self._generate_event_resources()
        resources.extend(event_resources)

        return resources

    def _construct_definition_uri(self) -> Dict[str, Any]:
        """
        Constructs the State Machine's `DefinitionS3 property`_, from the SAM State Machines's DefinitionUri property.

        :returns: a DefinitionUri dict, containing the S3 Bucket, Key, and Version of the State Machine definition.
        :rtype: dict
        """
        if isinstance(self.definition_uri, dict):
            if not self.definition_uri.get("Bucket", None) or not self.definition_uri.get("Key", None):
                # DefinitionUri is a dictionary but does not contain Bucket or Key property
                raise InvalidResourceException(
                    self.logical_id, "'DefinitionUri' requires Bucket and Key properties to be specified."
                )
            s3_pointer = self.definition_uri
        else:
            # DefinitionUri is a string
            parsed_s3_pointer = parse_s3_uri(self.definition_uri)
            if parsed_s3_pointer is None:
                raise InvalidResourceException(
                    self.logical_id,
                    "'DefinitionUri' is not a valid S3 Uri of the form "
                    "'s3://bucket/key' with optional versionId query parameter.",
                )
            s3_pointer = parsed_s3_pointer

        definition_s3 = {"Bucket": s3_pointer["Bucket"], "Key": s3_pointer["Key"]}
        if "Version" in s3_pointer:
            definition_s3["Version"] = s3_pointer["Version"]
        return definition_s3

    def _build_definition_string(self, definition_dict):  # type: ignore[no-untyped-def]
        """
        Builds a CloudFormation definition string from a definition dictionary. The definition string constructed is
        a Fn::Join intrinsic function to make it readable.

        :param definition_dict: State machine definition as a dictionary

        :returns: the state machine definition.
        :rtype: dict
        """
        # Indenting and then splitting the JSON-encoded string for readability of the state machine definition in the CloudFormation translated resource.
        # Separators are passed explicitly to maintain trailing whitespace consistency across Py2 and Py3
        definition_lines = json.dumps(definition_dict, sort_keys=True, indent=4, separators=(",", ": ")).split("\n")
        return fnJoin("\n", definition_lines)

    def _construct_role(self) -> IAMRole:
        """
        Constructs a State Machine execution role based on this SAM State Machine's Policies property.

        :returns: the generated IAM Role
        :rtype: model.iam.IAMRole
        """
        policies = self.policies[:]
        if self.tracing and self.tracing.get("Enabled") is True:
            policies.append(get_xray_managed_policy_name())

        state_machine_policies = ResourcePolicies(
            {"Policies": policies},
            # No support for policy templates in the "core"
            policy_template_processor=None,
        )

        return construct_role_for_resource(
            resource_logical_id=self.logical_id,
            role_path=self.role_path,
            attributes=self.passthrough_resource_attributes,
            managed_policy_map=self.managed_policy_map,
            assume_role_policy_document=IAMRolePolicies.stepfunctions_assume_role_policy(),
            resource_policies=state_machine_policies,
            tags=self._construct_tag_list(),
            permissions_boundary=self.permissions_boundary,
            get_managed_policy_map=self.get_managed_policy_map,
        )

    def _construct_tag_list(self) -> List[Dict[str, Any]]:
        """
        Transforms the SAM defined Tags into the form CloudFormation is expecting.

        :returns: List of Tag Dictionaries
        :rtype: list
        """
        sam_tag = {self._SAM_KEY: self._SAM_VALUE}
        return get_tag_list(sam_tag) + get_tag_list(self.tags)

    def _construct_version(self) -> StepFunctionsStateMachineVersion:
        """Constructs a state machine version resource that will be auto-published when the revision id of the state machine changes.

        :return: Step Functions state machine version resource
        """

        # Unlike Lambda function versions, state machine versions do not need a hash suffix because
        # they are always replaced when their corresponding state machine is updated.
        # I.e. A SAM StateMachine resource will never have multiple version resources at the same time.
        logical_id = f"{self.logical_id}Version"
        attributes = self.passthrough_resource_attributes.copy()

        # Both UpdateReplacePolicy and DeletionPolicy are needed to protect previous version from deletion
        # to ensure gradual deployment works.
        if "DeletionPolicy" not in attributes:
            attributes["DeletionPolicy"] = "Retain"
        if "UpdateReplacePolicy" not in attributes:
            attributes["UpdateReplacePolicy"] = "Retain"

        state_machine_version = StepFunctionsStateMachineVersion(logical_id=logical_id, attributes=attributes)
        state_machine_version.StateMachineArn = self.state_machine.get_runtime_attr("arn")
        state_machine_version.StateMachineRevisionId = self.state_machine.get_runtime_attr("state_machine_revision_id")

        return state_machine_version

    def _construct_alias(self, version: StepFunctionsStateMachineVersion) -> StepFunctionsStateMachineAlias:
        """Constructs a state machine alias resource pointing to the given state machine version.
        :return: Step Functions state machine alias resource
        """
        logical_id = f"{self.logical_id}Alias{self.auto_publish_alias}"
        attributes = self.passthrough_resource_attributes

        state_machine_alias = StepFunctionsStateMachineAlias(logical_id=logical_id, attributes=attributes)
        state_machine_alias.Name = self.auto_publish_alias

        state_machine_version_arn = version.get_runtime_attr("arn")

        deployment_preference = {}
        if self.deployment_preference:
            deployment_preference = self.deployment_preference
        else:
            deployment_preference["Type"] = "ALL_AT_ONCE"

        deployment_preference["StateMachineVersionArn"] = state_machine_version_arn
        state_machine_alias.DeploymentPreference = deployment_preference

        return state_machine_alias

    def _generate_managed_traffic_shifting_resources(
        self,
    ) -> List[Any]:
        """Generates and returns the version and alias resources associated with this state machine's managed traffic shifting.

        :returns: a list containing the state machine's version and alias resources
        :rtype: list
        """
        if not self.auto_publish_alias and not self.deployment_preference:
            return []
        if not self.auto_publish_alias and self.deployment_preference:
            raise InvalidResourceException(
                self.logical_id, "'DeploymentPreference' requires 'AutoPublishAlias' property to be specified."
            )

        state_machine_version = self._construct_version()
        return [state_machine_version, self._construct_alias(state_machine_version)]

    def _generate_event_resources(self) -> List[Dict[str, Any]]:
        """Generates and returns the resources associated with this state machine's event sources.

        :returns: a list containing the state machine's event resources
        :rtype: list
        """
        resources = []
        if self.events:
            for logical_id, event_dict in self.events.items():
                kwargs = {
                    "intrinsics_resolver": self.intrinsics_resolver,
                    "permissions_boundary": self.permissions_boundary,
                }
                try:
                    eventsource = self.event_resolver.resolve_resource_type(event_dict).from_dict(
                        self.state_machine.logical_id + logical_id, event_dict, logical_id
                    )
                    for name, resource in self.event_resources[logical_id].items():
                        kwargs[name] = resource
                except (TypeError, AttributeError) as e:
                    raise InvalidEventException(logical_id, str(e)) from e
                resources += eventsource.to_cloudformation(resource=self.state_machine, **kwargs)

        return resources

    def _replace_dynamic_values_with_substitutions(self, _input):  # type: ignore[no-untyped-def]
        """
        Replaces the CloudFormation instrinsic functions and dynamic references within the input with substitutions.

        :param _input: Input dictionary in which the dynamic values need to be replaced with substitutions

        :returns: List of substitution to dynamic value mappings
        :rtype: dict
        """
        substitution_map = {}
        for path in self._get_paths_to_intrinsics(_input):  # type: ignore[no-untyped-call]
            location = _input
            for step in path[:-1]:
                location = location[step]
            sub_name, sub_key = self._generate_substitution()
            substitution_map[sub_name] = location[path[-1]]
            location[path[-1]] = sub_key
        return substitution_map

    def _get_paths_to_intrinsics(self, _input, path=None):  # type: ignore[no-untyped-def]
        """
        Returns all paths to dynamic values within a dictionary

        :param _input: Input dictionary to find paths to dynamic values in
        :param path: Optional list to keep track of the path to the input dictionary
        :returns list: List of keys that defines the path to a dynamic value within the input dictionary
        """
        if path is None:
            path = []
        dynamic_value_paths = []  # type: ignore[var-annotated]
        if isinstance(_input, dict):
            iterator = _input.items()
        elif isinstance(_input, list):
            iterator = enumerate(_input)  # type: ignore[assignment]
        else:
            return dynamic_value_paths

        for key, value in sorted(iterator, key=lambda item: item[0]):  # type: ignore[no-any-return]
            if is_intrinsic(value) or is_dynamic_reference(value):
                dynamic_value_paths.append([*path, key])
            elif isinstance(value, (dict, list)):
                dynamic_value_paths.extend(self._get_paths_to_intrinsics(value, [*path, key]))  # type: ignore[no-untyped-call]

        return dynamic_value_paths

    def _generate_substitution(self) -> Tuple[str, str]:
        """
        Generates a name and key for a new substitution.

        :returns: Substitution name and key
        :rtype: string, string
        """
        substitution_name = self._SUBSTITUTION_NAME_TEMPLATE % self.substitution_counter
        substitution_key = self._SUBSTITUTION_KEY_TEMPLATE % self.substitution_counter
        self.substitution_counter += 1
        return substitution_name, substitution_key
