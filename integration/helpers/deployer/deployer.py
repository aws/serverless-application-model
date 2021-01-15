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
import sys
import math
from collections import OrderedDict
import logging
import time
from datetime import datetime

import botocore

from integration.helpers.deployer.utils.colors import DeployColor
from integration.helpers.deployer.exceptions import exceptions as deploy_exceptions
from integration.helpers.deployer.utils.table_print import (
    pprint_column_names,
    pprint_columns,
    newline_per_item,
    MIN_OFFSET,
)
from integration.helpers.deployer.utils.artifact_exporter import mktempfile, parse_s3_url
from integration.helpers.deployer.utils.time import utc_to_timestamp

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

    def has_stack(self, stack_name):
        """
        Checks if a CloudFormation stack with given name exists

        :param stack_name: Name or ID of the stack
        :return: True if stack exists. False otherwise
        """
        try:
            resp = self._client.describe_stacks(StackName=stack_name)
            if not resp["Stacks"]:
                return False

            # When you run CreateChangeSet on a a stack that does not exist,
            # CloudFormation will create a stack and set it's status
            # REVIEW_IN_PROGRESS. However this stack is cannot be manipulated
            # by "update" commands. Under this circumstances, we treat like
            # this stack does not exist and call CreateChangeSet will
            # ChangeSetType set to CREATE and not UPDATE.
            stack = resp["Stacks"][0]
            return stack["StackStatus"] != "REVIEW_IN_PROGRESS"

        except botocore.exceptions.ClientError as e:
            # If a stack does not exist, describe_stacks will throw an
            # exception. Unfortunately we don't have a better way than parsing
            # the exception msg to understand the nature of this exception.

            if "Stack with id {0} does not exist".format(stack_name) in str(e):
                LOG.debug("Stack with id %s does not exist", stack_name)
                return False
        except botocore.exceptions.BotoCoreError as e:
            # If there are credentials, environment errors,
            # catch that and throw a deploy failed error.

            LOG.debug("Botocore Exception : %s", str(e))
            raise deploy_exceptions.DeployFailedError(stack_name=stack_name, msg=str(e))

        except Exception as e:
            # We don't know anything about this exception. Don't handle
            LOG.debug("Unable to get stack details.", exc_info=e)
            raise e

    def create_changeset(
        self, stack_name, cfn_template, parameter_values, capabilities, role_arn, notification_arns, s3_uploader, tags
    ):
        """
        Call Cloudformation to create a changeset and wait for it to complete

        :param stack_name: Name or ID of stack
        :param cfn_template: CloudFormation template string
        :param parameter_values: Template parameters object
        :param capabilities: Array of capabilities passed to CloudFormation
        :param tags: Array of tags passed to CloudFormation
        :return:
        """
        if not self.has_stack(stack_name):
            changeset_type = "CREATE"
            # When creating a new stack, UsePreviousValue=True is invalid.
            # For such parameters, users should either override with new value,
            # or set a Default value in template to successfully create a stack.
            parameter_values = [x for x in parameter_values if not x.get("UsePreviousValue", False)]
        else:
            changeset_type = "UPDATE"
            # UsePreviousValue not valid if parameter is new
            summary = self._client.get_template_summary(StackName=stack_name)
            existing_parameters = [parameter["ParameterKey"] for parameter in summary["Parameters"]]
            parameter_values = [
                x
                for x in parameter_values
                if not (x.get("UsePreviousValue", False) and x["ParameterKey"] not in existing_parameters)
            ]

        # Each changeset will get a unique name based on time.
        # Description is also setup based on current date and that SAM CLI is used.
        kwargs = {
            "ChangeSetName": self.changeset_prefix + str(int(time.time())),
            "StackName": stack_name,
            "TemplateBody": cfn_template,
            "ChangeSetType": changeset_type,
            "Parameters": parameter_values,
            "Capabilities": capabilities,
            "Description": "Created by SAM CLI at {0} UTC".format(datetime.utcnow().isoformat()),
            "Tags": tags,
        }

        # If an S3 uploader is available, use TemplateURL to deploy rather than
        # TemplateBody. This is required for large templates.
        if s3_uploader:
            with mktempfile() as temporary_file:
                temporary_file.write(kwargs.pop("TemplateBody"))
                temporary_file.flush()

                # TemplateUrl property requires S3 URL to be in path-style format
                parts = parse_s3_url(
                    s3_uploader.upload_with_dedup(temporary_file.name, "template"), version_property="Version"
                )
                kwargs["TemplateURL"] = s3_uploader.to_path_style_s3_url(parts["Key"], parts.get("Version", None))

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
                    "Failed to create/update stack {}".format(stack_name)
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
                        "Replacement": "N/A"
                        if resource_props.get("Replacement") is None
                        else resource_props.get("Replacement"),
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
        sys.stdout.write("\nWaiting for changeset to be created..\n")
        sys.stdout.flush()

        # Wait for changeset to be created
        waiter = self._client.get_waiter("change_set_create_complete")
        # Poll every 5 seconds. Changeset creation should be fast
        waiter_config = {"Delay": 5}
        try:
            waiter.wait(ChangeSetName=changeset_id, StackName=stack_name, WaiterConfig=waiter_config)
        except botocore.exceptions.WaiterError as ex:

            resp = ex.last_response
            status = resp["Status"]
            reason = resp["StatusReason"]

            if (
                status == "FAILED"
                and "The submitted information didn't contain changes." in reason
                or "No updates are to be performed" in reason
            ):
                raise deploy_exceptions.ChangeEmptyError(stack_name=stack_name)

            raise deploy_exceptions.ChangeSetError(
                stack_name=stack_name, msg="ex: {0} Status: {1}. Reason: {2}".format(ex, status, reason)
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

    @pprint_column_names(
        format_string=DESCRIBE_STACK_EVENTS_FORMAT_STRING,
        format_kwargs=DESCRIBE_STACK_EVENTS_DEFAULT_ARGS,
        table_header=DESCRIBE_STACK_EVENTS_TABLE_HEADER_NAME,
    )
    def describe_stack_events(self, stack_name, time_stamp_marker, **kwargs):
        """
        Calls CloudFormation to get current stack events
        :param stack_name: Name or ID of the stack
        :param time_stamp_marker: last event time on the stack to start streaming events from.
        :return:
        """

        stack_change_in_progress = True
        events = set()
        retry_attempts = 0

        while stack_change_in_progress and retry_attempts <= self.max_attempts:
            try:

                # Only sleep if there have been no retry_attempts
                time.sleep(self.client_sleep if retry_attempts == 0 else 0)
                describe_stacks_resp = self._client.describe_stacks(StackName=stack_name)
                paginator = self._client.get_paginator("describe_stack_events")
                response_iterator = paginator.paginate(StackName=stack_name)
                stack_status = describe_stacks_resp["Stacks"][0]["StackStatus"]
                latest_time_stamp_marker = time_stamp_marker
                for event_items in response_iterator:
                    for event in event_items["StackEvents"]:
                        if event["EventId"] not in events and utc_to_timestamp(event["Timestamp"]) > time_stamp_marker:
                            events.add(event["EventId"])
                            latest_time_stamp_marker = max(
                                latest_time_stamp_marker, utc_to_timestamp(event["Timestamp"])
                            )
                            row_color = self.deploy_color.get_stack_events_status_color(status=event["ResourceStatus"])
                            pprint_columns(
                                columns=[
                                    event["ResourceStatus"],
                                    event["ResourceType"],
                                    event["LogicalResourceId"],
                                    event.get("ResourceStatusReason", "-"),
                                ],
                                width=kwargs["width"],
                                margin=kwargs["margin"],
                                format_string=DESCRIBE_STACK_EVENTS_FORMAT_STRING,
                                format_args=kwargs["format_args"],
                                columns_dict=DESCRIBE_STACK_EVENTS_DEFAULT_ARGS.copy(),
                                color=row_color,
                            )
                        # Skip already shown old event entries
                        elif utc_to_timestamp(event["Timestamp"]) <= time_stamp_marker:
                            time_stamp_marker = latest_time_stamp_marker
                            break
                    else:  # go to next loop if not break from inside loop
                        time_stamp_marker = latest_time_stamp_marker  # update marker if all events are new
                        continue
                    break  # reached here only if break from inner loop!

                if self._check_stack_complete(stack_status):
                    stack_change_in_progress = False
                    break
            except botocore.exceptions.ClientError as ex:
                retry_attempts = retry_attempts + 1
                if retry_attempts > self.max_attempts:
                    LOG.error("Describing stack events for %s failed: %s", stack_name, str(ex))
                    return
                # Sleep in exponential backoff mode
                time.sleep(math.pow(self.backoff, retry_attempts))

    def _check_stack_complete(self, status):
        return "COMPLETE" in status and "CLEANUP" not in status

    def wait_for_execute(self, stack_name, changeset_type):
        sys.stdout.write(
            "\n{} - Waiting for stack create/update "
            "to complete\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        sys.stdout.flush()

        self.describe_stack_events(stack_name, self.get_last_event_time(stack_name))

        # Pick the right waiter
        if changeset_type == "CREATE":
            waiter = self._client.get_waiter("stack_create_complete")
        elif changeset_type == "UPDATE":
            waiter = self._client.get_waiter("stack_update_complete")
        else:
            raise RuntimeError("Invalid changeset type {0}".format(changeset_type))

        # Poll every 30 seconds. Polling too frequently risks hitting rate limits
        # on CloudFormation's DescribeStacks API
        waiter_config = {"Delay": 30, "MaxAttempts": 120}

        try:
            waiter.wait(StackName=stack_name, WaiterConfig=waiter_config)
        except botocore.exceptions.WaiterError as ex:
            LOG.debug("Execute changeset waiter exception", exc_info=ex)

            raise deploy_exceptions.DeployFailedError(stack_name=stack_name, msg=str(ex))

        outputs = self.get_stack_outputs(stack_name=stack_name, echo=False)
        if outputs:
            self._display_stack_outputs(outputs)

    def create_and_wait_for_changeset(
        self, stack_name, cfn_template, parameter_values, capabilities, role_arn, notification_arns, s3_uploader, tags
    ):
        try:
            result, changeset_type = self.create_changeset(
                stack_name, cfn_template, parameter_values, capabilities, role_arn, notification_arns, s3_uploader, tags
            )
            self.wait_for_changeset(result["Id"], stack_name)
            self.describe_changeset(result["Id"], stack_name)
            return result, changeset_type
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
                    columns=["{k:<{0}}{v:<{0}}".format(MIN_OFFSET, k=k, v=v)],
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

    def get_stack_outputs(self, stack_name, echo=True):
        try:
            stacks_description = self._client.describe_stacks(StackName=stack_name)
            try:
                outputs = stacks_description["Stacks"][0]["Outputs"]
                if echo:
                    sys.stdout.write("\nStack {stack_name} outputs:\n".format(stack_name=stack_name))
                    sys.stdout.flush()
                    self._display_stack_outputs(stack_outputs=outputs)
                return outputs
            except KeyError:
                return None

        except botocore.exceptions.ClientError as ex:
            raise deploy_exceptions.DeployStackOutPutFailedError(stack_name=stack_name, msg=str(ex))
