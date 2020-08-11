import boto3


def get_all_available_regions(service_name):
    """
    Wrapper function to get all available regions including ones that are not regional endpoints

    :param service_name: Name of service to get available regions like 's3' etc.
    :return:Returns a list of endpoint names (e.g., ["us-east-1"]).
    """

    return boto3._get_default_session().get_available_regions(service_name, allow_non_regional=True)


def get_available_serviceable_regions(service_name):
    """
    Wrapper function to get available regions excluding ones that are not regional endpoints

    :param service_name: Name of service to get available regions like 's3' etc.
    :return:Returns a list of endpoint names (e.g., ["us-east-1"]).
    """

    return boto3._get_default_session().get_available_regions(service_name, allow_non_regional=False)


def get_available_nonserviceable_regions(service_name):
    """
    Wrapper function to get only non serviceable regions

    :param service_name: Name of service to get available regions like 's3' etc.
    :return:Returns a list of endpoint names (e.g., ["us-east-1"]).
    """

    all_regions = boto3._get_default_session().get_available_regions(service_name, allow_non_regional=True)
    s_regions = boto3._get_default_session().get_available_regions(service_name, allow_non_regional=False)

    return list(set(all_regions) - set(s_regions))
