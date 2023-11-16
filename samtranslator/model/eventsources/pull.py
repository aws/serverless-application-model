from abc import ABCMeta, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from samtranslator.internal.deprecation_control import deprecated
from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.model import PassThroughProperty, Property, PropertyType, ResourceMacro
from samtranslator.model.eventsources import FUNCTION_EVETSOURCE_METRIC_PREFIX
from samtranslator.model.exceptions import InvalidEventException
from samtranslator.model.iam import IAMRolePolicies
from samtranslator.model.intrinsics import is_intrinsic
from samtranslator.model.lambda_ import LambdaEventSourceMapping
from samtranslator.model.types import IS_BOOL, IS_DICT, IS_INT, IS_LIST, IS_STR, PassThrough
from samtranslator.translator.arn_generator import ArnGenerator
from samtranslator.utils.types import Intrinsicable
from samtranslator.validator.value_validator import sam_expect


class PullEventSource(ResourceMacro, metaclass=ABCMeta):
    """Base class for pull event sources for SAM Functions.

    The pull events are Kinesis Streams, DynamoDB Streams, Kafka Topics, Amazon MQ Queues, SQS Queues, and DocumentDB Clusters. All of these correspond to an
    EventSourceMapping in Lambda, and require that the execution role be given to Kinesis Streams, DynamoDB
    Streams, or SQS Queues, respectively.

    :cvar str policy_arn: The ARN of the AWS managed role policy corresponding to this pull event source
    """

    # Event types that support `FilterCriteria`, stored as a list to keep the alphabetical order
    RESOURCE_TYPES_WITH_EVENT_FILTERING = ["DocumentDB", "DynamoDB", "Kinesis", "MQ", "MSK", "SelfManagedKafka", "SQS"]

    # Note(xinhol): `PullEventSource` should have been an abstract class. Disabling the type check for the next
    # line to avoid any potential behavior change.
    # TODO: Make `PullEventSource` an abstract class and not giving `resource_type` initial value.
    resource_type: str = None  # type: ignore
    relative_id: str  # overriding the Optional[str]: for event, relative id is not None
    property_types: Dict[str, PropertyType] = {
        "BatchSize": PropertyType(False, IS_INT),
        "StartingPosition": PassThroughProperty(False),
        "StartingPositionTimestamp": PassThroughProperty(False),
        "Enabled": PropertyType(False, IS_BOOL),
        "MaximumBatchingWindowInSeconds": PropertyType(False, IS_INT),
        "MaximumRetryAttempts": PropertyType(False, IS_INT),
        "BisectBatchOnFunctionError": PropertyType(False, IS_BOOL),
        "MaximumRecordAgeInSeconds": PropertyType(False, IS_INT),
        "DestinationConfig": PropertyType(False, IS_DICT),
        "ParallelizationFactor": PropertyType(False, IS_INT),
        "Topics": PropertyType(False, IS_LIST),
        "Queues": PropertyType(False, IS_LIST),
        "SourceAccessConfigurations": PropertyType(False, IS_LIST),
        "SecretsManagerKmsKeyId": PropertyType(False, IS_STR),
        "TumblingWindowInSeconds": PropertyType(False, IS_INT),
        "FunctionResponseTypes": PropertyType(False, IS_LIST),
        "KafkaBootstrapServers": PropertyType(False, IS_LIST),
        "FilterCriteria": PropertyType(False, IS_DICT),
        "ConsumerGroupId": PropertyType(False, IS_STR),
        "ScalingConfig": PropertyType(False, IS_DICT),
    }

    BatchSize: Optional[Intrinsicable[int]]
    StartingPosition: Optional[PassThrough]
    StartingPositionTimestamp: Optional[PassThrough]
    Enabled: Optional[bool]
    MaximumBatchingWindowInSeconds: Optional[Intrinsicable[int]]
    MaximumRetryAttempts: Optional[Intrinsicable[int]]
    BisectBatchOnFunctionError: Optional[Intrinsicable[bool]]
    MaximumRecordAgeInSeconds: Optional[Intrinsicable[int]]
    DestinationConfig: Optional[Dict[str, Any]]
    ParallelizationFactor: Optional[Intrinsicable[int]]
    Topics: Optional[List[Any]]
    Queues: Optional[List[Any]]
    SourceAccessConfigurations: Optional[List[Any]]
    SecretsManagerKmsKeyId: Optional[str]
    TumblingWindowInSeconds: Optional[Intrinsicable[int]]
    FunctionResponseTypes: Optional[List[Any]]
    KafkaBootstrapServers: Optional[List[Any]]
    FilterCriteria: Optional[Dict[str, Any]]
    ConsumerGroupId: Optional[Intrinsicable[str]]
    ScalingConfig: Optional[Dict[str, Any]]

    @abstractmethod
    def get_policy_arn(self) -> Optional[str]:
        """Policy to be added to the role (if a role applies)."""

    @abstractmethod
    def get_policy_statements(self) -> Optional[List[Dict[str, Any]]]:
        """Inline policy statements to be added to the role (if a role applies)."""

    @abstractmethod
    def get_event_source_arn(self) -> Optional[PassThrough]:
        """Return the value to assign to lambda event source mapping's EventSourceArn."""

    def add_extra_eventsourcemapping_fields(self, _lambda_eventsourcemapping: LambdaEventSourceMapping) -> None:
        """Adds extra fields to the CloudFormation ESM resource.
        This method can be overriden by a subclass if it has extra fields specific to that subclass.

        :param LambdaEventSourceMapping lambda_eventsourcemapping: the Event source mapping resource to add the fields to.
        """
        return

    @cw_timer(prefix=FUNCTION_EVETSOURCE_METRIC_PREFIX)
    def to_cloudformation(self, **kwargs):  # type: ignore[no-untyped-def] # noqa: PLR0912, PLR0915
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
        except KeyError:
            function_name_or_arn = function.get_runtime_attr("arn")

        lambda_eventsourcemapping.FunctionName = function_name_or_arn
        lambda_eventsourcemapping.EventSourceArn = self.get_event_source_arn()
        lambda_eventsourcemapping.StartingPosition = self.StartingPosition
        lambda_eventsourcemapping.StartingPositionTimestamp = self.StartingPositionTimestamp
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
        lambda_eventsourcemapping.ScalingConfig = self.ScalingConfig
        self._validate_filter_criteria()

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
                    f"Property ConsumerGroupId not defined for resource of type {self.resource_type}.",
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

            # SAM attaches the policies for SQS, SNS or S3 only if 'Type' is given
            if destination_type:
                # delete this field as its used internally for SAM to determine the policy
                del on_failure["Type"]
                # the values 'SQS', 'SNS', and 'S3' are allowed. No intrinsics are allowed
                if destination_type not in ["SQS", "SNS", "S3"]:
                    raise InvalidEventException(
                        self.logical_id, "The only valid values for 'Type' are 'SQS', 'SNS', and 'S3'"
                    )
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
                elif destination_type == "S3":
                    s3_arn = on_failure.get("Destination")
                    destination_config_policy = IAMRolePolicies().s3_send_event_payload_role_policy(
                        s3_arn, self.logical_id
                    )

            lambda_eventsourcemapping.DestinationConfig = self.DestinationConfig

        self.add_extra_eventsourcemapping_fields(lambda_eventsourcemapping)

        if "role" in kwargs:
            self._link_policy(kwargs["role"], destination_config_policy)  # type: ignore[no-untyped-call]

        return resources

    def _link_policy(self, role, destination_config_policy=None):  # type: ignore[no-untyped-def]
        """If this source triggers a Lambda function whose execution role is auto-generated by SAM, add the
        appropriate managed policy to this Role.

        :param model.iam.IAMRole role: the execution role generated for the function
        """
        policy_arn = self.get_policy_arn()
        policy_statements = self.get_policy_statements()
        if role is not None:
            if policy_arn is not None and policy_arn not in role.ManagedPolicyArns:
                role.ManagedPolicyArns.append(policy_arn)
            if policy_statements is not None:
                if role.Policies is None:
                    role.Policies = []
                for policy in policy_statements:
                    if policy not in role.Policies and policy.get("PolicyDocument") not in [
                        d["PolicyDocument"] for d in role.Policies
                    ]:
                        role.Policies.append(policy)
        # add SQS or SNS policy only if role is present in kwargs
        if role is not None and destination_config_policy is not None and destination_config_policy:
            if role.Policies is None:
                role.Policies = []
                role.Policies.append(destination_config_policy)
            if role.Policies and destination_config_policy not in role.Policies:
                policy_document = destination_config_policy.get("PolicyDocument")
                # do not add the policy if the same policy document is already present
                if policy_document not in [d["PolicyDocument"] for d in role.Policies]:
                    role.Policies.append(destination_config_policy)

    def _validate_filter_criteria(self) -> None:
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

    def validate_secrets_manager_kms_key_id(self) -> None:
        if self.SecretsManagerKmsKeyId:
            sam_expect(
                self.SecretsManagerKmsKeyId, self.relative_id, "SecretsManagerKmsKeyId", is_sam_event=True
            ).to_be_a_string()

    def _validate_source_access_configurations(self, supported_types: List[str], required_type: str) -> str:
        """
        Validate the SourceAccessConfigurations parameter and return the URI to
        be used for policy statement creation.
        """

        if not self.SourceAccessConfigurations:
            raise InvalidEventException(
                self.relative_id,
                f"No SourceAccessConfigurations for Amazon {self.resource_type} event provided.",
            )
        if not isinstance(self.SourceAccessConfigurations, list):
            raise InvalidEventException(
                self.relative_id,
                "Provided SourceAccessConfigurations cannot be parsed into a list.",
            )

        required_type_uri: Optional[str] = None
        for index, conf in enumerate(self.SourceAccessConfigurations):
            sam_expect(conf, self.relative_id, f"SourceAccessConfigurations[{index}]", is_sam_event=True).to_be_a_map()
            event_type: str = sam_expect(
                conf.get("Type"), self.relative_id, f"SourceAccessConfigurations[{index}].Type", is_sam_event=True
            ).to_be_a_string()
            if event_type not in supported_types:
                raise InvalidEventException(
                    self.relative_id,
                    f"Invalid property Type specified in SourceAccessConfigurations. The supported values are: {supported_types}.",
                )
            if event_type == required_type:
                if required_type_uri:
                    raise InvalidEventException(
                        self.relative_id,
                        f"Multiple {required_type} properties specified in SourceAccessConfigurations.",
                    )
                required_type_uri = conf.get("URI")
                if not required_type_uri:
                    raise InvalidEventException(
                        self.relative_id,
                        f"No {required_type} URI property specified in SourceAccessConfigurations.",
                    )

        if not required_type_uri:
            raise InvalidEventException(
                self.relative_id,
                f"No {required_type} property specified in SourceAccessConfigurations.",
            )
        return required_type_uri

    @staticmethod
    def _get_kms_decrypt_policy(secrets_manager_kms_key_id: str) -> Dict[str, Any]:
        return {
            "Action": ["kms:Decrypt"],
            "Effect": "Allow",
            "Resource": {
                "Fn::Sub": "arn:${AWS::Partition}:kms:${AWS::Region}:${AWS::AccountId}:key/"
                + secrets_manager_kms_key_id
            },
        }


