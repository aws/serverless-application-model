import json
import logging
from functools import reduce

import boto3

from samtranslator.model.exceptions import InvalidDocumentException
from samtranslator.translator.managed_policy_translator import ManagedPolicyLoader
from samtranslator.translator.transform import transform
from samtranslator.yaml_helper import yaml_parse


def transform_template(sam_template_path, cfn_output_path):
    """
    Locally transforms a SAM template to a Cloud Formation template

    Parameters
    ----------
    sam_template_path : Path
        SAM template input path
    cfn_output_path : Path
        Cloud formation template output path
    """
    LOG = logging.getLogger(__name__)
    iam_client = boto3.client("iam")

    with open(sam_template_path) as f:
        sam_template = yaml_parse(f)

    try:
        cloud_formation_template = transform(sam_template, {}, ManagedPolicyLoader(iam_client))
        cloud_formation_template_prettified = json.dumps(cloud_formation_template, indent=2)

        with open(cfn_output_path, "w") as f:
            f.write(cloud_formation_template_prettified)

        print("Wrote transformed CloudFormation template to: " + cfn_output_path)
    except InvalidDocumentException as e:
        error_message = reduce(lambda message, error: message + " " + error.message, e.causes, e.message)
        LOG.error(error_message)
        errors = map(lambda cause: cause.message, e.causes)
        LOG.error(errors)
