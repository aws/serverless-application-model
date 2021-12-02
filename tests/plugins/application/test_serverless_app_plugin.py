import boto3
import itertools
from botocore.exceptions import ClientError

from mock import Mock, patch
from unittest import TestCase
from parameterized import parameterized, param

from samtranslator.plugins.application.serverless_app_plugin import ServerlessAppPlugin
from samtranslator.plugins.exceptions import InvalidPluginException
from samtranslator.model.exceptions import InvalidResourceException

# TODO: run tests when AWS CLI is not configured (so they can run in brazil)

MOCK_TEMPLATE_URL = "https://awsserverlessrepo-changesets-xxx.s3.amazonaws.com/pre-signed-url"
MOCK_TEMPLATE_ID = "id-xx-xx"
STATUS_ACTIVE = "ACTIVE"
STATUS_PREPARING = "PREPARING"
STATUS_EXPIRED = "EXPIRED"


def mock_create_cloud_formation_template(ApplicationId=None, SemanticVersion=None):
    message = {
        "ApplicationId": ApplicationId,
        "SemanticVersion": SemanticVersion,
        "Status": STATUS_ACTIVE,
        "TemplateId": MOCK_TEMPLATE_ID,
        "TemplateUrl": MOCK_TEMPLATE_URL,
    }
    return message


def mock_get_application(ApplicationId=None, SemanticVersion=None):
    message = {
        "ApplicationId": ApplicationId,
        "Author": "AWS",
        "Description": "Application description",
        "Name": "application-name",
        "ParameterDefinitions": [{"Name": "Parameter1", "ReferencedByResources": ["resource1"], "Type": "String"}],
        "SemanticVersion": SemanticVersion,
    }
    return message


def mock_get_cloud_formation_template(ApplicationId=None, TemplateId=None):
    message = {
        "ApplicationId": ApplicationId,
        "SemanticVersion": "1.0.0",
        "Status": STATUS_ACTIVE,
        "TemplateId": TemplateId,
        "TemplateUrl": MOCK_TEMPLATE_URL,
    }
    return message


def mock_get_region(self, service_name, region_name):
    return "us-east-1"


class TestServerlessAppPlugin_init(TestCase):
    def setUp(self):
        client = boto3.client("serverlessrepo", region_name="us-east-1")
        self.plugin = ServerlessAppPlugin(sar_client=client)

    def test_plugin_must_setup_correct_name(self):
        # Name is the class name
        expected_name = "ServerlessAppPlugin"
        self.assertEqual(self.plugin.name, expected_name)

    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_plugin_default_values(self):
        self.assertEqual(self.plugin._wait_for_template_active_status, False)
        self.assertEqual(self.plugin._validate_only, False)
        self.assertTrue(self.plugin._sar_client is not None)
        # For some reason, `isinstance` or comparing classes did not work here
        self.assertEqual(str(self.plugin._sar_client.__class__), str(boto3.client("serverlessrepo").__class__))

    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_plugin_accepts_different_sar_client(self):
        client = boto3.client("serverlessrepo", endpoint_url="https://example.com")
        self.plugin = ServerlessAppPlugin(sar_client=client)
        self.assertEqual(self.plugin._sar_client, client)
        self.assertEqual(self.plugin._sar_client._endpoint, client._endpoint)

    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_plugin_accepts_flags(self):
        self.plugin = ServerlessAppPlugin(wait_for_template_active_status=True)
        self.assertEqual(self.plugin._wait_for_template_active_status, True)

    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_plugin_invalid_configuration_raises_exception(self):
        with self.assertRaises(InvalidPluginException):
            plugin = ServerlessAppPlugin(wait_for_template_active_status=True, validate_only=True)

    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_plugin_accepts_parameters(self):
        parameters = {"a": "b"}
        self.plugin = ServerlessAppPlugin(parameters=parameters)
        self.assertEqual(self.plugin._parameters, parameters)


