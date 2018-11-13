import copy

from samtranslator.model import ResourceTypeResolver, sam_resources
from samtranslator.translator.verify_logical_id import verify_unique_logical_id
from samtranslator.model.preferences.deployment_preference_collection import DeploymentPreferenceCollection
from samtranslator.model.exceptions import InvalidDocumentException, InvalidResourceException, DuplicateLogicalIdException, \
    InvalidEventException
from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.intrinsics.resource_refs import SupportedResourceReferences
from samtranslator.plugins.api.default_definition_body_plugin import DefaultDefinitionBodyPlugin
from samtranslator.plugins import SamPlugins
from samtranslator.plugins.globals.globals_plugin import GlobalsPlugin
from samtranslator.plugins.policies.policy_templates_plugin import PolicyTemplatesForFunctionPlugin
from samtranslator.policy_template_processor.processor import PolicyTemplatesProcessor

class Translator:
    """Translates SAM templates into CloudFormation templates
    """
    def __init__(self, managed_policy_map, sam_parser, plugins=None):
        """
        :param dict managed_policy_map: Map of managed policy names to the ARNs
        :param sam_parser: Instance of a SAM Parser
        :param list of samtranslator.plugins.BasePlugin plugins: List of plugins to be installed in the translator, in addition
            to the default ones.
        """
        self.managed_policy_map = managed_policy_map
        self.plugins = plugins
        self.sam_parser = sam_parser

    def translate(self, sam_template, parameter_values):
        """Loads the SAM resources from the given SAM manifest, replaces them with their corresponding
        CloudFormation resources, and returns the resulting CloudFormation template.

        :param dict sam_template: the SAM manifest, as loaded by json.load() or yaml.load(), or as provided by \
                CloudFormation transforms.
        :param dict parameter_values: Map of template parameter names to their values. It is a required parameter that
                should at least be an empty map. By providing an empty map, the caller explicitly opts-into the idea that
                some functionality that relies on resolving parameter references might not work as expected
                (ex: auto-creating new Lambda Version when CodeUri contains reference to template parameter). This is why
                this parameter is required

        :returns: a copy of the template with SAM resources replaced with the corresponding CloudFormation, which may \
                be dumped into a valid CloudFormation JSON or YAML template
        """
        # Create & Install plugins
        sam_plugins = prepare_plugins(self.plugins)
        parameter_values = self._add_default_parameter_values(sam_template, parameter_values)

        self.sam_parser.parse(
            sam_template=sam_template,
            parameter_values=parameter_values,
            sam_plugins=sam_plugins
        )

        template = copy.deepcopy(sam_template)
        macro_resolver = ResourceTypeResolver(sam_resources)
        intrinsics_resolver = IntrinsicsResolver(parameter_values)
        deployment_preference_collection = DeploymentPreferenceCollection()
        supported_resource_refs = SupportedResourceReferences()
        document_errors = []

        for logical_id, resource_dict in self._get_resources_to_iterate(sam_template, macro_resolver):
            try:
                macro = macro_resolver\
                    .resolve_resource_type(resource_dict)\
                    .from_dict(logical_id, resource_dict, sam_plugins=sam_plugins)

                kwargs = macro.resources_to_link(sam_template['Resources'])
                kwargs['managed_policy_map'] = self.managed_policy_map
                kwargs['intrinsics_resolver'] = intrinsics_resolver
                kwargs['deployment_preference_collection'] = deployment_preference_collection
                translated = macro.to_cloudformation(**kwargs)

                supported_resource_refs = macro.get_resource_references(translated, supported_resource_refs)

                del template['Resources'][logical_id]
                for resource in translated:
                    if verify_unique_logical_id(resource, sam_template['Resources']):
                        template['Resources'].update(resource.to_dict())
                    else:
                        document_errors.append(DuplicateLogicalIdException(
                            logical_id, resource.logical_id, resource.resource_type))
            except (InvalidResourceException, InvalidEventException) as e:
                document_errors.append(e)

        if deployment_preference_collection.any_enabled():
            template['Resources'].update(deployment_preference_collection.codedeploy_application.to_dict())

            if not deployment_preference_collection.can_skip_service_role():
                template['Resources'].update(deployment_preference_collection.codedeploy_iam_role.to_dict())

            for logical_id in deployment_preference_collection.enabled_logical_ids():
                template['Resources'].update(deployment_preference_collection.deployment_group(logical_id).to_dict())
        
        # Cleanup
        if 'Transform' in template:
            del template['Transform']

        if len(document_errors) is 0:
            template = intrinsics_resolver.resolve_sam_resource_refs(template, supported_resource_refs)
            return template
        else:
            raise InvalidDocumentException(document_errors)

    # private methods
    def _get_resources_to_iterate(self, sam_template, macro_resolver):
        """
        Returns a list of resources to iterate, order them based on the following order:

            1. AWS::Serverless::Function - because API Events need to modify the corresponding Serverless::Api resource.
            2. AWS::Serverless::Api
            3. Anything else

        This is necessary because a Function resource with API Events will modify the API resource's Swagger JSON.
        Therefore API resource needs to be parsed only after all the Swagger modifications are complete.

        :param dict sam_template: SAM template
        :param macro_resolver: Resolver that knows if a resource can be processed or not
        :return list: List containing tuple of (logicalId, resource_dict) in the order of processing
        """

        functions = []
        apis = []
        others = []
        resources = sam_template["Resources"]

        for logicalId, resource in resources.items():

            data = (logicalId, resource)

            # Skip over the resource if it is not a SAM defined Resource
            if not macro_resolver.can_resolve(resource):
                continue
            elif resource["Type"] == "AWS::Serverless::Function":
                functions.append(data)
            elif resource["Type"] == "AWS::Serverless::Api":
                apis.append(data)
            else:
                others.append(data)

        return functions + apis + others

    # Ideally this should belong to a separate class called "Parameters" or something that knows how to manage parameters. An instance of this class should be passed as input to the Translate class.
    def _add_default_parameter_values(self, sam_template, parameter_values):
        """
        Method to read default values for template parameters and merge with user supplied values.

        Example:
        If the template contains the following parameters defined

        Parameters:
            Param1:
                Type: String
                Default: default_value
            Param2:
                Type: String
                Default: default_value

        And, the user explicitly provided the following parameter values:

        {
            Param2: "new value"
        }

        then, this method will grab default value for Param1 and return the following result:

        {
            Param1: "default_value",
            Param2: "new value"
        }


        :param dict sam_template: SAM template
        :param dict parameter_values: Dictionary of parameter values provided by the user
        :return dict: Merged parameter values
        """

        parameter_definition = sam_template.get("Parameters", None)
        if not parameter_definition or not isinstance(parameter_definition, dict):
            return parameter_values

        default_values = {}
        for param_name, value in parameter_definition.items():
            if isinstance(value, dict) and "Default" in value:
                default_values[param_name] = value["Default"]

        # Any explicitly provided value must override the default
        default_values.update(parameter_values)

        return default_values

