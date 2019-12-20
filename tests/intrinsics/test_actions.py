from unittest import TestCase
from mock import patch, Mock
from samtranslator.intrinsics.actions import Action, RefAction, SubAction, GetAttAction, FindInMapAction
from samtranslator.intrinsics.resource_refs import SupportedResourceReferences
from samtranslator.model.exceptions import InvalidTemplateException, InvalidDocumentException


class TestAction(TestCase):
    def test_subclass_must_override_type(self):

        # Subclass must override the intrinsic_name
        class MyAction(Action):
            pass

        with self.assertRaises(TypeError):
            MyAction()

    def test_subclass_must_implement_resolve_method(self):
        class MyAction(Action):
            intrinsic_name = "foo"

        with self.assertRaises(NotImplementedError):
            MyAction().resolve_parameter_refs({}, {})

        with self.assertRaises(NotImplementedError):
            MyAction().resolve_resource_refs({}, {})

        with self.assertRaises(NotImplementedError):
            MyAction().resolve_resource_id_refs({}, {})

    def test_can_handle_input(self):
        class MyAction(Action):
            intrinsic_name = "foo"

        input = {"foo": ["something"]}

        action = MyAction()
        self.assertTrue(action.can_handle(input))

    def test_can_handle_invalid_type(self):
        class MyAction(Action):
            intrinsic_name = "foo"

        input = {"bar": "something"}
        action = MyAction()
        self.assertFalse(action.can_handle(input))

    def test_can_handle_invalid_input(self):
        class MyAction(Action):
            intrinsic_name = "foo"

        input = "string input"
        action = MyAction()
        self.assertFalse(action.can_handle(input))

    def test_can_handle_invalid_dict(self):
        class MyAction(Action):
            intrinsic_name = "foo"

        # Intrinsic functions can be only in dict of length 1
        input = {"foo": "some value", "bar": "some other value"}
        action = MyAction()
        self.assertFalse(action.can_handle(input))

    def test_can_handle_empty_input(self):
        class MyAction(Action):
            intrinsic_name = "foo"

        # Intrinsic functions can be only in dict of length 1
        input = None
        action = MyAction()
        self.assertFalse(action.can_handle(input))

    def test_parse_resource_references_with_one_property(self):
        input = "LogicalId.Property"
        expected = ("LogicalId", "Property")

        self.assertEqual(expected, Action._parse_resource_reference(input))

    def test_parse_resource_references_with_multiple_properties(self):
        input = "LogicalId.Property1.Property2.Property3"
        expected = ("LogicalId", "Property1.Property2.Property3")

        self.assertEqual(expected, Action._parse_resource_reference(input))

    def test_parse_resource_references_with_other_special_characters(self):
        input = "some logical id . some value"
        expected = ("some logical id ", " some value")

        self.assertEqual(expected, Action._parse_resource_reference(input))

    def test_parse_resource_references_with_empty_property(self):
        # Just a dot at the end! This is equivalent of no property
        input = "LogicalId."
        expected = (None, None)

        self.assertEqual(expected, Action._parse_resource_reference(input))

    def test_parse_resource_references_with_empty_logical_id(self):
        # Just a dot at the beginning! This is equivalent of no LogicalId
        input = ".Property"
        expected = (None, None)

        self.assertEqual(expected, Action._parse_resource_reference(input))

    def test_parse_resource_references_with_no_property(self):
        input = "LogicalId"
        expected = (None, None)

        self.assertEqual(expected, Action._parse_resource_reference(input))

    def test_parse_resource_references_not_string(self):
        input = {"not a": "string"}
        expected = (None, None)

        self.assertEqual(expected, Action._parse_resource_reference(input))