class Kinesis(PullEventSource):
    """Kinesis event source."""

    resource_type = "Kinesis"
    property_types: Dict[str, PropertyType] = {
        **PullEventSource.property_types,
        "Stream": PassThroughProperty(True),
        "StartingPosition": PassThroughProperty(True),
    }

    Stream: PassThrough

    def get_event_source_arn(self) -> Optional[PassThrough]:
        return self.Stream

    def get_policy_arn(self) -> Optional[str]:
        return ArnGenerator.generate_aws_managed_policy_arn("service-role/AWSLambdaKinesisExecutionRole")

    def get_policy_statements(self) -> Optional[List[Dict[str, Any]]]:
        return None


class DynamoDB(PullEventSource):
    """DynamoDB Streams event source."""

    resource_type = "DynamoDB"
    property_types: Dict[str, PropertyType] = {
        **PullEventSource.property_types,
        "Stream": PassThroughProperty(True),
        "StartingPosition": PassThroughProperty(True),
    }

    Stream: PassThrough

    def get_event_source_arn(self) -> Optional[PassThrough]:
        return self.Stream

    def get_policy_arn(self) -> Optional[str]:
        return ArnGenerator.generate_aws_managed_policy_arn("service-role/AWSLambdaDynamoDBExecutionRole")

    def get_policy_statements(self) -> Optional[List[Dict[str, Any]]]:
        return None


