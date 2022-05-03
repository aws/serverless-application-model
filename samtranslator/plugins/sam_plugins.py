import logging
from samtranslator.model.exceptions import InvalidResourceException, InvalidDocumentException, InvalidTemplateException
from samtranslator.plugins import BasePlugin, LifeCycleEvents

LOG = logging.getLogger(__name__)


class SamPlugins(object):
    """
    Class providing support for arbitrary plugins that can extend core SAM translator in interesting ways.
    Use this class to register plugins that get called when certain life cycle events happen in the translator.
    Plugins work only on resources that are natively supported by SAM (ie. AWS::Serverless::* resources)

    Following Life Cycle Events are available:

    **Resource Level**
    - before_transform_resource: Invoked before SAM translator processes a resource's properties.
    - [Coming Soon] after_transform_resource

    **Template Level**
    - before_transform_template
    - after_transform_template

    When a life cycle event happens in the translator, this class will invoke the corresponding "hook" method on the
    each of the registered plugins to process. Plugins are free to modify internal state of the template or resources
    as they see fit. They can even raise an exception when the resource or template doesn't contain properties
    of certain structure (Ex: Only PolicyTemplates are allowed in SAM template)

    ## Plugin Implementation

    ### Defining a plugin
    A plugin is a subclass of `BasePlugin` that implements one or more methods capable of processing the life cycle
    events.
    These methods have a prefix `on_` followed by the name of the life cycle event. For example, to  handle
    `before_transform_resource` event, implement a method called `on_before_transform_resource`. We call these methods
    as "hooks" which are methods capable of handling this event.

    ### Hook Methods
    Arguments passed to the hook method is different for each life cycle event. Check out the hook methods in the
    `BasePlugin` class for detailed description of the method signature

    ### Raising validation errors
    Plugins must raise an `samtranslator.model.exception.InvalidResourceException` when the input SAM template does
    not conform to the expectation
    set by the plugin. SAM translator will convert this into a nice error message and display to the user.
    """

    def __init__(self, initial_plugins=None):
        """
        Initialize the plugins class with an optional list of plugins

        :param BasePlugin or list initial_plugins: Single plugin or a List of plugins to initialize with
        """
        self._plugins = []

        if initial_plugins is None:
            initial_plugins = []

        if not isinstance(initial_plugins, list):
            initial_plugins = [initial_plugins]

        for plugin in initial_plugins:
            self.register(plugin)

    def register(self, plugin):
        """
        Register a plugin. New plugins are added to the end of the plugins list.

        :param samtranslator.plugins.BasePlugin plugin: Instance/subclass of BasePlugin class that implements hooks
        :raises ValueError: If plugin is not an instance of samtranslator.plugins.BasePlugin or if it is already
            registered
        :return: None
        """

        if not plugin or not isinstance(plugin, BasePlugin):
            raise ValueError("Plugin must be implemented as a subclass of BasePlugin class")

        if self.is_registered(plugin.name):
            raise ValueError("Plugin with name {} is already registered".format(plugin.name))

        self._plugins.append(plugin)

    def is_registered(self, plugin_name):
        """
        Checks if a plugin with given name is already registered

        :param plugin_name: Name of the plugin
        :return: True if plugin with given name is already registered. False, otherwise
        """

        return plugin_name in [p.name for p in self._plugins]

    def _get(self, plugin_name):
        """
        Retrieves the plugin with given name

        :param plugin_name: Name of the plugin to retrieve
        :return samtranslator.plugins.BasePlugin: Returns the plugin object if found. None, otherwise
        """

        for p in self._plugins:
            if p.name == plugin_name:
                return p

        return None

    def act(self, event, *args, **kwargs):
        """
        Act on the specific life cycle event. The action here is to invoke the hook function on all registered plugins.
        *args and **kwargs will be passed directly to the plugin's hook functions

        :param samtranslator.plugins.LifeCycleEvents event: Event to act upon
        :return: Nothing
        :raises ValueError: If event is not a valid life cycle event
        :raises NameError: If a plugin does not have the hook method defined
        :raises Exception: Any exception that a plugin raises
        """

        if not isinstance(event, LifeCycleEvents):
            raise ValueError("'event' must be an instance of LifeCycleEvents class")

        method_name = "on_" + event.name

        for plugin in self._plugins:

            if not hasattr(plugin, method_name):
                raise NameError(
                    "'{}' method is not found in the plugin with name '{}'".format(method_name, plugin.name)
                )

            try:
                getattr(plugin, method_name)(*args, **kwargs)
            except (InvalidResourceException, InvalidDocumentException, InvalidTemplateException) as ex:
                # Don't need to log these because they don't result in crashes
                raise ex
            except Exception as ex:
                LOG.exception("Plugin '%s' raised an exception: %s", plugin.name, ex)
                raise ex

    def __len__(self):
        """
        Returns the number of plugins registered with this class

        :return integer: Number of plugins registered
        """
        return len(self._plugins)