class TestRefCanResolveParameterRefs(TestCase):
    def test_can_resolve_ref(self):
        parameters = {"key": "value"}
        input = {"Ref": "key"}

        ref = RefAction()
        self.assertEqual(parameters["key"], ref.resolve_parameter_refs(input, parameters))

    def test_unknown_ref(self):
        parameters = {"key": "value"}
        input = {"Ref": "someotherkey"}
        expected = {"Ref": "someotherkey"}

        ref = RefAction()
        self.assertEqual(expected, ref.resolve_parameter_refs(input, parameters))

    def test_must_ignore_invalid_value(self):
        parameters = {"key": "value"}
        input = {"Ref": ["invalid value"]}
        expected = {"Ref": ["invalid value"]}

        ref = RefAction()
        self.assertEqual(expected, ref.resolve_parameter_refs(input, parameters))

    @patch.object(RefAction, "can_handle")
    def test_return_value_if_cannot_handle(self, can_handle_mock):
        parameters = {"key": "value"}
        input = {"Ref": "key"}
        expected = {"Ref": "key"}

        ref = RefAction()
        can_handle_mock.return_value = False  # Simulate failure to handle the input. Result should be same as input
        self.assertEqual(expected, ref.resolve_parameter_refs(input, parameters))


class TestRefCanResolveResourceRefs(TestCase):
    def setUp(self):
        self.supported_resource_refs_mock = Mock()
        self.ref = RefAction()

    @patch.object(RefAction, "_parse_resource_reference")
    def test_must_replace_refs(self, _parse_resource_reference_mock):
        resolved_value = "SomeOtherValue"
        input = {"Ref": "LogicalId.Property"}
        expected = {"Ref": resolved_value}
        _parse_resource_reference_mock.return_value = ("LogicalId", "Property")
        self.supported_resource_refs_mock.get.return_value = resolved_value

        output = self.ref.resolve_resource_refs(input, self.supported_resource_refs_mock)

        self.assertEqual(expected, output)
        self.supported_resource_refs_mock.get.assert_called_once_with("LogicalId", "Property")
        _parse_resource_reference_mock.assert_called_once_with("LogicalId.Property")

    @patch.object(RefAction, "_parse_resource_reference")
    def test_handle_unsupported_references(self, _parse_resource_reference_mock):
        input = {"Ref": "LogicalId.Property"}
        expected = {"Ref": "LogicalId.Property"}

        _parse_resource_reference_mock.return_value = ("LogicalId", "Property")
        self.supported_resource_refs_mock.get.return_value = None

        output = self.ref.resolve_resource_refs(input, self.supported_resource_refs_mock)
        self.assertEqual(expected, output)
        self.supported_resource_refs_mock.get.assert_called_once_with("LogicalId", "Property")
        _parse_resource_reference_mock.assert_called_once_with("LogicalId.Property")

    @patch.object(RefAction, "_parse_resource_reference")
    def test_handle_unparsable_reference_value(self, _parse_resource_reference_mock):
        input = {"Ref": "some value"}
        expected = {"Ref": "some value"}

        _parse_resource_reference_mock.return_value = (None, None)

        output = self.ref.resolve_resource_refs(input, self.supported_resource_refs_mock)

        self.assertEqual(expected, output)
        self.supported_resource_refs_mock.get.assert_not_called()
        _parse_resource_reference_mock.assert_called_once_with("some value")

    @patch.object(RefAction, "can_handle")
    def test_return_value_if_cannot_handle(self, can_handle_mock):
        input = {"Ref": "key"}
        expected = {"Ref": "key"}

        ref = RefAction()
        can_handle_mock.return_value = False  # Simulate failure to handle the input. Result should be same as input
        self.assertEqual(expected, ref.resolve_resource_refs(input, self.supported_resource_refs_mock))


