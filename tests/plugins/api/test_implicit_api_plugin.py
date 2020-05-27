from unittest import TestCase
from mock import Mock, patch, call

from samtranslator.public.sdk.resource import SamResource, SamResourceType
from samtranslator.public.exceptions import InvalidEventException, InvalidResourceException, InvalidDocumentException
from samtranslator.plugins.api.implicit_rest_api_plugin import ImplicitRestApiPlugin, ImplicitApiResource
from samtranslator.public.plugins import BasePlugin

IMPLICIT_API_LOGICAL_ID = "ServerlessRestApi"


class TestImplicitRestApiPluginEndtoEnd(TestCase):
    def test_must_work_for_single_function(self):
        """
        Test the basic case of one function with a few API events
        """
        pass

    def test_must_work_with_multiple_functions(self):
        """
        Test a more advanced case of multiple functions with API events
        """
        pass

    def test_must_work_with_api_events_with_intrinsic_function(self):
        pass

    def test_must_ignore_function_without_api_events(self):
        """
        Functions without API events must not be processed
        """
        pass

    def test_must_ignore_api_events_with_restapiid(self):
        """
        API event sources that are already connected to a AWS::Serverless::Api resource must be skipped
        """
        pass

    def test_must_ignore_template_without_function(self):
        """
        Template without function resource must be unmodified
        """
        pass


class TestImplicitRestApiPlugin_init(TestCase):
    def setUp(self):
        self.plugin = ImplicitRestApiPlugin()

    def test_plugin_must_setup_correct_name(self):
        # Name is the class name
        expected_name = "ImplicitRestApiPlugin"

        self.assertEqual(self.plugin.name, expected_name)

    def test_plugin_must_be_instance_of_base_plugin_class(self):
        self.assertTrue(isinstance(self.plugin, BasePlugin))


