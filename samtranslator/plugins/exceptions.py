class InvalidPluginException(Exception):
    """Exception raised when the provided plugin configuration is not valid.

    Attributes:
        plugin_name -- name of the plugin that caused this error
        message -- explanation of the error
    """

    def __init__(self, plugin_name: str, message: str) -> None:
        self._plugin_name = plugin_name
        self._message = message

    @property
    def message(self) -> str:
        return f"The {self._plugin_name} plugin is invalid. {self._message}"
