import copy

from samtranslator.metrics.method_decorator import MetricsMethodWrapperSingleton
from samtranslator.metrics.metrics import DummyMetricsPublisher, Metrics

from samtranslator.feature_toggle.feature_toggle import (
    FeatureToggle,
    FeatureToggleDefaultConfigProvider,
)
from samtranslator.model import ResourceTypeResolver, sam_resources
from samtranslator.model.api.api_generator import SharedApiUsagePlan
from samtranslator.translator.verify_logical_id import verify_unique_logical_id
from samtranslator.model.preferences.deployment_preference_collection import DeploymentPreferenceCollection
from samtranslator.model.exceptions import (
    InvalidDocumentException,
    InvalidResourceException,
    DuplicateLogicalIdException,
    InvalidEventException,
    InvalidTemplateException,
)
from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.intrinsics.actions import FindInMapAction
from samtranslator.intrinsics.resource_refs import SupportedResourceReferences
from samtranslator.plugins.api.default_definition_body_plugin import DefaultDefinitionBodyPlugin
from samtranslator.plugins.application.serverless_app_plugin import ServerlessAppPlugin
from samtranslator.plugins import LifeCycleEvents
from samtranslator.plugins.sam_plugins import SamPlugins
from samtranslator.plugins.globals.globals_plugin import GlobalsPlugin
from samtranslator.plugins.policies.policy_templates_plugin import PolicyTemplatesForResourcePlugin
from samtranslator.policy_template_processor.processor import PolicyTemplatesProcessor
from samtranslator.sdk.parameter import SamParameterValues
from samtranslator.translator.arn_generator import ArnGenerator
from samtranslator.model.eventsources.push import Api


