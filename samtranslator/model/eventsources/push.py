import copy
import re
from six import string_types
from samtranslator.model import ResourceMacro, PropertyType
from samtranslator.model.types import is_type, list_of, dict_of, one_of, is_str
from samtranslator.model.intrinsics import ref, fnSub, make_shorthand, make_conditional
from samtranslator.model.tags.resource_tagging import get_tag_list

from samtranslator.model.s3 import S3Bucket
from samtranslator.model.sns import SNSSubscription
from samtranslator.model.lambda_ import LambdaPermission
from samtranslator.model.events import EventsRule
from samtranslator.model.iot import IotTopicRule
from samtranslator.translator.arn_generator import ArnGenerator
from samtranslator.model.exceptions import InvalidEventException, InvalidResourceException
from samtranslator.swagger.swagger import SwaggerEditor

CONDITION = 'Condition'


class PushEventSource(ResourceMacro):
    """Base class for push event sources for SAM Functions.

    Push event sources correspond to services that call Lambda's Invoke API whenever an event occurs. Each Push event
    needs an Lambda Permission resource, which will add permissions for the source service to invoke the Lambda function
    to the function's resource policy.

    SourceArn is attached to the resource policy to avoid giving lambda invoke permissions to every resource of that
    category.
    ARN is currently constructed in ARN format http://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html
    for:
    - API gateway
    - IotRule

    ARN is accessible through Fn:GetAtt for:
    - Schedule
    - Cloudwatch

    :cvar str principal: The AWS service principal of the source service.
    """
    principal = None

    def _construct_permission(self, function, source_arn=None, source_account=None, suffix="", event_source_token=None):
        """Constructs the Lambda Permission resource allowing the source service to invoke the function this event
        source triggers.

        :returns: the permission resource
        :rtype: model.lambda_.LambdaPermission
        """
        lambda_permission = LambdaPermission(self.logical_id + 'Permission' + suffix,
                                             attributes=function.get_passthrough_resource_attributes())

        try:
            # Name will not be available for Alias resources
            function_name_or_arn = function.get_runtime_attr("name")
        except NotImplementedError:
            function_name_or_arn = function.get_runtime_attr("arn")

        lambda_permission.Action = 'lambda:invokeFunction'
        lambda_permission.FunctionName = function_name_or_arn
        lambda_permission.Principal = self.principal
        lambda_permission.SourceArn = source_arn
        lambda_permission.SourceAccount = source_account
        lambda_permission.EventSourceToken = event_source_token

        return lambda_permission


class Schedule(PushEventSource):
    """Scheduled executions for SAM Functions."""
    resource_type = 'Schedule'
    principal = 'events.amazonaws.com'
    property_types = {
            'Schedule': PropertyType(True, is_str()),
            'Input': PropertyType(False, is_str())
    }

    def to_cloudformation(self, **kwargs):
        """Returns the CloudWatch Events Rule and Lambda Permission to which this Schedule event source corresponds.

        :param dict kwargs: no existing resources need to be modified
        :returns: a list of vanilla CloudFormation Resources, to which this pull event expands
        :rtype: list
        """
        function = kwargs.get('function')

        if not function:
            raise TypeError("Missing required keyword argument: function")

        resources = []

        events_rule = EventsRule(self.logical_id)
        resources.append(events_rule)

        events_rule.ScheduleExpression = self.Schedule
        events_rule.Targets = [self._construct_target(function)]

        source_arn = events_rule.get_runtime_attr("arn")
        if CONDITION in function.resource_attributes:
            events_rule.set_resource_attribute(CONDITION, function.resource_attributes[CONDITION])
        resources.append(self._construct_permission(function, source_arn=source_arn))

        return resources

    def _construct_target(self, function):
        """Constructs the Target property for the CloudWatch Events Rule.

        :returns: the Target property
        :rtype: dict
        """
        target = {
                'Arn': function.get_runtime_attr("arn"),
                'Id': self.logical_id + 'LambdaTarget'
        }
        if self.Input is not None:
            target['Input'] = self.Input

        return target


