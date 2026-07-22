"""Unit tests for MicroVMImage generator"""

from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.model.microvm_image.generators import MicroVMImageGenerator


class TestMicroVMImageGenerator:
    def test_to_cloudformation_auto_generates_build_role(self):
        gen = MicroVMImageGenerator(
            logical_id="MyAgent",
            name="my-agent",
            code_uri="s3://bucket/agent.zip",
            base_image_arn="arn:aws:lambda:::microvm-image:base",
        )
        resources = gen.to_cloudformation()

        assert len(resources) == 2
        role = resources[0]
        image = resources[1]

        assert role.logical_id == "MyAgentBuildRole"
        assert role.resource_type == "AWS::IAM::Role"
        assert image.logical_id == "MyAgent"
        assert image.resource_type == "AWS::Lambda::MicrovmImage"
        assert image.BuildRoleArn == {"Fn::GetAtt": ["MyAgentBuildRole", "Arn"]}

    def test_to_cloudformation_with_provided_build_role(self):
        gen = MicroVMImageGenerator(
            logical_id="MyAgent",
            name="my-agent",
            code_uri="s3://bucket/agent.zip",
            base_image_arn="arn:aws:lambda:::microvm-image:base",
            build_role_arn="arn:aws:iam::123456789012:role/CustomRole",
        )
        resources = gen.to_cloudformation()

        assert len(resources) == 1
        image = resources[0]
        assert image.BuildRoleArn == "arn:aws:iam::123456789012:role/CustomRole"

    def test_code_uri_wraps_into_code_artifact(self):
        gen = MicroVMImageGenerator(
            logical_id="MyAgent",
            name="my-agent",
            code_uri="s3://bucket/agent.zip",
            base_image_arn="arn:aws:lambda:::microvm-image:base",
            build_role_arn="arn:aws:iam::123456789012:role/Role",
        )
        resources = gen.to_cloudformation()
        image = resources[0]

        assert image.CodeArtifact == {"Uri": "s3://bucket/agent.zip"}

    def test_tags_converted_to_array_with_sam_tag(self):
        gen = MicroVMImageGenerator(
            logical_id="MyAgent",
            name="my-agent",
            code_uri="s3://bucket/agent.zip",
            base_image_arn="arn:aws:lambda:::microvm-image:base",
            build_role_arn="arn:aws:iam::123456789012:role/Role",
            tags={"Environment": "Production"},
        )
        resources = gen.to_cloudformation()
        image = resources[0]

        assert {"Key": "Environment", "Value": "Production"} in image.Tags
        assert {"Key": "lambda:createdBy", "Value": "SAM"} in image.Tags

    def test_environment_variables_converted_to_array(self):
        gen = MicroVMImageGenerator(
            logical_id="MyAgent",
            name="my-agent",
            code_uri="s3://bucket/agent.zip",
            base_image_arn="arn:aws:lambda:::microvm-image:base",
            build_role_arn="arn:aws:iam::123456789012:role/Role",
            environment_variables={"LOG_LEVEL": "info", "APP_ENV": "production"},
        )
        resources = gen.to_cloudformation()
        image = resources[0]

        assert {"Key": "LOG_LEVEL", "Value": "info"} in image.EnvironmentVariables
        assert {"Key": "APP_ENV", "Value": "production"} in image.EnvironmentVariables

    def test_passthrough_fields(self):
        gen = MicroVMImageGenerator(
            logical_id="MyAgent",
            name="my-agent",
            code_uri="s3://bucket/agent.zip",
            base_image_arn="arn:aws:lambda:::microvm-image:base",
            build_role_arn="arn:aws:iam::123456789012:role/Role",
            resources=[{"MinimumMemoryInMiB": 1024}],
            cpu_configurations=[{"Architecture": "ARM_64"}],
            egress_network_connectors=["arn:aws:lambda:::network-connector:INTERNET_EGRESS"],
            additional_os_capabilities=["ALL"],
            hooks={"Port": 9000, "MicrovmHooks": {"Run": "ENABLED"}},
        )
        resources = gen.to_cloudformation()
        image = resources[0]

        assert image.Resources == [{"MinimumMemoryInMiB": 1024}]
        assert image.CpuConfigurations == [{"Architecture": "ARM_64"}]
        assert image.EgressNetworkConnectors == ["arn:aws:lambda:::network-connector:INTERNET_EGRESS"]
        assert image.AdditionalOsCapabilities == ["ALL"]
        assert image.Hooks == {"Port": 9000, "MicrovmHooks": {"Run": "ENABLED"}}

    def test_build_role_trust_policy(self):
        gen = MicroVMImageGenerator(
            logical_id="MyAgent",
            name="my-agent",
            code_uri="s3://bucket/agent.zip",
            base_image_arn="arn:aws:lambda:::microvm-image:base",
        )
        resources = gen.to_cloudformation()
        role = resources[0]

        statement = role.AssumeRolePolicyDocument["Statement"][0]
        assert statement["Principal"]["Service"] == ["lambda.amazonaws.com"]
        assert statement["Action"] == ["sts:AssumeRole"]

    def test_build_role_s3_scoped_literal_uri(self):
        gen = MicroVMImageGenerator(
            logical_id="MyAgent",
            name="my-agent",
            code_uri="s3://my-bucket/agent.zip",
            base_image_arn="arn:aws:lambda:::microvm-image:base",
        )
        resources = gen.to_cloudformation()
        role = resources[0]

        statements = role.Policies[0]["PolicyDocument"]["Statement"]
        s3_statement = statements[0]
        logs_statement = statements[1]

        assert s3_statement["Action"] == ["s3:GetObject"]
        assert s3_statement["Resource"] == {"Fn::Sub": "arn:${AWS::Partition}:s3:::my-bucket/*"}

        assert "logs:CreateLogGroup" in logs_statement["Action"]
        assert logs_statement["Resource"] == "*"

    def test_build_role_s3_scoped_intrinsic_with_resolver(self):
        resolver = IntrinsicsResolver({"CodeUriParam": "s3://resolved-bucket/app.zip"})
        gen = MicroVMImageGenerator(
            logical_id="MyAgent",
            name="my-agent",
            code_uri={"Ref": "CodeUriParam"},
            base_image_arn="arn:aws:lambda:::microvm-image:base",
            intrinsics_resolver=resolver,
        )
        resources = gen.to_cloudformation()
        role = resources[0]

        s3_statement = role.Policies[0]["PolicyDocument"]["Statement"][0]
        assert s3_statement["Resource"] == {"Fn::Sub": "arn:${AWS::Partition}:s3:::resolved-bucket/*"}

    def test_build_role_s3_scoped_intrinsic_fallback_fn_split(self):
        gen = MicroVMImageGenerator(
            logical_id="MyAgent",
            name="my-agent",
            code_uri={"Fn::ImportValue": "SharedBucketUri"},
            base_image_arn="arn:aws:lambda:::microvm-image:base",
        )
        resources = gen.to_cloudformation()
        role = resources[0]

        s3_statement = role.Policies[0]["PolicyDocument"]["Statement"][0]
        resource = s3_statement["Resource"]
        assert resource["Fn::Sub"][0] == "arn:${AWS::Partition}:s3:::${Bucket}/*"
        assert resource["Fn::Sub"][1]["Bucket"]["Fn::Select"][0] == 2
        assert resource["Fn::Sub"][1]["Bucket"]["Fn::Select"][1]["Fn::Split"] == [
            "/",
            {"Fn::ImportValue": "SharedBucketUri"},
        ]

    def test_empty_defaults_injected_when_omitted(self):
        gen = MicroVMImageGenerator(
            logical_id="MyAgent",
            name="my-agent",
            code_uri="s3://bucket/agent.zip",
            base_image_arn="arn:aws:lambda:::microvm-image:base",
            base_image_version="0.2",
            build_role_arn="arn:aws:iam::123456789012:role/Role",
        )
        resources = gen.to_cloudformation()
        image = resources[0]

        assert image.Logging == {}
        assert image.Description == ""
        assert image.EgressNetworkConnectors == []
        assert image.CpuConfigurations == []
        assert image.Resources == []
        assert image.AdditionalOsCapabilities == []
        assert image.Hooks == {}
        assert image.EnvironmentVariables == []