class Translator:
    """Translates SAM templates into CloudFormation templates"""

    def __init__(self, managed_policy_map, sam_parser, plugins=None, boto_session=None, metrics=None):
        """
        :param dict managed_policy_map: Map of managed policy names to the ARNs
        :param sam_parser: Instance of a SAM Parser
        :param list of samtranslator.plugins.BasePlugin plugins: List of plugins to be installed in the translator,
            in addition to the default ones.
        """
        self.managed_policy_map = managed_policy_map
        self.plugins = plugins
        self.sam_parser = sam_parser
        self.feature_toggle = None
        self.boto_session = boto_session
        self.metrics = metrics if metrics else Metrics("ServerlessTransform", DummyMetricsPublisher())
        MetricsMethodWrapperSingleton.set_instance(self.metrics)
        self._translated_resouce_mapping = {}

        if self.boto_session:
            ArnGenerator.BOTO_SESSION_REGION_NAME = self.boto_session.region_name

    def _get_function_names(self, resource_dict, intrinsics_resolver):
        """
        :param resource_dict: AWS::Serverless::Function resource is provided as input
        :param intrinsics_resolver: to resolve intrinsics for function_name
        :return: a dictionary containing api_logical_id as the key and concatenated String of all function_names
                 associated with this api as the value
        """
        if resource_dict.get("Type", "").strip() == "AWS::Serverless::Function":
            events_properties = resource_dict.get("Properties", {}).get("Events", {})
            events = list(events_properties.values()) if events_properties else []
            for item in events:
                # If the function event type is `Api` then gets the function name and
                # adds to the function_names dict with key as the api_name and value as the function_name
                item_properties = item.get("Properties", {})
                if item.get("Type") == "Api" and item_properties.get("RestApiId"):
                    rest_api = item_properties.get("RestApiId")
                    api_name = Api.get_rest_api_id_string(rest_api)
                    if isinstance(api_name, str):
                        resource_dict_copy = copy.deepcopy(resource_dict)
                        function_name = intrinsics_resolver.resolve_parameter_refs(
                            resource_dict_copy.get("Properties").get("FunctionName")
                        )
                        if function_name:
                            self.function_names[api_name] = str(self.function_names.get(api_name, "")) + str(
                                function_name
                            )
        return self.function_names

    def translate(self, sam_template, parameter_values, feature_toggle=None, passthrough_metadata=False):
        """Loads the SAM resources from the given SAM manifest, replaces them with their corresponding
        CloudFormation resources, and returns the resulting CloudFormation template.

        :param dict sam_template: the SAM manifest, as loaded by json.load() or yaml.load(), or as provided by \
                CloudFormation transforms.
        :param dict parameter_values: Map of template parameter names to their values. It is a required parameter that
                should at least be an empty map. By providing an empty map, the caller explicitly opts-into the idea
                that some functionality that relies on resolving parameter references might not work as expected
                (ex: auto-creating new Lambda Version when CodeUri contains reference to template parameter). This is
                why this parameter is required

        :returns: a copy of the template with SAM resources replaced with the corresponding CloudFormation, which may \
                be dumped into a valid CloudFormation JSON or YAML template
        """
        self.feature_toggle = (
            feature_toggle
            if feature_toggle
            else FeatureToggle(FeatureToggleDefaultConfigProvider(), stage=None, account_id=None, region=None)
        )
        self.function_names = dict()
        self.redeploy_restapi_parameters = dict()
        sam_parameter_values = SamParameterValues(parameter_values)
        sam_parameter_values.add_default_parameter_values(sam_template)
        sam_parameter_values.add_pseudo_parameter_values(self.boto_session)
        parameter_values = sam_parameter_values.parameter_values
        # Create & Install plugins
        sam_plugins = prepare_plugins(self.plugins, parameter_values)

        self.sam_parser.parse(sam_template=sam_template, parameter_values=parameter_values, sam_plugins=sam_plugins)

        template = copy.deepcopy(sam_template)
        macro_resolver = ResourceTypeResolver(sam_resources)
        intrinsics_resolver = IntrinsicsResolver(parameter_values)
        mappings_resolver = IntrinsicsResolver(
            template.get("Mappings", {}), {FindInMapAction.intrinsic_name: FindInMapAction()}
        )
        deployment_preference_collection = DeploymentPreferenceCollection()
        supported_resource_refs = SupportedResourceReferences()
        shared_api_usage_plan = SharedApiUsagePlan()
        document_errors = []
        changed_logical_ids = {}
        route53_record_set_groups = {}
        for logical_id, resource_dict in self._get_resources_to_iterate(sam_template, macro_resolver):
            try:
                macro = macro_resolver.resolve_resource_type(resource_dict).from_dict(
                    logical_id, resource_dict, sam_plugins=sam_plugins
                )

                kwargs = macro.resources_to_link(sam_template["Resources"])
                kwargs["managed_policy_map"] = self.managed_policy_map
                kwargs["intrinsics_resolver"] = intrinsics_resolver
                kwargs["mappings_resolver"] = mappings_resolver
                kwargs["deployment_preference_collection"] = deployment_preference_collection
                kwargs["conditions"] = template.get("Conditions")
                # add the value of FunctionName property if the function is referenced with the api resource
                self.redeploy_restapi_parameters["function_names"] = self._get_function_names(
                    resource_dict, intrinsics_resolver
                )
                kwargs["redeploy_restapi_parameters"] = self.redeploy_restapi_parameters
                kwargs["shared_api_usage_plan"] = shared_api_usage_plan
                kwargs["feature_toggle"] = self.feature_toggle
                kwargs["route53_record_set_groups"] = route53_record_set_groups
                translated = macro.to_cloudformation(**kwargs)

                supported_resource_refs = macro.get_resource_references(translated, supported_resource_refs)

                # Some resources mutate their logical ids. Track those to change all references to them:
                if logical_id != macro.logical_id:
                    changed_logical_ids[logical_id] = macro.logical_id

                del template["Resources"][logical_id]
                for resource in translated:
                    if verify_unique_logical_id(resource, sam_template["Resources"]):
                        # For each generated resource, pass through existing metadata that may exist on the original SAM resource.
                        _r = resource.to_dict()
                        if resource_dict.get("Metadata") and passthrough_metadata:
                            if not template["Resources"].get(resource.logical_id):
                                _r[resource.logical_id]["Metadata"] = resource_dict["Metadata"]
                        template["Resources"].update(_r)
                    else:
                        document_errors.append(
                            DuplicateLogicalIdException(logical_id, resource.logical_id, resource.resource_type)
                        )
            except (InvalidResourceException, InvalidEventException, InvalidTemplateException) as e:
                document_errors.append(e)

        if deployment_preference_collection.any_enabled():
            template["Resources"].update(deployment_preference_collection.get_codedeploy_application().to_dict())
            if deployment_preference_collection.needs_resource_condition():
                new_conditions = deployment_preference_collection.create_aggregate_deployment_condition()
                if new_conditions:
                    template.get("Conditions").update(new_conditions)

            if not deployment_preference_collection.can_skip_service_role():
                template["Resources"].update(deployment_preference_collection.get_codedeploy_iam_role().to_dict())

            for logical_id in deployment_preference_collection.enabled_logical_ids():
                try:
                    template["Resources"].update(
                        deployment_preference_collection.deployment_group(logical_id).to_dict()
                    )
                except InvalidResourceException as e:
                    document_errors.append(e)

        # Run the after-transform plugin target
        try:
            sam_plugins.act(LifeCycleEvents.after_transform_template, template)
        except (InvalidDocumentException, InvalidResourceException, InvalidTemplateException) as e:
            document_errors.append(e)

        # Cleanup
        if "Transform" in template:
            del template["Transform"]

        if len(document_errors) == 0:
            template = intrinsics_resolver.resolve_sam_resource_id_refs(template, changed_logical_ids)
            template = intrinsics_resolver.resolve_sam_resource_refs(template, supported_resource_refs)
            return template
        else:
            raise InvalidDocumentException(document_errors)

    # private methods
    def _get_resources_to_iterate(self, sam_template, macro_resolver):
        """
        Returns a list of resources to iterate, order them based on the following order:

            1. AWS::Serverless::Function - because API Events need to modify the corresponding Serverless::Api resource.
            2. AWS::Serverless::StateMachine - because API Events need to modify the corresponding Serverless::Api resource.
            3. AWS::Serverless::Api
            4. Anything else

        This is necessary because a Function or State Machine resource with API Events will modify the API resource's Swagger JSON.
        Therefore API resource needs to be parsed only after all the Swagger modifications are complete.

        :param dict sam_template: SAM template
        :param macro_resolver: Resolver that knows if a resource can be processed or not
        :return list: List containing tuple of (logicalId, resource_dict) in the order of processing
        """

        functions = []
        statemachines = []
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
            elif resource["Type"] == "AWS::Serverless::StateMachine":
                statemachines.append(data)
            elif resource["Type"] == "AWS::Serverless::Api" or resource["Type"] == "AWS::Serverless::HttpApi":
                apis.append(data)
            else:
                others.append(data)

        return functions + statemachines + apis + others