class CloudWatchEvent(PushEventSource):
    """CloudWatch Events event source for SAM Functions."""
    resource_type = 'CloudWatchEvent'
    principal = 'events.amazonaws.com'
    property_types = {
            'Pattern': PropertyType(False, is_type(dict)),
            'Input': PropertyType(False, is_str()),
            'InputPath': PropertyType(False, is_str())
    }

    def to_cloudformation(self, **kwargs):
        """Returns the CloudWatch Events Rule and Lambda Permission to which this CloudWatch Events event source
        corresponds.

        :param dict kwargs: no existing resources need to be modified
        :returns: a list of vanilla CloudFormation Resources, to which this pull event expands
        :rtype: list
        """
        function = kwargs.get('function')

        if not function:
            raise TypeError("Missing required keyword argument: function")

        resources = []

        events_rule = EventsRule(self.logical_id)
        events_rule.EventPattern = self.Pattern
        events_rule.Targets = [self._construct_target(function)]
        if CONDITION in function.resource_attributes:
            events_rule.set_resource_attribute(CONDITION, function.resource_attributes[CONDITION])

        resources.append(events_rule)

        source_arn = events_rule.get_runtime_attr("arn")
        resources.append(self._construct_permission(function, source_arn=source_arn))

        return resources

    def _construct_target(self, function):
        """Constructs the Target property for the CloudWatch Events Rule.

        :returns: the Target property
        :rtype: dict
        """
        target = {
                'Arn': function.get_runtime_attr("arn"),
                'Id': self.logical_id + 'LambdaTarget'
        }
        if self.Input is not None:
            target['Input'] = self.Input

        if self.InputPath is not None:
            target['InputPath'] = self.InputPath
        return target


class S3(PushEventSource):
    """S3 bucket event source for SAM Functions."""
    resource_type = 'S3'
    principal = 's3.amazonaws.com'
    property_types = {
            'Bucket': PropertyType(True, is_str()),
            'Events': PropertyType(True, one_of(is_str(), list_of(is_str()))),
            'Filter': PropertyType(False, dict_of(is_str(), is_str()))
    }

    def resources_to_link(self, resources):
        if isinstance(self.Bucket, dict) and 'Ref' in self.Bucket:
            bucket_id = self.Bucket['Ref']
            if bucket_id in resources:
                return {
                    'bucket': resources[bucket_id],
                    'bucket_id': bucket_id
                }
        raise InvalidEventException(self.relative_id, "S3 events must reference an S3 bucket in the same template.")

    def to_cloudformation(self, **kwargs):
        """Returns the Lambda Permission resource allowing S3 to invoke the function this event source triggers.

        :param dict kwargs: S3 bucket resource
        :returns: a list of vanilla CloudFormation Resources, to which this S3 event expands
        :rtype: list
        """
        function = kwargs.get('function')

        if not function:
            raise TypeError("Missing required keyword argument: function")

        if 'bucket' not in kwargs or kwargs['bucket'] is None:
            raise TypeError("Missing required keyword argument: bucket")

        if 'bucket_id' not in kwargs or kwargs['bucket_id'] is None:
            raise TypeError("Missing required keyword argument: bucket_id")

        bucket = kwargs['bucket']
        bucket_id = kwargs['bucket_id']

        resources = []

        source_account = ref('AWS::AccountId')
        permission = self._construct_permission(function, source_account=source_account)
        if CONDITION in permission.resource_attributes:
            self._depend_on_lambda_permissions_using_tag(bucket, permission)
        else:
            self._depend_on_lambda_permissions(bucket, permission)
        resources.append(permission)

        # NOTE: `bucket` here is a dictionary representing the S3 Bucket resource in your SAM template. If there are
        # multiple S3 Events attached to the same bucket, we will update the Bucket resource with notification
        # configuration for each event. This is the reason why we continue to use existing bucket dict and append onto
        # it.
        #
        # NOTE: There is some fragile logic here where we will append multiple resources to output
        #   SAM template but de-dupe them when merging into output CFN template. This is scary because the order of
        #   merging is literally "last one wins", which works fine because we linearly loop through the template once.
        #   The de-dupe happens inside `samtranslator.translator.Translator.translate` method when merging results of
        #   to_cloudformation() to output template.
        self._inject_notification_configuration(function, bucket)
        resources.append(S3Bucket.from_dict(bucket_id, bucket))

        return resources

    def _depend_on_lambda_permissions(self, bucket, permission):
        """
        Make the S3 bucket depends on Lambda Permissions resource because when S3 adds a Notification Configuration,
        it will check whether it has permissions to access Lambda. This will fail if the Lambda::Permissions is not
        already applied for this bucket to invoke the Lambda.

        :param dict bucket: Dictionary representing the bucket in SAM template. This is a raw dictionary and not a
            "resource" object
        :param model.lambda_.lambda_permission permission: Lambda Permission resource that needs to be created before
            the bucket.
        :return: Modified Bucket dictionary
        """

        depends_on = bucket.get("DependsOn", [])

        # DependsOn can be either a list of strings or a scalar string
        if isinstance(depends_on, string_types):
            depends_on = [depends_on]

        depends_on_set = set(depends_on)
        depends_on_set.add(permission.logical_id)
        bucket["DependsOn"] = list(depends_on_set)

        return bucket

    def _depend_on_lambda_permissions_using_tag(self, bucket, permission):
        """
        Since conditional DependsOn is not supported this undocumented way of
        implicitely  making dependency through tags is used.

        See https://stackoverflow.com/questions/34607476/cloudformation-apply-condition-on-dependson

        It is done by using Ref wrapped in a conditional Fn::If. Using Ref implies a
        dependency, so CloudFormation will automatically wait once it reaches that function, the same
        as if you were using a DependsOn.
        """
        properties = bucket.get('Properties', None)
        if properties is None:
            properties = {}
            bucket['Properties'] = properties
        tags = properties.get('Tags', None)
        if tags is None:
            tags = []
            properties['Tags'] = tags
        dep_tag = {
            'sam:ConditionalDependsOn:' + permission.logical_id: {
                'Fn::If': [
                    permission.resource_attributes[CONDITION],
                    ref(permission.logical_id),
                    'no dependency'
                ]
            }
        }
        properties['Tags'] = tags + get_tag_list(dep_tag)
        return bucket

    def _inject_notification_configuration(self, function, bucket):
        base_event_mapping = {
            'Function': function.get_runtime_attr("arn")
        }

        if self.Filter is not None:
            base_event_mapping['Filter'] = self.Filter

        event_types = self.Events
        if isinstance(self.Events, string_types):
            event_types = [self.Events]

        event_mappings = []
        for event_type in event_types:

            lambda_event = copy.deepcopy(base_event_mapping)
            lambda_event['Event'] = event_type
            if CONDITION in function.resource_attributes:
                lambda_event = make_conditional(function.resource_attributes[CONDITION], lambda_event)
            event_mappings.append(lambda_event)

        properties = bucket.get('Properties', None)
        if properties is None:
            properties = {}
            bucket['Properties'] = properties

        notification_config = properties.get('NotificationConfiguration', None)
        if notification_config is None:
            notification_config = {}
            properties['NotificationConfiguration'] = notification_config

        lambda_notifications = notification_config.get('LambdaConfigurations', None)
        if lambda_notifications is None:
            lambda_notifications = []
            notification_config['LambdaConfigurations'] = lambda_notifications

        for event_mapping in event_mappings:
            if event_mapping not in lambda_notifications:
                lambda_notifications.append(event_mapping)
        return bucket


