from enum import Enum
from samtranslator.plugins import SamPlugins, BasePlugin, LifeCycleEvents

from unittest import TestCase
from mock import Mock, patch, call


class TestSamPluginsRegistration(TestCase):
    def setUp(self):

        # Setup the plugin to be a "subclass" of the BasePlugin
        self.mock_plugin_name = "mock_plugin"
        self.mock_plugin = Mock(spec=BasePlugin)
        self.mock_plugin.name = self.mock_plugin_name

        self.sam_plugins = SamPlugins()

    def test_register_must_work(self):

        self.sam_plugins.register(self.mock_plugin)

        self.assertEqual(self.mock_plugin, self.sam_plugins._get(self.mock_plugin_name))

    def test_register_must_raise_on_duplicate_plugin(self):

        self.sam_plugins.register(self.mock_plugin)

        with self.assertRaises(ValueError):
            self.sam_plugins.register(self.mock_plugin)

    def test_register_must_raise_on_invalid_plugin_type(self):

        # Plugin which is not an instance of BaseClass
        bad_plugin = Mock()
        bad_plugin.name = "some name"

        with self.assertRaises(ValueError):
            self.sam_plugins.register(bad_plugin)

    def test_register_must_append_plugins_to_end(self):

        plugin1 = _make_mock_plugin("plugin1")
        plugin2 = _make_mock_plugin("plugin2")
        plugin3 = _make_mock_plugin("plugin3")

        self.sam_plugins.register(plugin1)
        self.sam_plugins.register(plugin2)
        self.sam_plugins.register(plugin3)

        expected = [plugin1, plugin2, plugin3]

        self.assertEqual(expected, self.sam_plugins._plugins)

    def test_must_register_plugins_list_on_initialization(self):

        plugin1 = _make_mock_plugin("plugin1")
        plugin2 = _make_mock_plugin("plugin2")

        plugins_list = [plugin1, plugin2]

        new_sam_plugin = SamPlugins(plugins_list)

        # Also make sure the plugins are in the same order as in input
        self.assertEqual(plugins_list, new_sam_plugin._plugins)

    def test_must_register_single_plugin_on_initialization(self):
        new_sam_plugin = SamPlugins(self.mock_plugin)

        self.assertTrue(new_sam_plugin.is_registered(self.mock_plugin_name))

    def test_len_must_get_num_registered_plugins(self):
        plugin1 = _make_mock_plugin("plugin1")
        plugin2 = _make_mock_plugin("plugin2")

        self.sam_plugins.register(plugin1)
        self.sam_plugins.register(plugin2)

        self.assertEqual(2, len(self.sam_plugins))

    def test_is_registered_must_find_registered_plugins(self):
        self.sam_plugins.register(self.mock_plugin)

        self.assertTrue(self.sam_plugins.is_registered(self.mock_plugin_name))

    def test_is_registered_must_return_false_when_no_plugins_registered(self):

        # No Plugins are registered
        self.assertFalse(self.sam_plugins.is_registered(self.mock_plugin_name))

    def test_is_registered_must_return_false_for_non_existent_plugins(self):
        # Register a plugin but check with some random name
        self.sam_plugins.register(self.mock_plugin)
        self.assertFalse(self.sam_plugins.is_registered("some plugin name"))

    def test_get_must_return_a_registered_plugin(self):

        plugin1 = _make_mock_plugin("plugin1")
        plugin2 = _make_mock_plugin("plugin2")

        self.sam_plugins.register(plugin1)
        self.sam_plugins.register(plugin2)

        self.assertEqual(plugin1, self.sam_plugins._get(plugin1.name))
        self.assertEqual(plugin2, self.sam_plugins._get(plugin2.name))

    def test_get_must_handle_no_registered_plugins(self):

        # NO plugins registered
        self.assertIsNone(self.sam_plugins._get("some plugin"))

    def test_get_must_handle_non_registered_plugins(self):
        # Register one plugin, but try to retrieve some other non-existent plugin
        self.sam_plugins.register(self.mock_plugin)
        self.assertIsNone(self.sam_plugins._get("some plugin"))


