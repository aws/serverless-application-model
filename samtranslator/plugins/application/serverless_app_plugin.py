import copy
import json
import logging
from time import sleep
from typing import Any, Callable, Dict, List, Optional, Tuple

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import ClientError, EndpointConnectionError

from samtranslator.intrinsics.actions import FindInMapAction
from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.plugins import BasePlugin
from samtranslator.plugins.exceptions import InvalidPluginException
from samtranslator.public.sdk.resource import SamResourceType
from samtranslator.public.sdk.template import SamTemplate
from samtranslator.region_configuration import RegionConfiguration
from samtranslator.utils.constants import BOTO3_CONNECT_TIMEOUT
from samtranslator.validator.value_validator import sam_expect

LOG = logging.getLogger(__name__)

PLUGIN_METRICS_PREFIX = "Plugin-ServerlessApp"


class ServerlessAppPlugin(BasePlugin):
    """
    Resolves all the ApplicationId and Semantic Version pairs
    for AWS::Serverless::Application to template URLs.

    To retrieve a template from the Serverless Application Repository (SAR),
    this plugin needs to call the CreateCloudFormationTemplate API, which
    initiates the process of creating and copying the application template and
    all of its assets from the region it is in to the current region. This
    API returns a pre-signed S3 url that can be passed to CFN. When the template
    reaches ACTIVE status, all assets have been successfully copied and are
    ready to be deployed. This plugin verfies that applications are in an
    ACTIVE state by calling the GetCloudFormation API from SAR.
    """

    SUPPORTED_RESOURCE_TYPE = "AWS::Serverless::Application"
    SLEEP_TIME_SECONDS = 2
    # CloudFormation times out on transforms after 2 minutes, so setting this
    # timeout below that to leave some buffer
    TEMPLATE_WAIT_TIMEOUT_SECONDS = 105
    APPLICATION_ID_KEY = "ApplicationId"
    SEMANTIC_VERSION_KEY = "SemanticVersion"
    LOCATION_KEY = "Location"
    TEMPLATE_URL_KEY = "TemplateUrl"

    def __init__(
        self,
        sar_client: Optional[BaseClient] = None,
        wait_for_template_active_status: bool = False,
        validate_only: bool = False,
        parameters: Optional[Dict[str, Any]] = None,
        sar_client_creator: Optional[Callable[[], BaseClient]] = None,
    ) -> None:
        """
        Initialize the plugin.

        Explain that Validate_only uses a different API call, and does not produce a valid template.
        :param boto3.client sar_client: The boto3 client to use to access the Serverless Application Repository
        :param bool wait_for_template_active_status: Flag to wait for all templates to become active
        :param bool validate_only: Flag to only validate application access (uses get_application API instead)
        :param bool sar_client_creator: A function to return a SAR client.
                                        Only used when sar_client is None and SAR calls are made.
        """
        super().__init__()
        if parameters is None:
            parameters = {}
        self._applications: Dict[Tuple[str, str], Any] = {}
        self._in_progress_templates: List[Tuple[str, str]] = []
        self.__sar_client = sar_client
        self._sar_client_creator = sar_client_creator
        self._wait_for_template_active_status = wait_for_template_active_status
        self._validate_only = validate_only
        self._parameters = parameters
        self._total_wait_time = 0

        # make sure the flag combination makes sense
        if self._validate_only is True and self._wait_for_template_active_status is True:
            message = "Cannot set both validate_only and wait_for_template_active_status flags to True."
            raise InvalidPluginException(ServerlessAppPlugin.__name__, message)

    @property
    def _sar_client(self) -> BaseClient:
        # Lazy initialization of the client-create it when it is needed
        if not self.__sar_client:
            if self._sar_client_creator:
                self.__sar_client = self._sar_client_creator()
            else:
                # a SAR call could take a while to finish, leaving the read_timeout default (60s).
                client_config = Config(connect_timeout=BOTO3_CONNECT_TIMEOUT)
                self.__sar_client = boto3.client("serverlessrepo", config=client_config)
        return self.__sar_client

    @staticmethod
    def _make_app_key(app_id: Any, semver: Any) -> Tuple[str, str]:
        """Generate a key that is always hashable."""
        return json.dumps(app_id, default=str), json.dumps(semver, default=str)

    @cw_timer(prefix=PLUGIN_METRICS_PREFIX)
    def on_before_transform_template(self, template_dict):  # type: ignore[no-untyped-def]
        """
        Hook method that gets called before the SAM template is processed.
        The template has passed the validation and is guaranteed to contain a non-empty "Resources" section.

        This plugin needs to run as soon as possible to allow some time for templates to become available.
        This verifies that the user has access to all specified applications.

        :param dict template_dict: Dictionary of the SAM template
        """
        template = SamTemplate(template_dict)
        intrinsic_resolvers = self._get_intrinsic_resolvers(template_dict.get("Mappings", {}))  # type: ignore[no-untyped-call]

        service_call = None
        service_call = (
            self._handle_get_application_request if self._validate_only else self._handle_create_cfn_template_request
        )
        for logical_id, app in template.iterate({SamResourceType.Application.value}):
            if not self._can_process_application(app):  # type: ignore[no-untyped-call]
                # Handle these cases in the on_before_transform_resource event
                continue

            app_id = self._replace_value(  # type: ignore[no-untyped-call]
                app.properties[self.LOCATION_KEY], self.APPLICATION_ID_KEY, intrinsic_resolvers
            )

            semver = self._replace_value(  # type: ignore[no-untyped-call]
                app.properties[self.LOCATION_KEY], self.SEMANTIC_VERSION_KEY, intrinsic_resolvers
            )

            key = self._make_app_key(app_id, semver)

            if isinstance(app_id, dict) or isinstance(semver, dict):
                self._applications[key] = False
                continue

            if key not in self._applications:
                try:
                    # Examine the type of ApplicationId and SemanticVersion
                    # before calling SAR API.
                    sam_expect(app_id, logical_id, "Location.ApplicationId").to_be_a_string()
                    sam_expect(semver, logical_id, "Location.SemanticVersion").to_be_a_string()
                    if not RegionConfiguration.is_service_supported("serverlessrepo"):  # type: ignore[no-untyped-call]
                        raise InvalidResourceException(
                            logical_id, "Serverless Application Repository is not available in this region."
                        )
                    self._make_service_call_with_retry(service_call, app_id, semver, key, logical_id)  # type: ignore[no-untyped-call]
                except InvalidResourceException as e:
                    # Catch all InvalidResourceExceptions, raise those in the before_resource_transform target.
                    self._applications[key] = e

    def _make_service_call_with_retry(self, service_call, app_id, semver, key, logical_id):  # type: ignore[no-untyped-def]
        call_succeeded = False
        while self._total_wait_time < self.TEMPLATE_WAIT_TIMEOUT_SECONDS:
            try:
                service_call(app_id, semver, key, logical_id)
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "TooManyRequestsException":
                    LOG.debug(f"SAR call timed out for application id {app_id}")
                    sleep_time = self._get_sleep_time_sec()
                    sleep(sleep_time)
                    self._total_wait_time += sleep_time
                    continue
                raise e
            call_succeeded = True
            break
        if not call_succeeded:
            raise InvalidResourceException(logical_id, "Failed to call SAR, timeout limit exceeded.")

    def _replace_value(self, input_dict, key, intrinsic_resolvers):  # type: ignore[no-untyped-def]
        value = self._resolve_location_value(input_dict.get(key), intrinsic_resolvers)  # type: ignore[no-untyped-call]
        input_dict[key] = value
        return value

    def _get_intrinsic_resolvers(self, mappings):  # type: ignore[no-untyped-def]
        return [
            IntrinsicsResolver(self._parameters),
            IntrinsicsResolver(mappings, {FindInMapAction.intrinsic_name: FindInMapAction()}),
        ]

    def _resolve_location_value(self, value, intrinsic_resolvers):  # type: ignore[no-untyped-def]
        resolved_value = copy.deepcopy(value)
        for intrinsic_resolver in intrinsic_resolvers:
            resolved_value = intrinsic_resolver.resolve_parameter_refs(resolved_value)
        return resolved_value

    def _can_process_application(self, app):  # type: ignore[no-untyped-def]
        """
        Determines whether or not the on_before_transform_template event can process this application

        :param dict app: the application and its properties
        """
        return (
            self.LOCATION_KEY in app.properties
            and isinstance(app.properties[self.LOCATION_KEY], dict)
            and self.APPLICATION_ID_KEY in app.properties[self.LOCATION_KEY]
            and app.properties[self.LOCATION_KEY][self.APPLICATION_ID_KEY] is not None
            and self.SEMANTIC_VERSION_KEY in app.properties[self.LOCATION_KEY]
            and app.properties[self.LOCATION_KEY][self.SEMANTIC_VERSION_KEY] is not None
        )

    def _handle_get_application_request(self, app_id, semver, key, logical_id):  # type: ignore[no-untyped-def]
        """
        Method that handles the get_application API call to the serverless application repo

        This method puts something in the `_applications` dictionary because the plugin expects
        something there in a later event.

        :param string app_id: ApplicationId
        :param string semver: SemanticVersion
        :param string key: The dictionary key consisting of (ApplicationId, SemanticVersion)
        :param string logical_id: the logical_id of this application resource
        """
        LOG.info(f"Getting application {app_id}/{semver} from serverless application repo...")
        try:
            self._sar_service_call(self._get_application, logical_id, app_id, semver)
            self._applications[key] = {"Available"}
            LOG.info(f"Finished getting application {app_id}/{semver}.")
        except EndpointConnectionError as e:
            # No internet connection. Don't break verification, but do show a warning.
            warning_message = f"{e}. Unable to verify access to {app_id}/{semver}."
            LOG.warning(warning_message)
            self._applications[key] = {"Unable to verify"}

    def _handle_create_cfn_template_request(self, app_id, semver, key, logical_id):  # type: ignore[no-untyped-def]
        """
        Method that handles the create_cloud_formation_template API call to the serverless application repo

        :param string app_id: ApplicationId
        :param string semver: SemanticVersion
        :param string key: The dictionary key consisting of (ApplicationId, SemanticVersion)
        :param string logical_id: the logical_id of this application resource
        """
        LOG.info(f"Requesting to create CFN template {app_id}/{semver} in serverless application repo...")
        response = self._sar_service_call(self._create_cfn_template, logical_id, app_id, semver)

        LOG.info(f"Requested to create CFN template {app_id}/{semver} in serverless application repo.")
        self._applications[key] = response[self.TEMPLATE_URL_KEY]
        if response["Status"] != "ACTIVE":
            self._in_progress_templates.append((response[self.APPLICATION_ID_KEY], response["TemplateId"]))

    def _sanitize_sar_str_param(self, param):  # type: ignore[no-untyped-def]
        """
        Sanitize SAR API parameter expected to be a string.

        If customer passes something like 1.0 as SemanticVersion, python
        converts it to a float instead of a basestring, so need to explicitly
        convert it for API calls to SAR that expect a string input.

        :param object param: Parameter to sanitize
        """
        if param is None:
            # str(None) returns 'None' so need to explicitly handle this case
            return None
        return str(param)

    @cw_timer(prefix=PLUGIN_METRICS_PREFIX)
    def on_before_transform_resource(self, logical_id, resource_type, resource_properties):  # type: ignore[no-untyped-def]
        """
        Hook method that gets called before "each" SAM resource gets processed

        Replaces the ApplicationId and Semantic Version pairs with a TemplateUrl.

        :param string logical_id: Logical ID of the resource being processed
        :param string resource_type: Type of the resource being processed
        :param dict resource_properties: Properties of the resource
        """

        if not self._resource_is_supported(resource_type):  # type: ignore[no-untyped-call]
            return

        # Sanitize properties
        self._check_for_dictionary_key(logical_id, resource_properties, [self.LOCATION_KEY])  # type: ignore[no-untyped-call]

        # If location isn't a dictionary, don't modify the resource.
        if not isinstance(resource_properties[self.LOCATION_KEY], dict):
            resource_properties[self.TEMPLATE_URL_KEY] = resource_properties[self.LOCATION_KEY]
            return

        # If it is a dictionary, check for other required parameters
        self._check_for_dictionary_key(  # type: ignore[no-untyped-call]
            logical_id, resource_properties[self.LOCATION_KEY], [self.APPLICATION_ID_KEY, self.SEMANTIC_VERSION_KEY]
        )

        app_id = resource_properties[self.LOCATION_KEY].get(self.APPLICATION_ID_KEY)
        app_id = sam_expect(app_id, logical_id, "ApplicationId").to_not_be_none()

        if isinstance(app_id, dict):
            raise InvalidResourceException(
                logical_id,
                "Property 'ApplicationId' cannot be resolved. Only FindInMap "
                "and Ref intrinsic functions are supported.",
            )

        semver = resource_properties[self.LOCATION_KEY].get(self.SEMANTIC_VERSION_KEY)

        if not semver:
            raise InvalidResourceException(logical_id, "Property 'SemanticVersion' cannot be blank.")

        if isinstance(semver, dict):
            raise InvalidResourceException(
                logical_id,
                "Property 'SemanticVersion' cannot be resolved. Only FindInMap "
                "and Ref intrinsic functions are supported.",
            )

        key = self._make_app_key(app_id, semver)

        # Throw any resource exceptions saved from the before_transform_template event
        if isinstance(self._applications[key], InvalidResourceException):
            raise self._applications[key]

        # validation does not resolve an actual template url
        if not self._validate_only:
            resource_properties[self.TEMPLATE_URL_KEY] = self._applications[key]

    def _check_for_dictionary_key(self, logical_id, dictionary, keys):  # type: ignore[no-untyped-def]
        """
        Checks a dictionary to make sure it has a specific key. If it does not, an
        InvalidResourceException is thrown.

        :param string logical_id: logical id of this resource
        :param dict dictionary: the dictionary to check
        :param list keys: list of keys that should exist in the dictionary
        """
        for key in keys:
            if key not in dictionary:
                raise InvalidResourceException(logical_id, f"Resource is missing the required [{key}] property.")

    @cw_timer(prefix=PLUGIN_METRICS_PREFIX)
    def on_after_transform_template(self, template):  # type: ignore[no-untyped-def]
        """
        Hook method that gets called after the template is processed

        Go through all the stored applications and make sure they're all ACTIVE.

        :param dict template: Dictionary of the SAM template
        """
        if not self._wait_for_template_active_status or self._validate_only:
            return

        while self._total_wait_time < self.TEMPLATE_WAIT_TIMEOUT_SECONDS:
            # Check each resource to make sure it's active
            LOG.info("Checking resources in serverless application repo...")
            idx = 0
            while idx < len(self._in_progress_templates):
                application_id, template_id = self._in_progress_templates[idx]

                try:
                    response = self._sar_service_call(
                        self._get_cfn_template, application_id, application_id, template_id
                    )
                except ClientError as e:
                    error_code = e.response["Error"]["Code"]
                    if error_code == "TooManyRequestsException":
                        LOG.debug(f"SAR call timed out for application id {application_id}")
                        break  # We were throttled by SAR, break out to a sleep
                    raise e

                if self._is_template_active(response, application_id, template_id):
                    self._in_progress_templates.remove((application_id, template_id))
                else:
                    idx += 1  # check next template

            LOG.info("Finished checking resources in serverless application repo.")

            # Don't sleep if there are no more templates with PREPARING status
            if len(self._in_progress_templates) == 0:
                break

            # Sleep a little so we don't spam service calls
            sleep_time = self._get_sleep_time_sec()
            sleep(sleep_time)
            self._total_wait_time += sleep_time

        # Not all templates reached active status
        if len(self._in_progress_templates) != 0:
            application_ids = [items[0] for items in self._in_progress_templates]
            raise InvalidResourceException(
                application_ids, "Timed out waiting for nested stack templates to reach ACTIVE status."
            )

    def _get_sleep_time_sec(self) -> int:
        return self.SLEEP_TIME_SECONDS

    def _is_template_active(self, response: Dict[str, Any], application_id: str, template_id: str) -> bool:
        """
        Checks the response from a SAR service call; returns True if the template is active,
        throws an exception if the request expired and returns False in all other cases.

        :param dict response: the response dictionary from the app repo
        :param string application_id: the ApplicationId
        :param string template_id: the unique TemplateId for this application
        """
        status: str = response["Status"]  # options: PREPARING, EXPIRED or ACTIVE

        if status == "EXPIRED":
            message = (
                f"Template for {application_id} with id {template_id} returned status: {status}. "
                "Cannot access an expired template."
            )
            raise InvalidResourceException(application_id, message)

        return status == "ACTIVE"

    @cw_timer(prefix="External", name="SAR")
    def _sar_service_call(self, service_call_lambda, logical_id, *args):  # type: ignore[no-untyped-def]
        """
        Handles service calls and exception management for service calls
        to the Serverless Application Repository.

        :param lambda service_call_lambda: lambda function that contains the service call
        :param string logical_id: Logical ID of the resource being processed
        :param list *args: arguments for the service call lambda
        """
        try:
            response = service_call_lambda(*args)
            return response
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ("AccessDeniedException", "NotFoundException"):
                raise InvalidResourceException(logical_id, e.response["Error"]["Message"]) from e
            raise e

    def _resource_is_supported(self, resource_type):  # type: ignore[no-untyped-def]
        """
        Is this resource supported by this plugin?

        :param string resource_type: Type of the resource
        :return: True, if this plugin supports this resource. False otherwise
        """
        return resource_type == self.SUPPORTED_RESOURCE_TYPE

    def _get_application(self, app_id, semver):  # type: ignore[no-untyped-def]
        return self._sar_client.get_application(  # type: ignore[attr-defined]
            ApplicationId=self._sanitize_sar_str_param(app_id), SemanticVersion=self._sanitize_sar_str_param(semver)  # type: ignore[no-untyped-call]
        )

    def _create_cfn_template(self, app_id, semver):  # type: ignore[no-untyped-def]
        return self._sar_client.create_cloud_formation_template(  # type: ignore[attr-defined]
            ApplicationId=self._sanitize_sar_str_param(app_id), SemanticVersion=self._sanitize_sar_str_param(semver)  # type: ignore[no-untyped-call]
        )

    def _get_cfn_template(self, app_id, template_id):  # type: ignore[no-untyped-def]
        return self._sar_client.get_cloud_formation_template(  # type: ignore[attr-defined]
            ApplicationId=self._sanitize_sar_str_param(app_id),  # type: ignore[no-untyped-call]
            TemplateId=self._sanitize_sar_str_param(template_id),  # type: ignore[no-untyped-call]
        )
