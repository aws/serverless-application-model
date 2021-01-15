"""
Wrapper to generated colored messages for printing in Terminal
This was ported over from the sam-cli repo
"""

import click


class Colored:
    """
    Helper class to add ANSI colors and decorations to text. Given a string, ANSI colors are added with special prefix
    and suffix characters that are specially interpreted by Terminals to display colors.

        Ex: "message" -> add red color -> \x1b[31mmessage\x1b[0m

    This class serves two purposes:
        - Hide the underlying library used to provide colors: In this case, we use ``click`` library which is usually
            used to build a CLI interface. We use ``click`` just to minimize the number of dependencies we add to this
            project. This class allows us to replace click with any other color library like ``pygments`` without
            changing callers.

        - Transparently turn off colors: In cases when the string is not written to Terminal (ex: log file) the ANSI
            color codes should not be written. This class supports the scenario by allowing you to turn off colors.
            Calls to methods like `red()` will simply return the input string.
    """

    def __init__(self, colorize=True):
        """
        Initialize the object

        Parameters
        ----------
        colorize : bool
            Optional. Set this to True to turn on coloring. False will turn off coloring
        """
        self.colorize = colorize

    def red(self, msg):
        """Color the input red"""
        return self._color(msg, "red")

    def green(self, msg):
        """Color the input green"""
        return self._color(msg, "green")

    def cyan(self, msg):
        """Color the input cyan"""
        return self._color(msg, "cyan")

    def white(self, msg):
        """Color the input white"""
        return self._color(msg, "white")

    def yellow(self, msg):
        """Color the input yellow"""
        return self._color(msg, "yellow")

    def underline(self, msg):
        """Underline the input"""
        return click.style(msg, underline=True) if self.colorize else msg

    def _color(self, msg, color):
        """Internal helper method to add colors to input"""
        kwargs = {"fg": color}
        return click.style(msg, **kwargs) if self.colorize else msg


class DeployColor:
    def __init__(self):
        self._color = Colored()
        self.changeset_color_map = {"Add": "green", "Modify": "yellow", "Remove": "red"}
        self.status_color_map = {
            "CREATE_COMPLETE": "green",
            "CREATE_FAILED": "red",
            "CREATE_IN_PROGRESS": "yellow",
            "DELETE_COMPLETE": "green",
            "DELETE_FAILED": "red",
            "DELETE_IN_PROGRESS": "red",
            "REVIEW_IN_PROGRESS": "yellow",
            "ROLLBACK_COMPLETE": "red",
            "ROLLBACK_IN_PROGRESS": "red",
            "UPDATE_COMPLETE": "green",
            "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS": "yellow",
            "UPDATE_IN_PROGRESS": "yellow",
            "UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS": "red",
            "UPDATE_ROLLBACK_FAILED": "red",
            "UPDATE_ROLLBACK_IN_PROGRESS": "red",
        }

    def get_stack_events_status_color(self, status):
        return self.status_color_map.get(status, "yellow")

    def get_changeset_action_color(self, action):
        return self.changeset_color_map.get(action, "yellow")