class TestImplicitRestApiPlugin_on_before_transform_template(TestCase):
    def setUp(self):
        self.plugin = ImplicitRestApiPlugin()

        # Mock all methods but the one we are testing
        self.plugin._get_api_events = Mock()
        self.plugin._process_api_events = Mock()
        self.plugin._maybe_remove_implicit_api = Mock()

    @patch("samtranslator.plugins.api.implicit_api_plugin.SamTemplate")
    def test_must_process_functions(self, SamTemplateMock):

        template_dict = {"a": "b"}
        function1 = SamResource({"Type": "AWS::Serverless::Function"})
        function2 = SamResource({"Type": "AWS::Serverless::Function"})
        function3 = SamResource({"Type": "AWS::Serverless::Function"})
        function_resources = [("id1", function1), ("id2", function2), ("id3", function3)]
        api_events = ["event1", "event2"]

        sam_template = Mock()
        SamTemplateMock.return_value = sam_template
        sam_template.set = Mock()
        sam_template.iterate = Mock()
        sam_template.iterate.return_value = function_resources
        self.plugin._get_api_events.return_value = api_events

        self.plugin.on_before_transform_template(template_dict)

        SamTemplateMock.assert_called_with(template_dict)
        sam_template.set.assert_called_with(IMPLICIT_API_LOGICAL_ID, ImplicitApiResource().to_dict())

        # Make sure this is called only for Functions and State Machines
        sam_template.iterate.assert_any_call({"AWS::Serverless::Function", "AWS::Serverless::StateMachine"})
        sam_template.iterate.assert_any_call({"AWS::Serverless::Api"})

        self.plugin._get_api_events.assert_has_calls([call(function1), call(function2), call(function3)])
        self.plugin._process_api_events.assert_has_calls(
            [
                call(function1, ["event1", "event2"], sam_template, None),
                call(function2, ["event1", "event2"], sam_template, None),
                call(function3, ["event1", "event2"], sam_template, None),
            ]
        )

        self.plugin._maybe_remove_implicit_api.assert_called_with(sam_template)

    @patch("samtranslator.plugins.api.implicit_api_plugin.SamTemplate")
    def test_must_process_state_machines(self, SamTemplateMock):

        template_dict = {"a": "b"}
        statemachine1 = SamResource({"Type": "AWS::Serverless::StateMachine"})
        statemachine2 = SamResource({"Type": "AWS::Serverless::StateMachine"})
        statemachine3 = SamResource({"Type": "AWS::Serverless::StateMachine"})
        statemachine_resources = [("id1", statemachine1), ("id2", statemachine2), ("id3", statemachine3)]
        api_events = ["event1", "event2"]

        sam_template = Mock()
        SamTemplateMock.return_value = sam_template
        sam_template.set = Mock()
        sam_template.iterate = Mock()
        sam_template.iterate.return_value = statemachine_resources
        self.plugin._get_api_events.return_value = api_events

        self.plugin.on_before_transform_template(template_dict)

        SamTemplateMock.assert_called_with(template_dict)
        sam_template.set.assert_called_with(IMPLICIT_API_LOGICAL_ID, ImplicitApiResource().to_dict())

        # Make sure this is called only for Functions and State Machines
        sam_template.iterate.assert_any_call({"AWS::Serverless::Function", "AWS::Serverless::StateMachine"})
        sam_template.iterate.assert_any_call({"AWS::Serverless::Api"})

        self.plugin._get_api_events.assert_has_calls([call(statemachine1), call(statemachine2), call(statemachine3)])
        self.plugin._process_api_events.assert_has_calls(
            [
                call(statemachine1, ["event1", "event2"], sam_template, None),
                call(statemachine2, ["event1", "event2"], sam_template, None),
                call(statemachine3, ["event1", "event2"], sam_template, None),
            ]
        )

        self.plugin._maybe_remove_implicit_api.assert_called_with(sam_template)

    @patch("samtranslator.plugins.api.implicit_api_plugin.SamTemplate")
    def test_must_skip_functions_without_events(self, SamTemplateMock):

        template_dict = {"a": "b"}
        function1 = SamResource({"Type": "AWS::Serverless::Function"})
        function2 = SamResource({"Type": "AWS::Serverless::Function"})
        function3 = SamResource({"Type": "AWS::Serverless::Function"})
        function_resources = [("id1", function1), ("id2", function2), ("id3", function3)]
        # NO EVENTS for any function
        api_events = []

        sam_template = Mock()
        SamTemplateMock.return_value = sam_template
        sam_template.set = Mock()
        sam_template.iterate = Mock()
        sam_template.iterate.return_value = function_resources
        self.plugin._get_api_events.return_value = api_events

        self.plugin.on_before_transform_template(template_dict)

        self.plugin._get_api_events.assert_has_calls([call(function1), call(function2), call(function3)])
        self.plugin._process_api_events.assert_not_called()

        self.plugin._maybe_remove_implicit_api.assert_called_with(sam_template)

    @patch("samtranslator.plugins.api.implicit_api_plugin.SamTemplate")
    def test_must_skip_state_machines_without_events(self, SamTemplateMock):

        template_dict = {"a": "b"}
        statemachine1 = SamResource({"Type": "AWS::Serverless::StateMachine"})
        statemachine2 = SamResource({"Type": "AWS::Serverless::StateMachine"})
        statemachine3 = SamResource({"Type": "AWS::Serverless::StateMachine"})
        statemachine_resources = [("id1", statemachine1), ("id2", statemachine2), ("id3", statemachine3)]
        # NO EVENTS for any state machine
        api_events = []

        sam_template = Mock()
        SamTemplateMock.return_value = sam_template
        sam_template.set = Mock()
        sam_template.iterate = Mock()
        sam_template.iterate.return_value = statemachine_resources
        self.plugin._get_api_events.return_value = api_events

        self.plugin.on_before_transform_template(template_dict)

        self.plugin._get_api_events.assert_has_calls([call(statemachine1), call(statemachine2), call(statemachine3)])
        self.plugin._process_api_events.assert_not_called()

        self.plugin._maybe_remove_implicit_api.assert_called_with(sam_template)

    @patch("samtranslator.plugins.api.implicit_api_plugin.SamTemplate")
    def test_must_skip_without_functions_or_statemachines(self, SamTemplateMock):

        template_dict = {"a": "b"}
        # NO FUNCTIONS OR STATE MACHINES
        function_resources = []

        sam_template = Mock()
        SamTemplateMock.return_value = sam_template
        sam_template.set = Mock()
        sam_template.iterate = Mock()
        sam_template.iterate.return_value = function_resources

        self.plugin.on_before_transform_template(template_dict)

        self.plugin._get_api_events.assert_not_called()
        self.plugin._process_api_events.assert_not_called()

        # This is called always, even if there are no functions
        self.plugin._maybe_remove_implicit_api.assert_called_with(sam_template)

    @patch("samtranslator.plugins.api.implicit_api_plugin.SamTemplate")
    def test_must_collect_errors_and_raise_on_invalid_events(self, SamTemplateMock):

        template_dict = {"a": "b"}
        function_resources = [
            ("id1", SamResource({"Type": "AWS::Serverless::Function"})),
            ("id2", SamResource({"Type": "AWS::Serverless::Function"})),
            ("id3", SamResource({"Type": "AWS::Serverless::Function"})),
        ]
        api_event_errors = [
            InvalidEventException("eventid1", "msg"),
            InvalidEventException("eventid3", "msg"),
            InvalidEventException("eventid3", "msg"),
        ]

        sam_template = Mock()
        SamTemplateMock.return_value = sam_template
        sam_template.set = Mock()
        sam_template.iterate = Mock()
        sam_template.iterate.return_value = function_resources
        self.plugin._get_api_events.return_value = ["1", "2"]
        self.plugin._process_api_events.side_effect = api_event_errors

        with self.assertRaises(InvalidDocumentException) as context:
            self.plugin.on_before_transform_template(template_dict)

        # Verify the content of exception. There are two exceptions embedded one inside another
        #   InvalidDocumentException -> InvalidResourceException -> contains the msg from InvalidEventException
        causes = context.exception.causes
        self.assertEqual(3, len(causes))
        for index, cause in enumerate(causes):
            self.assertTrue(isinstance(cause, InvalidResourceException))

            # Resource's logicalID must be correctly passed
            self.assertEqual(function_resources[index][0], cause._logical_id)

            # Message must directly come from InvalidEventException
            self.assertEqual(api_event_errors[index].message, cause._message)

        # Must cleanup even if there an exception
        self.plugin._maybe_remove_implicit_api.assert_called_with(sam_template)