class TestRefCanResolveResourceIdRefs(TestCase):
    def setUp(self):
        self.supported_resource_id_refs_mock = Mock()
        self.ref = RefAction()

    def test_must_replace_refs(self):
        resolved_value = "NewLogicalId"
        input = {"Ref": "LogicalId"}
        expected = {"Ref": resolved_value}
        self.supported_resource_id_refs_mock.get.return_value = resolved_value

        output = self.ref.resolve_resource_id_refs(input, self.supported_resource_id_refs_mock)

        self.assertEqual(expected, output)
        self.supported_resource_id_refs_mock.get.assert_called_once_with("LogicalId")

    def test_handle_unsupported_references(self):
        input = {"Ref": "OtherLogicalId.Property"}
        expected = {"Ref": "OtherLogicalId.Property"}

        self.supported_resource_id_refs_mock.get.return_value = None

        output = self.ref.resolve_resource_id_refs(input, self.supported_resource_id_refs_mock)
        self.assertEqual(expected, output)
        self.supported_resource_id_refs_mock.get.assert_not_called()

    @patch.object(RefAction, "can_handle")
    def test_return_value_if_cannot_handle(self, can_handle_mock):
        input = {"Ref": "key"}
        expected = {"Ref": "key"}

        ref = RefAction()
        can_handle_mock.return_value = False  # Simulate failure to handle the input. Result should be same as input
        self.assertEqual(expected, ref.resolve_resource_id_refs(input, self.supported_resource_id_refs_mock))


class TestSubCanResolveParameterRefs(TestCase):
    def test_must_resolve_string_value(self):
        parameters = {"key1": "value1"}
        input = {"Fn::Sub": "Hello ${key1}"}
        expected = {"Fn::Sub": "Hello value1"}

        sub = SubAction()
        result = sub.resolve_parameter_refs(input, parameters)

        self.assertEqual(expected, result)

    def test_must_resolve_array_value(self):
        parameters = {"key1": "value1"}
        input = {"Fn::Sub": ["Hello ${key1} ${a}", {"a": "b"}]}

        expected = {"Fn::Sub": ["Hello value1 ${a}", {"a": "b"}]}

        sub = SubAction()
        result = sub.resolve_parameter_refs(input, parameters)

        self.assertEqual(expected, result)

    @patch.object(SubAction, "can_handle")
    def test_return_value_if_cannot_handle(self, can_handle_mock):
        parameters = {"key": "value"}
        input = {"Fn::Sub": "${key}"}
        expected = {"Fn::Sub": "${key}"}

        sub = SubAction()
        can_handle_mock.return_value = False  # Simulate failure to handle the input. Result should be same as input
        self.assertEqual(expected, sub.resolve_parameter_refs(input, parameters))

    def test_sub_all_refs_multiple_references(self):
        parameters = {"key1": "value1", "key2": "value2"}
        input = {"Fn::Sub": "hello ${key1} ${key2} ${key1}${key2} ${unknown} ${key1.attr}"}
        expected = {"Fn::Sub": "hello value1 value2 value1value2 ${unknown} ${key1.attr}"}

        sub = SubAction()
        result = sub.resolve_parameter_refs(input, parameters)

        self.assertEqual(expected, result)

    def test_sub_all_refs_with_literals(self):
        parameters = {"key1": "value1", "key2": "value2"}
        input = {"Fn::Sub": "hello ${key1} ${key2} ${!key1} ${!key2}"}
        expected = {
            # ${! is the prefix for literal. These won't be substituted
            "Fn::Sub": "hello value1 value2 ${!key1} ${!key2}"
        }

        sub = SubAction()
        result = sub.resolve_parameter_refs(input, parameters)

        self.assertEqual(expected, result)

    def test_sub_all_refs_with_list_input(self):
        parameters = {"key1": "value1", "key2": "value2"}
        input = {"Fn::Sub": ["key1", "key2"]}
        expected = {"Fn::Sub": ["key1", "key2"]}

        sub = SubAction()
        result = sub.resolve_parameter_refs(input, parameters)

        self.assertEqual(expected, result)

    def test_sub_all_refs_with_dict_input(self):
        parameters = {"key1": "value1", "key2": "value2"}
        input = {"Fn::Sub": {"a": "key1", "b": "key2"}}
        expected = {"Fn::Sub": {"a": "key1", "b": "key2"}}

        sub = SubAction()
        result = sub.resolve_parameter_refs(input, parameters)

        self.assertEqual(expected, result)

    def test_sub_all_refs_with_pseudo_parameters(self):
        parameters = {"key1": "value1", "AWS::Region": "ap-southeast-1"}
        input = {"Fn::Sub": "hello ${AWS::Region} ${key1}"}
        expected = {"Fn::Sub": "hello ap-southeast-1 value1"}

        sub = SubAction()
        result = sub.resolve_parameter_refs(input, parameters)

        self.assertEqual(expected, result)


