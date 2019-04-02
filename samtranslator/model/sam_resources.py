""" SAM macro definitions """
from six import string_types

import samtranslator.model.eventsources
import samtranslator.model.eventsources.pull
import samtranslator.model.eventsources.push
import samtranslator.model.eventsources.cloudwatchlogs
from .api.api_generator import ApiGenerator
from .s3_utils.uri_parser import construct_s3_location_object
from .tags.resource_tagging import get_tag_list
from samtranslator.model import (PropertyType, SamResourceMacro,
                                 ResourceTypeResolver)
from samtranslator.model.apigateway import ApiGatewayDeployment, ApiGatewayStage
from samtranslator.model.cloudformation import NestedStack
from samtranslator.model.dynamodb import DynamoDBTable
from samtranslator.model.exceptions import (InvalidEventException,
                                            InvalidResourceException)
from samtranslator.model.function_policies import FunctionPolicies, PolicyTypes
from samtranslator.model.iam import IAMRole, IAMRolePolicies
from samtranslator.model.lambda_ import (LambdaFunction, LambdaVersion, LambdaAlias,
                                         LambdaLayerVersion)
from samtranslator.model.types import dict_of, is_str, is_type, list_of, one_of, any_type
from samtranslator.translator import logical_id_generator
from samtranslator.translator.arn_generator import ArnGenerator