class SNS(PushEventSource):
    """SNS topic event source for SAM Functions."""
    resource_type = 'SNS'
    principal = 'sns.amazonaws.com'
    property_types = {
            'Topic': PropertyType(True, is_str()),
            'FilterPolicy': PropertyType(False, dict_of(is_str(), list_of(one_of(is_str(), is_type(dict)))))
    }

    def to_cloudformation(self, **kwargs):
        """Returns the Lambda Permission resource allowing SNS to invoke the function this event source triggers.

        :param dict kwargs: no existing resources need to be modified
        :returns: a list of vanilla CloudFormation Resources, to which this SNS event expands
        :rtype: list
        """
        function = kwargs.get('function')

        if not function:
            raise TypeError("Missing required keyword argument: function")

        return [self._construct_permission(function, source_arn=self.Topic),
                self._inject_subscription(function, self.Topic, self.FilterPolicy)]

    def _inject_subscription(self, function, topic, filterPolicy):
        subscription = SNSSubscription(self.logical_id)
        subscription.Protocol = 'lambda'
        subscription.Endpoint = function.get_runtime_attr("arn")
        subscription.TopicArn = topic
        if CONDITION in function.resource_attributes:
            subscription.set_resource_attribute(CONDITION, function.resource_attributes[CONDITION])

        if filterPolicy is not None:
            subscription.FilterPolicy = filterPolicy

        return subscription