class TestSubInternalMethods(TestCase):
    @patch.object(SubAction, "_sub_all_refs")
    def test_handle_sub_value_must_call_handler_on_string(self, sub_all_refs_mock):
        input = "sub string"
        expected = "result"
        handler_mock = Mock()
        sub_all_refs_mock.return_value = expected

        sub = SubAction()
        result = sub._handle_sub_value(input, handler_mock)

        self.assertEqual(expected, result)
        sub_all_refs_mock.assert_called_once_with(input, handler_mock)

    @patch.object(SubAction, "_sub_all_refs")
    def test_handle_sub_value_must_call_handler_on_array(self, sub_all_refs_mock):
        input = ["sub string", {"a": "b"}]
        expected = ["sub string", {"a": "b"}]
        handler_mock = Mock()
        sub_all_refs_mock.return_value = expected[0]

        sub = SubAction()
        result = sub._handle_sub_value(input, handler_mock)

        self.assertEqual(expected, result)
        sub_all_refs_mock.assert_called_once_with(input[0], handler_mock)

    @patch.object(SubAction, "_sub_all_refs")
    def test_handle_sub_value_must_skip_no_string(self, sub_all_refs_mock):
        input = [{"a": "b"}]
        expected = [{"a": "b"}]
        handler_mock = Mock()

        sub = SubAction()
        result = sub._handle_sub_value(input, handler_mock)

        self.assertEqual(expected, result)
        handler_mock.assert_not_called()
        sub_all_refs_mock.assert_not_called()

    @patch.object(SubAction, "_sub_all_refs")
    def test_must_skip_invalid_input_empty_list(self, sub_all_refs_mock):
        input = []
        expected = []
        handler_mock = Mock()

        sub = SubAction()
        result = sub._handle_sub_value(input, handler_mock)

        self.assertEqual(expected, result)
        handler_mock.assert_not_called()
        sub_all_refs_mock.assert_not_called()

    @patch.object(SubAction, "_sub_all_refs")
    def test_must_skip_invalid_input_dict(self, sub_all_refs_mock):
        input = {"a": "b"}
        expected = {"a": "b"}
        handler_mock = Mock()

        sub = SubAction()
        result = sub._handle_sub_value(input, handler_mock)

        self.assertEqual(expected, result)
        handler_mock.assert_not_called()
        sub_all_refs_mock.assert_not_called()