class SQS(PullEventSource):
    """SQS Queue event source."""

    resource_type = "SQS"
    property_types: Dict[str, PropertyType] = {
        **PullEventSource.property_types,
        "Queue": PassThroughProperty(True),
    }

    Queue: PassThrough

    def get_event_source_arn(self) -> Optional[PassThrough]:
        return self.Queue

    def get_policy_arn(self) -> Optional[str]:
        return ArnGenerator.generate_aws_managed_policy_arn("service-role/AWSLambdaSQSQueueExecutionRole")

    def get_policy_statements(self) -> Optional[List[Dict[str, Any]]]:
        return None


class MSK(PullEventSource):
    """MSK event source."""

    resource_type = "MSK"
    property_types: Dict[str, PropertyType] = {
        **PullEventSource.property_types,
        "Stream": PassThroughProperty(True),
        "StartingPosition": PassThroughProperty(True),
    }

    Stream: PassThrough

    def get_event_source_arn(self) -> Optional[PassThrough]:
        return self.Stream

    def get_policy_arn(self) -> Optional[str]:
        return ArnGenerator.generate_aws_managed_policy_arn("service-role/AWSLambdaMSKExecutionRole")

    def get_policy_statements(self) -> Optional[List[Dict[str, Any]]]:
        if self.SourceAccessConfigurations:
            for conf in self.SourceAccessConfigurations:
                # Lambda does not support multiple CLIENT_CERTIFICATE_TLS_AUTH configurations
                if isinstance(conf, dict) and conf.get("Type") == "CLIENT_CERTIFICATE_TLS_AUTH" and conf.get("URI"):
                    return [
                        {
                            "PolicyName": "MSKExecutionRolePolicy",
                            "PolicyDocument": {
                                "Statement": [
                                    {
                                        "Action": [
                                            "secretsmanager:GetSecretValue",
                                        ],
                                        "Effect": "Allow",
                                        "Resource": conf.get("URI"),
                                    }
                                ]
                            },
                        }
                    ]

        return None