class TestImplicitRestApiPlugin_get_api_events(TestCase):
    def setUp(self):
        self.plugin = ImplicitRestApiPlugin()

    def test_must_get_all_api_events_in_function(self):

        properties = {
            "Events": {
                "Api1": {"Type": "Api", "Properties": {"a": "b"}},
                "Api2": {"Type": "Api", "Properties": {"c": "d"}},
                "Other": {"Type": "Something", "Properties": {}},
            }
        }

        function = SamResource({"Type": SamResourceType.Function.value, "Properties": properties})

        expected = {
            "Api1": {"Type": "Api", "Properties": {"a": "b"}},
            "Api2": {"Type": "Api", "Properties": {"c": "d"}},
        }
        result = self.plugin._get_api_events(function)
        self.assertEqual(expected, result)

    def test_must_work_with_no_api_events(self):

        properties = {
            "Events": {
                "Event1": {"Type": "some", "Properties": {"a": "b"}},
                "EventWithNoType": {"Properties": {"c": "d"}},
                "Event3": {"Type": "Something", "Properties": {}},
            }
        }

        function = SamResource({"Type": SamResourceType.Function.value, "Properties": properties})

        expected = {}
        result = self.plugin._get_api_events(function)
        self.assertEqual(expected, result)

    def test_must_skip_with_bad_events_structure(self):

        function = SamResource({"Type": SamResourceType.Function.value, "Properties": {"Events": "must not be string"}})

        expected = {}
        result = self.plugin._get_api_events(function)
        self.assertEqual(expected, result)

    def test_must_skip_if_no_events_property(self):

        function = SamResource({"Type": SamResourceType.Function.value, "Properties": {"no": "events"}})

        expected = {}
        result = self.plugin._get_api_events(function)
        self.assertEqual(expected, result)

    def test_must_skip_if_no_property_dictionary(self):

        function = SamResource({"Type": SamResourceType.Function.value, "Properties": "bad value"})

        expected = {}
        result = self.plugin._get_api_events(function)
        self.assertEqual(expected, result)

    def test_must_return_reference_to_event_dict(self):
        function = SamResource(
            {
                "Type": SamResourceType.Function.value,
                "Properties": {"Events": {"Api1": {"Type": "Api", "Properties": {"a": "b"}}}},
            }
        )

        result = self.plugin._get_api_events(function)

        # Make sure that the result contains a direct reference to Event properties.
        # This is an important contract necessary for other parts of the plugin to work.
        self.assertTrue(result["Api1"] is function.properties["Events"]["Api1"])

    def test_must_skip_if_function_is_not_valid(self):

        function = SamResource(
            {
                # NOT a SAM resource
                "Type": "AWS::Lambda::Function",
                "Properties": {"Events": {"Api1": {"Type": "Api", "Properties": {}}}},
            }
        )

        expected = {}
        result = self.plugin._get_api_events(function)
        self.assertEqual(expected, result)