class SamFunction(SamResourceMacro):
    """SAM function macro.
    """

    resource_type = 'AWS::Serverless::Function'
    property_types = {
        'FunctionName': PropertyType(False, one_of(is_str(), is_type(dict))),
        'Handler': PropertyType(True, is_str()),
        'Runtime': PropertyType(True, is_str()),
        'CodeUri': PropertyType(False, one_of(is_str(), is_type(dict))),
        'InlineCode': PropertyType(False, one_of(is_str(), is_type(dict))),
        'DeadLetterQueue': PropertyType(False, is_type(dict)),
        'Description': PropertyType(False, is_str()),
        'MemorySize': PropertyType(False, is_type(int)),
        'Timeout': PropertyType(False, is_type(int)),
        'VpcConfig': PropertyType(False, is_type(dict)),
        'Role': PropertyType(False, is_str()),
        'Policies': PropertyType(False, one_of(is_str(), list_of(one_of(is_str(), is_type(dict), is_type(dict))))),
        'PermissionsBoundary': PropertyType(False, is_str()),
        'Environment': PropertyType(False, dict_of(is_str(), is_type(dict))),
        'Events': PropertyType(False, dict_of(is_str(), is_type(dict))),
        'Tags': PropertyType(False, is_type(dict)),
        'Tracing': PropertyType(False, one_of(is_type(dict), is_str())),
        'KmsKeyArn': PropertyType(False, one_of(is_type(dict), is_str())),
        'DeploymentPreference': PropertyType(False, is_type(dict)),
        'ReservedConcurrentExecutions': PropertyType(False, any_type()),
        'Layers': PropertyType(False, list_of(one_of(is_str(), is_type(dict)))),

        # Intrinsic functions in value of Alias property are not supported, yet
        'AutoPublishAlias': PropertyType(False, one_of(is_str())),
        'VersionDescription': PropertyType(False, is_str())
    }
    event_resolver = ResourceTypeResolver(samtranslator.model.eventsources, samtranslator.model.eventsources.pull,
                                          samtranslator.model.eventsources.push,
                                          samtranslator.model.eventsources.cloudwatchlogs)

    # DeadLetterQueue
    dead_letter_queue_policy_actions = {'SQS': 'sqs:SendMessage', 'SNS': 'sns:Publish'}

    # Customers can refer to the following properties of SAM function
    referable_properties = {
        "Alias": LambdaAlias.resource_type,
        "Version": LambdaVersion.resource_type,
    }

    def resources_to_link(self, resources):
        try:
            return {
                'event_resources': self._event_resources_to_link(resources)
            }
        except InvalidEventException as e:
            raise InvalidResourceException(self.logical_id, e.message)

    def to_cloudformation(self, **kwargs):
        """Returns the Lambda function, role, and event resources to which this SAM Function corresponds.

        :param dict kwargs: already-converted resources that may need to be modified when converting this \
        macro to pure CloudFormation
        :returns: a list of vanilla CloudFormation Resources, to which this Function expands
        :rtype: list
        """
        resources = []
        intrinsics_resolver = kwargs["intrinsics_resolver"]

        if self.DeadLetterQueue:
            self._validate_dlq()

        lambda_function = self._construct_lambda_function()
        resources.append(lambda_function)

        lambda_alias = None
        if self.AutoPublishAlias:
            alias_name = self._get_resolved_alias_name("AutoPublishAlias", self.AutoPublishAlias, intrinsics_resolver)
            lambda_version = self._construct_version(lambda_function, intrinsics_resolver=intrinsics_resolver)
            lambda_alias = self._construct_alias(alias_name, lambda_function, lambda_version)
            resources.append(lambda_version)
            resources.append(lambda_alias)

        if self.DeploymentPreference:
            self._validate_deployment_preference_and_add_update_policy(kwargs.get('deployment_preference_collection',
                                                                                  None),
                                                                       lambda_alias, intrinsics_resolver)

        managed_policy_map = kwargs.get('managed_policy_map', {})
        if not managed_policy_map:
            raise Exception('Managed policy map is empty, but should not be.')

        execution_role = None
        if lambda_function.Role is None:
            execution_role = self._construct_role(managed_policy_map)
            lambda_function.Role = execution_role.get_runtime_attr('arn')
            resources.append(execution_role)

        try:
            resources += self._generate_event_resources(lambda_function, execution_role, kwargs['event_resources'],
                                                        lambda_alias=lambda_alias)
        except InvalidEventException as e:
            raise InvalidResourceException(self.logical_id, e.message)

        return resources

    def _get_resolved_alias_name(self, property_name, original_alias_value, intrinsics_resolver):
        """
        Alias names can be supplied as an intrinsic function. This method tries to extract alias name from a reference
        to a parameter. If it cannot completely resolve (ie. if a complex intrinsic function was used), then this
        method raises an exception. If alias name is just a plain string, it will return as is

        :param dict or string original_alias_value: Value of Alias property as provided by the customer
        :param samtranslator.intrinsics.resolver.IntrinsicsResolver intrinsics_resolver: Instance of the resolver that
            knows how to resolve parameter references
        :return string: Alias name
        :raises InvalidResourceException: If the value is a complex intrinsic function that cannot be resolved
        """

        # Try to resolve.
        resolved_alias_name = intrinsics_resolver.resolve_parameter_refs(original_alias_value)

        if not isinstance(resolved_alias_name, string_types):
            # This is still a dictionary which means we are not able to completely resolve intrinsics
            raise InvalidResourceException(self.logical_id,
                                           "'{}' must be a string or a Ref to a template parameter"
                                           .format(property_name))

        return resolved_alias_name

    def _construct_lambda_function(self):
        """Constructs and returns the Lambda function.

        :returns: a list containing the Lambda function and execution role resources
        :rtype: list
        """
        lambda_function = LambdaFunction(self.logical_id, depends_on=self.depends_on,
                                         attributes=self.resource_attributes)

        if self.FunctionName:
            lambda_function.FunctionName = self.FunctionName

        lambda_function.Handler = self.Handler
        lambda_function.Runtime = self.Runtime
        lambda_function.Description = self.Description
        lambda_function.MemorySize = self.MemorySize
        lambda_function.Timeout = self.Timeout
        lambda_function.VpcConfig = self.VpcConfig
        lambda_function.Role = self.Role
        lambda_function.Environment = self.Environment
        lambda_function.Code = self._construct_code_dict()
        lambda_function.KmsKeyArn = self.KmsKeyArn
        lambda_function.ReservedConcurrentExecutions = self.ReservedConcurrentExecutions
        lambda_function.Tags = self._construct_tag_list(self.Tags)
        lambda_function.Layers = self.Layers

        if self.Tracing:
            lambda_function.TracingConfig = {"Mode": self.Tracing}

        if self.DeadLetterQueue:
            lambda_function.DeadLetterConfig = {"TargetArn": self.DeadLetterQueue['TargetArn']}

        return lambda_function

    def _construct_role(self, managed_policy_map):
        """Constructs a Lambda execution role based on this SAM function's Policies property.

        :returns: the generated IAM Role
        :rtype: model.iam.IAMRole
        """
        execution_role = IAMRole(self.logical_id + 'Role', attributes=self.get_passthrough_resource_attributes())
        execution_role.AssumeRolePolicyDocument = IAMRolePolicies.lambda_assume_role_policy()

        managed_policy_arns = [ArnGenerator.generate_aws_managed_policy_arn('service-role/AWSLambdaBasicExecutionRole')]
        if self.Tracing:
            managed_policy_arns.append(ArnGenerator.generate_aws_managed_policy_arn('AWSXrayWriteOnlyAccess'))

        function_policies = FunctionPolicies({"Policies": self.Policies},
                                             # No support for policy templates in the "core"
                                             policy_template_processor=None)
        policy_documents = []

        if self.DeadLetterQueue:
            policy_documents.append(IAMRolePolicies.dead_letter_queue_policy(
                self.dead_letter_queue_policy_actions[self.DeadLetterQueue['Type']],
                self.DeadLetterQueue['TargetArn']))

        for index, policy_entry in enumerate(function_policies.get()):

            if policy_entry.type is PolicyTypes.POLICY_STATEMENT:

                policy_documents.append({
                    'PolicyName': execution_role.logical_id + 'Policy' + str(index),
                    'PolicyDocument': policy_entry.data
                })
            elif policy_entry.type is PolicyTypes.MANAGED_POLICY:

                # There are three options:
                #   Managed Policy Name (string): Try to convert to Managed Policy ARN
                #   Managed Policy Arn (string): Insert it directly into the list
                #   Intrinsic Function (dict): Insert it directly into the list
                #
                # When you insert into managed_policy_arns list, de-dupe to prevent same ARN from showing up twice
                #

                policy_arn = policy_entry.data
                if isinstance(policy_entry.data, string_types) and policy_entry.data in managed_policy_map:
                    policy_arn = managed_policy_map[policy_entry.data]

                # De-Duplicate managed policy arns before inserting. Mainly useful
                # when customer specifies a managed policy which is already inserted
                # by SAM, such as AWSLambdaBasicExecutionRole
                if policy_arn not in managed_policy_arns:
                    managed_policy_arns.append(policy_arn)
            else:
                # Policy Templates are not supported here in the "core"
                raise InvalidResourceException(
                    self.logical_id,
                    "Policy at index {} in the 'Policies' property is not valid".format(index))

        execution_role.ManagedPolicyArns = list(managed_policy_arns)
        execution_role.Policies = policy_documents or None
        execution_role.PermissionsBoundary = self.PermissionsBoundary

        return execution_role

    def _validate_dlq(self):
        """Validates whether the DeadLetterQueue LogicalId is validation
        :raise: InvalidResourceException
        """
        # Validate required logical ids
        valid_dlq_types = str(list(self.dead_letter_queue_policy_actions.keys()))
        if not self.DeadLetterQueue.get('Type') or not self.DeadLetterQueue.get('TargetArn'):
            raise InvalidResourceException(self.logical_id,
                                           "'DeadLetterQueue' requires Type and TargetArn properties to be specified"
                                           .format(valid_dlq_types))

        # Validate required Types
        if not self.DeadLetterQueue['Type'] in self.dead_letter_queue_policy_actions:
            raise InvalidResourceException(self.logical_id,
                                           "'DeadLetterQueue' requires Type of {}".format(valid_dlq_types))

    def _event_resources_to_link(self, resources):
        event_resources = {}
        if self.Events:
            for logical_id, event_dict in self.Events.items():
                try:
                    event_source = self.event_resolver.resolve_resource_type(event_dict).from_dict(
                        self.logical_id + logical_id, event_dict, logical_id)
                except TypeError as e:
                    raise InvalidEventException(logical_id, "{}".format(e))
                event_resources[logical_id] = event_source.resources_to_link(resources)
        return event_resources

    def _generate_event_resources(self, lambda_function, execution_role, event_resources, lambda_alias=None):
        """Generates and returns the resources associated with this function's events.

        :param model.lambda_.LambdaFunction lambda_function: generated Lambda function
        :param iam.IAMRole execution_role: generated Lambda execution role
        :param implicit_api: Global Implicit API resource where the implicit APIs get attached to, if necessary
        :param implicit_api_stage: Global implicit API stage resource where implicit APIs get attached to, if necessary
        :param event_resources: All the event sources associated with this Lambda function
        :param model.lambda_.LambdaAlias lambda_alias: Optional Lambda Alias resource if we want to connect the
            event sources to this alias

        :returns: a list containing the function's event resources
        :rtype: list
        """
        resources = []
        if self.Events:
            for logical_id, event_dict in self.Events.items():
                try:
                    eventsource = self.event_resolver.resolve_resource_type(event_dict).from_dict(
                        lambda_function.logical_id + logical_id, event_dict, logical_id)
                except TypeError as e:
                    raise InvalidEventException(logical_id, "{}".format(e))

                kwargs = {
                    # When Alias is provided, connect all event sources to the alias and *not* the function
                    'function': lambda_alias or lambda_function,
                    'role': execution_role,
                }

                for name, resource in event_resources[logical_id].items():
                    kwargs[name] = resource
                resources += eventsource.to_cloudformation(**kwargs)

        return resources

    def _construct_code_dict(self):
        if self.InlineCode:
            return {
                "ZipFile": self.InlineCode
            }
        elif self.CodeUri:
            return construct_s3_location_object(self.CodeUri, self.logical_id, 'CodeUri')
        else:
            raise InvalidResourceException(self.logical_id, "Either 'InlineCode' or 'CodeUri' must be set")

    def _construct_version(self, function, intrinsics_resolver):
        """Constructs a Lambda Version resource that will be auto-published when CodeUri of the function changes.
        Old versions will not be deleted without a direct reference from the CloudFormation template.

        :param model.lambda_.LambdaFunction function: Lambda function object that is being connected to a version
        :param model.intrinsics.resolver.IntrinsicsResolver intrinsics_resolver: Class that can help resolve
            references to parameters present in CodeUri. It is a common usecase to set S3Key of Code to be a
            template parameter. Need to resolve the values otherwise we will never detect a change in Code dict
        :return: Lambda function Version resource
        """
        code_dict = function.Code
        if not code_dict:
            raise ValueError("Lambda function code must be a valid non-empty dictionary")

        if not intrinsics_resolver:
            raise ValueError("intrinsics_resolver is required for versions creation")

        # Resolve references to template parameters before creating hash. This will *not* resolve all intrinsics
        # because we cannot resolve runtime values like Arn of a resource. For purposes of detecting changes, this
        # is good enough. Here is why:
        #
        # When using intrinsic functions there are two cases when has must change:
        #   - Value of the template parameter changes
        #   - (or) LogicalId of a referenced resource changes ie. !GetAtt NewResource.Arn
        #
        # Later case will already change the hash because some value in the Code dictionary changes. We handle the
        # first case by resolving references to template parameters. It is okay even if these references are
        # present inside another intrinsic such as !Join. The resolver will replace the reference with the parameter's
        # value and keep all other parts of !Join identical. This will still trigger a change in the hash.
        code_dict = intrinsics_resolver.resolve_parameter_refs(code_dict)

        # Construct the LogicalID of Lambda version by appending 10 characters of SHA of CodeUri. This is necessary
        # to trigger creation of a new version every time code location changes. Since logicalId changes, CloudFormation
        # will drop the old version and create a new one for us. We set a DeletionPolicy on the version resource to
        # prevent CloudFormation from actually deleting the underlying version resource
        #
        # SHA Collisions: For purposes of triggering a new update, we are concerned about just the difference previous
        #                 and next hashes. The chances that two subsequent hashes collide is fairly low.
        prefix = "{id}Version".format(id=self.logical_id)
        logical_id = logical_id_generator.LogicalIdGenerator(prefix, code_dict).gen()

        attributes = self.get_passthrough_resource_attributes()
        if attributes is None:
            attributes = {}
        attributes["DeletionPolicy"] = "Retain"

        lambda_version = LambdaVersion(logical_id=logical_id, attributes=attributes)
        lambda_version.FunctionName = function.get_runtime_attr('name')
        lambda_version.Description = self.VersionDescription

        return lambda_version

    def _construct_alias(self, name, function, version):
        """Constructs a Lambda Alias for the given function and pointing to the given version

        :param string name: Name of the alias
        :param model.lambda_.LambdaFunction function: Lambda function object to associate the alias with
        :param model.lambda_.LambdaVersion version: Lambda version object to associate the alias with
        :return: Lambda alias object
        :rtype model.lambda_.LambdaAlias
        """

        if not name:
            raise InvalidResourceException(self.logical_id, "Alias name is required to create an alias")

        logical_id = "{id}Alias{suffix}".format(id=function.logical_id, suffix=name)
        alias = LambdaAlias(logical_id=logical_id, attributes=self.get_passthrough_resource_attributes())
        alias.Name = name
        alias.FunctionName = function.get_runtime_attr('name')
        alias.FunctionVersion = version.get_runtime_attr("version")

        return alias

    def _validate_deployment_preference_and_add_update_policy(self, deployment_preference_collection, lambda_alias,
                                                              intrinsics_resolver):
        if 'Enabled' in self.DeploymentPreference:
            self.DeploymentPreference['Enabled'] = intrinsics_resolver.resolve_parameter_refs(
                self.DeploymentPreference['Enabled'])
            if isinstance(self.DeploymentPreference['Enabled'], dict):
                raise InvalidResourceException(self.logical_id, "'Enabled' must be a boolean value")

        if deployment_preference_collection is None:
            raise ValueError('deployment_preference_collection required for parsing the deployment preference')

        deployment_preference_collection.add(self.logical_id, self.DeploymentPreference)

        if deployment_preference_collection.get(self.logical_id).enabled:
            if self.AutoPublishAlias is None:
                raise InvalidResourceException(
                    self.logical_id,
                    "'DeploymentPreference' requires AutoPublishAlias property to be specified")
            if lambda_alias is None:
                raise ValueError('lambda_alias expected for updating it with the appropriate update policy')

            lambda_alias.set_resource_attribute("UpdatePolicy",
                                                deployment_preference_collection.update_policy(
                                                    self.logical_id).to_dict())


