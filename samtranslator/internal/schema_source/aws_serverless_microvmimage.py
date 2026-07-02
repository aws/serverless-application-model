from __future__ import annotations

from typing import Literal

from samtranslator.internal.schema_source.common import (
    BaseModel,
    DictStrAny,
    ResourceAttributes,
    SamIntrinsicable,
    get_prop,
)

PROPERTIES_STEM = "sam-resource-microvmimage"
HOOKS_STEM = "sam-property-microvmimage-hooks"
MICROVM_HOOKS_STEM = "sam-property-microvmimage-microvmhooks"
MICROVM_IMAGE_HOOKS_STEM = "sam-property-microvmimage-microvmimagehooks"
RESOURCE_SPEC_STEM = "sam-property-microvmimage-resource"
CPU_CONFIGURATION_STEM = "sam-property-microvmimage-cpuconfiguration"
LOGGING_STEM = "sam-property-microvmimage-logging"
CLOUDWATCH_LOGGING_STEM = "sam-property-microvmimage-cloudwatchlogging"

properties = get_prop(PROPERTIES_STEM)
hooks_props = get_prop(HOOKS_STEM)
microvm_hooks_props = get_prop(MICROVM_HOOKS_STEM)
microvm_image_hooks_props = get_prop(MICROVM_IMAGE_HOOKS_STEM)
resource_spec = get_prop(RESOURCE_SPEC_STEM)
cpu_configuration = get_prop(CPU_CONFIGURATION_STEM)
logging_props = get_prop(LOGGING_STEM)
cloudwatch_logging_props = get_prop(CLOUDWATCH_LOGGING_STEM)

HookState = SamIntrinsicable[Literal["ENABLED", "DISABLED"]]


class ResourceSpec(BaseModel):
    MinimumMemoryInMiB: SamIntrinsicable[int] = resource_spec("MinimumMemoryInMiB")


class CpuConfiguration(BaseModel):
    Architecture: SamIntrinsicable[Literal["ARM_64"]] = cpu_configuration("Architecture")


class MicrovmHooks(BaseModel):
    Run: HookState | None = microvm_hooks_props("Run")
    RunTimeoutInSeconds: SamIntrinsicable[int] | None = microvm_hooks_props("RunTimeoutInSeconds")
    Resume: HookState | None = microvm_hooks_props("Resume")
    ResumeTimeoutInSeconds: SamIntrinsicable[int] | None = microvm_hooks_props("ResumeTimeoutInSeconds")
    Suspend: HookState | None = microvm_hooks_props("Suspend")
    SuspendTimeoutInSeconds: SamIntrinsicable[int] | None = microvm_hooks_props("SuspendTimeoutInSeconds")
    Terminate: HookState | None = microvm_hooks_props("Terminate")
    TerminateTimeoutInSeconds: SamIntrinsicable[int] | None = microvm_hooks_props("TerminateTimeoutInSeconds")


class MicrovmImageHooks(BaseModel):
    Ready: HookState | None = microvm_image_hooks_props("Ready")
    ReadyTimeoutInSeconds: SamIntrinsicable[int] | None = microvm_image_hooks_props("ReadyTimeoutInSeconds")
    Validate: HookState | None = microvm_image_hooks_props("Validate")
    ValidateTimeoutInSeconds: SamIntrinsicable[int] | None = microvm_image_hooks_props("ValidateTimeoutInSeconds")


class Hooks(BaseModel):
    Port: SamIntrinsicable[int] | None = hooks_props("Port")
    MicrovmHooks: MicrovmHooks | None = hooks_props("MicrovmHooks")
    MicrovmImageHooks: MicrovmImageHooks | None = hooks_props("MicrovmImageHooks")


class CloudWatchLogging(BaseModel):
    LogGroup: SamIntrinsicable[str] | None = cloudwatch_logging_props("LogGroup")
    LogStream: SamIntrinsicable[str] | None = cloudwatch_logging_props("LogStream")


class Logging(BaseModel):
    Disabled: bool | None = logging_props("Disabled")
    CloudWatch: CloudWatchLogging | None = logging_props("CloudWatch")


class Properties(BaseModel):
    Name: SamIntrinsicable[str] = properties("Name")
    CodeUri: SamIntrinsicable[str] = properties("CodeUri")
    BaseImageArn: SamIntrinsicable[str] = properties("BaseImageArn")
    BaseImageVersion: SamIntrinsicable[str] = properties("BaseImageVersion")
    BuildRoleArn: SamIntrinsicable[str] | None = properties("BuildRoleArn")
    Description: SamIntrinsicable[str] | None = properties("Description")
    Tags: DictStrAny | None = properties("Tags")
    Logging: Logging | None = properties("Logging")
    EgressNetworkConnectors: list[SamIntrinsicable[str]] | None = properties("EgressNetworkConnectors")
    CpuConfigurations: list[CpuConfiguration] | None = properties("CpuConfigurations")
    Resources: list[ResourceSpec] | None = properties("Resources")
    AdditionalOsCapabilities: list[SamIntrinsicable[Literal["ALL"]]] | None = properties("AdditionalOsCapabilities")
    Hooks: Hooks | None = properties("Hooks")
    EnvironmentVariables: DictStrAny | None = properties("EnvironmentVariables")
    PropagateTags: bool | None = properties("PropagateTags")


class Globals(BaseModel):
    BuildRoleArn: SamIntrinsicable[str] | None = properties("BuildRoleArn")
    BaseImageArn: SamIntrinsicable[str] | None = properties("BaseImageArn")
    BaseImageVersion: SamIntrinsicable[str] | None = properties("BaseImageVersion")
    Logging: Logging | None = properties("Logging")
    EgressNetworkConnectors: list[SamIntrinsicable[str]] | None = properties("EgressNetworkConnectors")
    CpuConfigurations: list[CpuConfiguration] | None = properties("CpuConfigurations")
    Resources: list[ResourceSpec] | None = properties("Resources")
    AdditionalOsCapabilities: list[SamIntrinsicable[Literal["ALL"]]] | None = properties("AdditionalOsCapabilities")
    Hooks: Hooks | None = properties("Hooks")
    EnvironmentVariables: DictStrAny | None = properties("EnvironmentVariables")
    Tags: DictStrAny | None = properties("Tags")
    PropagateTags: bool | None = properties("PropagateTags")


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::MicrovmImage"]
    Properties: Properties