class TestImplicitRestApiPlugin_process_api_events(TestCase):
    def setUp(self):
        self.plugin = ImplicitRestApiPlugin()
        self.plugin._add_api_to_swagger = Mock()
        self.plugin._add_implicit_api_id_if_necessary = Mock()

    def test_must_work_with_api_events(self):
        api_events = {
            "Api1": {"Type": "Api", "Properties": {"Path": "/", "Method": "GET"}},
            "Api2": {"Type": "Api", "Properties": {"Path": "/foo", "Method": "POST"}},
        }

        template = Mock()
        function_events_mock = Mock()
        function = SamResource({"Type": SamResourceType.Function.value, "Properties": {"Events": function_events_mock}})
        function_events_mock.update = Mock()

        self.plugin._process_api_events(function, api_events, template)

        self.plugin._add_implicit_api_id_if_necessary.assert_has_calls(
            [call({"Path": "/", "Method": "GET"}), call({"Path": "/foo", "Method": "POST"})]
        )

        self.plugin._add_api_to_swagger.assert_has_calls(
            [
                call("Api1", {"Path": "/", "Method": "GET"}, template),
                call("Api2", {"Path": "/foo", "Method": "POST"}, template),
            ]
        )

        function_events_mock.update.assert_called_with(api_events)

    def test_must_verify_expected_keys_exist(self):

        api_events = {"Api1": {"Type": "Api", "Properties": {"Path": "/", "Methid": "POST"}}}

        template = Mock()
        function_events_mock = Mock()
        function = SamResource({"Type": SamResourceType.Function.value, "Properties": {"Events": function_events_mock}})
        function_events_mock.update = Mock()

        with self.assertRaises(InvalidEventException) as context:
            self.plugin._process_api_events(function, api_events, template)

    def test_must_verify_method_is_string(self):
        api_events = {"Api1": {"Type": "Api", "Properties": {"Path": "/", "Method": ["POST"]}}}

        template = Mock()
        function_events_mock = Mock()
        function = SamResource({"Type": SamResourceType.Function.value, "Properties": {"Events": function_events_mock}})
        function_events_mock.update = Mock()

        with self.assertRaises(InvalidEventException) as context:
            self.plugin._process_api_events(function, api_events, template)

    def test_must_verify_rest_api_id_is_string(self):
        api_events = {
            "Api1": {
                "Type": "Api",
                "Properties": {
                    "Path": "/",
                    "Method": ["POST"],
                    "RestApiId": {"Fn::ImportValue": {"Fn::Sub": {"ApiName"}}},
                },
            }
        }

        template = Mock()
        function_events_mock = Mock()
        function = SamResource({"Type": SamResourceType.Function.value, "Properties": {"Events": function_events_mock}})
        function_events_mock.update = Mock()

        with self.assertRaises(InvalidEventException) as context:
            self.plugin._process_api_events(function, api_events, template)

    def test_must_verify_path_is_string(self):
        api_events = {"Api1": {"Type": "Api", "Properties": {"Path": ["/"], "Method": "POST"}}}

        template = Mock()
        function_events_mock = Mock()
        function = SamResource({"Type": SamResourceType.Function.value, "Properties": {"Events": function_events_mock}})
        function_events_mock.update = Mock()

        with self.assertRaises(InvalidEventException) as context:
            self.plugin._process_api_events(function, api_events, template)

    def test_must_skip_events_without_properties(self):

        api_events = {"Api1": {"Type": "Api"}, "Api2": {"Type": "Api", "Properties": {"Path": "/", "Method": "GET"}}}

        template = Mock()
        function = SamResource({"Type": SamResourceType.Function.value, "Properties": {"Events": api_events}})

        self.plugin._process_api_events(function, api_events, template)

        self.plugin._add_implicit_api_id_if_necessary.assert_has_calls([call({"Path": "/", "Method": "GET"})])

        self.plugin._add_api_to_swagger.assert_has_calls([call("Api2", {"Path": "/", "Method": "GET"}, template)])

    def test_must_retain_side_effect_of_modifying_events(self):
        """
        It must retain any changes made to the Event dictionary by helper methods
        """

        api_events = {
            "Api1": {"Type": "Api", "Properties": {"Path": "/", "Method": "get"}},
            "Api2": {"Type": "Api", "Properties": {"Path": "/foo", "Method": "post"}},
        }

        template = Mock()
        function = SamResource(
            {
                "Type": SamResourceType.Function.value,
                "Properties": {
                    "Events": {
                        "Api1": "Intentionally setting this value to a string for testing. "
                        "This should be replaced by API Event after processing",
                        "Api2": "must be replaced",
                    }
                },
            }
        )

        def add_key_to_event(event_properties):
            event_properties["Key"] = "Value"

        # Apply the side effect of adding a key to events dict
        self.plugin._add_implicit_api_id_if_necessary.side_effect = add_key_to_event

        self.plugin._process_api_events(function, api_events, template)

        # Side effect must be visible after call returns on the input object
        self.assertEqual(api_events["Api1"]["Properties"], {"Path": "/", "Method": "get", "Key": "Value"})
        self.assertEqual(api_events["Api2"]["Properties"], {"Path": "/foo", "Method": "post", "Key": "Value"})

        # Every Event object inside the SamResource class must be entirely replaced by input api_events with side effect
        self.assertEqual(
            function.properties["Events"]["Api1"]["Properties"], {"Path": "/", "Method": "get", "Key": "Value"}
        )
        self.assertEqual(
            function.properties["Events"]["Api2"]["Properties"], {"Path": "/foo", "Method": "post", "Key": "Value"}
        )

        # Subsequent calls must be made with the side effect. This is important.
        self.plugin._add_api_to_swagger.assert_has_calls(
            [
                call(
                    "Api1",
                    # Side effects should be visible here
                    {"Path": "/", "Method": "get", "Key": "Value"},
                    template,
                ),
                call(
                    "Api2",
                    # Side effects should be visible here
                    {"Path": "/foo", "Method": "post", "Key": "Value"},
                    template,
                ),
            ]
        )


