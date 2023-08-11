import copy
from typing import Any, Dict, List, Optional, Union, cast

from samtranslator.model.codedeploy import CodeDeployApplication, CodeDeployDeploymentGroup
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.iam import IAMRole
from samtranslator.model.intrinsics import (
    fnGetAtt,
    fnSub,
    is_intrinsic,
    is_intrinsic_if,
    is_intrinsic_no_value,
    make_combined_condition,
    ref,
    validate_intrinsic_if_items,
)
from samtranslator.model.update_policy import UpdatePolicy
from samtranslator.translator.arn_generator import ArnGenerator

from .deployment_preference import DeploymentPreference

CODE_DEPLOY_SERVICE_ROLE_LOGICAL_ID = "CodeDeployServiceRole"
CODEDEPLOY_APPLICATION_LOGICAL_ID = "ServerlessDeploymentApplication"
CODEDEPLOY_PREDEFINED_CONFIGURATIONS_LIST = [
    "Canary10Percent5Minutes",
    "Canary10Percent10Minutes",
    "Canary10Percent15Minutes",
    "Canary10Percent30Minutes",
    "Linear10PercentEvery1Minute",
    "Linear10PercentEvery2Minutes",
    "Linear10PercentEvery3Minutes",
    "Linear10PercentEvery10Minutes",
    "AllAtOnce",
]
CODE_DEPLOY_CONDITION_NAME = "ServerlessCodeDeployCondition"