class Api(PushEventSource):
    """Api method event source for SAM Functions."""
    resource_type = 'Api'
    principal = 'apigateway.amazonaws.com'
    property_types = {
            'Path': PropertyType(True, is_str()),
            'Method': PropertyType(True, is_str()),

            # Api Event sources must "always" be paired with a Serverless::Api
            'RestApiId': PropertyType(True, is_str()),
            'Auth': PropertyType(False, is_type(dict))
    }

    def resources_to_link(self, resources):
        """
        If this API Event Source refers to an explicit API resource, resolve the reference and grab
        necessary data from the explicit API
        """

        rest_api_id = self.RestApiId
        if isinstance(rest_api_id, dict) and "Ref" in rest_api_id:
            rest_api_id = rest_api_id["Ref"]

        # If RestApiId is a resource in the same template, then we try find the StageName by following the reference
        # Otherwise we default to a wildcard. This stage name is solely used to construct the permission to
        # allow this stage to invoke the Lambda function. If we are unable to resolve the stage name, we will
        # simply permit all stages to invoke this Lambda function
        # This hack is necessary because customers could use !ImportValue, !Ref or other intrinsic functions which
        # can be sometimes impossible to resolve (ie. when it has cross-stack references)
        permitted_stage = "*"
        stage_suffix = "AllStages"
        explicit_api = None
        if isinstance(rest_api_id, string_types):

            if rest_api_id in resources \
               and "Properties" in resources[rest_api_id] \
               and "StageName" in resources[rest_api_id]["Properties"]:

                explicit_api = resources[rest_api_id]["Properties"]
                permitted_stage = explicit_api["StageName"]

                # Stage could be a intrinsic, in which case leave the suffix to default value
                if isinstance(permitted_stage, string_types):
                    if not permitted_stage:
                        raise InvalidResourceException(rest_api_id, 'StageName cannot be empty.')
                    stage_suffix = permitted_stage
                else:
                    stage_suffix = "Stage"

            else:
                # RestApiId is a string, not an intrinsic, but we did not find a valid API resource for this ID
                raise InvalidEventException(self.relative_id, "RestApiId property of Api event must reference a valid "
                                                              "resource in the same template.")

        return {
            'explicit_api': explicit_api,
            'explicit_api_stage': {
                'permitted_stage': permitted_stage,
                'suffix': stage_suffix
            }
        }

    def to_cloudformation(self, **kwargs):
        """If the Api event source has a RestApi property, then simply return the Lambda Permission resource allowing
        API Gateway to call the function. If no RestApi is provided, then additionally inject the path, method, and the
        x-amazon-apigateway-integration into the Swagger body for a provided implicit API.

        :param dict kwargs: a dict containing the implicit RestApi to be modified, should no explicit RestApi \
                be provided.
        :returns: a list of vanilla CloudFormation Resources, to which this Api event expands
        :rtype: list
        """
        resources = []

        function = kwargs.get('function')

        if not function:
            raise TypeError("Missing required keyword argument: function")

        if self.Method is not None:
            # Convert to lower case so that user can specify either GET or get
            self.Method = self.Method.lower()

        resources.extend(self._get_permissions(kwargs))

        explicit_api = kwargs['explicit_api']
        if explicit_api.get("__MANAGE_SWAGGER"):
            self._add_swagger_integration(explicit_api, function)

        return resources

    def _get_permissions(self, resources_to_link):
        permissions = []

        permissions.append(self._get_permission(resources_to_link, "*", "Test"))

        # By default, implicit APIs get a stage called Prod. If the API event refers to an
        # explicit API using RestApiId property, we should grab the stage name of the explicit API
        permitted_stage = suffix = "Prod"
        if 'explicit_api_stage' in resources_to_link:
            permitted_stage = resources_to_link['explicit_api_stage']['permitted_stage']
            suffix = resources_to_link['explicit_api_stage']['suffix']

        permissions.append(self._get_permission(resources_to_link, permitted_stage, suffix))
        return permissions

    def _get_permission(self, resources_to_link, stage, suffix):
        # It turns out that APIGW doesn't like trailing slashes in paths (#665)
        # and removes as a part of their behaviour, but this isn't documented.
        # The regex removes the tailing slash to ensure the permission works as intended
        path = re.sub(r'^(.+)/$', r'\1', self.Path)

        if not stage or not suffix:
            raise RuntimeError("Could not add permission to lambda function.")

        path = path.replace('{proxy+}', '*')
        method = '*' if self.Method.lower() == 'any' else self.Method.upper()

        api_id = self.RestApiId

        # RestApiId can be a simple string or intrinsic function like !Ref. Using Fn::Sub will handle both cases
        resource = '${__ApiId__}/' + '${__Stage__}/' + method + path
        partition = ArnGenerator.get_partition_name()
        source_arn = fnSub(ArnGenerator.generate_arn(partition=partition, service='execute-api', resource=resource),
                           {"__ApiId__": api_id, "__Stage__": stage})

        return self._construct_permission(resources_to_link['function'], source_arn=source_arn, suffix=suffix)

    def _add_swagger_integration(self, api, function):
        """Adds the path and method for this Api event source to the Swagger body for the provided RestApi.

        :param model.apigateway.ApiGatewayRestApi rest_api: the RestApi to which the path and method should be added.
        """
        swagger_body = api.get("DefinitionBody")
        if swagger_body is None:
            return

        function_arn = function.get_runtime_attr('arn')
        partition = ArnGenerator.get_partition_name()
        uri = fnSub('arn:' + partition + ':apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/' +
                    make_shorthand(function_arn) + '/invocations')

        editor = SwaggerEditor(swagger_body)

        if editor.has_integration(self.Path, self.Method):
            # Cannot add the Lambda Integration, if it is already present
            raise InvalidEventException(
                self.relative_id,
                'API method "{method}" defined multiple times for path "{path}".'.format(
                    method=self.Method, path=self.Path))

        condition = None
        if CONDITION in function.resource_attributes:
            condition = function.resource_attributes[CONDITION]

        editor.add_lambda_integration(self.Path, self.Method, uri, self.Auth, api.get('Auth'), condition=condition)

        if self.Auth:
            method_authorizer = self.Auth.get('Authorizer')

            if method_authorizer:
                api_auth = api.get('Auth')
                api_authorizers = api_auth and api_auth.get('Authorizers')

                if method_authorizer != 'AWS_IAM':
                    if not api_authorizers:
                        raise InvalidEventException(
                            self.relative_id,
                            'Unable to set Authorizer [{authorizer}] on API method [{method}] for path [{path}] '
                            'because the related API does not define any Authorizers.'.format(
                                authorizer=method_authorizer, method=self.Method, path=self.Path))

                    if method_authorizer != 'NONE' and not api_authorizers.get(method_authorizer):
                        raise InvalidEventException(
                            self.relative_id,
                            'Unable to set Authorizer [{authorizer}] on API method [{method}] for path [{path}] '
                            'because it wasn\'t defined in the API\'s Authorizers.'.format(
                                authorizer=method_authorizer, method=self.Method, path=self.Path))

                    if method_authorizer == 'NONE' and not api_auth.get('DefaultAuthorizer'):
                        raise InvalidEventException(
                            self.relative_id,
                            'Unable to set Authorizer on API method [{method}] for path [{path}] because \'NONE\' '
                            'is only a valid value when a DefaultAuthorizer on the API is specified.'.format(
                                method=self.Method, path=self.Path))

                editor.add_auth_to_method(api=api, path=self.Path, method_name=self.Method, auth=self.Auth)

        api["DefinitionBody"] = editor.swagger