class TestImplicitRestApiPlugin_add_implicit_api_id_if_necessary(TestCase):
    def setUp(self):
        self.plugin = ImplicitRestApiPlugin()

    def test_must_add_if_not_present(self):

        input = {"a": "b"}

        expected = {"a": "b", "RestApiId": {"Ref": IMPLICIT_API_LOGICAL_ID}}

        self.plugin._add_implicit_api_id_if_necessary(input)
        self.assertEqual(input, expected)

    def test_must_skip_if_present(self):

        input = {"a": "b", "RestApiId": "Something"}

        expected = {"a": "b", "RestApiId": "Something"}

        self.plugin._add_implicit_api_id_if_necessary(input)
        self.assertEqual(input, expected)


class TestImplicitRestApiPlugin_add_api_to_swagger(TestCase):
    def setUp(self):
        self.plugin = ImplicitRestApiPlugin()

    @patch("samtranslator.plugins.api.implicit_rest_api_plugin.SwaggerEditor")
    def test_must_add_path_method_to_swagger_of_api_resource(self, SwaggerEditorMock):
        event_id = "id"
        properties = {"RestApiId": {"Ref": "restid"}, "Path": "/hello", "Method": "GET"}
        original_swagger = {"this": "is", "valid": "swagger"}
        updated_swagger = "updated swagger"
        mock_api = SamResource(
            {
                "Type": "AWS::Serverless::Api",
                "Properties": {"__MANAGE_SWAGGER": True, "DefinitionBody": original_swagger, "a": "b"},
            }
        )

        SwaggerEditorMock.is_valid = Mock()
        SwaggerEditorMock.is_valid.return_value = True
        editor_mock = Mock()
        SwaggerEditorMock.return_value = editor_mock
        editor_mock.swagger = updated_swagger
        self.plugin.editor = SwaggerEditorMock

        template_mock = Mock()
        template_mock.get = Mock()
        template_mock.set = Mock()
        template_mock.get.return_value = mock_api

        self.plugin._add_api_to_swagger(event_id, properties, template_mock)

        SwaggerEditorMock.is_valid.assert_called_with(original_swagger)
        template_mock.get.assert_called_with("restid")
        editor_mock.add_path("/hello", "GET")
        template_mock.set.assert_called_with("restid", mock_api)
        self.assertEqual(mock_api.properties["DefinitionBody"], updated_swagger)

    @patch("samtranslator.plugins.api.implicit_rest_api_plugin.SwaggerEditor")
    def test_must_work_with_rest_api_id_as_string(self, SwaggerEditorMock):
        event_id = "id"
        properties = {
            # THIS IS A STRING, not a {"Ref"}
            "RestApiId": "restid",
            "Path": "/hello",
            "Method": "GET",
        }
        original_swagger = {"this": "is", "valid": "swagger"}
        updated_swagger = "updated swagger"
        mock_api = SamResource(
            {
                "Type": "AWS::Serverless::Api",
                "Properties": {"__MANAGE_SWAGGER": True, "DefinitionBody": original_swagger, "a": "b"},
            }
        )

        SwaggerEditorMock.is_valid = Mock()
        SwaggerEditorMock.is_valid.return_value = True
        editor_mock = Mock()
        SwaggerEditorMock.return_value = editor_mock
        editor_mock.swagger = updated_swagger
        self.plugin.editor = SwaggerEditorMock

        template_mock = Mock()
        template_mock.get = Mock()
        template_mock.set = Mock()
        template_mock.get.return_value = mock_api

        self.plugin._add_api_to_swagger(event_id, properties, template_mock)

        SwaggerEditorMock.is_valid.assert_called_with(original_swagger)
        template_mock.get.assert_called_with("restid")
        editor_mock.add_path("/hello", "GET")
        template_mock.set.assert_called_with("restid", mock_api)
        self.assertEqual(mock_api.properties["DefinitionBody"], updated_swagger)

    def test_must_raise_when_api_is_not_found(self):
        event_id = "id"
        properties = {"RestApiId": "unknown", "Path": "/hello", "Method": "GET"}

        template_mock = Mock()
        template_mock.get = Mock()
        template_mock.get.return_value = None

        with self.assertRaises(InvalidEventException) as context:
            self.plugin._add_api_to_swagger(event_id, properties, template_mock)

        self.assertEqual(event_id, context.exception._event_id)

    def test_must_raise_when_api_id_is_intrinsic(self):
        event_id = "id"
        properties = {"RestApiId": {"Fn::GetAtt": "restapi"}, "Path": "/hello", "Method": "GET"}

        template_mock = Mock()
        template_mock.get = Mock()
        template_mock.get.return_value = None

        with self.assertRaises(InvalidEventException) as context:
            self.plugin._add_api_to_swagger(event_id, properties, template_mock)

        self.assertEqual(event_id, context.exception._event_id)

    @patch("samtranslator.plugins.api.implicit_rest_api_plugin.SwaggerEditor")
    def test_must_skip_invalid_swagger(self, SwaggerEditorMock):

        event_id = "id"
        properties = {"RestApiId": {"Ref": "restid"}, "Path": "/hello", "Method": "GET"}
        original_swagger = {"this": "is", "valid": "swagger"}
        mock_api = SamResource(
            {"Type": "AWS::Serverless::Api", "Properties": {"DefinitionBody": original_swagger, "a": "b"}}
        )

        SwaggerEditorMock.is_valid = Mock()
        SwaggerEditorMock.is_valid.return_value = False
        self.plugin.editor = SwaggerEditorMock

        template_mock = Mock()
        template_mock.get = Mock()
        template_mock.set = Mock()
        template_mock.get.return_value = mock_api

        self.plugin._add_api_to_swagger(event_id, properties, template_mock)

        SwaggerEditorMock.is_valid.assert_called_with(original_swagger)
        template_mock.get.assert_called_with("restid")
        SwaggerEditorMock.assert_not_called()
        template_mock.set.assert_not_called()

    @patch("samtranslator.plugins.api.implicit_rest_api_plugin.SwaggerEditor")
    def test_must_skip_if_definition_body_is_not_present(self, SwaggerEditorMock):

        event_id = "id"
        properties = {"RestApiId": {"Ref": "restid"}, "Path": "/hello", "Method": "GET"}
        mock_api = SamResource({"Type": "AWS::Serverless::Api", "Properties": {"DefinitionUri": "s3://bucket/key"}})

        SwaggerEditorMock.is_valid = Mock()
        SwaggerEditorMock.is_valid.return_value = False
        self.plugin.editor = SwaggerEditorMock

        template_mock = Mock()
        template_mock.get = Mock()
        template_mock.set = Mock()
        template_mock.get.return_value = mock_api

        self.plugin._add_api_to_swagger(event_id, properties, template_mock)

        SwaggerEditorMock.is_valid.assert_called_with(None)
        template_mock.get.assert_called_with("restid")
        SwaggerEditorMock.assert_not_called()
        template_mock.set.assert_not_called()

    @patch("samtranslator.plugins.api.implicit_rest_api_plugin.SwaggerEditor")
    def test_must_skip_if_api_resource_properties_are_invalid(self, SwaggerEditorMock):

        event_id = "id"
        properties = {"RestApiId": {"Ref": "restid"}, "Path": "/hello", "Method": "GET"}
        mock_api = SamResource({"Type": "AWS::Serverless::Api", "Properties": "this is not a valid property"})

        SwaggerEditorMock.is_valid = Mock()
        self.plugin.editor = SwaggerEditorMock

        template_mock = Mock()
        template_mock.get = Mock()
        template_mock.set = Mock()
        template_mock.get.return_value = mock_api

        self.plugin._add_api_to_swagger(event_id, properties, template_mock)

        SwaggerEditorMock.is_valid.assert_not_called()
        template_mock.get.assert_called_with("restid")
        SwaggerEditorMock.assert_not_called()
        template_mock.set.assert_not_called()

    @patch("samtranslator.plugins.api.implicit_rest_api_plugin.SwaggerEditor")
    def test_must_skip_if_api_manage_swagger_flag_is_false(self, SwaggerEditorMock):

        event_id = "id"
        properties = {"RestApiId": {"Ref": "restid"}, "Path": "/hello", "Method": "GET"}
        original_swagger = {"this": "is a valid swagger"}
        mock_api = SamResource(
            {
                "Type": "AWS::Serverless::Api",
                "Properties": {
                    "DefinitionBody": original_swagger,
                    "StageName": "prod",
                    # Don't manage swagger
                    "__MANAGE_SWAGGER": False,
                },
            }
        )

        SwaggerEditorMock.is_valid = Mock()
        self.plugin.editor = SwaggerEditorMock

        template_mock = Mock()
        template_mock.get = Mock()
        template_mock.set = Mock()
        template_mock.get.return_value = mock_api

        self.plugin._add_api_to_swagger(event_id, properties, template_mock)

        SwaggerEditorMock.is_valid.assert_called_with(original_swagger)
        template_mock.get.assert_called_with("restid")
        SwaggerEditorMock.assert_not_called()
        template_mock.set.assert_not_called()

    @patch("samtranslator.plugins.api.implicit_rest_api_plugin.SwaggerEditor")
    def test_must_skip_if_api_manage_swagger_flag_is_not_present(self, SwaggerEditorMock):

        event_id = "id"
        properties = {"RestApiId": {"Ref": "restid"}, "Path": "/hello", "Method": "GET"}
        original_swagger = {"this": "is a valid swagger"}
        mock_api = SamResource(
            {
                "Type": "AWS::Serverless::Api",
                "Properties": {
                    "DefinitionBody": original_swagger,
                    "StageName": "prod",
                    # __MANAGE_SWAGGER flag is *not* present
                },
            }
        )

        SwaggerEditorMock.is_valid = Mock()
        self.plugin.editor = SwaggerEditorMock

        template_mock = Mock()
        template_mock.get = Mock()
        template_mock.set = Mock()
        template_mock.get.return_value = mock_api

        self.plugin._add_api_to_swagger(event_id, properties, template_mock)

        SwaggerEditorMock.is_valid.assert_called_with(original_swagger)
        template_mock.get.assert_called_with("restid")
        SwaggerEditorMock.assert_not_called()
        template_mock.set.assert_not_called()