class TestSubCanResolveResourceRefs(TestCase):
    def setUp(self):
        self.supported_resource_refs = SupportedResourceReferences()
        self.supported_resource_refs.add("id1", "prop1", "value1")
        self.supported_resource_refs.add("id1", "prop2", "value2")
        self.supported_resource_refs.add("id2", "prop3", "value3")

        self.input_sub_value = "Hello ${id1.prop1} ${id1.prop2}${id2.prop3} ${id1.prop1.arn} ${id1.prop2.arn.name.foo} ${!id1.prop1} ${unknown} ${some.arn} World"
        self.expected_output_sub_value = "Hello ${value1} ${value2}${value3} ${value1.arn} ${value2.arn.name.foo} ${!id1.prop1} ${unknown} ${some.arn} World"

    def test_must_resolve_string_value(self):

        input = {"Fn::Sub": self.input_sub_value}
        expected = {"Fn::Sub": self.expected_output_sub_value}

        sub = SubAction()
        result = sub.resolve_resource_refs(input, self.supported_resource_refs)

        self.assertEqual(expected, result)

    def test_must_resolve_array_value(self):
        input = {"Fn::Sub": [self.input_sub_value, {"unknown": "a"}]}

        expected = {"Fn::Sub": [self.expected_output_sub_value, {"unknown": "a"}]}

        sub = SubAction()
        result = sub.resolve_resource_refs(input, self.supported_resource_refs)

        self.assertEqual(expected, result)

    def test_sub_all_refs_with_list_input(self):
        parameters = {"key1": "value1", "key2": "value2"}
        input = {"Fn::Sub": ["key1", "key2"]}
        expected = {"Fn::Sub": ["key1", "key2"]}

        sub = SubAction()
        result = sub.resolve_resource_refs(input, parameters)

        self.assertEqual(expected, result)

    def test_sub_all_refs_with_dict_input(self):
        parameters = {"key1": "value1", "key2": "value2"}
        input = {"Fn::Sub": {"a": "key1", "b": "key2"}}
        expected = {"Fn::Sub": {"a": "key1", "b": "key2"}}

        sub = SubAction()
        result = sub.resolve_resource_refs(input, parameters)

        self.assertEqual(expected, result)

    @patch.object(SubAction, "can_handle")
    def test_return_value_if_cannot_handle(self, can_handle_mock):
        parameters = {"key": "value"}
        input = {"Fn::Sub": "${key}"}
        expected = {"Fn::Sub": "${key}"}

        sub = SubAction()
        can_handle_mock.return_value = False  # Simulate failure to handle the input. Result should be same as input
        self.assertEqual(expected, sub.resolve_resource_refs(input, parameters))


class TestSubCanResolveResourceIdRefs(TestCase):
    def setUp(self):
        self.supported_resource_id_refs = {}
        self.supported_resource_id_refs["id1"] = "newid1"
        self.supported_resource_id_refs["id2"] = "newid2"
        self.supported_resource_id_refs["id3"] = "newid3"

        self.input_sub_value = (
            "Hello ${id1} ${id2}${id3} ${id1.arn} ${id2.arn.name.foo} ${!id1.prop1} ${unknown} ${some.arn} World"
        )
        self.expected_output_sub_value = "Hello ${newid1} ${newid2}${newid3} ${newid1.arn} ${newid2.arn.name.foo} ${!id1.prop1} ${unknown} ${some.arn} World"

    def test_must_resolve_string_value(self):

        input = {"Fn::Sub": self.input_sub_value}
        expected = {"Fn::Sub": self.expected_output_sub_value}

        sub = SubAction()
        result = sub.resolve_resource_id_refs(input, self.supported_resource_id_refs)

        self.assertEqual(expected, result)

    def test_must_resolve_array_value(self):
        input = {"Fn::Sub": [self.input_sub_value, {"unknown": "a"}]}

        expected = {"Fn::Sub": [self.expected_output_sub_value, {"unknown": "a"}]}

        sub = SubAction()
        result = sub.resolve_resource_id_refs(input, self.supported_resource_id_refs)

        self.assertEqual(expected, result)

    def test_sub_all_refs_with_list_input(self):
        parameters = {"key1": "value1", "key2": "value2"}
        input = {"Fn::Sub": ["key1", "key2"]}
        expected = {"Fn::Sub": ["key1", "key2"]}

        sub = SubAction()
        result = sub.resolve_resource_id_refs(input, parameters)

        self.assertEqual(expected, result)

    def test_sub_all_refs_with_dict_input(self):
        parameters = {"key1": "value1", "key2": "value2"}
        input = {"Fn::Sub": {"a": "key1", "b": "key2"}}
        expected = {"Fn::Sub": {"a": "key1", "b": "key2"}}

        sub = SubAction()
        result = sub.resolve_resource_id_refs(input, parameters)

        self.assertEqual(expected, result)

    @patch.object(SubAction, "can_handle")
    def test_return_value_if_cannot_handle(self, can_handle_mock):
        parameters = {"key": "value"}
        input = {"Fn::Sub": "${key}"}
        expected = {"Fn::Sub": "${key}"}

        sub = SubAction()
        can_handle_mock.return_value = False  # Simulate failure to handle the input. Result should be same as input
        self.assertEqual(expected, sub.resolve_resource_id_refs(input, parameters))


