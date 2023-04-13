"""
Exceptions that are raised by sam deploy
This was ported over from the sam-cli repo
"""


class UserException(Exception):
    """
    Base class for all exceptions that need to be surfaced to the user. Typically, we will display the exception
    message to user and return the error code from CLI process
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ChangeEmptyError(UserException):
    def __init__(self, stack_name: str) -> None:
        message_fmt = "No changes to deploy. Stack {stack_name} is up to date"
        super().__init__(message=message_fmt.format(stack_name=stack_name))


class ChangeSetError(UserException):
    def __init__(self, stack_name, msg):
        self.stack_name = stack_name
        self.msg = msg
        message_fmt = "Failed to create changeset for the stack: {stack_name}, {msg}"
        super().__init__(message=message_fmt.format(stack_name=self.stack_name, msg=self.msg))


class DeployFailedError(UserException):
    def __init__(self, stack_name, msg):
        self.stack_name = stack_name
        self.msg = msg

        message_fmt = "Failed to create/update the stack: {stack_name}, {msg}"

        super().__init__(message=message_fmt.format(stack_name=self.stack_name, msg=msg))


class TerminationProtectionUpdateFailedError(UserException):
    def __init__(self, stack_name, msg):
        self.stack_name = stack_name
        self.msg = msg

        message_fmt = "Failed to update termination protection of the stack: {stack_name}, {msg}"

        super().__init__(message=message_fmt.format(stack_name=self.stack_name, msg=msg))


class DeployStackOutPutFailedError(UserException):
    def __init__(self, stack_name, msg):
        self.stack_name = stack_name
        self.msg = msg

        message_fmt = "Failed to get outputs from stack: {stack_name}, {msg}"

        super().__init__(message=message_fmt.format(stack_name=self.stack_name, msg=msg))


class DeployBucketInDifferentRegionError(UserException):
    def __init__(self, msg):
        self.msg = msg

        message_fmt = "{msg} : deployment s3 bucket is in a different region, try sam deploy --guided"

        super().__init__(message=message_fmt.format(msg=self.msg))


class ThrottlingError(UserException):
    def __init__(self, stack_name, msg):
        self.stack_name = stack_name
        self.msg = msg

        message_fmt = "Throttling issue occurred: {stack_name}, {msg}"

        super().__init__(message=message_fmt.format(stack_name=self.stack_name, msg=msg))


class S3DoesNotExistException(UserException):
    def __init__(self, bucket_name, msg):
        self.bucket_name = bucket_name
        self.msg = msg

        message_fmt = "Companion S3 bucket used for resource upload does not exist: {bucket_name}, {msg}"

        super().__init__(message=message_fmt.format(bucket_name=self.bucket_name, msg=msg))