class SamApi(SamResourceMacro):
    """SAM rest API macro.
    """
    resource_type = 'AWS::Serverless::Api'
    property_types = {
        # Internal property set only by Implicit API plugin. If set to True, the API Event Source code will inject
        # Lambda Integration URI to the Swagger. To preserve backwards compatibility, this must be set only for
        # Implicit APIs. For Explicit APIs, customer is expected to set integration URI themselves.
        # In the future, we might rename and expose this property to customers so they can have SAM manage Explicit APIs
        # Swagger.
        '__MANAGE_SWAGGER': PropertyType(False, is_type(bool)),

        'Name': PropertyType(False, one_of(is_str(), is_type(dict))),
        'StageName': PropertyType(True, one_of(is_str(), is_type(dict))),
        'DefinitionBody': PropertyType(False, is_type(dict)),
        'DefinitionUri': PropertyType(False, one_of(is_str(), is_type(dict))),
        'CacheClusterEnabled': PropertyType(False, is_type(bool)),
        'CacheClusterSize': PropertyType(False, is_str()),
        'Variables': PropertyType(False, is_type(dict)),
        'EndpointConfiguration': PropertyType(False, is_str()),
        'MethodSettings': PropertyType(False, is_type(list)),
        'BinaryMediaTypes': PropertyType(False, is_type(list)),
        'MinimumCompressionSize': PropertyType(False, is_type(int)),
        'Cors': PropertyType(False, one_of(is_str(), is_type(dict))),
        'Auth': PropertyType(False, is_type(dict)),
        'GatewayResponses': PropertyType(False, is_type(dict)),
        'AccessLogSetting': PropertyType(False, is_type(dict)),
        'CanarySetting': PropertyType(False, is_type(dict)),
        'TracingEnabled': PropertyType(False, is_type(bool))
    }

    referable_properties = {
        "Stage": ApiGatewayStage.resource_type,
        "Deployment": ApiGatewayDeployment.resource_type,
    }

    def to_cloudformation(self, **kwargs):
        """Returns the API Gateway RestApi, Deployment, and Stage to which this SAM Api corresponds.

        :param dict kwargs: already-converted resources that may need to be modified when converting this \
        macro to pure CloudFormation
        :returns: a list of vanilla CloudFormation Resources, to which this Function expands
        :rtype: list
        """
        resources = []

        api_generator = ApiGenerator(self.logical_id,
                                     self.CacheClusterEnabled,
                                     self.CacheClusterSize,
                                     self.Variables,
                                     self.depends_on,
                                     self.DefinitionBody,
                                     self.DefinitionUri,
                                     self.Name,
                                     self.StageName,
                                     endpoint_configuration=self.EndpointConfiguration,
                                     method_settings=self.MethodSettings,
                                     binary_media=self.BinaryMediaTypes,
                                     minimum_compression_size=self.MinimumCompressionSize,
                                     cors=self.Cors,
                                     auth=self.Auth,
                                     gateway_responses=self.GatewayResponses,
                                     access_log_setting=self.AccessLogSetting,
                                     canary_setting=self.CanarySetting,
                                     tracing_enabled=self.TracingEnabled,
                                     resource_attributes=self.resource_attributes,
                                     passthrough_resource_attributes=self.get_passthrough_resource_attributes())

        rest_api, deployment, stage, permissions = api_generator.to_cloudformation()

        resources.extend([rest_api, deployment, stage])
        resources.extend(permissions)

        return resources


