from .deployment_preference import DeploymentPreference
from samtranslator.model.codedeploy import CodeDeployApplication
from samtranslator.model.codedeploy import CodeDeployDeploymentGroup
from samtranslator.model.iam import IAMRole
from samtranslator.model.intrinsics import fnSub, is_intrinsic
from samtranslator.model.update_policy import UpdatePolicy
from samtranslator.translator.arn_generator import ArnGenerator
import copy

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


class DeploymentPreferenceCollection(object):
    """
    This class contains the collection of all global and
    specific / per function deployment preferences. It includes ways to add
    the deployment preference information from the SAM template and how to
    generate the update policy (and dependencies of the update policy) for
    each function alias. Dependencies include the codedeploy cloudformation
    resources.
    """

    def __init__(self):
        """
        This collection stores an intenral dict of the deployment preferences for each function's
            deployment preference in the SAM Template.
        """
        self._resource_preferences = {}
        self.codedeploy_application = self._codedeploy_application()
        self.codedeploy_iam_role = self._codedeploy_iam_role()

    def add(self, logical_id, deployment_preference_dict):
        """
        Add this deployment preference to the collection

        :raise ValueError if an existing logical id already exists in the _resource_preferences
        :param logical_id: logical id of the resource where this deployment preference applies
        :param deployment_preference_dict: the input SAM template deployment preference mapping
        """
        if logical_id in self._resource_preferences:
            raise ValueError(
                "logical_id {logical_id} previously added to this deployment_preference_collection".format(
                    logical_id=logical_id
                )
            )

        self._resource_preferences[logical_id] = DeploymentPreference.from_dict(logical_id, deployment_preference_dict)

    def get(self, logical_id):
        """
        :rtype: DeploymentPreference object previously added for this given logical_id
        """
        return self._resource_preferences.get(logical_id)

    def any_enabled(self):
        """
        :return: boolean whether any deployment preferences in the collection are enabled
        """
        return any(preference.enabled for preference in self._resource_preferences.values())

    def can_skip_service_role(self):
        """
        If every one of the deployment preferences have a custom IAM role provided, we can skip creating the
        service role altogether.
        :return: True, if we can skip creating service role. False otherwise
        """
        return all(preference.role for preference in self._resource_preferences.values())

    def enabled_logical_ids(self):
        """
        :return: only the logical id's for the deployment preferences in this collection which are enabled
        """
        return [logical_id for logical_id, preference in self._resource_preferences.items() if preference.enabled]

    def _codedeploy_application(self):
        codedeploy_application_resource = CodeDeployApplication(CODEDEPLOY_APPLICATION_LOGICAL_ID)
        codedeploy_application_resource.ComputePlatform = "Lambda"
        return codedeploy_application_resource

    def _codedeploy_iam_role(self):
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
        iam_role.ManagedPolicyArns = [
            ArnGenerator.generate_aws_managed_policy_arn("service-role/AWSCodeDeployRoleForLambda")
        ]

        return iam_role

    def deployment_group(self, function_logical_id):
        """
        :param function_logical_id: logical_id of the function this deployment group belongs to
        :return: CodeDeployDeploymentGroup resource
        """

        deployment_preference = self.get(function_logical_id)

        deployment_group = CodeDeployDeploymentGroup(self.deployment_group_logical_id(function_logical_id))

        if deployment_preference.alarms is not None:
            deployment_group.AlarmConfiguration = {
                "Enabled": True,
                "Alarms": [{"Name": alarm} for alarm in deployment_preference.alarms],
            }

        deployment_group.ApplicationName = self.codedeploy_application.get_runtime_attr("name")
        deployment_group.AutoRollbackConfiguration = {
            "Enabled": True,
            "Events": ["DEPLOYMENT_FAILURE", "DEPLOYMENT_STOP_ON_ALARM", "DEPLOYMENT_STOP_ON_REQUEST"],
        }

        deployment_group.DeploymentConfigName = self._replace_deployment_types(
            copy.deepcopy(deployment_preference.deployment_type)
        )

        deployment_group.DeploymentStyle = {"DeploymentType": "BLUE_GREEN", "DeploymentOption": "WITH_TRAFFIC_CONTROL"}

        deployment_group.ServiceRoleArn = self.codedeploy_iam_role.get_runtime_attr("arn")
        if deployment_preference.role:
            deployment_group.ServiceRoleArn = deployment_preference.role

        if deployment_preference.trigger_configurations:
            deployment_group.TriggerConfigurations = deployment_preference.trigger_configurations

        return deployment_group

    def _replace_deployment_types(self, value, key=None):
        if isinstance(value, list):
            for i in range(len(value)):
                value[i] = self._replace_deployment_types(value[i])
            return value
        elif is_intrinsic(value):
            for (k, v) in value.items():
                value[k] = self._replace_deployment_types(v, k)
            return value
        else:
            if value in CODEDEPLOY_PREDEFINED_CONFIGURATIONS_LIST:
                if key == "Fn::Sub":  # Don't nest a "Sub" in a "Sub"
                    return ["CodeDeployDefault.Lambda${ConfigName}", {"ConfigName": value}]
                return fnSub("CodeDeployDefault.Lambda${ConfigName}", {"ConfigName": value})
            return value

    def update_policy(self, function_logical_id):
        deployment_preference = self.get(function_logical_id)

        return UpdatePolicy(
            self.codedeploy_application.get_runtime_attr("name"),
            self.deployment_group(function_logical_id).get_runtime_attr("name"),
            deployment_preference.pre_traffic_hook,
            deployment_preference.post_traffic_hook,
        )

    def deployment_group_logical_id(self, function_logical_id):
        return function_logical_id + "DeploymentGroup"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        return NotImplemented

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))
