""" CloudFormation Resource serialization, deserialization, and validation """

import inspect
import re
from abc import ABC, ABCMeta, abstractmethod
from contextlib import suppress
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar

from samtranslator.compat import pydantic
from samtranslator.model.exceptions import (
    ExpectedType,
    InvalidResourceException,
    InvalidResourcePropertyTypeException,
)
from samtranslator.model.tags.resource_tagging import get_tag_list
from samtranslator.model.types import IS_DICT, IS_STR, PassThrough, Validator, any_type, is_type
from samtranslator.plugins import LifeCycleEvents

RT = TypeVar("RT", bound=pydantic.BaseModel)  # return type


class PropertyType:
    """Stores validation information for a CloudFormation resource property.

    The attribute "expected_type" is only used by InvalidResourcePropertyTypeException
    to generate an error message. When it is not found,
    customers will see "Type of property 'xxx' is invalid."
    If it is provided, customers will see "Property 'xxx' should be a yyy."

    DEPRECATED: Use `Property` instead.

    :ivar bool required: True if the property is required, False otherwise
    :ivar callable validate: A function that returns True if the provided value is valid for this property, and raises \
        TypeError if it isn't.
    :ivar supports_intrinsics True to allow intrinsic function support on this property. Setting this to False will
        raise an error when intrinsic function dictionary is supplied as value
    """

    EXPECTED_TYPE_BY_VALIDATOR = {IS_DICT: ExpectedType.MAP, IS_STR: ExpectedType.STRING}

    def __init__(
        self,
        required: bool,
        validate: Validator = lambda value: True,
        supports_intrinsics: bool = True,
    ) -> None:
        self.required = required
        self.validate = validate
        self.supports_intrinsics = supports_intrinsics
        self.expected_type = self.EXPECTED_TYPE_BY_VALIDATOR.get(validate)


class Property(PropertyType):
    """Like `PropertyType`, except without intrinsics support.

    Intrinsics are already resolved by AWS::LanguageExtensions (see https://github.com/aws/serverless-application-model/issues/2533),
    and supporting intrinsics in the transform is error-prone due to more relaxed types (e.g. a
    boolean property will evaluate as truthy when an intrinsic is passed to it).
    """

    def __init__(self, required: bool, validate: Validator) -> None:
        super().__init__(required, validate, False)


class PassThroughProperty(PropertyType):
    """
    Pass-through property.

    SAM Translator should not try to read the value other than passing it to underlaying CFN resources.
    """

    def __init__(self, required: bool) -> None:
        super().__init__(required, any_type(), False)


class MutatedPassThroughProperty(PassThroughProperty):
    """
    Mutated pass-through property.

    SAM Translator may read and add/remove/modify the value before passing it to underlaying CFN resources.
    """


class GeneratedProperty(PropertyType):
    """
    Property of a generated CloudFormation resource.
    """

    def __init__(self) -> None:
        # Intentionally the most lenient; we don't want the risk of potential
        # runtime exceptions, and the object attributes are statically typed
        super().__init__(False, any_type(), False)