def prepare_plugins(plugins, parameters=None):
    """
    Creates & returns a plugins object with the given list of plugins installed. In addition to the given plugins,
    we will also install a few "required" plugins that are necessary to provide complete support for SAM template spec.

    :param plugins: list of samtranslator.plugins.BasePlugin plugins: List of plugins to install
    :param parameters: Dictionary of parameter values
    :return samtranslator.plugins.SamPlugins: Instance of `SamPlugins`
    """

    if parameters is None:
        parameters = {}
    required_plugins = [
        DefaultDefinitionBodyPlugin(),
        make_implicit_rest_api_plugin(),
        make_implicit_http_api_plugin(),
        GlobalsPlugin(),
        make_policy_template_for_function_plugin(),
    ]

    plugins = [] if not plugins else plugins

    # If a ServerlessAppPlugin does not yet exist, create one and add to the beginning of the required plugins list.
    if not any(isinstance(plugin, ServerlessAppPlugin) for plugin in plugins):
        required_plugins.insert(0, ServerlessAppPlugin(parameters=parameters))

    # Execute customer's plugins first before running SAM plugins. It is very important to retain this order because
    # other plugins will be dependent on this ordering.
    return SamPlugins(plugins + required_plugins)


def make_implicit_rest_api_plugin():
    # This is necessary to prevent a circular dependency on imports when loading package
    from samtranslator.plugins.api.implicit_rest_api_plugin import ImplicitRestApiPlugin

    return ImplicitRestApiPlugin()


def make_implicit_http_api_plugin():
    # This is necessary to prevent a circular dependency on imports when loading package
    from samtranslator.plugins.api.implicit_http_api_plugin import ImplicitHttpApiPlugin

    return ImplicitHttpApiPlugin()


def make_policy_template_for_function_plugin():
    """
    Constructs an instance of policy templates processing plugin using default policy templates JSON data

    :return plugins.policies.policy_templates_plugin.PolicyTemplatesForResourcePlugin: Instance of the plugin
    """

    policy_templates = PolicyTemplatesProcessor.get_default_policy_templates_json()
    processor = PolicyTemplatesProcessor(policy_templates)
    return PolicyTemplatesForResourcePlugin(processor)