class AlexaSkill(PushEventSource):
    resource_type = 'AlexaSkill'
    principal = 'alexa-appkit.amazon.com'

    property_types = {
        'SkillId': PropertyType(False, is_str()),
    }

    def to_cloudformation(self, **kwargs):
        function = kwargs.get('function')

        if not function:
            raise TypeError("Missing required keyword argument: function")

        resources = []
        resources.append(self._construct_permission(function, event_source_token=self.SkillId))

        return resources


class IoTRule(PushEventSource):
    resource_type = 'IoTRule'
    principal = 'iot.amazonaws.com'

    property_types = {
        'Sql': PropertyType(True, is_str()),
        'AwsIotSqlVersion': PropertyType(False, is_str())
    }

    def to_cloudformation(self, **kwargs):
        function = kwargs.get('function')

        if not function:
            raise TypeError("Missing required keyword argument: function")

        resources = []

        resource = 'rule/${RuleName}'

        partition = ArnGenerator.get_partition_name()
        source_arn = fnSub(ArnGenerator.generate_arn(partition=partition, service='iot', resource=resource),
                           {'RuleName': ref(self.logical_id)})
        source_account = fnSub('${AWS::AccountId}')

        resources.append(self._construct_permission(function, source_arn=source_arn,
                                                    source_account=source_account))
        resources.append(self._construct_iot_rule(function))

        return resources

    def _construct_iot_rule(self, function):
        rule = IotTopicRule(self.logical_id)

        payload = {
            'Sql': self.Sql,
            'RuleDisabled': False,
            'Actions': [
                {
                    'Lambda': {
                        'FunctionArn': function.get_runtime_attr("arn")
                    }
                }
            ]
        }

        if self.AwsIotSqlVersion:
            payload['AwsIotSqlVersion'] = self.AwsIotSqlVersion

        rule.TopicRulePayload = payload
        if CONDITION in function.resource_attributes:
            rule.set_resource_attribute(CONDITION, function.resource_attributes[CONDITION])

        return rule
