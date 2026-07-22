"""
AWS::Serverless::MicroVMImage resource transformer
"""

from typing import Any

from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.model import Resource
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.iam import IAMRole, IAMRolePolicies
from samtranslator.model.intrinsics import fnGetAtt
from samtranslator.model.microvm_image.resources import LambdaMicroVMImage
from samtranslator.model.tags.resource_tagging import get_tag_list

MICROVM_BUILD_SERVICE_PRINCIPAL = "lambda.amazonaws.com"


class MicroVMImageGenerator:
    """
    Generator for Lambda MicroVMImage resources
    """

    def __init__(  # noqa: PLR0913
        self,
        logical_id: str,
        name: Any,
        code_uri: Any,
        base_image_arn: Any,
        intrinsics_resolver: IntrinsicsResolver | None = None,
        build_role_arn: Any | None = None,
        base_image_version: Any | None = None,
        description: Any | None = None,
        tags: dict[str, Any] | None = None,
        logging: dict[str, Any] | None = None,
        egress_network_connectors: list[Any] | None = None,
        cpu_configurations: list[dict[str, Any]] | None = None,
        resources: list[dict[str, Any]] | None = None,
        additional_os_capabilities: list[str] | None = None,
        hooks: dict[str, Any] | None = None,
        environment_variables: dict[str, Any] | None = None,
        depends_on: list[str] | None = None,
        resource_attributes: dict[str, Any] | None = None,
        passthrough_resource_attributes: dict[str, Any] | None = None,
    ) -> None:
        self.logical_id = logical_id
        self.name = name
        self.code_uri = code_uri
        self.base_image_arn = base_image_arn
        self.intrinsics_resolver = intrinsics_resolver
        self.build_role_arn = build_role_arn
        self.base_image_version = base_image_version
        self.description = description
        self.tags = tags
        self.logging = logging
        self.egress_network_connectors = egress_network_connectors
        self.cpu_configurations = cpu_configurations
        self.resources = resources
        self.additional_os_capabilities = additional_os_capabilities
        self.hooks = hooks
        self.environment_variables = environment_variables
        self.depends_on = depends_on
        self.resource_attributes = resource_attributes
        self.passthrough_resource_attributes = passthrough_resource_attributes

    def to_cloudformation(self) -> list[Resource]:
        resources: list[Resource] = []

        if not self.build_role_arn:
            build_role = self._create_build_role()
            resources.append(build_role)
            self.build_role_arn = fnGetAtt(build_role.logical_id, "Arn")

        microvm_image = self._create_microvm_image()
        resources.append(microvm_image)

        return resources

    def _create_microvm_image(self) -> LambdaMicroVMImage:
        microvm_image = LambdaMicroVMImage(
            self.logical_id, depends_on=self.depends_on, attributes=self.resource_attributes
        )

        microvm_image.Name = self.name
        microvm_image.CodeArtifact = {"Uri": self.code_uri}
        microvm_image.BaseImageArn = self.base_image_arn
        microvm_image.BuildRoleArn = self.build_role_arn
        microvm_image.BaseImageVersion = self.base_image_version

        microvm_image.Description = self.description or ""

        microvm_image.Tags = self._transform_tags(self.tags)

        microvm_image.Logging = self.logging or {}

        # Flattened fields (all required in CFN, inject empty defaults if not provided)
        microvm_image.EgressNetworkConnectors = self.egress_network_connectors or []
        microvm_image.CpuConfigurations = self.cpu_configurations or []
        microvm_image.Resources = self.resources or []
        microvm_image.AdditionalOsCapabilities = self.additional_os_capabilities or []
        microvm_image.Hooks = self.hooks or {}
        microvm_image.EnvironmentVariables = self._transform_environment_variables(self.environment_variables)

        if self.passthrough_resource_attributes:
            for attr_name, attr_value in self.passthrough_resource_attributes.items():
                microvm_image.set_resource_attribute(attr_name, attr_value)

        return microvm_image

    def _create_build_role(self) -> IAMRole:
        role_logical_id = f"{self.logical_id}BuildRole"

        assume_role_policy = IAMRolePolicies.construct_assume_role_policy_for_service_principal(
            MICROVM_BUILD_SERVICE_PRINCIPAL
        )

        build_role = IAMRole(role_logical_id, attributes=self.passthrough_resource_attributes)
        build_role.AssumeRolePolicyDocument = assume_role_policy
        build_role.Policies = [
            {
                "PolicyName": "MicrovmImageBuildPolicy",
                "PolicyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["s3:GetObject"],
                            "Resource": self._build_s3_resource_arn(),
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            "Resource": "*",
                        },
                    ],
                },
            }
        ]

        build_role.Tags = self._transform_tags()

        return build_role

    def _build_s3_resource_arn(self) -> Any:
        """
        Build the S3 resource ARN for the policy statement.
        1. Try to resolve CodeUri via intrinsics_resolver to get a literal string
        2. If literal s3:// URI → parse bucket and return scoped ARN
        3. Otherwise → use Fn::Split + Fn::Select to let CFN resolve at deploy time
        """
        # Try resolving intrinsics to get a literal value
        resolved = self.code_uri
        if self.intrinsics_resolver and isinstance(self.code_uri, dict):
            resolved = self.intrinsics_resolver.resolve_parameter_refs(self.code_uri)

        # If resolved to a literal s3:// URI, parse the bucket
        if isinstance(resolved, str) and resolved.startswith("s3://"):
            parts = resolved[len("s3://") :].split("/", 1)
            bucket = parts[0]
            if bucket:
                return {"Fn::Sub": f"arn:${{AWS::Partition}}:s3:::{bucket}/*"}
            raise InvalidResourceException(
                self.logical_id, "CodeUri must be a valid S3 URI with a bucket name (e.g. s3://bucket/key.zip)."
            )

        # Otherwise, use Fn::Split to extract bucket at deploy time
        return {
            "Fn::Sub": [
                "arn:${AWS::Partition}:s3:::${Bucket}/*",
                {
                    "Bucket": {
                        "Fn::Select": [
                            2,
                            {"Fn::Split": ["/", self.code_uri]},
                        ]
                    }
                },
            ]
        }

    def _transform_tags(self, tags: dict[str, Any] | None = None) -> list[dict[str, str]]:
        tags_dict = (tags or {}).copy()
        tags_dict["lambda:createdBy"] = "SAM"
        return get_tag_list(tags_dict)

    def _transform_environment_variables(self, env_vars: dict[str, Any] | None) -> list[dict[str, str]]:
        """Convert EnvironmentVariables from map form to CFN array of {Key, Value}."""
        if not env_vars:
            return []
        return [{"Key": k, "Value": v} for k, v in env_vars.items()]
