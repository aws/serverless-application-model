from collections import namedtuple

from samtranslator.model.intrinsics import ref

CodeDeployLambdaAliasUpdate = namedtuple('CodeDeployLambdaAliasUpdate',
                                         ['ApplicationName', 'DeploymentGroupName', 'BeforeAllowTrafficHook',
                                          'AfterAllowTrafficHook'])

"""
This class is a model for the update policy which becomes present on any function alias for which there is an enabled
deployment preference. Another words, if the customer specifies a deployment preference for how they want their
function aliases updated this update policy shows up to connect their lambda function alias with the correct
CodeDeploy resources.
:param ApplicationName: A reference to the name of the CodeDeploy Application (one per stack)
:param DeploymentGroupName: A reference to the name of the deployment group (in this version one per function)
:param BeforeAllowTrafficHook: A reference to the lambda function which is used to test their new version before we
    shift traffic
:param AfterAllowTrafficHook: A reference to the lambda function used for testing after we're done shifting traffic
"""


class UpdatePolicy(CodeDeployLambdaAliasUpdate):
    def to_dict(self):
        """
        :return: a dict that can be used as part of a cloudformation template
        """
        dict_with_nones = self._asdict()
        codedeploy_lambda_alias_update_dict = dict((k, v) for k, v in dict_with_nones.items()
                                                   if v != ref(None) and v is not None)
        return {'CodeDeployLambdaAliasUpdate': codedeploy_lambda_alias_update_dict}
