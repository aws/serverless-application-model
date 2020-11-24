"""
Exceptions that are raised by sam deploy
"""
import click


class UserException(click.ClickException):
    """
    Base class for all exceptions that need to be surfaced to the user. Typically, we will display the exception
    message to user and return the error code from CLI process
    """

    exit_code = 1

    def __init__(self, message, wrapped_from=None):
        self.wrapped_from = wrapped_from

        click.ClickException.__init__(self, message)


class ChangeEmptyError(UserException):
    def __init__(self, stack_name):
        self.stack_name = stack_name
        message_fmt = "No changes to deploy. Stack {stack_name} is up to date"
        super(ChangeEmptyError, self).__init__(message=message_fmt.format(stack_name=self.stack_name))


class ChangeSetError(UserException):
    def __init__(self, stack_name, msg):
        self.stack_name = stack_name
        self.msg = msg
        message_fmt = "Failed to create changeset for the stack: {stack_name}, {msg}"
        super(ChangeSetError, self).__init__(message=message_fmt.format(stack_name=self.stack_name, msg=self.msg))


class DeployFailedError(UserException):
    def __init__(self, stack_name, msg):
        self.stack_name = stack_name
        self.msg = msg

        message_fmt = "Failed to create/update the stack: {stack_name}, {msg}"

        super(DeployFailedError, self).__init__(message=message_fmt.format(stack_name=self.stack_name, msg=msg))


class GuidedDeployFailedError(UserException):
    def __init__(self, msg):
        self.msg = msg
        super(GuidedDeployFailedError, self).__init__(message=msg)


class DeployStackOutPutFailedError(UserException):
    def __init__(self, stack_name, msg):
        self.stack_name = stack_name
        self.msg = msg

        message_fmt = "Failed to get outputs from stack: {stack_name}, {msg}"

        super(DeployStackOutPutFailedError, self).__init__(
            message=message_fmt.format(stack_name=self.stack_name, msg=msg)
        )


class DeployBucketInDifferentRegionError(UserException):
    def __init__(self, msg):
        self.msg = msg

        message_fmt = "{msg} : deployment s3 bucket is in a different region, try sam deploy --guided"

        super(DeployBucketInDifferentRegionError, self).__init__(message=message_fmt.format(msg=self.msg))


class DeployBucketRequiredError(UserException):
    def __init__(self):

        message_fmt = (
            "Templates with a size greater than 51,200 bytes must be deployed "
            "via an S3 Bucket. Please add the --s3-bucket parameter to your "
            "command. The local template will be copied to that S3 bucket and "
            "then deployed."
        )

        super(DeployBucketRequiredError, self).__init__(message=message_fmt)


class DeployResolveS3AndS3SetError(UserException):
    def __init__(self):
        message_fmt = (
            "Cannot use both --resolve-s3 and --s3-bucket parameters in non-guided deployments."
            " Please use only one or use the --guided option for a guided deployment."
        )

        super(DeployResolveS3AndS3SetError, self).__init__(message=message_fmt)
