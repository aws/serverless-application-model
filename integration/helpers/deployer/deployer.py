"""
Cloudformation deploy class which also streams events and changeset information
This was ported over from the sam-cli repo
"""

# Copyright 2012-2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

# This is a modified version of the Deployer class from aws-sam-cli
# (and its dependencies) to work with python 2
# Modifications:
#  - Imports now reference local classes
#  - Alternative imports for python2
#  - py3 -> py2 migrations (ex: "".format() instead of f"", no "from" for raise)
#  - Moved UserException to exceptions.py
#  - Moved DeployColor to colors.py
#  - Removed unnecessary functions from artifact_exporter
import logging
import sys
import time
from collections import OrderedDict
from datetime import datetime, timezone

import botocore

from integration.helpers.deployer.exceptions import exceptions as deploy_exceptions
from integration.helpers.deployer.utils.artifact_exporter import mktempfile
from integration.helpers.deployer.utils.colors import DeployColor
from integration.helpers.deployer.utils.retry import retry_with_exponential_backoff_and_jitter
from integration.helpers.deployer.utils.table_print import (
    MIN_OFFSET,
    newline_per_item,
    pprint_column_names,
    pprint_columns,
)
from integration.helpers.deployer.utils.time_util import utc_to_timestamp
from integration.helpers.resource import generate_suffix

LOG = logging.getLogger(__name__)

DESCRIBE_STACK_EVENTS_FORMAT_STRING = (
    "{ResourceStatus:<{0}} {ResourceType:<{1}} {LogicalResourceId:<{2}} {ResourceStatusReason:<{3}}"
)
DESCRIBE_STACK_EVENTS_DEFAULT_ARGS = OrderedDict(
    {
        "ResourceStatus": "ResourceStatus",
        "ResourceType": "ResourceType",
        "LogicalResourceId": "LogicalResourceId",
        "ResourceStatusReason": "ResourceStatusReason",
    }
)

DESCRIBE_STACK_EVENTS_TABLE_HEADER_NAME = "CloudFormation events from changeset"

DESCRIBE_CHANGESET_FORMAT_STRING = "{Operation:<{0}} {LogicalResourceId:<{1}} {ResourceType:<{2}} {Replacement:<{3}}"
DESCRIBE_CHANGESET_DEFAULT_ARGS = OrderedDict(
    {
        "Operation": "Operation",
        "LogicalResourceId": "LogicalResourceId",
        "ResourceType": "ResourceType",
        "Replacement": "Replacement",
    }
)

DESCRIBE_CHANGESET_TABLE_HEADER_NAME = "CloudFormation stack changeset"

OUTPUTS_FORMAT_STRING = "{Outputs:<{0}}"
OUTPUTS_DEFAULTS_ARGS = OrderedDict({"Outputs": "Outputs"})

OUTPUTS_TABLE_HEADER_NAME = "CloudFormation outputs from deployed stack"


