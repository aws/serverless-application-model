

class TemplateNotFoundException(Exception):
    """
    Exception raised when a template with given name is not found
    """
    def __init__(self, template_name):
        super(TemplateNotFoundException, self).__init__("Template with name '{}' is not found".format(template_name))


class InsufficientParameterValues(Exception):
    """
    Exception raised when not every parameter in the template is given a value.
    """
    def __init__(self, message):
        super(InsufficientParameterValues, self).__init__(message)


class InvalidParameterValues(Exception):
    """
    Exception raised when parameter values passed to this template is invalid
    """
    def __init__(self, message):
        super(InvalidParameterValues, self).__init__(message)