class TestGetAttCanResolveParameterRefs(TestCase):
    def test_must_do_nothing(self):
        # Parameter references are not resolved by GetAtt
        input = "foo"
        expected = "foo"
        supported_resource_refs = Mock()
        self.assertEqual(expected, GetAttAction().resolve_parameter_refs(input, supported_resource_refs))

        supported_resource_refs.assert_not_called()


class TestGetAttCanResolveResourceRefs(TestCase):
    def setUp(self):
        self.supported_resource_refs = SupportedResourceReferences()
        self.supported_resource_refs.add("id1", "prop1", "value1")

    def test_must_resolve_simple_refs(self):
        input = {"Fn::GetAtt": ["id1.prop1", "Arn"]}

        expected = {"Fn::GetAtt": ["value1", "Arn"]}

        getatt = GetAttAction()
        output = getatt.resolve_resource_refs(input, self.supported_resource_refs)

        self.assertEqual(expected, output)

    def test_must_resolve_refs_with_many_attributes(self):
        input = {"Fn::GetAtt": ["id1.prop1", "Arn1", "Arn2", "Arn3"]}

        expected = {"Fn::GetAtt": ["value1", "Arn1", "Arn2", "Arn3"]}

        getatt = GetAttAction()
        output = getatt.resolve_resource_refs(input, self.supported_resource_refs)

        self.assertEqual(expected, output)

    def test_must_resolve_with_splitted_resource_refs(self):
        input = {
            # Reference to resource `id1.prop1` is split into different elements
            "Fn::GetAtt": ["id1", "prop1", "Arn1", "Arn2", "Arn3"]
        }

        expected = {"Fn::GetAtt": ["value1", "Arn1", "Arn2", "Arn3"]}

        getatt = GetAttAction()
        output = getatt.resolve_resource_refs(input, self.supported_resource_refs)

        self.assertEqual(expected, output)

    def test_must_ignore_refs_without_attributes(self):
        input = {
            # No actual attributes. But since we have two entries in the array, we try to resolve them
            "Fn::GetAtt": ["id1", "prop1"]
        }

        expected = {"Fn::GetAtt": ["value1"]}

        getatt = GetAttAction()
        output = getatt.resolve_resource_refs(input, self.supported_resource_refs)

        self.assertEqual(expected, output)

    def test_must_ignore_refs_without_attributes_in_concatenated_form(self):
        input = {
            # No actual attributes. with just only one entry in array, the value never gets resolved
            "Fn::GetAtt": ["id1.prop1"]
        }

        expected = {"Fn::GetAtt": ["id1.prop1"]}

        getatt = GetAttAction()
        output = getatt.resolve_resource_refs(input, self.supported_resource_refs)

        self.assertEqual(expected, output)

    def test_must_ignore_invalid_value_array(self):
        input = {
            # No actual attributes
            "Fn::GetAtt": ["id1"]
        }

        expected = {"Fn::GetAtt": ["id1"]}

        getatt = GetAttAction()
        output = getatt.resolve_resource_refs(input, self.supported_resource_refs)

        self.assertEqual(expected, output)

    def test_must_ignore_invalid_value_type(self):
        input = {
            # No actual attributes
            "Fn::GetAtt": {"a": "b"}
        }

        expected = {"Fn::GetAtt": {"a": "b"}}

        getatt = GetAttAction()
        output = getatt.resolve_resource_refs(input, self.supported_resource_refs)

        self.assertEqual(expected, output)

    def test_must_ignore_missing_properties_with_dot_after(self):
        input = {"Fn::GetAtt": ["id1.", "foo"]}
        expected = {"Fn::GetAtt": ["id1.", "foo"]}

        getatt = GetAttAction()
        output = getatt.resolve_resource_refs(input, self.supported_resource_refs)

        self.assertEqual(expected, output)

    def test_must_ignore_missing_properties_with_dot_before(self):
        input = {"Fn::GetAtt": [".id1", "foo"]}
        expected = {"Fn::GetAtt": [".id1", "foo"]}

        getatt = GetAttAction()
        output = getatt.resolve_resource_refs(input, self.supported_resource_refs)

        self.assertEqual(expected, output)

    @patch.object(GetAttAction, "can_handle")
    def test_return_value_if_cannot_handle(self, can_handle_mock):
        input = {"Fn::GetAtt": ["id1", "prop1"]}
        expected = {"Fn::GetAtt": ["id1", "prop1"]}

        getatt = GetAttAction()
        can_handle_mock.return_value = False  # Simulate failure to handle the input. Result should be same as input
        self.assertEqual(expected, getatt.resolve_resource_refs(input, self.supported_resource_refs))