class Deployer:
    def __init__(self, cloudformation_client, changeset_prefix="sam-integ-"):
        self._client = cloudformation_client
        self.changeset_prefix = changeset_prefix
        # 500ms of sleep time between stack checks and describe stack events.
        self.client_sleep = 0.5
        # 2000ms of backoff time which is exponentially used, when there are exceptions during describe stack events
        self.backoff = 2
        # Maximum number of attempts before raising exception back up the chain.
        self.max_attempts = 3
        self.deploy_color = DeployColor()

    def create_changeset(
        self,
        stack_name,
        cfn_template,
        parameter_values,
        capabilities,
        role_arn,
        notification_arns,
        s3_uploader,
        tags,
        changeset_type,
    ):
        """
        Call Cloudformation to create a changeset and wait for it to complete

        :param stack_name: Name or ID of stack
        :param cfn_template: CloudFormation template string
        :param parameter_values: Template parameters object
        :param capabilities: Array of capabilities passed to CloudFormation
        :param tags: Array of tags passed to CloudFormation
        :param tags: the type of the changeset
        :return:
        """

        if type == "UPDATE":
            # UsePreviousValue not valid if parameter is new
            summary = self._client.get_template_summary(StackName=stack_name)
            existing_parameters = [parameter["ParameterKey"] for parameter in summary["Parameters"]]
            parameter_values = [
                x
                for x in parameter_values
                if not (x.get("UsePreviousValue", False) and x["ParameterKey"] not in existing_parameters)
            ]
        else:
            # When creating a new stack, UsePreviousValue=True is invalid.
            # For such parameters, users should either override with new value,
            # or set a Default value in template to successfully create a stack.
            parameter_values = [x for x in parameter_values if not x.get("UsePreviousValue", False)]

        # Each changeset will get a unique name based on time.
        # Description is also setup based on current date and that SAM CLI is used.
        kwargs = {
            "ChangeSetName": self.changeset_prefix + str(int(time.time())),
            "StackName": stack_name,
            "TemplateBody": cfn_template,
            "ChangeSetType": changeset_type,
            "Parameters": parameter_values,
            "Capabilities": capabilities,
            "Description": f"Created by SAM CLI at {datetime.now(timezone.utc).isoformat()} UTC",
            "Tags": tags,
        }

        # If an S3 uploader is available, use TemplateURL to deploy rather than
        # TemplateBody. This is required for large templates.
        if s3_uploader:
            with mktempfile() as temporary_file:
                temporary_file.write(kwargs.pop("TemplateBody"))
                temporary_file.flush()

                # add random suffix to file_name to enable multiple tests run in the same time
                template_file_name = "template" + generate_suffix()

                # TemplateUrl property requires S3 URL to be in path-style format
                s3_uploader.upload_file(template_file_name, temporary_file.name)
                kwargs["TemplateURL"] = s3_uploader.get_s3_uri(template_file_name)

        # don't set these arguments if not specified to use existing values
        if role_arn is not None:
            kwargs["RoleARN"] = role_arn
        if notification_arns is not None:
            kwargs["NotificationARNs"] = notification_arns
        return self._create_change_set(stack_name=stack_name, changeset_type=changeset_type, **kwargs)

    def _create_change_set(self, stack_name, changeset_type, **kwargs):
        try:
            resp = self._client.create_change_set(**kwargs)
            return resp, changeset_type
        except botocore.exceptions.ClientError as ex:
            if "The bucket you are attempting to access must be addressed using the specified endpoint" in str(ex):
                raise deploy_exceptions.DeployBucketInDifferentRegionError(
                    f"Failed to create/update stack {stack_name}"
                )
            raise deploy_exceptions.ChangeSetError(stack_name=stack_name, msg=str(ex))

        except Exception as ex:
            LOG.debug("Unable to create changeset", exc_info=ex)
            raise deploy_exceptions.ChangeSetError(stack_name=stack_name, msg=str(ex))

    @pprint_column_names(
        format_string=DESCRIBE_CHANGESET_FORMAT_STRING,
        format_kwargs=DESCRIBE_CHANGESET_DEFAULT_ARGS,
        table_header=DESCRIBE_CHANGESET_TABLE_HEADER_NAME,
    )
    def describe_changeset(self, change_set_id, stack_name, **kwargs):
        """
        Call Cloudformation to describe a changeset

        :param change_set_id: ID of the changeset
        :param stack_name: Name of the CloudFormation stack
        :return: dictionary of changes described in the changeset.
        """
        paginator = self._client.get_paginator("describe_change_set")
        response_iterator = paginator.paginate(ChangeSetName=change_set_id, StackName=stack_name)
        changes = {"Add": [], "Modify": [], "Remove": []}
        changes_showcase = {"Add": "+ Add", "Modify": "* Modify", "Remove": "- Delete"}
        changeset = False
        for item in response_iterator:
            cf_changes = item.get("Changes")
            for change in cf_changes:
                changeset = True
                resource_props = change.get("ResourceChange")
                action = resource_props.get("Action")
                changes[action].append(
                    {
                        "LogicalResourceId": resource_props.get("LogicalResourceId"),
                        "ResourceType": resource_props.get("ResourceType"),
                        "Replacement": (
                            "N/A" if resource_props.get("Replacement") is None else resource_props.get("Replacement")
                        ),
                    }
                )

        for k, v in changes.items():
            for value in v:
                row_color = self.deploy_color.get_changeset_action_color(action=k)
                pprint_columns(
                    columns=[
                        changes_showcase.get(k, k),
                        value["LogicalResourceId"],
                        value["ResourceType"],
                        value["Replacement"],
                    ],
                    width=kwargs["width"],
                    margin=kwargs["margin"],
                    format_string=DESCRIBE_CHANGESET_FORMAT_STRING,
                    format_args=kwargs["format_args"],
                    columns_dict=DESCRIBE_CHANGESET_DEFAULT_ARGS.copy(),
                    color=row_color,
                )

        if not changeset:
            # There can be cases where there are no changes,
            # but could be an an addition of a SNS notification topic.
            pprint_columns(
                columns=["-", "-", "-", "-"],
                width=kwargs["width"],
                margin=kwargs["margin"],
                format_string=DESCRIBE_CHANGESET_FORMAT_STRING,
                format_args=kwargs["format_args"],
                columns_dict=DESCRIBE_CHANGESET_DEFAULT_ARGS.copy(),
            )

        return changes

    def wait_for_changeset(self, changeset_id, stack_name):
        """
        Waits until the changeset creation completes

        :param changeset_id: ID or name of the changeset
        :param stack_name:   Stack name
        :return: Latest status of the create-change-set operation
        """
        sys.stdout.write("\nWaiting for changeset to be created...\n")
        sys.stdout.flush()

        # Wait for changeset to be created
        waiter = self._client.get_waiter("change_set_create_complete")
        # Poll every 5 seconds. Changeset creation should be fast
        waiter_config = {"Delay": 5}
        try:
            waiter.wait(ChangeSetName=changeset_id, StackName=stack_name, WaiterConfig=waiter_config)
        except botocore.exceptions.WaiterError as ex:
            LOG.error("Waiter exception waiting for changeset", exc_info=ex)

            resp = ex.last_response
            status = resp.get("Status", "")
            reason = resp.get("StatusReason", "")

            if (
                status == "FAILED"
                and "The submitted information didn't contain changes." in reason
                or "No updates are to be performed" in reason
            ):
                raise deploy_exceptions.ChangeEmptyError(stack_name=stack_name)

            raise deploy_exceptions.ChangeSetError(
                stack_name=stack_name, msg=f"ex: {ex} Status: {status}. Reason: {reason}"
            )

    def execute_changeset(self, changeset_id, stack_name):
        """
        Calls CloudFormation to execute changeset

        :param changeset_id: ID of the changeset
        :param stack_name: Name or ID of the stack
        :return: Response from execute-change-set call
        """
        try:
            return self._client.execute_change_set(ChangeSetName=changeset_id, StackName=stack_name)
        except botocore.exceptions.ClientError as ex:
            raise deploy_exceptions.DeployFailedError(stack_name=stack_name, msg=str(ex))

    def get_last_event_time(self, stack_name):
        """
        Finds the last event time stamp thats present for the stack, if not get the current time
        :param stack_name: Name or ID of the stack
        :return: unix epoch
        """
        try:
            return utc_to_timestamp(
                self._client.describe_stack_events(StackName=stack_name)["StackEvents"][0]["Timestamp"]
            )
        except KeyError:
            return time.time()

    def _check_stack_complete(self, status):
        return "COMPLETE" in status and "CLEANUP" not in status

    def wait_for_execute(self, stack_name, changeset_type):
        sys.stdout.write(
            "\n{} - Waiting for stack create/update "
            "to complete\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        sys.stdout.flush()

        # Pick the right waiter
        if changeset_type == "CREATE":
            waiter = self._client.get_waiter("stack_create_complete")
        elif changeset_type == "UPDATE":
            waiter = self._client.get_waiter("stack_update_complete")
        else:
            raise RuntimeError(f"Invalid changeset type {changeset_type}")

        # Poll every 30 seconds. Polling too frequently risks hitting rate limits
        # on CloudFormation's DescribeStacks API
        waiter_config = {"Delay": 30, "MaxAttempts": 120}
        self._wait(stack_name, waiter, waiter_config)

        outputs = self.get_stack_outputs(stack_name=stack_name, echo=False)
        if outputs:
            self._display_stack_outputs(outputs)

    @retry_with_exponential_backoff_and_jitter(deploy_exceptions.ThrottlingError, 5, 360)
    def _wait(self, stack_name, waiter, waiter_config):
        try:
            waiter.wait(StackName=stack_name, WaiterConfig=waiter_config)
        except botocore.exceptions.WaiterError as ex:
            LOG.debug("Execute changeset waiter exception", exc_info=ex)
            if "Throttling" in str(ex):
                raise deploy_exceptions.ThrottlingError(stack_name=stack_name, msg=str(ex))
            else:
                raise deploy_exceptions.DeployFailedError(stack_name=stack_name, msg=str(ex))

    def create_and_wait_for_changeset(
        self,
        stack_name,
        cfn_template,
        parameter_values,
        capabilities,
        role_arn,
        notification_arns,
        s3_uploader,
        tags,
        changeset_type,
    ):
        try:
            result, changeset_type = self.create_changeset(
                stack_name,
                cfn_template,
                parameter_values,
                capabilities,
                role_arn,
                notification_arns,
                s3_uploader,
                tags,
                changeset_type,
            )
            self.wait_for_changeset(result["Id"], stack_name)
            self.describe_changeset(result["Id"], stack_name)
            return result
        except deploy_exceptions.ChangeEmptyError:
            try:
                # Delete the most recent change set that failed to create because it was empty
                changeset = sorted(self._client.list_change_sets(StackName=stack_name).get("Summaries"), key=lambda c: c["CreationTime"])[-1]
                if changeset.get("Status") == "FAILED" and changeset.get("ExecutionStatus") == "UNAVAILABLE":
                    self._client.delete_change_set(ChangeSetName=changeset["ChangeSetId"], StackName=stack_name)
            except Exception as ex:
                LOG.warning("Failed to clean up empty changeset", exc_info=ex)
            return {}
        except botocore.exceptions.ClientError as ex:
            raise deploy_exceptions.DeployFailedError(stack_name=stack_name, msg=str(ex))

    @pprint_column_names(
        format_string=OUTPUTS_FORMAT_STRING, format_kwargs=OUTPUTS_DEFAULTS_ARGS, table_header=OUTPUTS_TABLE_HEADER_NAME
    )
    def _display_stack_outputs(self, stack_outputs, **kwargs):
        for counter, output in enumerate(stack_outputs):
            for k, v in [
                ("Key", output.get("OutputKey")),
                ("Description", output.get("Description", "-")),
                ("Value", output.get("OutputValue")),
            ]:
                pprint_columns(
                    columns=[f"{k:<{MIN_OFFSET}}{v:<{MIN_OFFSET}}"],
                    width=kwargs["width"],
                    margin=kwargs["margin"],
                    format_string=OUTPUTS_FORMAT_STRING,
                    format_args=kwargs["format_args"],
                    columns_dict=OUTPUTS_DEFAULTS_ARGS.copy(),
                    color="green",
                    replace_whitespace=False,
                    break_long_words=False,
                    drop_whitespace=False,
                )
            newline_per_item(stack_outputs, counter)

    @retry_with_exponential_backoff_and_jitter(deploy_exceptions.ThrottlingError, 5, 360)
    def get_stack_outputs(self, stack_name, echo=True):
        try:
            stacks_description = self._client.describe_stacks(StackName=stack_name)
            try:
                outputs = stacks_description["Stacks"][0]["Outputs"]
                if echo:
                    sys.stdout.write(f"\nStack {stack_name} outputs:\n")
                    sys.stdout.flush()
                    self._display_stack_outputs(stack_outputs=outputs)
                return outputs
            except KeyError:
                return None

        except botocore.exceptions.ClientError as ex:
            if "Throttling" in str(ex):
                raise deploy_exceptions.ThrottlingError(stack_name=stack_name, msg=str(ex))
            else:
                raise deploy_exceptions.DeployStackOutPutFailedError(stack_name=stack_name, msg=str(ex))