class TestSamPluginsAct(TestCase):
    def setUp(self):
        self.sam_plugins = SamPlugins()

        # Create a mock of LifeCycleEvents object with ONE event called "my_event"
        self.mock_lifecycle_events = Mock(spec=LifeCycleEvents)
        self.my_event = Mock(spec=LifeCycleEvents)
        self.my_event.name = "my_event"
        self.my_event.value = "my_event"
        self.mock_lifecycle_events.my_event = self.my_event

    def test_act_must_invoke_correct_hook_method(self):

        # Setup the plugin to return a mock when the "on_" method is invoked
        plugin = _make_mock_plugin("plugin")
        hook_method = Mock()
        setattr(plugin, "on_" + self.my_event.name, hook_method)

        self.sam_plugins.register(plugin)

        # Call the act method with some arguments and verify that the hook was invoked with correct arguments
        arg1 = "foo"
        arg2 = "bar"
        kwargs1 = "kwargs1"
        kwargs2 = "kwargs2"
        self.sam_plugins.act(self.my_event, arg1, arg2, kwargs1=kwargs1, kwargs2=kwargs2)

        hook_method.assert_called_once_with(arg1, arg2, kwargs1=kwargs1, kwargs2=kwargs2)

    def test_act_must_invoke_hook_on_all_plugins(self):

        # Create three plugins, and setup hook methods on it
        plugin1 = _make_mock_plugin("plugin1")
        setattr(plugin1, "on_" + self.my_event.name, Mock())
        plugin2 = _make_mock_plugin("plugin2")
        setattr(plugin2, "on_" + self.my_event.name, Mock())
        plugin3 = _make_mock_plugin("plugin3")
        setattr(plugin3, "on_" + self.my_event.name, Mock())

        self.sam_plugins.register(plugin1)
        self.sam_plugins.register(plugin2)
        self.sam_plugins.register(plugin3)

        # Call the act method with some arguments and verify that the hook was invoked with correct arguments
        arg1 = "foo"
        arg2 = "bar"
        kwargs1 = "kwargs1"
        kwargs2 = "kwargs2"
        self.sam_plugins.act(self.my_event, arg1, arg2, kwargs1=kwargs1, kwargs2=kwargs2)

        plugin1.on_my_event.assert_called_once_with(arg1, arg2, kwargs1=kwargs1, kwargs2=kwargs2)
        plugin2.on_my_event.assert_called_once_with(arg1, arg2, kwargs1=kwargs1, kwargs2=kwargs2)
        plugin3.on_my_event.assert_called_once_with(arg1, arg2, kwargs1=kwargs1, kwargs2=kwargs2)

    def test_act_must_invoke_plugins_in_sequence(self):

        # Create three plugins, and setup hook methods on it
        plugin1 = _make_mock_plugin("plugin1")
        setattr(plugin1, "on_" + self.my_event.name, Mock())
        plugin2 = _make_mock_plugin("plugin2")
        setattr(plugin2, "on_" + self.my_event.name, Mock())
        plugin3 = _make_mock_plugin("plugin3")
        setattr(plugin3, "on_" + self.my_event.name, Mock())

        # Create a parent mock and attach child mocks to help assert order of the calls
        # https://stackoverflow.com/questions/32463321/how-to-assert-method-call-order-with-python-mock
        parent_mock = Mock()
        parent_mock.attach_mock(plugin1.on_my_event, "plugin1_hook")
        parent_mock.attach_mock(plugin2.on_my_event, "plugin2_hook")
        parent_mock.attach_mock(plugin3.on_my_event, "plugin3_hook")

        self.sam_plugins.register(plugin1)
        self.sam_plugins.register(plugin2)
        self.sam_plugins.register(plugin3)

        # Call the act method
        self.sam_plugins.act(self.my_event)

        # Verify calls were made in the specific sequence
        parent_mock.assert_has_calls([call.plugin1_hook(), call.plugin2_hook(), call.plugin3_hook()])

    def test_act_must_skip_if_no_plugins_are_registered(self):

        # Create three plugins, and setup hook methods on it
        plugin1 = _make_mock_plugin("plugin1")
        setattr(plugin1, "on_" + self.my_event.name, Mock())

        # Don't register any plugin

        # Call the act method
        self.sam_plugins.act(self.my_event)

        plugin1.on_my_event.assert_not_called()

    def test_act_must_fail_on_invalid_event_type_string(self):

        with self.assertRaises(ValueError):
            self.sam_plugins.act("some event")

    def test_act_must_fail_on_invalid_event_type_object(self):

        with self.assertRaises(ValueError):
            self.sam_plugins.act(Mock())

    def test_act_must_fail_on_invalid_event_type_enum(self):
        class SomeEnum(Enum):
            A = 1

        with self.assertRaises(ValueError):
            self.sam_plugins.act(SomeEnum.A)

    def test_act_must_fail_on_non_existent_hook_method(self):

        # Create a plugin but setup hook method with wrong name
        plugin1 = _make_mock_plugin("plugin1")
        setattr(plugin1, "on_unknown_event", Mock())
        self.sam_plugins.register(plugin1)

        with self.assertRaises(NameError):
            self.sam_plugins.act(self.my_event)

        plugin1.on_unknown_event.assert_not_called()

    def test_act_must_raise_exceptions_raised_by_plugins(self):

        # Create a plugin but setup hook method with wrong name
        plugin1 = _make_mock_plugin("plugin1")
        setattr(plugin1, "on_" + self.my_event.name, Mock())
        self.sam_plugins.register(plugin1)

        # Setup the hook to raise exception
        plugin1.on_my_event.side_effect = IOError

        with self.assertRaises(IOError):
            self.sam_plugins.act(self.my_event)

        plugin1.on_my_event.assert_called_once_with()

    def test_act_must_abort_hooks_after_exception(self):
        # ie. after a hook raises an exception, subsequent hooks must NOT be run

        # Create three plugins, and setup hook methods on it
        plugin1 = _make_mock_plugin("plugin1")
        setattr(plugin1, "on_" + self.my_event.name, Mock())
        plugin2 = _make_mock_plugin("plugin2")
        setattr(plugin2, "on_" + self.my_event.name, Mock())
        plugin3 = _make_mock_plugin("plugin3")
        setattr(plugin3, "on_" + self.my_event.name, Mock())

        # Create a parent mock and attach child mocks to help assert order of the calls
        # https://stackoverflow.com/questions/32463321/how-to-assert-method-call-order-with-python-mock
        parent_mock = Mock()
        parent_mock.attach_mock(plugin1.on_my_event, "plugin1_hook")
        parent_mock.attach_mock(plugin2.on_my_event, "plugin2_hook")
        parent_mock.attach_mock(plugin3.on_my_event, "plugin3_hook")

        self.sam_plugins.register(plugin1)
        self.sam_plugins.register(plugin2)
        self.sam_plugins.register(plugin3)

        # setup plugin2 to raise exception
        plugin2.on_my_event.side_effect = IOError

        # Call the act method
        with self.assertRaises(IOError):
            self.sam_plugins.act(self.my_event)

        # Since Plugin2 raised the exception, plugin3's hook must NEVER be called
        parent_mock.assert_has_calls([call.plugin1_hook(), call.plugin2_hook()])


class TestBasePlugin(TestCase):
    def test_initialization_should_set_name(self):

        name = "some name"
        plugin = BasePlugin(name)
        self.assertEqual(name, plugin.name)

    def test_initialization_without_name_must_raise_exception(self):

        with self.assertRaises(ValueError):
            BasePlugin(None)

    def test_on_methods_must_not_do_anything(self):
        data_mock = Mock()

        # Simple test to verify that all methods starting with "on_" prefix must not implement any functionality
        plugin = BasePlugin("name")

        # Add every on_ method here
        plugin.on_before_transform_resource(data_mock, data_mock, data_mock)

        # `method_calls` tracks calls to the mock, its methods, attributes, and *their* methods & attributes
        self.assertEqual([], data_mock.method_calls)


def _make_mock_plugin(name):
    m = Mock(spec=BasePlugin)
    m.name = name
    return m
