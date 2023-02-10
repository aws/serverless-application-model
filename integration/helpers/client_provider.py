from threading import Lock

import boto3
from botocore.config import Config


class ClientProvider:
    def __init__(self):
        self._lock = Lock()
        self._cloudformation_client = None
        self._s3_client = None
        self._api_client = None
        self._lambda_client = None
        self._iam_client = None
        self._api_v2_client = None
        self._sfn_client = None
        self._cloudwatch_log_client = None
        self._cloudwatch_event_client = None
        self._cloudwatch_client = None
        self._sqs_client = None
        self._sns_client = None
        self._dynamoDB_streams_client = None
        self._kinesis_client = None
        self._mq_client = None
        self._iot_client = None
        self._kafka_client = None
        self._code_deploy_client = None
        self._sar_client = None
        self._ec2_client = None

    @property
    def cfn_client(self):
        """
        Cloudformation Client
        """
        with self._lock:
            if not self._cloudformation_client:
                config = Config(retries={"max_attempts": 10, "mode": "standard"})
                self._cloudformation_client = boto3.client("cloudformation", config=config)
        return self._cloudformation_client

    @property
    def s3_client(self):
        """
        S3 Client
        """
        with self._lock:
            if not self._s3_client:
                self._s3_client = boto3.client("s3")
        return self._s3_client

    @property
    def api_client(self):
        """
        APIGateway Client
        """
        with self._lock:
            if not self._api_client:
                self._api_client = boto3.client("apigateway")
        return self._api_client

    @property
    def lambda_client(self):
        """
        Lambda Client
        """
        with self._lock:
            if not self._lambda_client:
                self._lambda_client = boto3.client("lambda")
        return self._lambda_client

    @property
    def iam_client(self):
        """
        IAM Client
        """
        with self._lock:
            if not self._iam_client:
                self._iam_client = boto3.client("iam")
        return self._iam_client

    @property
    def api_v2_client(self):
        """
        APIGatewayV2 Client
        """
        with self._lock:
            if not self._api_v2_client:
                self._api_v2_client = boto3.client("apigatewayv2")
        return self._api_v2_client

    @property
    def sfn_client(self):
        """
        Step Functions Client
        """
        with self._lock:
            if not self._sfn_client:
                self._sfn_client = boto3.client("stepfunctions")
        return self._sfn_client

    @property
    def cloudwatch_log_client(self):
        """
        CloudWatch Log Client
        """
        with self._lock:
            if not self._cloudwatch_log_client:
                self._cloudwatch_log_client = boto3.client("logs")
        return self._cloudwatch_log_client

    @property
    def cloudwatch_event_client(self):
        """
        CloudWatch Event Client
        """
        with self._lock:
            if not self._cloudwatch_event_client:
                self._cloudwatch_event_client = boto3.client("events")
        return self._cloudwatch_event_client

    @property
    def cloudwatch_client(self):
        """
        CloudWatch Client
        """
        with self._lock:
            if not self._cloudwatch_client:
                self._cloudwatch_client = boto3.client("cloudwatch")
        return self._cloudwatch_client

    @property
    def sqs_client(self):
        """
        SQS Client
        """
        with self._lock:
            if not self._sqs_client:
                self._sqs_client = boto3.client("sqs")
        return self._sqs_client

    @property
    def sns_client(self):
        """
        SQS Client
        """
        with self._lock:
            if not self._sns_client:
                self._sns_client = boto3.client("sns")
        return self._sns_client

    @property
    def dynamodb_streams_client(self):
        """
        DynamoDB Stream Client
        """
        with self._lock:
            if not self._dynamoDB_streams_client:
                self._dynamoDB_streams_client = boto3.client("dynamodbstreams")
        return self._dynamoDB_streams_client

    @property
    def kinesis_client(self):
        """
        DynamoDB Stream Client
        """
        with self._lock:
            if not self._kinesis_client:
                self._kinesis_client = boto3.client("kinesis")
        return self._kinesis_client

    @property
    def mq_client(self):
        """
        MQ Client
        """
        with self._lock:
            if not self._mq_client:
                self._mq_client = boto3.client("mq")
        return self._mq_client

    @property
    def iot_client(self):
        """
        IOT Client
        """
        with self._lock:
            if not self._iot_client:
                self._iot_client = boto3.client("iot")
        return self._iot_client

    @property
    def kafka_client(self):
        """
        Kafka Client
        """
        with self._lock:
            if not self._kafka_client:
                self._kafka_client = boto3.client("kafka")
        return self._kafka_client

    @property
    def code_deploy_client(self):
        """
        Kafka Client
        """
        with self._lock:
            if not self._code_deploy_client:
                self._code_deploy_client = boto3.client("codedeploy")
        return self._code_deploy_client

    @property
    def sar_client(self):
        """
        Serverless Application Repo. Client
        """
        with self._lock:
            if not self._sar_client:
                self._sar_client = boto3.client("serverlessrepo")
        return self._sar_client

    @property
    def ec2_client(self):
        """
        EC2 Client
        """
        with self._lock:
            if not self._ec2_client:
                self._ec2_client = boto3.client("ec2")
        return self._ec2_client
