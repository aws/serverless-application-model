from typing import Dict, List

from samtranslator.public.sdk.resource import SamResourceType
from samtranslator.public.intrinsics import is_intrinsics
from samtranslator.swagger.swagger import SwaggerEditor


class Globals(object):
    """
    Class to parse and process Globals section in SAM template. If a property is specified at Global section for
    say Function, then this class will add it to each resource of AWS::Serverless::Function type.
    """

    # Key of the dictionary containing Globals section in SAM template
    _KEYWORD = "Globals"
    _RESOURCE_PREFIX = "AWS::Serverless::"
    _OPENAPIVERSION = "OpenApiVersion"
    _API_TYPE = "AWS::Serverless::Api"
    _MANAGE_SWAGGER = "__MANAGE_SWAGGER"

    supported_properties = {
        # Everything on Serverless::Function except Role, Policies, FunctionName, Events
        SamResourceType.Function.value: [
            "Handler",
            "Runtime",
            "CodeUri",
            "DeadLetterQueue",
            "Description",
            "MemorySize",
            "Timeout",
            "VpcConfig",
            "Environment",
            "Tags",
            "Tracing",
            "KmsKeyArn",
            "AutoPublishAlias",
            "Layers",
            "DeploymentPreference",
            "PermissionsBoundary",
            "ReservedConcurrentExecutions",
            "ProvisionedConcurrencyConfig",
            "AssumeRolePolicyDocument",
            "EventInvokeConfig",
            "FileSystemConfigs",
            "CodeSigningConfigArn",
            "Architectures",
            "EphemeralStorage",
            "FunctionUrlConfig",
        ],
        # Everything except
        #   DefinitionBody: because its hard to reason about merge of Swagger dictionaries
        #   StageName: Because StageName cannot be overridden for Implicit APIs because of the current plugin
        #              architecture
        SamResourceType.Api.value: [
            "Auth",
            "Name",
            "DefinitionUri",
            "CacheClusterEnabled",
            "CacheClusterSize",
            "Variables",
            "EndpointConfiguration",
            "MethodSettings",
            "BinaryMediaTypes",
            "MinimumCompressionSize",
            "Cors",
            "GatewayResponses",
            "AccessLogSetting",
            "CanarySetting",
            "TracingEnabled",
            "OpenApiVersion",
            "Domain",
        ],
        SamResourceType.HttpApi.value: [
            "Auth",
            "AccessLogSettings",
            "StageVariables",
            "Tags",
            "CorsConfiguration",
            "DefaultRouteSettings",
            "Domain",
            "RouteSettings",
            "FailOnWarnings",
        ],
        SamResourceType.SimpleTable.value: ["SSESpecification"],
    }
    # unreleased_properties *must be* part of supported_properties too
    unreleased_properties: Dict[str, List[str]] = {}

    def __init__(self, template):
        """
        Constructs an instance of this object

        :param dict template: SAM template to be parsed
        """
        self.supported_resource_section_names = [
            x.replace(self._RESOURCE_PREFIX, "") for x in self.supported_properties.keys()
        ]
        # Sort the names for stability in list ordering
        self.supported_resource_section_names.sort()

        self.template_globals = {}

        if self._KEYWORD in template:
            self.template_globals = self._parse(template[self._KEYWORD])

    def merge(self, resource_type, resource_properties):
        """
        Adds global properties to the resource, if necessary. This method is a no-op if there are no global properties
        for this resource type

        :param string resource_type: Type of the resource (Ex: AWS::Serverless::Function)
        :param dict resource_properties: Properties of the resource that need to be merged
        :return dict: Merged properties of the resource
        """

        if resource_type not in self.template_globals:
            # Nothing to do. Return the template unmodified
            return resource_properties

        global_props = self.template_globals[resource_type]

        return global_props.merge(resource_properties)

    @classmethod
    def del_section(cls, template):
        """
        Helper method to delete the Globals section altogether from the template

        :param dict template: SAM template
        :return: Modified SAM template with Globals section
        """

        if cls._KEYWORD in template:
            del template[cls._KEYWORD]

    @classmethod
    def fix_openapi_definitions(cls, template):
        """
        Helper method to postprocess the resources to make sure the swagger doc version matches
        the one specified on the resource with flag OpenApiVersion.

        This is done postprocess in globals because, the implicit api plugin runs before globals, \
        and at that point the global flags aren't applied on each resource, so we do not know \
        whether OpenApiVersion flag is specified. Running the globals plugin before implicit api \
        was a risky change, so we decided to postprocess the openapi version here.

        To make sure we don't modify customer defined swagger, we also check for __MANAGE_SWAGGER flag.

        :param dict template: SAM template
        :return: Modified SAM template with corrected swagger doc matching the OpenApiVersion.
        """
        resources = template.get("Resources", {})

        for _, resource in resources.items():
            if ("Type" in resource) and (resource["Type"] == cls._API_TYPE):
                properties = resource["Properties"]
                if (
                    (cls._OPENAPIVERSION in properties)
                    and (cls._MANAGE_SWAGGER in properties)
                    and SwaggerEditor.safe_compare_regex_with_string(
                        SwaggerEditor.get_openapi_version_3_regex(), properties[cls._OPENAPIVERSION]
                    )
                ):
                    if not isinstance(properties[cls._OPENAPIVERSION], str):
                        properties[cls._OPENAPIVERSION] = str(properties[cls._OPENAPIVERSION])
                        resource["Properties"] = properties
                    if "DefinitionBody" in properties:
                        definition_body = properties["DefinitionBody"]
                        definition_body["openapi"] = properties[cls._OPENAPIVERSION]
                        if definition_body.get("swagger"):
                            del definition_body["swagger"]

    def _parse(self, globals_dict):
        """
        Takes a SAM template as input and parses the Globals section

        :param globals_dict: Dictionary representation of the Globals section
        :return: Processed globals dictionary which can be used to quickly identify properties to merge
        :raises: InvalidResourceException if the input contains properties that we don't support
        """

        globals = {}
        if not isinstance(globals_dict, dict):
            raise InvalidGlobalsSectionException(self._KEYWORD, "It must be a non-empty dictionary")

        for section_name, properties in globals_dict.items():
            resource_type = self._make_resource_type(section_name)

            if resource_type not in self.supported_properties:
                raise InvalidGlobalsSectionException(
                    self._KEYWORD,
                    "'{section}' is not supported. "
                    "Must be one of the following values - {supported}".format(
                        section=section_name, supported=self.supported_resource_section_names
                    ),
                )

            if not isinstance(properties, dict):
                raise InvalidGlobalsSectionException(self._KEYWORD, "Value of ${section} must be a dictionary")

            supported = self.supported_properties[resource_type]
            supported_displayed = [
                prop for prop in supported if prop not in self.unreleased_properties.get(resource_type, [])
            ]
            for key, value in properties.items():
                if key not in supported:
                    raise InvalidGlobalsSectionException(
                        self._KEYWORD,
                        "'{key}' is not a supported property of '{section}'. "
                        "Must be one of the following values - {supported}".format(
                            key=key, section=section_name, supported=supported_displayed
                        ),
                    )

            # Store all Global properties in a map with key being the AWS::Serverless::* resource type
            globals[resource_type] = GlobalProperties(properties)

        return globals

    def _make_resource_type(self, key):
        return self._RESOURCE_PREFIX + key


