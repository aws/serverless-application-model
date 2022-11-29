from typing import Any, Dict, List, Optional

from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.model import ResourceMacro, PropertyType
from samtranslator.model.eventsources import FUNCTION_EVETSOURCE_METRIC_PREFIX
from samtranslator.model.types import is_type, is_str
from samtranslator.model.intrinsics import is_intrinsic

from samtranslator.model.lambda_ import LambdaEventSourceMapping
from samtranslator.translator.arn_generator import ArnGenerator
from samtranslator.model.exceptions import InvalidEventException
from samtranslator.model.iam import IAMRolePolicies
from samtranslator.utils.types import Intrinsicable
from samtranslator.validator.value_validator import sam_expect


class PullEventSource(ResourceMacro):
    """Base class for pull event sources for SAM Functions.

    The pull events are Kinesis Streams, DynamoDB Streams, Kafka Topics, Amazon MQ Queues and SQS Queues. All of these correspond to an
    EventSourceMapping in Lambda, and require that the execution role be given to Kinesis Streams, DynamoDB
    Streams, or SQS Queues, respectively.

    :cvar str policy_arn: The ARN of the AWS managed role policy corresponding to this pull event source
    """

    # Event types that support `FilterCriteria`, stored as a list to keep the alphabetical order
    RESOURCE_TYPES_WITH_EVENT_FILTERING = ["DynamoDB", "Kinesis", "MQ", "MSK", "SelfManagedKafka", "SQS"]

    # Note(xinhol): `PullEventSource` should have been an abstract class. Disabling the type check for the next
    # line to avoid any potential behavior change.
    # TODO: Make `PullEventSource` an abstract class and not giving `resource_type` initial value.
    resource_type: str = None  # type: ignore
    requires_stream_queue_broker = True
    relative_id: str  # overriding the Optional[str]: for event, relative id is not None
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
        "SecretsManagerKmsKeyId": PropertyType(False, is_str()),
        "TumblingWindowInSeconds": PropertyType(False, is_type(int)),
        "FunctionResponseTypes": PropertyType(False, is_type(list)),
        "KafkaBootstrapServers": PropertyType(False, is_type(list)),
        "FilterCriteria": PropertyType(False, is_type(dict)),
        "ConsumerGroupId": PropertyType(False, is_str()),
    }

    Stream: Optional[Intrinsicable[str]]
    Queue: Optional[Intrinsicable[str]]
    BatchSize: Optional[Intrinsicable[int]]
    StartingPosition: Optional[Intrinsicable[str]]
    Enabled: Optional[bool]
    MaximumBatchingWindowInSeconds: Optional[Intrinsicable[int]]
    MaximumRetryAttempts: Optional[Intrinsicable[int]]
    BisectBatchOnFunctionError: Optional[Intrinsicable[bool]]
    MaximumRecordAgeInSeconds: Optional[Intrinsicable[int]]
    DestinationConfig: Optional[Dict[str, Any]]
    ParallelizationFactor: Optional[Intrinsicable[int]]
    Topics: Optional[List[Any]]
    Broker: Optional[Intrinsicable[str]]
    Queues: Optional[List[Any]]
    SourceAccessConfigurations: Optional[List[Any]]
    SecretsManagerKmsKeyId: Optional[str]
    TumblingWindowInSeconds: Optional[Intrinsicable[int]]
    FunctionResponseTypes: Optional[List[Any]]
    KafkaBootstrapServers: Optional[List[Any]]
    FilterCriteria: Optional[Dict[str, Any]]
    ConsumerGroupId: Optional[Intrinsicable[str]]

    def get_policy_arn(self):  # type: ignore[no-untyped-def]
        raise NotImplementedError("Subclass must implement this method")

    def get_policy_statements(self):  # type: ignore[no-untyped-def]
        raise NotImplementedError("Subclass must implement this method")

    @cw_timer(prefix=FUNCTION_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, **kwargs):  # type: ignore[no-untyped-def]
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

        lambda_eventsourcemapping = LambdaEventSourceMapping(
            self.logical_id, attributes=function.get_passthrough_resource_attributes()
        )
        resources.append(lambda_eventsourcemapping)

        try:
            # Name will not be available for Alias resources
            function_name_or_arn = function.get_runtime_attr("name")
        except NotImplementedError:
            function_name_or_arn = function.get_runtime_attr("arn")

        if self.requires_stream_queue_broker and not self.Stream and not self.Queue and not self.Broker:
            raise InvalidEventException(
                self.relative_id,
                "No Queue (for SQS) or Stream (for Kinesis, DynamoDB or MSK) or Broker (for Amazon MQ) provided.",
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
        lambda_eventsourcemapping.FunctionResponseTypes = self.FunctionResponseTypes
        lambda_eventsourcemapping.FilterCriteria = self.FilterCriteria
        self._validate_filter_criteria()  # type: ignore[no-untyped-call]

        if self.KafkaBootstrapServers:
            lambda_eventsourcemapping.SelfManagedEventSource = {
                "Endpoints": {"KafkaBootstrapServers": self.KafkaBootstrapServers}
            }
        if self.ConsumerGroupId:
            consumer_group_id_structure = {"ConsumerGroupId": self.ConsumerGroupId}
            if self.resource_type == "MSK":
                lambda_eventsourcemapping.AmazonManagedKafkaEventSourceConfig = consumer_group_id_structure
            elif self.resource_type == "SelfManagedKafka":
                lambda_eventsourcemapping.SelfManagedKafkaEventSourceConfig = consumer_group_id_structure
            else:
                raise InvalidEventException(
                    self.logical_id,
                    "Property ConsumerGroupId not defined for resource of type {}.".format(self.resource_type),
                )

        destination_config_policy: Optional[Dict[str, Any]] = None
        if self.DestinationConfig:
            on_failure: Dict[str, Any] = sam_expect(
                self.DestinationConfig.get("OnFailure"),
                self.logical_id,
                "DestinationConfig.OnFailure",
                is_sam_event=True,
            ).to_be_a_map()

            # `Type` property is for sam to attach the right policies
            destination_type = on_failure.get("Type")

            # SAM attaches the policies for SQS or SNS only if 'Type' is given
            if destination_type:
                # delete this field as its used internally for SAM to determine the policy
                del on_failure["Type"]
                # the values 'SQS' and 'SNS' are allowed. No intrinsics are allowed
                if destination_type not in ["SQS", "SNS"]:
                    raise InvalidEventException(self.logical_id, "The only valid values for 'Type' are 'SQS' and 'SNS'")
                if destination_type == "SQS":
                    queue_arn = on_failure.get("Destination")
                    destination_config_policy = IAMRolePolicies().sqs_send_message_role_policy(
                        queue_arn, self.logical_id
                    )
                elif destination_type == "SNS":
                    sns_topic_arn = on_failure.get("Destination")
                    destination_config_policy = IAMRolePolicies().sns_publish_role_policy(
                        sns_topic_arn, self.logical_id
                    )

            lambda_eventsourcemapping.DestinationConfig = self.DestinationConfig

        if "role" in kwargs:
            self._link_policy(kwargs["role"], destination_config_policy)  # type: ignore[no-untyped-call]

        return resources

    def _link_policy(self, role, destination_config_policy=None):  # type: ignore[no-untyped-def]
        """If this source triggers a Lambda function whose execution role is auto-generated by SAM, add the
        appropriate managed policy to this Role.

        :param model.iam.IAMRole role: the execution role generated for the function
        """
        policy_arn = self.get_policy_arn()  # type: ignore[no-untyped-call]
        policy_statements = self.get_policy_statements()  # type: ignore[no-untyped-call]
        if role is not None:
            if policy_arn is not None and policy_arn not in role.ManagedPolicyArns:
                role.ManagedPolicyArns.append(policy_arn)
            if policy_statements is not None:
                if role.Policies is None:
                    role.Policies = []
                for policy in policy_statements:
                    if policy not in role.Policies:
                        if not policy.get("PolicyDocument") in [d["PolicyDocument"] for d in role.Policies]:
                            role.Policies.append(policy)
        # add SQS or SNS policy only if role is present in kwargs
        if role is not None and destination_config_policy is not None and destination_config_policy:
            if role.Policies is None:
                role.Policies = []
                role.Policies.append(destination_config_policy)
            if role.Policies and destination_config_policy not in role.Policies:
                # do not add the  policy if the same policy document is already present
                if not destination_config_policy.get("PolicyDocument") in [d["PolicyDocument"] for d in role.Policies]:
                    role.Policies.append(destination_config_policy)

    def _validate_filter_criteria(self):  # type: ignore[no-untyped-def]
        if not self.FilterCriteria or is_intrinsic(self.FilterCriteria):
            return
        if self.resource_type not in self.RESOURCE_TYPES_WITH_EVENT_FILTERING:
            raise InvalidEventException(
                self.relative_id,
                "FilterCriteria is only available for {} events.".format(
                    ", ".join(self.RESOURCE_TYPES_WITH_EVENT_FILTERING)
                ),
            )
        # FilterCriteria is either empty or only has "Filters"
        if list(self.FilterCriteria.keys()) not in [[], ["Filters"]]:
            raise InvalidEventException(self.relative_id, "FilterCriteria field has a wrong format")

    def validate_secrets_manager_kms_key_id(self):  # type: ignore[no-untyped-def]
        if self.SecretsManagerKmsKeyId and not isinstance(self.SecretsManagerKmsKeyId, str):
            raise InvalidEventException(
                self.relative_id,
                "Provided SecretsManagerKmsKeyId should be of type str.",
            )


class Kinesis(PullEventSource):
    """Kinesis event source."""

    resource_type = "Kinesis"

    def get_policy_arn(self):  # type: ignore[no-untyped-def]
        return ArnGenerator.generate_aws_managed_policy_arn("service-role/AWSLambdaKinesisExecutionRole")  # type: ignore[no-untyped-call]

    def get_policy_statements(self):  # type: ignore[no-untyped-def]
        return None


class DynamoDB(PullEventSource):
    """DynamoDB Streams event source."""

    resource_type = "DynamoDB"

    def get_policy_arn(self):  # type: ignore[no-untyped-def]
        return ArnGenerator.generate_aws_managed_policy_arn("service-role/AWSLambdaDynamoDBExecutionRole")  # type: ignore[no-untyped-call]

    def get_policy_statements(self):  # type: ignore[no-untyped-def]
        return None


class SQS(PullEventSource):
    """SQS Queue event source."""

    resource_type = "SQS"

    def get_policy_arn(self):  # type: ignore[no-untyped-def]
        return ArnGenerator.generate_aws_managed_policy_arn("service-role/AWSLambdaSQSQueueExecutionRole")  # type: ignore[no-untyped-call]

    def get_policy_statements(self):  # type: ignore[no-untyped-def]
        return None


class MSK(PullEventSource):
    """MSK event source."""

    resource_type = "MSK"

    def get_policy_arn(self):  # type: ignore[no-untyped-def]
        return ArnGenerator.generate_aws_managed_policy_arn("service-role/AWSLambdaMSKExecutionRole")  # type: ignore[no-untyped-call]

    def get_policy_statements(self):  # type: ignore[no-untyped-def]
        return None


class MQ(PullEventSource):
    """MQ event source."""

    resource_type = "MQ"

    def get_policy_arn(self):  # type: ignore[no-untyped-def]
        return None

    def get_policy_statements(self):  # type: ignore[no-untyped-def]
        if not self.SourceAccessConfigurations:
            raise InvalidEventException(
                self.relative_id,
                "No SourceAccessConfigurations for Amazon MQ event provided.",
            )
        if not isinstance(self.SourceAccessConfigurations, list):
            raise InvalidEventException(
                self.relative_id,
                "Provided SourceAccessConfigurations cannot be parsed into a list.",
            )
        basic_auth_uri = None
        for index, conf in enumerate(self.SourceAccessConfigurations):
            sam_expect(conf, self.relative_id, f"SourceAccessConfigurations[{index}]", is_sam_event=True).to_be_a_map()
            event_type: str = sam_expect(
                conf.get("Type"), self.relative_id, f"SourceAccessConfigurations[{index}].Type", is_sam_event=True
            ).to_be_a_string()
            if event_type not in ("BASIC_AUTH", "VIRTUAL_HOST"):
                raise InvalidEventException(
                    self.relative_id,
                    "Invalid property specified in SourceAccessConfigurations for Amazon MQ event.",
                )
            if event_type == "BASIC_AUTH":
                if basic_auth_uri:
                    raise InvalidEventException(
                        self.relative_id,
                        "Multiple BASIC_AUTH properties specified in SourceAccessConfigurations for Amazon MQ event.",
                    )
                basic_auth_uri = conf.get("URI")
                if not basic_auth_uri:
                    raise InvalidEventException(
                        self.relative_id,
                        "No BASIC_AUTH URI property specified in SourceAccessConfigurations for Amazon MQ event.",
                    )

        if not basic_auth_uri:
            raise InvalidEventException(
                self.relative_id,
                "No BASIC_AUTH property specified in SourceAccessConfigurations for Amazon MQ event.",
            )
        document = {
            "PolicyName": "SamAutoGeneratedAMQPolicy",
            "PolicyDocument": {
                "Statement": [
                    {
                        "Action": [
                            "secretsmanager:GetSecretValue",
                        ],
                        "Effect": "Allow",
                        "Resource": basic_auth_uri,
                    },
                    {
                        "Action": [
                            "mq:DescribeBroker",
                        ],
                        "Effect": "Allow",
                        "Resource": self.Broker,
                    },
                ]
            },
        }
        if self.SecretsManagerKmsKeyId:
            self.validate_secrets_manager_kms_key_id()  # type: ignore[no-untyped-call]
            kms_policy = {
                "Action": "kms:Decrypt",
                "Effect": "Allow",
                "Resource": {
                    "Fn::Sub": "arn:${AWS::Partition}:kms:${AWS::Region}:${AWS::AccountId}:key/"
                    + self.SecretsManagerKmsKeyId
                },
            }
            document["PolicyDocument"]["Statement"].append(kms_policy)  # type: ignore[index]
        return [document]


class SelfManagedKafka(PullEventSource):
    """
    SelfManagedKafka event source
    """

    resource_type = "SelfManagedKafka"
    requires_stream_queue_broker = False
    AUTH_MECHANISM = ["SASL_SCRAM_256_AUTH", "SASL_SCRAM_512_AUTH", "BASIC_AUTH"]

    def get_policy_arn(self):  # type: ignore[no-untyped-def]
        return None

    def get_policy_statements(self):  # type: ignore[no-untyped-def]
        if not self.KafkaBootstrapServers:
            raise InvalidEventException(
                self.relative_id,
                "No KafkaBootstrapServers provided for self managed kafka as an event source",
            )

        if not self.Topics:
            raise InvalidEventException(
                self.relative_id,
                "No Topics provided for self managed kafka as an event source",
            )

        if len(self.Topics) != 1:
            raise InvalidEventException(
                self.relative_id,
                "Topics for self managed kafka only supports single configuration entry.",
            )

        if not self.SourceAccessConfigurations:
            raise InvalidEventException(
                self.relative_id,
                "No SourceAccessConfigurations for self managed kafka event provided.",
            )
        document = self.generate_policy_document(self.SourceAccessConfigurations)
        return [document]

    def generate_policy_document(self, source_access_configurations: List[Any]):  # type: ignore[no-untyped-def]
        statements = []
        authentication_uri, has_vpc_config = self.get_secret_key(source_access_configurations)
        if authentication_uri:
            secret_manager = self.get_secret_manager_secret(authentication_uri)  # type: ignore[no-untyped-call]
            statements.append(secret_manager)

        if has_vpc_config:
            vpc_permissions = self.get_vpc_permission()  # type: ignore[no-untyped-call]
            statements.append(vpc_permissions)

        if self.SecretsManagerKmsKeyId:
            self.validate_secrets_manager_kms_key_id()  # type: ignore[no-untyped-call]
            kms_policy = self.get_kms_policy(self.SecretsManagerKmsKeyId)
            statements.append(kms_policy)

        document = {
            "PolicyDocument": {
                "Statement": statements,
                "Version": "2012-10-17",
            },
            "PolicyName": "SelfManagedKafkaExecutionRolePolicy",
        }

        return document

    def get_secret_key(self, source_access_configurations: List[Any]):  # type: ignore[no-untyped-def]
        authentication_uri = None
        has_vpc_subnet = False
        has_vpc_security_group = False

        if not isinstance(source_access_configurations, list):
            raise InvalidEventException(
                self.relative_id,
                "SourceAccessConfigurations for self managed kafka event should be a list.",
            )
        for config in source_access_configurations:
            sam_expect(config, self.relative_id, "SourceAccessConfigurations").to_be_a_map()
            if config.get("Type") == "VPC_SUBNET":
                self.validate_uri(config.get("URI"), "VPC_SUBNET")
                has_vpc_subnet = True

            elif config.get("Type") == "VPC_SECURITY_GROUP":
                self.validate_uri(config.get("URI"), "VPC_SECURITY_GROUP")
                has_vpc_security_group = True

            elif config.get("Type") in self.AUTH_MECHANISM:
                if authentication_uri:
                    raise InvalidEventException(
                        self.relative_id,
                        "Multiple auth mechanism properties specified in SourceAccessConfigurations for self managed kafka event.",
                    )
                self.validate_uri(config.get("URI"), "auth mechanism")
                authentication_uri = config.get("URI")

            else:
                raise InvalidEventException(
                    self.relative_id,
                    "Invalid SourceAccessConfigurations Type provided for self managed kafka event.",
                )

        if (not has_vpc_subnet and has_vpc_security_group) or (has_vpc_subnet and not has_vpc_security_group):
            raise InvalidEventException(
                self.relative_id,
                "VPC_SUBNET and VPC_SECURITY_GROUP in SourceAccessConfigurations for SelfManagedKafka must be both provided.",
            )
        return authentication_uri, (has_vpc_subnet and has_vpc_security_group)

    def validate_uri(self, uri: Optional[Any], msg: str) -> None:
        if not uri:
            raise InvalidEventException(
                self.relative_id,
                "No {} URI property specified in SourceAccessConfigurations for self managed kafka event.".format(msg),
            )

        if not isinstance(uri, str) and not is_intrinsic(uri):
            raise InvalidEventException(
                self.relative_id,
                "Wrong Type for {} URI property specified in SourceAccessConfigurations for self managed kafka event.".format(
                    msg
                ),
            )

    def get_secret_manager_secret(self, authentication_uri):  # type: ignore[no-untyped-def]
        return {
            "Action": ["secretsmanager:GetSecretValue"],
            "Effect": "Allow",
            "Resource": authentication_uri,
        }

    def get_vpc_permission(self):  # type: ignore[no-untyped-def]
        return {
            "Action": [
                "ec2:CreateNetworkInterface",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DeleteNetworkInterface",
                "ec2:DescribeVpcs",
                "ec2:DescribeSubnets",
                "ec2:DescribeSecurityGroups",
            ],
            "Effect": "Allow",
            "Resource": "*",
        }

    @staticmethod
    def get_kms_policy(secrets_manager_kms_key_id: str) -> Dict[str, Any]:
        return {
            "Action": ["kms:Decrypt"],
            "Effect": "Allow",
            "Resource": {
                "Fn::Sub": "arn:${AWS::Partition}:kms:${AWS::Region}:${AWS::AccountId}:key/"
                + secrets_manager_kms_key_id
            },
        }
