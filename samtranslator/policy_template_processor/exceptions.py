class TemplateNotFoundException(Exception):
    """
    Exception raised when a template with given name is not found
    """

    def __init__(self, template_name):  # type: ignore[no-untyped-def]
        super(TemplateNotFoundException, self).__init__(f"Template with name '{template_name}' is not found")


class InsufficientParameterValues(Exception):
    """
    Exception raised when not every parameter in the template is given a value.
    """

    def __init__(self, message):  # type: ignore[no-untyped-def]
        super(InsufficientParameterValues, self).__init__(message)


class InvalidParameterValues(Exception):
    """
    Exception raised when parameter values passed to this template is invalid
    """

    def __init__(self, message):  # type: ignore[no-untyped-def]
        super(InvalidParameterValues, self).__init__(message)