class SamSimpleTable(SamResourceMacro):
    """SAM simple table macro.
    """
    resource_type = 'AWS::Serverless::SimpleTable'
    property_types = {
        'PrimaryKey': PropertyType(False, dict_of(is_str(), is_str())),
        'ProvisionedThroughput': PropertyType(False, dict_of(is_str(), one_of(is_type(int), is_type(dict)))),
        'TableName': PropertyType(False, one_of(is_str(), is_type(dict))),
        'Tags': PropertyType(False, is_type(dict)),
        'SSESpecification': PropertyType(False, is_type(dict))
    }
    attribute_type_conversions = {
        'String': 'S',
        'Number': 'N',
        'Binary': 'B'
    }

    def to_cloudformation(self, **kwargs):
        dynamodb_resources = self._construct_dynamodb_table()

        return [dynamodb_resources]

    def _construct_dynamodb_table(self):
        dynamodb_table = DynamoDBTable(self.logical_id, depends_on=self.depends_on, attributes=self.resource_attributes)

        if self.PrimaryKey:
            primary_key = {
                'AttributeName': self.PrimaryKey['Name'],
                'AttributeType': self._convert_attribute_type(self.PrimaryKey['Type'])
            }

        else:
            primary_key = {'AttributeName': 'id', 'AttributeType': 'S'}

        dynamodb_table.AttributeDefinitions = [primary_key]
        dynamodb_table.KeySchema = [{
            'AttributeName': primary_key['AttributeName'],
            'KeyType': 'HASH'
        }]

        if self.ProvisionedThroughput:
            dynamodb_table.ProvisionedThroughput = self.ProvisionedThroughput
        else:
            dynamodb_table.BillingMode = 'PAY_PER_REQUEST'

        if self.SSESpecification:
            dynamodb_table.SSESpecification = self.SSESpecification

        if self.TableName:
            dynamodb_table.TableName = self.TableName

        if bool(self.Tags):
            dynamodb_table.Tags = get_tag_list(self.Tags)

        return dynamodb_table

    def _convert_attribute_type(self, attribute_type):
        if attribute_type in self.attribute_type_conversions:
            return self.attribute_type_conversions[attribute_type]
        raise InvalidResourceException(self.logical_id, 'Invalid \'Type\' "{actual}".'.format(actual=attribute_type))


