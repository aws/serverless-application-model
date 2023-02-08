class GeneratedLogicalId:
    """
    Class to generate LogicalIDs for various scenarios.  SAM generates LogicalIds for new resources based on code
    that is spread across the translator codebase. It becomes to difficult to audit them and to standardize
    the process. This class will generate LogicalIds for various use cases.
    """

    @staticmethod
    def implicit_api() -> str:
        return "ServerlessRestApi"

    @staticmethod
    def implicit_http_api() -> str:
        return "ServerlessHttpApi"