class TestServerlessAppPlugin_on_before_transform_template_translate(TestCase):
    def setUp(self):
        client = boto3.client("serverlessrepo", region_name="us-east-1")
        self.plugin = ServerlessAppPlugin(sar_client=client)

    @patch("samtranslator.plugins.application.serverless_app_plugin.SamTemplate")
    @patch("botocore.client.BaseClient._make_api_call", mock_create_cloud_formation_template)
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_must_process_applications(self, SamTemplateMock):

        self.plugin = ServerlessAppPlugin(sar_client=boto3.client("serverlessrepo"))
        template_dict = {"a": "b"}
        app_resources = [
            ("id1", ApplicationResource(app_id="id1")),
            ("id2", ApplicationResource(app_id="id2")),
            ("id3", ApplicationResource()),
        ]

        sam_template = Mock()
        SamTemplateMock.return_value = sam_template
        sam_template.iterate = Mock()
        sam_template.iterate.return_value = app_resources

        self.plugin.on_before_transform_template(template_dict)

        SamTemplateMock.assert_called_with(template_dict)

        # Make sure this is called only for Apis
        sam_template.iterate.assert_called_with({"AWS::Serverless::Application"})

    @patch("samtranslator.plugins.application.serverless_app_plugin.SamTemplate")
    @patch("botocore.client.BaseClient._make_api_call", mock_get_application)
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_must_process_applications_validate(self, SamTemplateMock):

        self.plugin = ServerlessAppPlugin(validate_only=True)
        template_dict = {"a": "b"}
        app_resources = [
            ("id1", ApplicationResource(app_id="id1")),
            ("id2", ApplicationResource(app_id="id2")),
            ("id3", ApplicationResource()),
        ]

        sam_template = Mock()
        SamTemplateMock.return_value = sam_template
        sam_template.iterate = Mock()
        sam_template.iterate.return_value = app_resources

        self.plugin.on_before_transform_template(template_dict)

        SamTemplateMock.assert_called_with(template_dict)

        # Make sure this is called only for Apis
        sam_template.iterate.assert_called_with({"AWS::Serverless::Application"})

    @patch("samtranslator.plugins.application.serverless_app_plugin.SamTemplate")
    @patch("botocore.client.BaseClient._make_api_call", mock_create_cloud_formation_template)
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_process_invalid_applications(self, SamTemplateMock):
        self.plugin = ServerlessAppPlugin(sar_client=boto3.client("serverlessrepo", region_name="us-east-1"))
        template_dict = {"a": "b"}
        app_resources = [
            ("id1", ApplicationResource(app_id="")),
            ("id2", ApplicationResource(app_id=None)),
            ("id3", ApplicationResource(app_id="id3", semver=None)),
        ]

        sam_template = Mock()
        SamTemplateMock.return_value = sam_template
        sam_template.iterate = Mock()
        sam_template.iterate.return_value = app_resources

        self.plugin.on_before_transform_template(template_dict)

        SamTemplateMock.assert_called_with(template_dict)

        # Make sure this is called only for Apis
        sam_template.iterate.assert_called_with({"AWS::Serverless::Application"})

    @patch("samtranslator.plugins.application.serverless_app_plugin.SamTemplate")
    @patch("botocore.client.BaseClient._make_api_call", mock_get_application)
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_process_invalid_applications_validate(self, SamTemplateMock):
        self.plugin = ServerlessAppPlugin(validate_only=True)
        template_dict = {"a": "b"}
        app_resources = [
            ("id1", ApplicationResource(app_id="")),
            ("id2", ApplicationResource(app_id=None)),
            ("id3", ApplicationResource(app_id="id3", semver=None)),
        ]

        sam_template = Mock()
        SamTemplateMock.return_value = sam_template
        sam_template.iterate = Mock()
        sam_template.iterate.return_value = app_resources

        self.plugin.on_before_transform_template(template_dict)

        SamTemplateMock.assert_called_with(template_dict)

        # Make sure this is called only for Apis
        sam_template.iterate.assert_called_with({"AWS::Serverless::Application"})

    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_sar_service_calls(self):
        service_call_lambda = mock_get_application
        logical_id = "logical_id"
        app_id = "app_id"
        semver = "1.0.0"
        response = self.plugin._sar_service_call(service_call_lambda, logical_id, app_id, semver)
        self.assertEqual(app_id, response["ApplicationId"])

    def test_resolve_intrinsics(self):
        self.plugin = ServerlessAppPlugin(parameters={"AWS::Region": "us-east-1"})
        mappings = {"MapA": {"us-east-1": {"SecondLevelKey1": "value1"}}}
        input = {"Fn::FindInMap": ["MapA", {"Ref": "AWS::Region"}, "SecondLevelKey1"]}
        intrinsic_resolvers = self.plugin._get_intrinsic_resolvers(mappings)
        output = self.plugin._resolve_location_value(input, intrinsic_resolvers)

        self.assertEqual("value1", output)


class ApplicationResource(object):
    def __init__(self, app_id="app_id", semver="1.3.5"):
        self.properties = {"ApplicationId": app_id, "SemanticVersion": semver}


# class TestServerlessAppPlugin_on_before_transform_resource(TestCase):

#    def setUp(self):
#        self.plugin = ServerlessAppPlugin()

# TODO: test this lifecycle event

# @parameterized.expand(
#   itertools.product([
#       ServerlessAppPlugin(),
#       ServerlessAppPlugin(wait_for_template_active_status=True),
#   ])
# )
# @patch("samtranslator.plugins.application.serverless_app_plugin.SamTemplate")
# @patch('botocore.client.BaseClient._make_api_call', mock_create_cloud_formation_template)
# def test_process_invalid_applications(self, plugin, SamTemplateMock):
#     self.plugin = plugin
#     template_dict = {"a": "b"}
#     app_resources = [("id1", ApplicationResource(app_id = '')), ("id2", ApplicationResource(app_id=None))]