def prepare_plugins(plugins):
    """
    Creates & returns a plugins object with the given list of plugins installed. In addition to the given plugins,
    we will also install a few "required" plugins that are necessary to provide complete support for SAM template spec.

    :param list of samtranslator.plugins.BasePlugin plugins: List of plugins to install
    :return samtranslator.plugins.SamPlugins: Instance of `SamPlugins`
    """

    required_plugins = [
        DefaultDefinitionBodyPlugin(),
        make_implicit_api_plugin(),
        GlobalsPlugin(),
        make_policy_template_for_function_plugin(),
    ]

    plugins = [] if not plugins else plugins

    # Execute customer's plugins first before running SAM plugins. It is very important to retain this order because
    # other plugins will be dependent on this ordering.
    return SamPlugins(plugins + required_plugins)


def make_implicit_api_plugin():
    # This is necessary to prevent a circular dependency on imports when loading package
    from samtranslator.plugins.api.implicit_api_plugin import ImplicitApiPlugin
    return ImplicitApiPlugin()


def make_policy_template_for_function_plugin():
    """
    Constructs an instance of policy templates processing plugin using default policy templates JSON data

    :return plugins.policies.policy_templates_plugin.PolicyTemplatesForFunctionPlugin: Instance of the plugin
    """

    policy_templates = PolicyTemplatesProcessor.get_default_policy_templates_json()
    processor = PolicyTemplatesProcessor(policy_templates)
    return PolicyTemplatesForFunctionPlugin(processor)