class SamApplication(SamResourceMacro):
    """SAM application macro.
    """

    APPLICATION_ID_KEY = 'ApplicationId'
    SEMANTIC_VERSION_KEY = 'SemanticVersion'

    resource_type = 'AWS::Serverless::Application'

    # The plugin will always insert the TemplateUrl parameter
    property_types = {
        'Location': PropertyType(True, one_of(is_str(), is_type(dict))),
        'TemplateUrl': PropertyType(False, is_str()),
        'Parameters': PropertyType(False, is_type(dict)),
        'NotificationArns': PropertyType(False, list_of(is_str())),
        'Tags': PropertyType(False, is_type(dict)),
        'TimeoutInMinutes': PropertyType(False, is_type(int))
    }

    def to_cloudformation(self, **kwargs):
        """Returns the stack with the proper parameters for this application
        """
        nested_stack = self._construct_nested_stack()
        return [nested_stack]

    def _construct_nested_stack(self):
        """Constructs a AWS::CloudFormation::Stack resource
        """
        nested_stack = NestedStack(self.logical_id, depends_on=self.depends_on,
                                   attributes=self.get_passthrough_resource_attributes())
        nested_stack.Parameters = self.Parameters
        nested_stack.NotificationArns = self.NotificationArns
        application_tags = self._get_application_tags()
        nested_stack.Tags = self._construct_tag_list(self.Tags, application_tags)
        nested_stack.TimeoutInMinutes = self.TimeoutInMinutes
        nested_stack.TemplateURL = self.TemplateUrl if self.TemplateUrl else ""

        return nested_stack

    def _get_application_tags(self):
        """Adds tags to the stack if this resource is using the serverless app repo
        """
        application_tags = {}
        if isinstance(self.Location, dict):
            if (self.APPLICATION_ID_KEY in self.Location.keys() and
                    self.Location[self.APPLICATION_ID_KEY] is not None):
                application_tags[self._SAR_APP_KEY] = self.Location[self.APPLICATION_ID_KEY]
            if (self.SEMANTIC_VERSION_KEY in self.Location.keys() and
                    self.Location[self.SEMANTIC_VERSION_KEY] is not None):
                application_tags[self._SAR_SEMVER_KEY] = self.Location[self.SEMANTIC_VERSION_KEY]
        return application_tags