class TestGetAttCanResolveResourceIdRefs(TestCase):
    def setUp(self):
        self.supported_resource_id_refs = {}
        self.supported_resource_id_refs["id1"] = "value1"

    def test_must_resolve_simple_refs(self):
        input = {"Fn::GetAtt": ["id1", "Arn"]}

        expected = {"Fn::GetAtt": ["value1", "Arn"]}

        getatt = GetAttAction()
        output = getatt.resolve_resource_id_refs(input, self.supported_resource_id_refs)

        self.assertEqual(expected, output)

    def test_must_resolve_refs_with_many_attributes(self):
        input = {"Fn::GetAtt": ["id1", "Arn1", "Arn2", "Arn3"]}

        expected = {"Fn::GetAtt": ["value1", "Arn1", "Arn2", "Arn3"]}

        getatt = GetAttAction()
        output = getatt.resolve_resource_id_refs(input, self.supported_resource_id_refs)

        self.assertEqual(expected, output)

    def test_must_ignore_invalid_value_array(self):
        input = {
            # No actual attributes
            "Fn::GetAtt": ["id1"]
        }

        expected = {"Fn::GetAtt": ["id1"]}

        getatt = GetAttAction()
        output = getatt.resolve_resource_id_refs(input, self.supported_resource_id_refs)

        self.assertEqual(expected, output)

    def test_must_ignore_invalid_value_type(self):
        input = {
            # No actual attributes
            "Fn::GetAtt": {"a": "b"}
        }

        expected = {"Fn::GetAtt": {"a": "b"}}

        getatt = GetAttAction()
        output = getatt.resolve_resource_id_refs(input, self.supported_resource_id_refs)

        self.assertEqual(expected, output)

    def test_must_ignore_missing_properties_with_dot_before(self):
        input = {"Fn::GetAtt": [".id1", "foo"]}
        expected = {"Fn::GetAtt": [".id1", "foo"]}

        getatt = GetAttAction()
        output = getatt.resolve_resource_id_refs(input, self.supported_resource_id_refs)

        self.assertEqual(expected, output)

    @patch.object(GetAttAction, "can_handle")
    def test_return_value_if_cannot_handle(self, can_handle_mock):
        input = {"Fn::GetAtt": ["id1", "Arn"]}
        expected = {"Fn::GetAtt": ["id1", "Arn"]}

        getatt = GetAttAction()
        can_handle_mock.return_value = False  # Simulate failure to handle the input. Result should be same as input
        self.assertEqual(expected, getatt.resolve_resource_id_refs(input, self.supported_resource_id_refs))