#     sam_template = Mock()
#     SamTemplateMock.return_value = sam_template
#     sam_template.iterate = Mock()
#     sam_template.iterate.return_value = app_resources

#     self.plugin.on_before_transform_template(template_dict)

#     self.plugin.on_before_transform_resource(app_resources[0][0], 'AWS::Serverless::Application', app_resources[0][1].properties)


class TestServerlessAppPlugin_on_after_transform_template(TestCase):
    def test_sar_throttling_doesnt_stop_processing(self):
        client = Mock()
        client.get_cloud_formation_template = Mock()
        client.get_cloud_formation_template.side_effect = ClientError(
            {"Error": {"Code": "TooManyRequestsException"}}, "GetCloudFormationTemplate"
        )
        plugin = ServerlessAppPlugin(sar_client=client, wait_for_template_active_status=True, validate_only=False)
        plugin._get_sleep_time_sec = Mock()
        plugin._get_sleep_time_sec.return_value = 0.02
        plugin._in_progress_templates = [("appid", "template"), ("appid2", "template2")]
        plugin.TEMPLATE_WAIT_TIMEOUT_SECONDS = 0.2
        with self.assertRaises(InvalidResourceException):
            plugin.on_after_transform_template("template")
        # confirm we had at least two attempts to call SAR and that we executed a sleep
        self.assertGreater(client.get_cloud_formation_template.call_count, 1)
        self.assertGreaterEqual(plugin._get_sleep_time_sec.call_count, 1)

    def test_unexpected_sar_error_stops_processing(self):
        client = Mock()
        client.get_cloud_formation_template = Mock()
        client.get_cloud_formation_template.side_effect = ClientError(
            {"Error": {"Code": "BadBadError"}}, "GetCloudFormationTemplate"
        )
        plugin = ServerlessAppPlugin(sar_client=client, wait_for_template_active_status=True, validate_only=False)
        plugin._in_progress_templates = [("appid", "template")]
        with self.assertRaises(ClientError):
            plugin.on_after_transform_template("template")

    def test_sar_success_one_app(self):
        client = Mock()
        client.get_cloud_formation_template = Mock()
        client.get_cloud_formation_template.return_value = {"Status": STATUS_ACTIVE}
        plugin = ServerlessAppPlugin(sar_client=client, wait_for_template_active_status=True, validate_only=False)
        plugin._in_progress_templates = [("appid", "template")]
        plugin.on_after_transform_template("template")
        # should have exactly one call to SAR
        self.assertEqual(client.get_cloud_formation_template.call_count, 1)

    def test_sar_success_two_apps(self):
        client = Mock()
        client.get_cloud_formation_template = Mock()
        client.get_cloud_formation_template.return_value = {"Status": STATUS_ACTIVE}
        plugin = ServerlessAppPlugin(sar_client=client, wait_for_template_active_status=True, validate_only=False)
        plugin._in_progress_templates = [("appid1", "template1"), ("appid2", "template2")]
        plugin.on_after_transform_template("template")
        # should have exactly one call to SAR per app
        self.assertEqual(client.get_cloud_formation_template.call_count, 2)

    def test_expired_sar_app_throws(self):
        client = Mock()
        client.get_cloud_formation_template = Mock()
        client.get_cloud_formation_template.return_value = {"Status": STATUS_EXPIRED}
        plugin = ServerlessAppPlugin(sar_client=client, wait_for_template_active_status=True, validate_only=False)
        plugin._in_progress_templates = [("appid1", "template1"), ("appid2", "template2")]
        with self.assertRaises(InvalidResourceException):
            plugin.on_after_transform_template("template")
        # should have exactly one call to SAR since the first app will be expired
        self.assertEqual(client.get_cloud_formation_template.call_count, 1)

    def test_sleep_between_sar_checks(self):
        client = Mock()
        client.get_cloud_formation_template = Mock()
        client.get_cloud_formation_template.side_effect = [{"Status": STATUS_PREPARING}, {"Status": STATUS_ACTIVE}]
        plugin = ServerlessAppPlugin(sar_client=client, wait_for_template_active_status=True, validate_only=False)
        plugin._in_progress_templates = [("appid1", "template1")]
        plugin._get_sleep_time_sec = Mock()
        plugin._get_sleep_time_sec.return_value = 0.001
        plugin.on_after_transform_template("template")
        # should have exactly two calls to SAR
        self.assertEqual(client.get_cloud_formation_template.call_count, 2)
        self.assertEqual(plugin._get_sleep_time_sec.call_count, 1)  # make sure we slept once
