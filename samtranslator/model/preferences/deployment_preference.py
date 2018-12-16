from collections import namedtuple

from samtranslator.model.exceptions import InvalidResourceException

"""
:param deployment_type: There are two types of deployments at the moment: Linear and Canary.
    There is a default percentage of traffic that is routed to the new function's version for a 30 minute bake
    period after which the alias will 100% be routed to the new function version.
    Linear deployment type means that every 10 minutes 10% more traffic will be routed to the new function
    version.
:param pre_traffic_hook: A lambda function reference that will be used to test the new function version before
    any traffic is shifted to it at all. If his pre_traffic_hook fails the lambda deployment stops leaving
    nothing unchanged for the customer's production traffic (lambda alias still pointed ot the old version)
:param post_traffic_hook: A lambda function reference that will be used to test the new function version after
    all traffic has been shifted for the alias to be 100% pointing to the new function version. If this test
    fails CodeDeploy is in charge of rolling back the deployment meaning 100% shifting traffic back to the old
    version.
:param alarms: A list of Cloudwatch Alarm references that if ever in the alarm state during a deployment (or
    before a deployment starts) cause the deployment to fail and rollback.
:param role: An IAM role ARN that CodeDeploy will use for traffic shifting, an IAM role will not be created if
    this is supplied
:param enabled: Whether this deployment preference is enabled (true by default)
"""
DeploymentPreferenceTuple = namedtuple('DeploymentPreferenceTuple',
                                       ['deployment_type', 'pre_traffic_hook', 'post_traffic_hook', 'alarms',
                                        'enabled', 'role'])


class DeploymentPreference(DeploymentPreferenceTuple):
    """
    The DeploymentPreference object representing the customer's lambda deployment preferences.
    Each parameter controls what happens whenever a customer wants to update their lambda function.
    The data is "immutable".
    """

    @classmethod
    def from_dict(cls, logical_id, deployment_preference_dict):
        """
        :param logical_id: the logical_id of the resource that owns this deployment preference
        :param deployment_preference_dict: the dict object taken from the SAM template
        :return:
        """
        enabled = deployment_preference_dict.get('Enabled', True)
        if not enabled:
            return DeploymentPreference(None, None, None, None, False, None)

        if 'Type' not in deployment_preference_dict:
            raise InvalidResourceException(logical_id, "'DeploymentPreference' is missing required Property 'Type'")

        deployment_type = deployment_preference_dict['Type']
        hooks = deployment_preference_dict.get('Hooks', dict())
        if not isinstance(hooks, dict):
            raise InvalidResourceException(logical_id,
                                           "'Hooks' property of 'DeploymentPreference' must be a dictionary")

        pre_traffic_hook = hooks.get('PreTraffic', None)
        post_traffic_hook = hooks.get('PostTraffic', None)
        alarms = deployment_preference_dict.get('Alarms', None)
        role = deployment_preference_dict.get('Role', None)
        return DeploymentPreference(deployment_type, pre_traffic_hook, post_traffic_hook, alarms, enabled, role)
