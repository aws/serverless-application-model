""" CloudFormation Resource serialization, deserialization, and validation """
import re
import inspect
from typing import Any, Callable, Dict

from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.plugins import LifeCycleEvents
from samtranslator.model.tags.resource_tagging import get_tag_list


class PropertyType(object):
    """Stores validation information for a CloudFormation resource property.

    :ivar bool required: True if the property is required, False otherwise
    :ivar callable validate: A function that returns True if the provided value is valid for this property, and raises \
        TypeError if it isn't.
    :ivar supports_intrinsics True to allow intrinsic function support on this property. Setting this to False will
        raise an error when intrinsic function dictionary is supplied as value
    """

    def __init__(self, required, validate=lambda value: True, supports_intrinsics=True):
        self.required = required
        self.validate = validate
        self.supports_intrinsics = supports_intrinsics


class Resource(object):
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
    _keywords = ["logical_id", "relative_id", "depends_on", "resource_attributes"]

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

    def __init__(self, logical_id, relative_id=None, depends_on=None, attributes=None):
        """Initializes a Resource object with the given logical id.

        :param str logical_id: The logical id of this Resource
        :param str relative_id: The logical id of this resource relative to the logical_id. This is useful
                                to identify sub-resources.
        :param depends_on Value of DependsOn resource attribute
        :param attributes Dictionary of resource attributes and their values
        """
        self._validate_logical_id(logical_id)
        self.logical_id = logical_id
        self.relative_id = relative_id
        self.depends_on = depends_on

        for name, _ in self.property_types.items():
            setattr(self, name, None)

        self.resource_attributes = {}
        if attributes is not None:
            for attr, value in attributes.items():
                self.set_resource_attribute(attr, value)

    @classmethod
    def get_supported_resource_attributes(cls):
        """
        A getter method for the supported resource attributes
        returns: a tuple that contains the name of all supported resource attributes
        """
        return tuple(cls._supported_resource_attributes)

    @classmethod
    def get_pass_through_attributes(cls):
        """
        A getter method for the resource attributes to be passed to auto-generated resources
        returns: a tuple that contains the name of all pass through attributes
        """
        return tuple(cls._pass_through_attributes)

    @classmethod
    def from_dict(cls, logical_id, resource_dict, relative_id=None, sam_plugins=None):
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

        resource._validate_resource_dict(logical_id, resource_dict)

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

    @classmethod
    def _validate_logical_id(cls, logical_id):
        """Validates that the provided logical id is an alphanumeric string.

        :param str logical_id: the logical id to validate
        :returns: True if the logical id is valid
        :rtype: bool
        :raises TypeError: if the logical id is invalid
        """
        pattern = re.compile(r"^[A-Za-z0-9]+$")
        if logical_id is not None and pattern.match(logical_id):
            return True
        raise InvalidResourceException(logical_id, "Logical ids must be alphanumeric.")

    @classmethod
    def _validate_resource_dict(cls, logical_id, resource_dict):
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

    def to_dict(self):
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

    def _generate_resource_dict(self):
        """Generates the resource dict for this Resource, the value associated with the logical id in a CloudFormation
        template's Resources section.

        :returns: the resource dict for this Resource
        :rtype: dict
        """
        resource_dict = {}

        resource_dict["Type"] = self.resource_type

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

    def __setattr__(self, name, value):
        """Allows an attribute of this resource to be set only if it is a keyword or a property of the Resource with a
        valid value.

        :param str name: the name of the attribute to be set
        :param value: the value of the attribute to be set
        :raises InvalidResourceException: if an invalid property is provided
        """
        if name in self._keywords or name in self.property_types:
            return super(Resource, self).__setattr__(name, value)

        raise InvalidResourceException(
            self.logical_id,
            "property {property_name} not defined for resource of type {resource_type}".format(
                resource_type=self.resource_type, property_name=name
            ),
        )

    def validate_properties(self):
        """Validates that the required properties for this Resource have been populated, and that all properties have
        valid values.

        :returns: True if all properties are valid
        :rtype: bool
        :raises TypeError: if any properties are invalid
        """
        for name, property_type in self.property_types.items():
            value = getattr(self, name)

            # If the property value is an intrinsic function, any remaining validation has to be left to CloudFormation
            if property_type.supports_intrinsics and self._is_intrinsic_function(value):
                continue

            # If the property value has not been set, verify that the property is not required.
            if value is None:
                if property_type.required:
                    raise InvalidResourceException(
                        self.logical_id, "Missing required property '{property_name}'.".format(property_name=name)
                    )
            # Otherwise, validate the value of the property.
            elif not property_type.validate(value, should_raise=False):
                raise InvalidResourceException(
                    self.logical_id, "Type of property '{property_name}' is invalid.".format(property_name=name)
                )

    def set_resource_attribute(self, attr, value):
        """Sets attributes on resource. Resource attributes are top-level entries of a CloudFormation resource
        that exist outside of the Properties dictionary

        :param attr: Attribute name
        :param value: Attribute value
        :return: None
        :raises KeyError if `attr` is not in the supported attribute list
        """

        if attr not in self._supported_resource_attributes:
            raise KeyError("Unsupported resource attribute specified: %s" % attr)

        self.resource_attributes[attr] = value

    def get_resource_attribute(self, attr):
        """Gets the resource attribute if available

        :param attr: Name of the attribute
        :return: Value of the attribute, if set in the resource. None otherwise
        """
        if attr not in self.resource_attributes:
            raise KeyError("%s is not in resource attributes" % attr)

        return self.resource_attributes[attr]

    @classmethod
    def _is_intrinsic_function(cls, value):
        """Checks whether the Property value provided has the format of an intrinsic function, that is ::

            { "<operation>": <parameter> }

        :param value: the property value to check
        :returns: True if the provided value has the format of an intrinsic function, False otherwise
        :rtype: bool
        """
        return isinstance(value, dict) and len(value) == 1

    def get_runtime_attr(self, attr_name):
        """
        Returns a CloudFormation construct that provides value for this attribute. If the resource does not provide
        this attribute, then this method raises an exception

        :return: Dictionary that will resolve to value of the attribute when CloudFormation stack update is executed
        """

        if attr_name in self.runtime_attrs:
            return self.runtime_attrs[attr_name](self)
        else:
            raise NotImplementedError(f"{attr_name} attribute is not implemented for resource {self.resource_type}")

    def get_passthrough_resource_attributes(self):
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