class MQ(PullEventSource):
    """MQ event source."""

    resource_type = "MQ"
    property_types: Dict[str, PropertyType] = {
        **PullEventSource.property_types,
        "Broker": PassThroughProperty(True),
        "DynamicPolicyName": Property(False, IS_BOOL),
    }

    Broker: PassThrough
    DynamicPolicyName: Optional[bool]

    @property
    def _policy_name(self) -> str:
        """Generate policy name based on DynamicPolicyName flag and MQ logical ID.

        Policy name is required though its update is "No interuption".
        https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-iam-policy.html#cfn-iam-policy-policyname #noqa

        Historically, policy name was hardcoded as `SamAutoGeneratedAMQPolicy` but it led to a policy name clash
        and failure to deploy, if a Function had at least 2 MQ event sources.
        Since policy is attached to the Lambda execution role,
        policy name should be based on MQ logical ID not to clash with policy names of other MQ event sources.
        However, to support backwards compatibility, we need to keep policy `SamAutoGeneratedAMQPolicy` by default,
        because customers might have code which relys on that policy name consistancy.

        To support both old policy name and ability to have more than one MQ event source, we introduce new field
        `DynamicPolicyName` which when set to true will use MQ logical ID to generate policy name.

        Q: Why to introduce a new field and not to make policy name dynamic by default if there are multiple
        MQ event sources?
        A: Since a customer could have a single MQ source and rely on it's policy name in their code. If that customer
        decides to add a new MQ source, they don't want to change the policy name for the first MQ all over their
        code base. But they can opt in using a dynamic policy name for all other MQ sources they add.

        Q: Why not use dynamic policy names automatically for all MQ event sources but first?
        A: SAM-T doesn't have state and doesn't know what was the CFN resource attribute in a previous transformation.
        Hence, trying to "use dynamic policy names automatically for all MQ event sources but first" can rely only
        on event source order. If a customer added a new MQ source __before__ an old one, an old one would receive
        a dynamic name and would break (potentially) customer's code.

        Returns
        -------
            Name of the policy which will be attached to the Lambda Execution role.
        """
        return f"{self.logical_id}AMQPolicy" if self.DynamicPolicyName else "SamAutoGeneratedAMQPolicy"

    def get_event_source_arn(self) -> Optional[PassThrough]:
        return self.Broker

    def get_policy_arn(self) -> Optional[str]:
        return None

    def get_policy_statements(self) -> Optional[List[Dict[str, Any]]]:
        basic_auth_uri = self._validate_source_access_configurations(["BASIC_AUTH", "VIRTUAL_HOST"], "BASIC_AUTH")

        document = {
            "PolicyName": self._policy_name,
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
            self.validate_secrets_manager_kms_key_id()
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
    AUTH_MECHANISM = [
        "SASL_SCRAM_256_AUTH",
        "SASL_SCRAM_512_AUTH",
        "BASIC_AUTH",
        "CLIENT_CERTIFICATE_TLS_AUTH",
    ]

    def get_event_source_arn(self) -> Optional[PassThrough]:
        return None

    def get_policy_arn(self) -> Optional[str]:
        return None

    def get_policy_statements(self) -> Optional[List[Dict[str, Any]]]:
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
        authentication_uri, authentication_uri_2, has_vpc_config = self.get_secret_key(source_access_configurations)
        if authentication_uri:
            secret_manager = self.get_secret_manager_secret(authentication_uri)  # type: ignore[no-untyped-call]
            statements.append(secret_manager)

        if authentication_uri_2:
            secret_manager = self.get_secret_manager_secret(authentication_uri)  # type: ignore[no-untyped-call]
            statements.append(secret_manager)

        if has_vpc_config:
            vpc_permissions = self.get_vpc_permission()
            statements.append(vpc_permissions)

        if self.SecretsManagerKmsKeyId:
            self.validate_secrets_manager_kms_key_id()
            kms_policy = self._get_kms_decrypt_policy(self.SecretsManagerKmsKeyId)
            statements.append(kms_policy)

        return {
            "PolicyDocument": {
                "Statement": statements,
                "Version": "2012-10-17",
            },
            "PolicyName": "SelfManagedKafkaExecutionRolePolicy",
        }

    def get_secret_key(self, source_access_configurations: List[Any]) -> Tuple[Optional[str], Optional[str], bool]:
        authentication_uri = None
        has_vpc_subnet = False
        has_vpc_security_group = False
        authentication_uri_2 = None

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

            elif config.get("Type") == "SERVER_ROOT_CA_CERTIFICATE":
                self.validate_uri(config.get("URI"), "SERVER_ROOT_CA_CERTIFICATE")
                authentication_uri_2 = config.get("URI")

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
        return authentication_uri, authentication_uri_2, (has_vpc_subnet and has_vpc_security_group)

    def validate_uri(self, uri: Optional[Any], msg: str) -> None:
        if not uri:
            raise InvalidEventException(
                self.relative_id,
                f"No {msg} URI property specified in SourceAccessConfigurations for self managed kafka event.",
            )

        if not isinstance(uri, str) and not is_intrinsic(uri):
            raise InvalidEventException(
                self.relative_id,
                f"Wrong Type for {msg} URI property specified in SourceAccessConfigurations for self managed kafka event.",
            )

    def get_secret_manager_secret(self, authentication_uri):  # type: ignore[no-untyped-def]
        return {
            "Action": ["secretsmanager:GetSecretValue"],
            "Effect": "Allow",
            "Resource": authentication_uri,
        }

    def get_vpc_permission(self) -> Dict[str, Any]:
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
    @deprecated()
    def get_kms_policy(secrets_manager_kms_key_id: str) -> Dict[str, Any]:
        return {
            "Action": ["kms:Decrypt"],
            "Effect": "Allow",
            "Resource": {
                "Fn::Sub": "arn:${AWS::Partition}:kms:${AWS::Region}:${AWS::AccountId}:key/"
                + secrets_manager_kms_key_id
            },
        }


class DocumentDB(PullEventSource):
    """DocumentDB event source."""

    resource_type = "DocumentDB"
    property_types: Dict[str, PropertyType] = {
        **PullEventSource.property_types,
        "Cluster": PassThroughProperty(True),
        "DatabaseName": PassThroughProperty(True),
        "CollectionName": PassThroughProperty(False),
        "FullDocument": PassThroughProperty(False),
    }

    Cluster: PassThrough
    DatabaseName: PassThrough
    CollectionName: Optional[PassThrough]
    FullDocument: Optional[PassThrough]

    def add_extra_eventsourcemapping_fields(self, lambda_eventsourcemapping: LambdaEventSourceMapping) -> None:
        lambda_eventsourcemapping.DocumentDBEventSourceConfig = {
            "DatabaseName": self.DatabaseName,
        }
        if self.CollectionName:
            lambda_eventsourcemapping.DocumentDBEventSourceConfig["CollectionName"] = self.CollectionName  # type: ignore[attr-defined]
        if self.FullDocument:
            lambda_eventsourcemapping.DocumentDBEventSourceConfig["FullDocument"] = self.FullDocument  # type: ignore[attr-defined]

    def get_event_source_arn(self) -> Optional[PassThrough]:
        return self.Cluster

    def get_policy_arn(self) -> Optional[str]:
        return None

    def get_policy_statements(self) -> List[Dict[str, Any]]:
        basic_auth_uri = self._validate_source_access_configurations(["BASIC_AUTH"], "BASIC_AUTH")

        statements = [
            {
                "Action": [
                    "secretsmanager:GetSecretValue",
                ],
                "Effect": "Allow",
                "Resource": basic_auth_uri,
            },
            {
                "Action": [
                    "rds:DescribeDBClusterParameters",
                ],
                "Effect": "Allow",
                "Resource": {"Fn::Sub": "arn:${AWS::Partition}:rds:${AWS::Region}:${AWS::AccountId}:cluster-pg:*"},
            },
            {
                "Action": [
                    "rds:DescribeDBSubnetGroups",
                ],
                "Effect": "Allow",
                "Resource": {"Fn::Sub": "arn:${AWS::Partition}:rds:${AWS::Region}:${AWS::AccountId}:subgrp:*"},
            },
            {
                "Action": [
                    "rds:DescribeDBClusters",
                ],
                "Effect": "Allow",
                "Resource": self.Cluster,
            },
            {
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
            },
        ]

        if self.SecretsManagerKmsKeyId:
            self.validate_secrets_manager_kms_key_id()
            kms_policy = self._get_kms_decrypt_policy(self.SecretsManagerKmsKeyId)
            statements.append(kms_policy)

        document = {
            "PolicyName": "SamAutoGeneratedDocumentDBPolicy",
            "PolicyDocument": {"Statement": statements},
        }

        return [document]