class SamLayerVersion(SamResourceMacro):
    """ SAM Layer macro
    """
    resource_type = 'AWS::Serverless::LayerVersion'
    property_types = {
        'LayerName': PropertyType(False, one_of(is_str(), is_type(dict))),
        'Description': PropertyType(False, is_str()),
        'ContentUri': PropertyType(True, one_of(is_str(), is_type(dict))),
        'CompatibleRuntimes': PropertyType(False, list_of(is_str())),
        'LicenseInfo': PropertyType(False, is_str()),
        'RetentionPolicy': PropertyType(False, is_str())
    }

    RETAIN = 'Retain'
    DELETE = 'Delete'
    retention_policy_options = [RETAIN.lower(), DELETE.lower()]

    def to_cloudformation(self, **kwargs):
        """Returns the Lambda layer to which this SAM Layer corresponds.

        :param dict kwargs: already-converted resources that may need to be modified when converting this \
        macro to pure CloudFormation
        :returns: a list of vanilla CloudFormation Resources, to which this Function expands
        :rtype: list
        """
        resources = []

        # Append any CFN resources:
        intrinsics_resolver = kwargs["intrinsics_resolver"]
        resources.append(self._construct_lambda_layer(intrinsics_resolver))

        return resources

    def _construct_lambda_layer(self, intrinsics_resolver):
        """Constructs and returns the Lambda function.

        :returns: a list containing the Lambda function and execution role resources
        :rtype: list
        """
        # Resolve intrinsics if applicable:
        self.LayerName = self._resolve_string_parameter(intrinsics_resolver, self.LayerName, 'LayerName')
        self.LicenseInfo = self._resolve_string_parameter(intrinsics_resolver, self.LicenseInfo, 'LicenseInfo')
        self.Description = self._resolve_string_parameter(intrinsics_resolver, self.Description, 'Description')
        self.RetentionPolicy = self._resolve_string_parameter(intrinsics_resolver, self.RetentionPolicy,
                                                              'RetentionPolicy')

        retention_policy_value = self._get_retention_policy_value()

        attributes = self.get_passthrough_resource_attributes()
        if attributes is None:
            attributes = {}
        attributes['DeletionPolicy'] = retention_policy_value

        old_logical_id = self.logical_id
        new_logical_id = logical_id_generator.LogicalIdGenerator(old_logical_id, self.to_dict()).gen()
        self.logical_id = new_logical_id

        lambda_layer = LambdaLayerVersion(self.logical_id, depends_on=self.depends_on, attributes=attributes)

        # Changing the LayerName property: when a layer is published, it is given an Arn
        # example: arn:aws:lambda:us-west-2:123456789012:layer:MyLayer:1
        # where MyLayer is the LayerName property if it exists; otherwise, it is the
        # LogicalId of this resource. Since a LayerVersion is an immutable resource, when
        # CloudFormation updates this resource, it will ALWAYS create a new version then
        # delete the old version if the logical ids match. What this does is change the
        # logical id of every layer (so a `DeletionPolicy: Retain` can work) and set the
        # LayerName property of the layer so that the Arn will still always be the same
        # with the exception of an incrementing version number.
        if not self.LayerName:
            self.LayerName = old_logical_id

        lambda_layer.LayerName = self.LayerName
        lambda_layer.Description = self.Description
        lambda_layer.Content = construct_s3_location_object(self.ContentUri, self.logical_id, 'ContentUri')
        lambda_layer.CompatibleRuntimes = self.CompatibleRuntimes
        lambda_layer.LicenseInfo = self.LicenseInfo

        return lambda_layer

    def _get_retention_policy_value(self):
        """
        Sets the deletion policy on this resource. The default is 'Retain'.

        :return: value for the DeletionPolicy attribute.
        """

        if self.RetentionPolicy is None or self.RetentionPolicy.lower() == self.RETAIN.lower():
            return self.RETAIN
        elif self.RetentionPolicy.lower() == self.DELETE.lower():
            return self.DELETE
        elif self.RetentionPolicy.lower() not in self.retention_policy_options:
            raise InvalidResourceException(self.logical_id,
                                           "'{}' must be one of the following options: {}."
                                           .format('RetentionPolicy', [self.RETAIN, self.DELETE]))
