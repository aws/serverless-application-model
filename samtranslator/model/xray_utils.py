from samtranslator.translator.arn_generator import ArnGenerator


def get_xray_managed_policy_name():
    partition_name = ArnGenerator.get_partition_name()
    if partition_name == "aws":
        return "AWSXrayWriteOnlyAccess"
    return "AWSXRayDaemonWriteAccess"