class Resource(ABC):
    """A Resource object represents an abstract entity that contains a Type and a Properties object. They map well to
    CloudFormation resources as well sub-types like AWS::Lambda::Function or `Events` section of
    AWS::Serverless::Function.

    This class provides the serialization and validation logic to construct CloudFormation Resources programmatically
    and convert them (see :func:`to_dict`) into valid CloudFormation templates. It also provides the deserialization
    logic (see :func:`from_dict`) to generate Resource objects from existing templates.

    :cvar str resource_type: the resource type, for example 'AWS::Lambda::Function'.
    :cvar dict property_types: a dict mapping the valid property names for this resource to PropertyType instances, \
    which indicate whether the property is required and the property's type. Properties that are not in this dict will \
    be considered invalid.
    """

    # Note(xinhol): `Resource` should have been an abstract class. Disabling the type check for the next
    # two lines to avoid any potential behavior change.
    # TODO: Make `Resource` an abstract class and not giving `resource_type`/`property_types` initial value.
    resource_type: str = None  # type: ignore
    property_types: Dict[str, PropertyType] = None  # type: ignore
    _keywords = {"logical_id", "relative_id", "depends_on", "resource_attributes"}

    # For attributes in this list, they will be passed into the translated template for the same resource itself.
    _supported_resource_attributes = ["DeletionPolicy", "UpdatePolicy", "Condition", "UpdateReplacePolicy", "Metadata"]
    # For attributes in this list, they will be passed into the translated template for the same resource,
    # as well as all the auto-generated resources that are created from this resource.
    _pass_through_attributes = ["Condition", "DeletionPolicy", "UpdateReplacePolicy"]

    # Runtime attributes that can be qureied resource. They are CloudFormation attributes like ARN, Name etc that
    # will be resolvable at runtime. This map will be implemented by sub-classes to express list of attributes they
    # support and the corresponding CloudFormation construct to fetch the attribute when stack update is executed.
    # Example:
    # attrs = {
    #   "arn": fnGetAtt(self.logical_id, "Arn")
    # }
    runtime_attrs: Dict[str, Callable[["Resource"], Any]] = {}  # TODO: replace Any with something more explicit

    # When "validate_setattr" is True, we cannot change the value of any class variables after instantiation unless they
    # are in "property_types" or "_keywords". We can set this to False in the inheriting class definition so we can
    # update other class variables as well after instantiation.
    validate_setattr: bool = True
    Tags: Optional[PassThrough]

    def __init__(
        self,
        logical_id: Optional[Any],
        relative_id: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initializes a Resource object with the given logical id.

        :param str logical_id: The logical id of this Resource
        :param str relative_id: The logical id of this resource relative to the logical_id. This is useful
                                to identify sub-resources.
        :param depends_on Value of DependsOn resource attribute
        :param attributes Dictionary of resource attributes and their values
        """
        self.logical_id = self._validate_logical_id(logical_id)
        self.relative_id = relative_id
        self.depends_on = depends_on

        for name, _ in self.property_types.items():
            setattr(self, name, None)

        self.resource_attributes: Dict[str, Any] = {}
        if attributes is not None:
            for attr, value in attributes.items():
                self.set_resource_attribute(attr, value)

    @classmethod
    def get_supported_resource_attributes(cls):  # type: ignore[no-untyped-def]
        """
        A getter method for the supported resource attributes
        returns: a tuple that contains the name of all supported resource attributes
        """
        return tuple(cls._supported_resource_attributes)

    @classmethod
    def get_pass_through_attributes(cls) -> Tuple[str, ...]:
        """
        A getter method for the resource attributes to be passed to auto-generated resources
        returns: a tuple that contains the name of all pass through attributes
        """
        return tuple(cls._pass_through_attributes)

    @classmethod
    def from_dict(cls, logical_id: str, resource_dict: Dict[str, Any], relative_id: Optional[str] = None, sam_plugins=None) -> "Resource":  # type: ignore[no-untyped-def]
        """Constructs a Resource object with the given logical id, based on the given resource dict. The resource dict
        is the value associated with the logical id in a CloudFormation template's Resources section, and takes the
        following format. ::

            {
                "Type": "<resource type>",
                "Properties": {
                    <set of properties>
                }
            }

        :param str logical_id: The logical id of this Resource
        :param dict resource_dict: The value associated with this logical id in the CloudFormation template, a mapping \
        containing the resource's Type and Properties.
        :param str relative_id: The logical id of this resource relative to the logical_id. This is useful
                                to identify sub-resources.
        :param samtranslator.plugins.SamPlugins sam_plugins: Optional plugins object to help enhance functionality of
            translator
        :returns: a Resource object populated from the provided parameters
        :rtype: Resource
        :raises TypeError: if the provided parameters are invalid
        """

        resource = cls(logical_id, relative_id=relative_id)

        resource._validate_resource_dict(logical_id, resource_dict)  # type: ignore[no-untyped-call]

        # Default to empty properties dictionary. If customers skip the Properties section, an empty dictionary
        # accurately captures the intent.
        properties = resource_dict.get("Properties", {})

        if sam_plugins:
            sam_plugins.act(LifeCycleEvents.before_transform_resource, logical_id, cls.resource_type, properties)

        for name, value in properties.items():
            setattr(resource, name, value)

        if "DependsOn" in resource_dict:
            resource.depends_on = resource_dict["DependsOn"]

        # Parse only well known properties. This is consistent with earlier behavior where we used to ignore resource
        # all resource attributes ie. all attributes were unsupported before
        for attr in resource._supported_resource_attributes:
            if attr in resource_dict:
                resource.set_resource_attribute(attr, resource_dict[attr])

        resource.validate_properties()
        return resource

    @staticmethod
    def _validate_logical_id(logical_id: Optional[Any]) -> str:
        """Validates that the provided logical id is an alphanumeric string.

        :param str logical_id: the logical id to validate
        :returns: True if the logical id is valid
        :rtype: bool
        :raises TypeError: if the logical id is invalid
        """
        pattern = re.compile(r"^[A-Za-z0-9]+$")
        if isinstance(logical_id, str) and pattern.match(logical_id):
            return logical_id
        # TODO: Doing validation in this class is kind of off,
        # we need to surface this validation to where the template is loaded
        # or the logical IDs are generated.
        raise InvalidResourceException(str(logical_id), "Logical ids must be alphanumeric.")

    @classmethod
    def _validate_resource_dict(cls, logical_id, resource_dict):  # type: ignore[no-untyped-def]
        """Validates that the provided resource dict contains the correct Type string, and the required Properties dict.

        :param dict resource_dict: the resource dict to validate
        :returns: True if the resource dict has the expected format
        :rtype: bool
        :raises InvalidResourceException: if the resource dict has an invalid format
        """
        if "Type" not in resource_dict:
            raise InvalidResourceException(logical_id, "Resource dict missing key 'Type'.")
        if resource_dict["Type"] != cls.resource_type:
            raise InvalidResourceException(
                logical_id,
                "Resource has incorrect Type; expected '{expected}', "
                "got '{actual}'".format(expected=cls.resource_type, actual=resource_dict["Type"]),
            )

        if "Properties" in resource_dict and not isinstance(resource_dict["Properties"], dict):
            raise InvalidResourceException(logical_id, "Properties of a resource must be an object.")

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Validates that the required properties for this Resource have been provided, then returns a dict
        corresponding to the given Resource object. This dict will take the format of a single entry in the Resources
        section of a CloudFormation template, and will take the following format. ::

            {
                "<logical id>": {
                    "Type": "<resource type>",
                    "DependsOn": "<value specified by user>",
                    "Properties": {
                        <set of properties>
                    }
                }
            }

        The resulting dict can then be serialized to JSON or YAML and included as part of a CloudFormation template.

        :returns: a dict corresponding to this Resource's entry in a CloudFormation template
        :rtype: dict
        :raises TypeError: if a required property is missing from this Resource
        """
        self.validate_properties()

        resource_dict = self._generate_resource_dict()

        return {self.logical_id: resource_dict}

    def _generate_resource_dict(self) -> Dict[str, Any]:
        """Generates the resource dict for this Resource, the value associated with the logical id in a CloudFormation
        template's Resources section.

        :returns: the resource dict for this Resource
        :rtype: dict
        """
        resource_dict: Dict[str, Any] = {"Type": self.resource_type}

        if self.depends_on:
            resource_dict["DependsOn"] = self.depends_on

        resource_dict.update(self.resource_attributes)

        properties_dict = {}
        for name in self.property_types:
            value = getattr(self, name)
            if value is not None:
                properties_dict[name] = value

        resource_dict["Properties"] = properties_dict

        return resource_dict

    def __setattr__(self, name, value):  # type: ignore[no-untyped-def]
        """Allows an attribute of this resource to be set only if it is a keyword or a property of the Resource with a
        valid value.

        :param str name: the name of the attribute to be set
        :param value: the value of the attribute to be set
        :raises InvalidResourceException: if an invalid property is provided
        """
        if (name in self._keywords or name in self.property_types) or not self.validate_setattr:
            return super().__setattr__(name, value)

        raise InvalidResourceException(
            self.logical_id,
            f"property {name} not defined for resource of type {self.resource_type}",
        )

    # Note: For compabitliy issue, we should ONLY use this with new abstraction/resources.
    def validate_properties_and_return_model(self, cls: Type[RT]) -> RT:
        """
        Given a resource properties, return a typed object from the definitions of SAM schema model

        param:
            resource_properties: properties from input template
            cls: schema models
        """
        try:
            return cls.parse_obj(self._generate_resource_dict()["Properties"])
        except pydantic.error_wrappers.ValidationError as e:
            error_properties: str = ""
            with suppress(KeyError):
                error_properties = ".".join(str(x) for x in e.errors()[0]["loc"])
            raise InvalidResourceException(self.logical_id, f"Property '{error_properties}' is invalid.") from e

    def validate_properties(self) -> None:
        """Validates that the required properties for this Resource have been populated, and that all properties have
        valid values.

        :returns: True if all properties are valid
        :rtype: bool
        :raises TypeError: if any properties are invalid
        """
        for name, property_type in self.property_types.items():
            value = getattr(self, name)

            # If the property value is an intrinsic function, any remaining validation has to be left to CloudFormation
            if property_type.supports_intrinsics and self._is_intrinsic_function(value):  # type: ignore[no-untyped-call]
                continue

            # If the property value has not been set, verify that the property is not required.
            if value is None:
                if property_type.required:
                    raise InvalidResourceException(self.logical_id, f"Missing required property '{name}'.")
            # Otherwise, validate the value of the property.
            elif not property_type.validate(value, should_raise=False):
                raise InvalidResourcePropertyTypeException(self.logical_id, name, property_type.expected_type)

    def set_resource_attribute(self, attr: str, value: Any) -> None:
        """Sets attributes on resource. Resource attributes are top-level entries of a CloudFormation resource
        that exist outside of the Properties dictionary

        :param attr: Attribute name
        :param value: Attribute value
        :return: None
        :raises KeyError if `attr` is not in the supported attribute list
        """

        if attr not in self._supported_resource_attributes:
            raise KeyError(f"Unsupported resource attribute specified: {attr}")

        self.resource_attributes[attr] = value

    def get_resource_attribute(self, attr: str) -> Any:
        """Gets the resource attribute if available

        :param attr: Name of the attribute
        :return: Value of the attribute, if set in the resource. None otherwise
        """
        if attr not in self.resource_attributes:
            raise KeyError(f"{attr} is not in resource attributes")

        return self.resource_attributes[attr]

    @classmethod
    def _is_intrinsic_function(cls, value):  # type: ignore[no-untyped-def]
        """Checks whether the Property value provided has the format of an intrinsic function, that is ::

            { "<operation>": <parameter> }

        :param value: the property value to check
        :returns: True if the provided value has the format of an intrinsic function, False otherwise
        :rtype: bool
        """
        return isinstance(value, dict) and len(value) == 1

    def get_runtime_attr(self, attr_name: str) -> Any:
        """
        Returns a CloudFormation construct that provides value for this attribute. If the resource does not provide
        this attribute, then this method raises an exception

        :return: Dictionary that will resolve to value of the attribute when CloudFormation stack update is executed
        """
        if attr_name not in self.runtime_attrs:
            raise KeyError(f"{attr_name} attribute is not supported for resource {self.resource_type}")

        return self.runtime_attrs[attr_name](self)

    def get_passthrough_resource_attributes(self) -> Dict[str, Any]:
        """
        Returns a dictionary of resource attributes of the ResourceMacro that should be passed through from the main
        vanilla CloudFormation resource to its children. Currently only Condition is copied.

        :return: Dictionary of resource attributes.
        """
        attributes = {}
        for resource_attribute in self.get_pass_through_attributes():
            if resource_attribute in self.resource_attributes:
                attributes[resource_attribute] = self.resource_attributes.get(resource_attribute)
        return attributes

    def assign_tags(self, tags: Dict[str, Any]) -> None:
        """
        Assigns tags to the resource. This function assumes that generated resources always have
        the tags property called `Tags` that takes a list of key-value objects.

        Override this function if the above assumptions do not apply to the resource (e.g. different
        property name or type (see e.g. 'AWS::ApiGatewayV2::Api').

        :param tags: Dictionary of tags to be assigned to the resource
        """
        if "Tags" in self.property_types:
            self.Tags = get_tag_list(tags)


class ResourceMacro(Resource, metaclass=ABCMeta):
    """A ResourceMacro object represents a CloudFormation macro. A macro appears in the CloudFormation template in the
    "Resources" mapping, but must be expanded into one or more vanilla CloudFormation resources before a stack can be
    created from it.

    In addition to the serialization, deserialization, and validation logic provided by the base Resource class,
    ResourceMacro defines an abstract method :func:`to_cloudformation` that returns a dict of vanilla CloudFormation
    Resources to which this macro should expand.
    """

    def resources_to_link(self, resources):  # type: ignore[no-untyped-def]
        """Returns a dictionary of resources which will need to be modified when this is turned into CloudFormation.
        The result of this will be passed to :func: `to_cloudformation`.

        :param dict resources: resources which potentially need to be modified along with this one.
        :returns: a dictionary of Resources to modify. This will be passed to :func: `to_cloudformation`.
        """
        return {}

    @abstractmethod
    def to_cloudformation(self, **kwargs: Any) -> List[Any]:
        """Returns a list of Resource instances, representing vanilla CloudFormation resources, to which this macro
        expands. The caller should be able to update their template with the expanded resources by calling
        :func:`to_dict` on each resource returned, then updating their "Resources" mapping with the results.

        :param dict kwargs
        :returns: a list of vanilla CloudFormation Resource instances, to which this macro expands
        """


class SamResourceMacro(ResourceMacro, metaclass=ABCMeta):
    """ResourceMacro that specifically refers to SAM (AWS::Serverless::*) resources."""

    # SAM resources can provide a list of properties that they expose. These properties usually resolve to
    # CFN resources that this SAM resource generates. This is provided as a map with the following format:
    #   {
    #      "PropertyName": "AWS::Resource::Type"
    #   }
    #
    # `PropertyName` is the property that customers can refer to using `!Ref LogicalId.PropertyName` or !GetAtt or !Sub.
    # Value of this map is the type of CFN resource that this property resolves to. After generating the CFN
    # resources, there is a separate process that associates this property with LogicalId of the generated CFN resource
    # of the given type.

    referable_properties: Dict[str, str] = {}

    # Each resource can optionally override this tag:
    _SAM_KEY = "lambda:createdBy"
    _SAM_VALUE = "SAM"

    # Tags reserved by the serverless application repo
    _SAR_APP_KEY = "serverlessrepo:applicationId"
    _SAR_SEMVER_KEY = "serverlessrepo:semanticVersion"

    # Aggregate list of all reserved tags
    _RESERVED_TAGS = [_SAM_KEY, _SAR_APP_KEY, _SAR_SEMVER_KEY]

    def get_resource_references(self, generated_cfn_resources, supported_resource_refs):  # type: ignore[no-untyped-def]
        """
        Constructs the list of supported resource references by going through the list of CFN resources generated
        by to_cloudformation() on this SAM resource. Each SAM resource must provide a map of properties that it
        supports and the type of CFN resource this property resolves to.

        :param list of Resource object generated_cfn_resources: List of CloudFormation resources generated by this
            SAM resource
        :param samtranslator.intrinsics.resource_refs.SupportedResourceReferences supported_resource_refs: Object
            holding the mapping between property names and LogicalId of the generated CFN resource it maps to
        :return: Updated supported_resource_refs
        """

        if supported_resource_refs is None:
            raise ValueError("`supported_resource_refs` object is required")

        # Create a map of {ResourceType: LogicalId} for quick access
        resource_id_by_type = {resource.resource_type: resource.logical_id for resource in generated_cfn_resources}

        for property_name, cfn_type in self.referable_properties.items():
            if cfn_type in resource_id_by_type:
                supported_resource_refs.add(self.logical_id, property_name, resource_id_by_type[cfn_type])

        return supported_resource_refs

    def _construct_tag_list(
        self, tags: Optional[Dict[str, Any]], additional_tags: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        if not bool(tags):
            tags = {}

        if additional_tags is None:
            additional_tags = {}

        for tag in self._RESERVED_TAGS:
            self._check_tag(tag, tags)  # type: ignore[no-untyped-call]

        sam_tag = {self._SAM_KEY: self._SAM_VALUE}

        # To maintain backwards compatibility with previous implementation, we *must* append SAM tag to the start of the
        # tags list. Changing this ordering will trigger a update on Lambda Function resource. Even though this
        # does not change the actual content of the tags, we don't want to trigger update of a resource without
        # customer's knowledge.
        return get_tag_list(sam_tag) + get_tag_list(additional_tags) + get_tag_list(tags)

    @staticmethod
    def propagate_tags(
        resources: List[Resource], tags: Optional[Dict[str, Any]], propagate_tags: Optional[bool] = False
    ) -> None:
        """
        Propagates tags to the resources.

        :param propagate_tags: Whether we should pass the tags to generated resources.
        :param resources: List of generated resources
        :param tags: dictionary of tags to propagate to the resources.

        :return: None
        """
        if not propagate_tags or not tags:
            return

        for resource in resources:
            resource.assign_tags(tags)

    def _check_tag(self, reserved_tag_name, tags):  # type: ignore[no-untyped-def]
        if reserved_tag_name in tags:
            raise InvalidResourceException(
                self.logical_id,
                f"{reserved_tag_name} is a reserved Tag key name and "
                "cannot be set on your resource. "
                "Please change the tag key in the "
                "input.",
            )


class ResourceTypeResolver:
    """ResourceTypeResolver maps Resource Types to Resource classes, e.g. AWS::Serverless::Function to
    samtranslator.model.sam_resources.SamFunction."""

    def __init__(self, *modules: Any) -> None:
        """Initializes the ResourceTypeResolver from the given modules.

        :param modules: one or more Python modules containing Resource definitions
        """
        self.resource_types = {}
        for module in modules:
            # Get all classes in the specified module which have a class variable resource_type.
            for _, resource_class in inspect.getmembers(
                module,
                lambda cls: inspect.isclass(cls)
                and cls.__module__ == module.__name__  # noqa: B023
                and hasattr(cls, "resource_type"),
            ):
                self.resource_types[resource_class.resource_type] = resource_class

    def can_resolve(self, resource_dict: Dict[str, Any]) -> bool:
        if not isinstance(resource_dict, dict) or not isinstance(resource_dict.get("Type"), str):
            return False

        return resource_dict["Type"] in self.resource_types

    def resolve_resource_type(self, resource_dict: Dict[str, Any]) -> Any:
        """Returns the Resource class corresponding to the 'Type' key in the given resource dict.

        :param dict resource_dict: the resource dict to resolve
        :returns: the resolved Resource class
        :rtype: class
        """
        if not self.can_resolve(resource_dict):
            raise TypeError(
                "Resource dict has missing or invalid value for key Type. Event Type is: {}.".format(
                    resource_dict.get("Type")
                )
            )
        if resource_dict["Type"] not in self.resource_types:
            raise TypeError("Invalid resource type {resource_type}".format(resource_type=resource_dict["Type"]))
        return self.resource_types[resource_dict["Type"]]


class ResourceResolver:
    def __init__(self, resources: Dict[str, Any]) -> None:
        """
        Instantiate the resolver
        :param dict resources: Map of resource
        """

        if not isinstance(resources, dict):
            raise TypeError("'Resources' is either null or not a valid dictionary.")

        self.resources = resources

    def get_all_resources(self) -> Dict[str, Any]:
        """Return a dictionary of all resources from the SAM template."""
        return self.resources

    def get_resource_by_logical_id(self, _input: str) -> Dict[str, Any]:
        """
        Recursively find resource with matching Logical ID that are present in the template and returns the value.
        If it is not in template, this method simply returns the input unchanged.

        :param _input: Logical ID of a resource

        :param resources: Dictionary of the resource from the SAM template
        """
        if not isinstance(_input, str):
            raise TypeError(f"Invalid logical ID '{_input}'. Expected a string.")

        return self.resources.get(_input, None)


__all__: List[str] = [
    "IS_DICT",
    "IS_STR",
    "Validator",
    "any_type",
    "is_type",
    "PropertyType",
    "Property",
    "PassThroughProperty",
    "MutatedPassThroughProperty",
    "Resource",
    "ResourceMacro",
    "SamResourceMacro",
    "ResourceTypeResolver",
    "ResourceResolver",
]