class TestFindInMapCanResolveParameterRefs(TestCase):
    def setUp(self):
        self.ref = FindInMapAction()

    @patch.object(FindInMapAction, "can_handle")
    def test_cannot_handle(self, can_handle_mock):
        input = {"Fn::FindInMap": ["a", "b", "c"]}
        can_handle_mock.return_value = False
        output = self.ref.resolve_parameter_refs(input, {})

        self.assertEqual(input, output)

    def test_value_not_list(self):
        input = {"Fn::FindInMap": "a string"}
        with self.assertRaises(InvalidDocumentException):
            self.ref.resolve_parameter_refs(input, {})

    def test_value_not_list_of_length_three(self):
        input = {"Fn::FindInMap": ["a string"]}

        with self.assertRaises(InvalidDocumentException):
            self.ref.resolve_parameter_refs(input, {})

    def test_mapping_not_string(self):
        mappings = {"MapA": {"TopKey1": {"SecondKey2": "value3"}, "TopKey2": {"SecondKey1": "value4"}}}
        input = {"Fn::FindInMap": [["MapA"], "TopKey2", "SecondKey1"]}
        output = self.ref.resolve_parameter_refs(input, mappings)

        self.assertEqual(input, output)

    def test_top_level_key_not_string(self):
        mappings = {"MapA": {"TopKey1": {"SecondKey2": "value3"}, "TopKey2": {"SecondKey1": "value4"}}}
        input = {"Fn::FindInMap": ["MapA", ["TopKey2"], "SecondKey1"]}
        output = self.ref.resolve_parameter_refs(input, mappings)

        self.assertEqual(input, output)

    def test_second_level_key_not_string(self):
        mappings = {"MapA": {"TopKey1": {"SecondKey2": "value3"}, "TopKey2": {"SecondKey1": "value4"}}}
        input = {"Fn::FindInMap": ["MapA", "TopKey1", ["SecondKey2"]]}
        output = self.ref.resolve_parameter_refs(input, mappings)

        self.assertEqual(input, output)

    def test_mapping_not_found(self):
        mappings = {"MapA": {"TopKey1": {"SecondKey2": "value3"}, "TopKey2": {"SecondKey1": "value4"}}}
        input = {"Fn::FindInMap": ["MapB", "TopKey2", "SecondKey1"]}
        output = self.ref.resolve_parameter_refs(input, mappings)

        self.assertEqual(input, output)

    def test_top_level_key_not_found(self):
        mappings = {"MapA": {"TopKey1": {"SecondKey2": "value3"}, "TopKey2": {"SecondKey1": "value4"}}}
        input = {"Fn::FindInMap": ["MapA", "TopKey3", "SecondKey1"]}
        output = self.ref.resolve_parameter_refs(input, mappings)

        self.assertEqual(input, output)

    def test_second_level_key_not_found(self):
        mappings = {"MapA": {"TopKey1": {"SecondKey2": "value3"}, "TopKey2": {"SecondKey1": "value4"}}}
        input = {"Fn::FindInMap": ["MapA", "TopKey1", "SecondKey1"]}
        output = self.ref.resolve_parameter_refs(input, mappings)

        self.assertEqual(input, output)

    def test_one_level_find_in_mappings(self):
        mappings = {"MapA": {"TopKey1": {"SecondKey2": "value3"}, "TopKey2": {"SecondKey1": "value4"}}}
        input = {"Fn::FindInMap": ["MapA", "TopKey2", "SecondKey1"]}
        expected = "value4"
        output = self.ref.resolve_parameter_refs(input, mappings)

        self.assertEqual(expected, output)

    def test_nested_find_in_mappings(self):
        mappings = {"MapA": {"TopKey1": {"SecondKey2": "value3"}, "TopKey2": {"SecondKey1": "TopKey1"}}}
        input = {"Fn::FindInMap": ["MapA", {"Fn::FindInMap": ["MapA", "TopKey2", "SecondKey1"]}, "SecondKey2"]}
        expected = "value3"
        output = self.ref.resolve_parameter_refs(input, mappings)

        self.assertEqual(expected, output)

    def test_nested_find_in_multiple_mappings(self):
        mappings = {"MapA": {"ATopKey1": {"ASecondKey2": "value3"}}, "MapB": {"BTopKey1": {"BSecondKey2": "ATopKey1"}}}
        input = {"Fn::FindInMap": ["MapA", {"Fn::FindInMap": ["MapB", "BTopKey1", "BSecondKey2"]}, "ASecondKey2"]}
        expected = "value3"
        output = self.ref.resolve_parameter_refs(input, mappings)

        self.assertEqual(expected, output)
