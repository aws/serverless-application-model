from samtranslator.plugins import BasePlugin
from samtranslator.model.function_policies import FunctionPolicies, PolicyTypes
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.policy_template_processor.exceptions import InsufficientParameterValues, InvalidParameterValues


class PolicyTemplatesForFunctionPlugin(BasePlugin):
    """
    Use this plugin to allow the usage of Policy Templates in `Policies` section of AWS::Serverless::Function resource.
    This plugin runs a `before_transform_resource` hook and converts policy templates into regular policy statements
    for the core SAM translator to take care of.
    """

    _plugin_name = ""
    SUPPORTED_RESOURCE_TYPE = "AWS::Serverless::Function"

    def __init__(self, policy_template_processor):
        """
        Initialize the plugin.

        :param policy_template_processor: Instance of the PolicyTemplateProcessor that knows how to convert policy
            template to a statement
        """

        # Plugin name is the class name for easy disambiguation
        _plugin_name = PolicyTemplatesForFunctionPlugin.__name__
        super(PolicyTemplatesForFunctionPlugin, self).__init__(_plugin_name)

        self._policy_template_processor = policy_template_processor

    def on_before_transform_resource(self, logical_id, resource_type, resource_properties):
        """
        Hook method that gets called before "each" SAM resource gets processed

        :param string logical_id: Logical ID of the resource being processed
        :param string resource_type: Type of the resource being processed
        :param dict resource_properties: Properties of the resource
        :return: Nothing
        """

        if not self._is_supported(resource_type):
            return

        function_policies = FunctionPolicies(resource_properties, self._policy_template_processor)

        if len(function_policies) == 0:
            # No policies to process
            return

        result = []
        for policy_entry in function_policies.get():

            if policy_entry.type is not PolicyTypes.POLICY_TEMPLATE:
                # If we don't know the type, skip processing and pass to result as is.
                result.append(policy_entry.data)
                continue

            # We are processing policy templates. We know they have a particular structure:
            # {"templateName": { parameter_values_dict }}
            template_data = policy_entry.data
            template_name = list(template_data.keys())[0]
            template_parameters = list(template_data.values())[0]

            try:

                # 'convert' will return a list of policy statements
                result.append(self._policy_template_processor.convert(template_name, template_parameters))

            except InsufficientParameterValues as ex:
                # Exception's message will give lot of specific details
                raise InvalidResourceException(logical_id, str(ex))
            except InvalidParameterValues:
                raise InvalidResourceException(logical_id,
                                               "Must specify valid parameter values for policy template '{}'"
                                               .format(template_name))

        # Save the modified policies list to the input
        resource_properties[FunctionPolicies.POLICIES_PROPERTY_NAME] = result

    def _is_supported(self, resource_type):
        """
        Is this resource supported by this plugin?

        :param string resource_type: Type of the resource
        :return: True, if this plugin supports this resource. False otherwise
        """
        return resource_type == self.SUPPORTED_RESOURCE_TYPE
