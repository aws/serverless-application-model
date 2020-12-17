from samtranslator.model import ResourceMacro, PropertyType
from samtranslator.model.types import is_type, is_str

from samtranslator.model.lambda_ import LambdaEventSourceMapping
from samtranslator.translator.arn_generator import ArnGenerator
from samtranslator.model.exceptions import InvalidEventException
from samtranslator.model.iam import IAMRolePolicies


class PullEventSource(ResourceMacro):
    """Base class for pull event sources for SAM Functions.

    The pull events are Kinesis Streams, DynamoDB Streams, Kafka Topics, ActiveMQ Queues and SQS Queues. All of these correspond to an
    EventSourceMapping in Lambda, and require that the execution role be given to Kinesis Streams, DynamoDB
    Streams, or SQS Queues, respectively.

    :cvar str policy_arn: The ARN of the AWS managed role policy corresponding to this pull event source
    """

    resource_type = None
    property_types = {
        "Stream": PropertyType(False, is_str()),
        "Queue": PropertyType(False, is_str()),
        "BatchSize": PropertyType(False, is_type(int)),
        "StartingPosition": PropertyType(False, is_str()),
        "Enabled": PropertyType(False, is_type(bool)),
        "MaximumBatchingWindowInSeconds": PropertyType(False, is_type(int)),
        "MaximumRetryAttempts": PropertyType(False, is_type(int)),
        "BisectBatchOnFunctionError": PropertyType(False, is_type(bool)),
        "MaximumRecordAgeInSeconds": PropertyType(False, is_type(int)),
        "DestinationConfig": PropertyType(False, is_type(dict)),
        "ParallelizationFactor": PropertyType(False, is_type(int)),
        "Topics": PropertyType(False, is_type(list)),
        "Broker": PropertyType(False, is_str()),
        "Queues": PropertyType(False, is_type(list)),
        "SourceAccessConfigurations": PropertyType(False, is_type(list)),
        "TumblingWindowInSeconds": PropertyType(False, is_type(int)),
    }

    def get_policy_arn(self):
        raise NotImplementedError("Subclass must implement this method")

    def to_cloudformation(self, **kwargs):
        """Returns the Lambda EventSourceMapping to which this pull event corresponds. Adds the appropriate managed
        policy to the function's execution role, if such a role is provided.

        :param dict kwargs: a dict containing the execution role generated for the function
        :returns: a list of vanilla CloudFormation Resources, to which this pull event expands
        :rtype: list
        """
        function = kwargs.get("function")

        if not function:
            raise TypeError("Missing required keyword argument: function")

        resources = []

        lambda_eventsourcemapping = LambdaEventSourceMapping(self.logical_id)
        resources.append(lambda_eventsourcemapping)

        try:
            # Name will not be available for Alias resources
            function_name_or_arn = function.get_runtime_attr("name")
        except NotImplementedError:
            function_name_or_arn = function.get_runtime_attr("arn")

        if not self.Stream and not self.Queue and not self.Broker:
            raise InvalidEventException(
                self.relative_id,
                "No Queue (for SQS) or Stream (for Kinesis, DynamoDB or MSK) or Broker (for ActiveMQ) provided.",
            )

        if self.Stream and not self.StartingPosition:
            raise InvalidEventException(self.relative_id, "StartingPosition is required for Kinesis, DynamoDB and MSK.")

        lambda_eventsourcemapping.FunctionName = function_name_or_arn
        lambda_eventsourcemapping.EventSourceArn = self.Stream or self.Queue or self.Broker
        lambda_eventsourcemapping.StartingPosition = self.StartingPosition
        lambda_eventsourcemapping.BatchSize = self.BatchSize
        lambda_eventsourcemapping.Enabled = self.Enabled
        lambda_eventsourcemapping.MaximumBatchingWindowInSeconds = self.MaximumBatchingWindowInSeconds
        lambda_eventsourcemapping.MaximumRetryAttempts = self.MaximumRetryAttempts
        lambda_eventsourcemapping.BisectBatchOnFunctionError = self.BisectBatchOnFunctionError
        lambda_eventsourcemapping.MaximumRecordAgeInSeconds = self.MaximumRecordAgeInSeconds
        lambda_eventsourcemapping.ParallelizationFactor = self.ParallelizationFactor
        lambda_eventsourcemapping.Topics = self.Topics
        lambda_eventsourcemapping.Queues = self.Queues
        lambda_eventsourcemapping.SourceAccessConfigurations = self.SourceAccessConfigurations
        lambda_eventsourcemapping.TumblingWindowInSeconds = self.TumblingWindowInSeconds

        destination_config_policy = None
        if self.DestinationConfig:
            # `Type` property is for sam to attach the right policies
            destination_type = self.DestinationConfig.get("OnFailure").get("Type")

            # SAM attaches the policies for SQS or SNS only if 'Type' is given
            if destination_type:
                # delete this field as its used internally for SAM to determine the policy
                del self.DestinationConfig["OnFailure"]["Type"]
                # the values 'SQS' and 'SNS' are allowed. No intrinsics are allowed
                if destination_type not in ["SQS", "SNS"]:
                    raise InvalidEventException(self.logical_id, "The only valid values for 'Type' are 'SQS' and 'SNS'")
                if self.DestinationConfig.get("OnFailure") is None:
                    raise InvalidEventException(
                        self.logical_id, "'OnFailure' is a required field for " "'DestinationConfig'"
                    )
                if destination_type == "SQS":
                    queue_arn = self.DestinationConfig.get("OnFailure").get("Destination")
                    destination_config_policy = IAMRolePolicies().sqs_send_message_role_policy(
                        queue_arn, self.logical_id
                    )
                elif destination_type == "SNS":
                    sns_topic_arn = self.DestinationConfig.get("OnFailure").get("Destination")
                    destination_config_policy = IAMRolePolicies().sns_publish_role_policy(
                        sns_topic_arn, self.logical_id
                    )
            lambda_eventsourcemapping.DestinationConfig = self.DestinationConfig

        if "Condition" in function.resource_attributes:
            lambda_eventsourcemapping.set_resource_attribute("Condition", function.resource_attributes["Condition"])

        if "role" in kwargs:
            self._link_policy(kwargs["role"], destination_config_policy)

        return resources

    def _link_policy(self, role, destination_config_policy=None):
        """If this source triggers a Lambda function whose execution role is auto-generated by SAM, add the
        appropriate managed policy to this Role.

        :param model.iam.IAMRole role: the execution role generated for the function
        """
        policy_arn = self.get_policy_arn()
        if role is not None and policy_arn not in role.ManagedPolicyArns:
            role.ManagedPolicyArns.append(policy_arn)
        # add SQS or SNS policy only if role is present in kwargs
        if role is not None and destination_config_policy is not None and destination_config_policy:
            if role.Policies is None:
                role.Policies = []
                role.Policies.append(destination_config_policy)
            if role.Policies and destination_config_policy not in role.Policies:
                # do not add the  policy if the same policy document is already present
                if not destination_config_policy.get("PolicyDocument") in [d["PolicyDocument"] for d in role.Policies]:
                    role.Policies.append(destination_config_policy)


class Kinesis(PullEventSource):
    """Kinesis event source."""

    resource_type = "Kinesis"

    def get_policy_arn(self):
        return ArnGenerator.generate_aws_managed_policy_arn("service-role/AWSLambdaKinesisExecutionRole")


class DynamoDB(PullEventSource):
    """DynamoDB Streams event source."""

    resource_type = "DynamoDB"

    def get_policy_arn(self):
        return ArnGenerator.generate_aws_managed_policy_arn("service-role/AWSLambdaDynamoDBExecutionRole")


class SQS(PullEventSource):
    """SQS Queue event source."""

    resource_type = "SQS"

    def get_policy_arn(self):
        return ArnGenerator.generate_aws_managed_policy_arn("service-role/AWSLambdaSQSQueueExecutionRole")


class MSK(PullEventSource):
    """MSK event source."""

    resource_type = "MSK"

    def get_policy_arn(self):
        return ArnGenerator.generate_aws_managed_policy_arn("service-role/AWSLambdaMSKExecutionRole")


class MQ(PullEventSource):
    """MQ event source."""

    resource_type = "MQ"

    def get_policy_arn(self):
        return ArnGenerator.generate_aws_managed_policy_arn("service-role/AWSLambdaAMQExecutionRole")