class ResourceMacro(Resource):
    """A ResourceMacro object represents a CloudFormation macro. A macro appears in the CloudFormation template in the
    "Resources" mapping, but must be expanded into one or more vanilla CloudFormation resources before a stack can be
    created from it.

    In addition to the serialization, deserialization, and validation logic provided by the base Resource class,
    ResourceMacro defines an abstract method :func:`to_cloudformation` that returns a dict of vanilla CloudFormation
    Resources to which this macro should expand.
    """

    def resources_to_link(self, resources):
        """Returns a dictionary of resources which will need to be modified when this is turned into CloudFormation.
        The result of this will be passed to :func: `to_cloudformation`.

        :param dict resources: resources which potentially need to be modified along with this one.
        :returns: a dictionary of Resources to modify. This will be passed to :func: `to_cloudformation`.
        """
        return {}

    def to_cloudformation(self, **kwargs):
        """Returns a list of Resource instances, representing vanilla CloudFormation resources, to which this macro
        expands. The caller should be able to update their template with the expanded resources by calling
        :func:`to_dict` on each resource returned, then updating their "Resources" mapping with the results.

        :param dict kwargs
        :returns: a list of vanilla CloudFormation Resource instances, to which this macro expands
        """
        raise NotImplementedError("Method to_cloudformation() must be implemented in a subclass of ResourceMacro")


class SamResourceMacro(ResourceMacro):
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

    def get_resource_references(self, generated_cfn_resources, supported_resource_refs):
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

        for property, cfn_type in self.referable_properties.items():
            if cfn_type in resource_id_by_type:
                supported_resource_refs.add(self.logical_id, property, resource_id_by_type[cfn_type])

        return supported_resource_refs

    def _construct_tag_list(self, tags, additional_tags=None):
        if not bool(tags):
            tags = {}

        if additional_tags is None:
            additional_tags = {}

        for tag in self._RESERVED_TAGS:
            self._check_tag(tag, tags)

        sam_tag = {self._SAM_KEY: self._SAM_VALUE}

        # To maintain backwards compatibility with previous implementation, we *must* append SAM tag to the start of the
        # tags list. Changing this ordering will trigger a update on Lambda Function resource. Even though this
        # does not change the actual content of the tags, we don't want to trigger update of a resource without
        # customer's knowledge.
        return get_tag_list(sam_tag) + get_tag_list(additional_tags) + get_tag_list(tags)

    def _check_tag(self, reserved_tag_name, tags):
        if reserved_tag_name in tags:
            raise InvalidResourceException(
                self.logical_id,
                f"{reserved_tag_name} is a reserved Tag key name and "
                "cannot be set on your resource. "
                "Please change the tag key in the "
                "input.",
            )

    def _resolve_string_parameter(self, intrinsics_resolver, parameter_value, parameter_name):
        if not parameter_value:
            return parameter_value
        value = intrinsics_resolver.resolve_parameter_refs(parameter_value)

        if not isinstance(value, str) and not isinstance(value, dict):
            raise InvalidResourceException(
                self.logical_id,
                "Could not resolve parameter for '{}' or parameter is not a String.".format(parameter_name),
            )
        return value


class ResourceTypeResolver(object):
    """ResourceTypeResolver maps Resource Types to Resource classes, e.g. AWS::Serverless::Function to
    samtranslator.model.sam_resources.SamFunction."""

    def __init__(self, *modules):
        """Initializes the ResourceTypeResolver from the given modules.

        :param modules: one or more Python modules containing Resource definitions
        """
        self.resource_types = {}
        for module in modules:
            # Get all classes in the specified module which have a class variable resource_type.
            for _, resource_class in inspect.getmembers(
                module,
                lambda cls: inspect.isclass(cls)
                and cls.__module__ == module.__name__
                and hasattr(cls, "resource_type"),
            ):
                self.resource_types[resource_class.resource_type] = resource_class

    def can_resolve(self, resource_dict):
        if not isinstance(resource_dict, dict) or not isinstance(resource_dict.get("Type"), str):
            return False

        return resource_dict["Type"] in self.resource_types

    def resolve_resource_type(self, resource_dict):
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