class DeploymentPreferenceCollection:
    """
    This class contains the collection of all global and
    specific / per function deployment preferences. It includes ways to add
    the deployment preference information from the SAM template and how to
    generate the update policy (and dependencies of the update policy) for
    each function alias. Dependencies include the codedeploy cloudformation
    resources.
    """

    def __init__(self) -> None:
        """
        This collection stores an internal dict of the deployment preferences for each function's
        deployment preference in the SAM Template.
        """
        self._resource_preferences: Dict[str, Any] = {}

    def add(self, logical_id: str, deployment_preference_dict: Dict[str, Any], condition: Optional[str] = None) -> None:
        """
        Add this deployment preference to the collection

        :raise ValueError if an existing logical id already exists in the _resource_preferences
        :param logical_id: logical id of the resource where this deployment preference applies
        :param deployment_preference_dict: the input SAM template deployment preference mapping
        :param condition: the condition (if it exists) on the serverless function
        """
        if logical_id in self._resource_preferences:
            raise ValueError(f"logical_id {logical_id} previously added to this deployment_preference_collection")

        self._resource_preferences[logical_id] = DeploymentPreference.from_dict(  # type: ignore[no-untyped-call]
            logical_id, deployment_preference_dict, condition
        )

    def get(self, logical_id: str) -> DeploymentPreference:
        """
        :rtype: DeploymentPreference object previously added for this given logical_id
        """
        # Note: it never returns None
        # TODO: find a way to deal with this implicit assumption
        return cast(DeploymentPreference, self._resource_preferences.get(logical_id))

    def any_enabled(self) -> bool:
        """
        :return: boolean whether any deployment preferences in the collection are enabled
        """
        return any(preference.enabled for preference in self._resource_preferences.values())

    def can_skip_service_role(self) -> bool:
        """
        If every one of the deployment preferences have a custom IAM role provided, we can skip creating the
        service role altogether.
        :return: True, if we can skip creating service role. False otherwise
        """
        return all(preference.role or not preference.enabled for preference in self._resource_preferences.values())

    def needs_resource_condition(self) -> Union[Dict[str, Any], bool]:
        """
        If all preferences have a condition, all code deploy resources need to be conditionally created
        :return: True, if a condition needs to be created
        """
        # If there are any enabled deployment preferences without conditions, return false
        return self._resource_preferences and not any(
            not preference.condition and preference.enabled for preference in self._resource_preferences.values()
        )

    def get_all_deployment_conditions(self) -> List[str]:
        """
        Returns a list of all conditions associated with the deployment preference resources
        :return: List of condition names
        """
        conditions_set = {preference.condition for preference in self._resource_preferences.values()}
        if None in conditions_set:
            # None can exist if there are disabled deployment preference(s)
            conditions_set.remove(None)
        return list(conditions_set)

    def create_aggregate_deployment_condition(self) -> Union[None, Dict[str, Dict[str, List[Dict[str, Any]]]]]:
        """
        Creates an aggregate deployment condition if necessary
        :return: None if <2 conditions are found, otherwise a dictionary of new conditions to add to template
        """
        return make_combined_condition(self.get_all_deployment_conditions(), CODE_DEPLOY_CONDITION_NAME)

    def enabled_logical_ids(self) -> List[str]:
        """
        :return: only the logical id's for the deployment preferences in this collection which are enabled
        """
        return [logical_id for logical_id, preference in self._resource_preferences.items() if preference.enabled]

    def get_codedeploy_application(self) -> CodeDeployApplication:
        codedeploy_application_resource = CodeDeployApplication(CODEDEPLOY_APPLICATION_LOGICAL_ID)
        codedeploy_application_resource.ComputePlatform = "Lambda"
        if self.needs_resource_condition():
            conditions = self.get_all_deployment_conditions()
            condition_name = CODE_DEPLOY_CONDITION_NAME
            if len(conditions) <= 1:
                condition_name = conditions.pop()
            codedeploy_application_resource.set_resource_attribute("Condition", condition_name)
        return codedeploy_application_resource

    def get_codedeploy_iam_role(self) -> IAMRole:
        iam_role = IAMRole(CODE_DEPLOY_SERVICE_ROLE_LOGICAL_ID)
        iam_role.AssumeRolePolicyDocument = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": ["sts:AssumeRole"],
                    "Effect": "Allow",
                    "Principal": {"Service": ["codedeploy.amazonaws.com"]},
                }
            ],
        }

        # CodeDeploy has a new managed policy. We cannot update any existing partitions, without customer reach out
        # that support AWSCodeDeployRoleForLambda since this could regress stacks that are currently deployed.
        if ArnGenerator.get_partition_name() in ["aws-iso", "aws-iso-b"]:
            iam_role.ManagedPolicyArns = [
                ArnGenerator.generate_aws_managed_policy_arn("service-role/AWSCodeDeployRoleForLambdaLimited")
            ]
        else:
            iam_role.ManagedPolicyArns = [
                ArnGenerator.generate_aws_managed_policy_arn("service-role/AWSCodeDeployRoleForLambda")
            ]

        if self.needs_resource_condition():
            conditions = self.get_all_deployment_conditions()
            condition_name = CODE_DEPLOY_CONDITION_NAME
            if len(conditions) <= 1:
                condition_name = conditions.pop()
            iam_role.set_resource_attribute("Condition", condition_name)
        return iam_role

    def deployment_group(self, function_logical_id: str) -> CodeDeployDeploymentGroup:
        """
        :param function_logical_id: logical_id of the function this deployment group belongs to
        :return: CodeDeployDeploymentGroup resource
        """

        deployment_preference = self.get(function_logical_id)

        deployment_group = CodeDeployDeploymentGroup(self.deployment_group_logical_id(function_logical_id))  # type: ignore[no-untyped-call, no-untyped-call]

        try:
            deployment_group.AlarmConfiguration = self._convert_alarms(deployment_preference.alarms)  # type: ignore[no-untyped-call]
        except ValueError as e:
            raise InvalidResourceException(function_logical_id, str(e)) from e

        deployment_group.ApplicationName = ref(CODEDEPLOY_APPLICATION_LOGICAL_ID)
        deployment_group.AutoRollbackConfiguration = {
            "Enabled": True,
            "Events": ["DEPLOYMENT_FAILURE", "DEPLOYMENT_STOP_ON_ALARM", "DEPLOYMENT_STOP_ON_REQUEST"],
        }

        deployment_group.DeploymentConfigName = self._replace_deployment_types(  # type: ignore[no-untyped-call]
            copy.deepcopy(deployment_preference.deployment_type)
        )

        deployment_group.DeploymentStyle = {"DeploymentType": "BLUE_GREEN", "DeploymentOption": "WITH_TRAFFIC_CONTROL"}

        deployment_group.ServiceRoleArn = fnGetAtt(CODE_DEPLOY_SERVICE_ROLE_LOGICAL_ID, "Arn")
        if deployment_preference.role:
            deployment_group.ServiceRoleArn = deployment_preference.role

        if deployment_preference.trigger_configurations:
            deployment_group.TriggerConfigurations = deployment_preference.trigger_configurations

        if deployment_preference.condition:
            deployment_group.set_resource_attribute("Condition", deployment_preference.condition)

        return deployment_group

    def _convert_alarms(self, preference_alarms):  # type: ignore[no-untyped-def]
        """
        Converts deployment preference alarms to an AlarmsConfiguration

        Parameters
        ----------
        preference_alarms : dict
            Deployment preference alarms

        Returns
        -------
        dict
            AlarmsConfiguration if alarms is set, None otherwise

        Raises
        ------
        ValueError
            If Alarms is in the wrong format
        """
        if not preference_alarms or is_intrinsic_no_value(preference_alarms):
            return None

        if is_intrinsic_if(preference_alarms):
            processed_alarms = copy.deepcopy(preference_alarms)
            alarms_list = processed_alarms.get("Fn::If")
            validate_intrinsic_if_items(alarms_list)
            alarms_list[1] = self._build_alarm_configuration(alarms_list[1])  # type: ignore[no-untyped-call]
            alarms_list[2] = self._build_alarm_configuration(alarms_list[2])  # type: ignore[no-untyped-call]
            return processed_alarms

        return self._build_alarm_configuration(preference_alarms)  # type: ignore[no-untyped-call]

    def _build_alarm_configuration(self, alarms):  # type: ignore[no-untyped-def]
        """
        Builds an AlarmConfiguration from a list of alarms

        Parameters
        ----------
        alarms : list[str]
            Alarms

        Returns
        -------
        dict
            AlarmsConfiguration for a deployment group

        Raises
        ------
        ValueError
            If alarms is not a list
        """
        if not isinstance(alarms, list):
            raise ValueError("Alarms must be a list")

        if len(alarms) == 0 or is_intrinsic_no_value(alarms[0]):
            return {}

        return {
            "Enabled": True,
            "Alarms": [{"Name": alarm} for alarm in alarms],
        }

    def _replace_deployment_types(self, value, key=None):  # type: ignore[no-untyped-def]
        if isinstance(value, list):
            for i, v in enumerate(value):
                value[i] = self._replace_deployment_types(v)  # type: ignore[no-untyped-call]
            return value
        if is_intrinsic(value):
            for k, v in value.items():
                value[k] = self._replace_deployment_types(v, k)  # type: ignore[no-untyped-call]
            return value
        if value in CODEDEPLOY_PREDEFINED_CONFIGURATIONS_LIST:
            if key == "Fn::Sub":  # Don't nest a "Sub" in a "Sub"
                return ["CodeDeployDefault.Lambda${ConfigName}", {"ConfigName": value}]
            return fnSub("CodeDeployDefault.Lambda${ConfigName}", {"ConfigName": value})
        return value

    def update_policy(self, function_logical_id: str) -> UpdatePolicy:
        deployment_preference = self.get(function_logical_id)

        return UpdatePolicy(
            ref(CODEDEPLOY_APPLICATION_LOGICAL_ID),
            self.deployment_group(function_logical_id).get_runtime_attr("name"),
            deployment_preference.pre_traffic_hook,
            deployment_preference.post_traffic_hook,
        )

    def deployment_group_logical_id(self, function_logical_id):  # type: ignore[no-untyped-def]
        return function_logical_id + "DeploymentGroup"

    def __eq__(self, other):  # type: ignore[no-untyped-def]
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __ne__(self, other):  # type: ignore[no-untyped-def]
        if isinstance(other, self.__class__):
            return not self.__eq__(other)  # type: ignore[no-untyped-call]
        return NotImplemented

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.__dict__.items())))