class TestImplicitRestApiPlugin_maybe_remove_implicit_api(TestCase):
    def setUp(self):
        self.plugin = ImplicitRestApiPlugin()

    def test_must_remove_if_no_path_present(self):
        resource = SamResource({"Type": "AWS::Serverless::Api", "Properties": {"DefinitionBody": {"paths": {}}}})
        template = Mock()
        template.get = Mock()
        template.delete = Mock()
        template.get.return_value = resource

        self.plugin._maybe_remove_implicit_api(template)
        template.get.assert_called_with(IMPLICIT_API_LOGICAL_ID)
        template.delete.assert_called_with(IMPLICIT_API_LOGICAL_ID)

    def test_must_skip_if_path_present(self):
        resource = SamResource(
            {"Type": "AWS::Serverless::Api", "Properties": {"DefinitionBody": {"paths": {"a": "b"}}}}
        )
        template = Mock()
        template.get = Mock()
        template.delete = Mock()
        template.get.return_value = resource

        self.plugin._maybe_remove_implicit_api(template)
        template.get.assert_called_with(IMPLICIT_API_LOGICAL_ID)

        # Must not delete
        template.delete.assert_not_called()

    def test_must_restore_if_existing_resource_present(self):
        resource = SamResource({"Type": "AWS::Serverless::Api", "Properties": {"DefinitionBody": {"paths": {}}}})
        template = Mock()
        template.get = Mock()
        template.set = Mock()
        template.get.return_value = resource

        self.plugin.existing_implicit_api_resource = resource
        self.plugin._maybe_remove_implicit_api(template)
        template.get.assert_called_with(IMPLICIT_API_LOGICAL_ID)

        # Must restore original resource
        template.set.assert_called_with(IMPLICIT_API_LOGICAL_ID, resource)