class GlobalProperties(object):
    """
    Object holding the global properties of given type. It also contains methods to perform a merge between
    Global & resource-level properties. Here are the different cases during the merge and how we handle them:

    **Primitive Type (String, Integer, Boolean etc)**
    If either global & local are of primitive types, then we the value at local will overwrite global.

    Example:

      ```
      Global:
        Function:
          Runtime: nodejs

      Function:
         Runtime: python
      ```

    After processing, Function resource will contain:
      ```
      Runtime: python
      ```

    **Different data types**
    If a value at Global is a array, but local is a dictionary, then we will simply use the local value.
    There is no merge to be done here. Similarly for other data type mismatches between global & local value.

    Example:

      ```
      Global:
        Function:
          CodeUri: s3://bucket/key

      Function:
         CodeUri:
           Bucket: foo
           Key: bar
      ```


    After processing, Function resource will contain:
      ```
        CodeUri:
           Bucket: foo
           Key: bar
      ```

    **Arrays**
    If a value is an array at both global & local level, we will simply concatenate them without de-duplicating.
    Customers can easily fix the duplicates:

    Example:

      ```
       Global:
         Function:
           Policy: [Policy1, Policy2]

       Function:
         Policy: [Policy1, Policy3]
      ```

    After processing, Function resource will contain:
    (notice the duplicates)
      ```
       Policy: [Policy1, Policy2, Policy1, Policy3]
      ```

    **Dictionaries**
    If both global & local value is a dictionary, we will recursively merge properties. If a value is one of the above
    types, they will handled according the above rules.

    Example:

      ```
       Global:
         EnvironmentVariables:
           TableName: foo
           DBName: generic-db

       Function:
          EnvironmentVariables:
            DBName: mydb
            ConnectionString: bar
      ```

    After processing, Function resource will contain:
      ```
          EnvironmentVariables:
            TableName: foo
            DBName: mydb
            ConnectionString: bar
      ```

    ***Optional Properties***
    Some resources might have optional properties with default values when it is skipped. If an optional property
    is skipped at local level, an explicitly specified value at global level will be used.

    Example:
      Global:
        DeploymentPreference:
           Enabled: False
           Type: Canary

      Function:
        DeploymentPreference:
          Type: Linear

    After processing, Function resource will contain:
      ```
      DeploymentPreference:
         Enabled: False
         Type: Linear
      ```
    (in other words, Deployments will be turned off for the Function)

    """

    def __init__(self, global_properties):
        self.global_properties = global_properties

    def merge(self, local_properties):
        """
        Merge Global & local level properties according to the above rules

        :return local_properties: Dictionary of local properties
        """
        return self._do_merge(self.global_properties, local_properties)

    def _do_merge(self, global_value, local_value):
        """
        Actually perform the merge operation for the given inputs. This method is used as part of the recursion.
        Therefore input values can be of any type. So is the output.

        :param global_value: Global value to be merged
        :param local_value: Local value to be merged
        :return: Merged result
        """

        token_global = self._token_of(global_value)
        token_local = self._token_of(local_value)

        # The following statements codify the rules explained in the doctring above
        if token_global != token_local:
            return self._prefer_local(global_value, local_value)

        elif self.TOKEN.PRIMITIVE == token_global == token_local:
            return self._prefer_local(global_value, local_value)

        elif self.TOKEN.DICT == token_global == token_local:
            return self._merge_dict(global_value, local_value)

        elif self.TOKEN.LIST == token_global == token_local:
            return self._merge_lists(global_value, local_value)

        else:
            raise TypeError(
                "Unsupported type of objects. GlobalType={}, LocalType={}".format(token_global, token_local)
            )

    def _merge_lists(self, global_list, local_list):
        """
        Merges the global list with the local list. List merging is simply a concatenation = global + local

        :param global_list: Global value list
        :param local_list: Local value list
        :return: New merged list with the elements shallow copied
        """

        return global_list + local_list

    def _merge_dict(self, global_dict, local_dict):
        """
        Merges the two dictionaries together

        :param global_dict: Global dictionary to be merged
        :param local_dict: Local dictionary to be merged
        :return: New merged dictionary with values shallow copied
        """

        # Local has higher priority than global. So iterate over local dict and merge into global if keys are overridden
        global_dict = global_dict.copy()

        for key in local_dict.keys():

            if key in global_dict:
                # Both local & global contains the same key. Let's do a merge.
                global_dict[key] = self._do_merge(global_dict[key], local_dict[key])

            else:
                # Key is not in globals, just in local. Copy it over
                global_dict[key] = local_dict[key]

        return global_dict

    def _prefer_local(self, global_value, local_value):
        """
        Literally returns the local value whatever it may be. This method is useful to provide a unified implementation
        for cases that don't require special handling.

        :param global_value: Global value
        :param local_value: Local value
        :return: Simply returns the local value
        """
        return local_value

    def _token_of(self, input):
        """
        Returns the token type of the input.

        :param input: Input whose type is to be determined
        :return TOKENS: Token type of the input
        """

        if isinstance(input, dict):

            # Intrinsic functions are always dicts
            if is_intrinsics(input):
                # Intrinsic functions are handled *exactly* like a primitive type because
                # they resolve to a primitive type when creating a stack with CloudFormation
                return self.TOKEN.PRIMITIVE
            else:
                return self.TOKEN.DICT

        elif isinstance(input, list):
            return self.TOKEN.LIST

        else:
            return self.TOKEN.PRIMITIVE

    class TOKEN:
        """
        Enum of tokens used in the merging
        """

        PRIMITIVE = "primitive"
        DICT = "dict"
        LIST = "list"


class InvalidGlobalsSectionException(Exception):
    """Exception raised when a Globals section is is invalid.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, logical_id, message):
        self._logical_id = logical_id
        self._message = message

    @property
    def message(self):
        return "'{}' section is invalid. {}".format(self._logical_id, self._message)
